package local.popupguard;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.media.AudioManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.SurfaceView;
import android.view.TextureView;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.lang.ref.WeakReference;
import java.net.URL;
import java.util.ArrayDeque;
import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.net.ssl.HttpsURLConnection;

/** Optional notices for this independent patch. Never downloads or installs files. */
final class PatchUpdateNotice implements Application.ActivityLifecycleCallbacks {
    private static final int MAX_JSON_BYTES = 256 * 1024;
    private static final long BROWSE_SETTLE_MS = 4000;
    private static PatchUpdateNotice instance;
    private final SharedPreferences preferences;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final AtomicBoolean checking = new AtomicBoolean();
    private final Set<Activity> started = Collections.newSetFromMap(new WeakHashMap<Activity, Boolean>());
    private WeakReference<Activity> foreground = new WeakReference<>(null);
    private long resumedAt;
    private AlertDialog dialog;
    private boolean postponeOnDismiss;

    static synchronized void install(Context context) {
        Context application = context.getApplicationContext();
        if (instance == null && application instanceof Application) {
            instance = new PatchUpdateNotice((Application) application);
        }
    }

    private PatchUpdateNotice(Application application) {
        preferences = application.getSharedPreferences("moviebox_patch_updates", Context.MODE_PRIVATE);
        application.registerActivityLifecycleCallbacks(this);
    }

    private final Runnable foregroundCheck = new Runnable() {
        @Override public void run() {
            Activity activity = foreground.get();
            if (activity == null) return;
            checkIfDue();
            showIfSafe(activity);
            main.postDelayed(this, 15000);
        }
    };

    private void checkIfDue() {
        long now = System.currentTimeMillis();
        if (!PatchUpdatePolicy.checkDue(preferences.getBoolean("enabled", true), now,
                preferences.getLong("last_check", 0)) || !checking.compareAndSet(false, true)) return;
        // Record attempts as well as successes; offline/rate-limited checks never loop.
        preferences.edit().putLong("last_check", now).apply();
        new Thread(new Runnable() {
            @Override public void run() {
                HttpsURLConnection connection = null;
                try {
                    connection = (HttpsURLConnection) new URL(PatchUpdatePolicy.API_URL).openConnection();
                    connection.setInstanceFollowRedirects(false);
                    connection.setConnectTimeout(8000);
                    connection.setReadTimeout(8000);
                    connection.setRequestProperty("Accept", "application/vnd.github+json");
                    connection.setRequestProperty("User-Agent", "MovieBoxAndroidPatch/" + PatchUpdatePolicy.CURRENT_VERSION);
                    if (connection.getResponseCode() != 200) return;
                    if (connection.getContentLengthLong() > MAX_JSON_BYTES) return;
                    JSONObject release;
                    long readDeadline = SystemClock.elapsedRealtime() + 20000;
                    try (InputStream stream = connection.getInputStream();
                         ByteArrayOutputStream body = new ByteArrayOutputStream()) {
                        byte[] buffer = new byte[4096];
                        int length;
                        while ((length = stream.read(buffer)) != -1) {
                            if (SystemClock.elapsedRealtime() > readDeadline) return;
                            if (body.size() + length > MAX_JSON_BYTES) return;
                            body.write(buffer, 0, length);
                        }
                        release = new JSONObject(body.toString("UTF-8"));
                    }
                    if (release.optBoolean("draft") || release.optBoolean("prerelease")) return;
                    String tag = release.optString("tag_name", "");
                    if (!PatchUpdatePolicy.newer(tag, PatchUpdatePolicy.CURRENT_VERSION)
                            || !PatchUpdatePolicy.trustedRelease(release.optString("html_url", ""), tag)) return;
                    JSONArray assets = release.optJSONArray("assets");
                    if (assets == null) return;
                    for (int i = 0; i < assets.length(); i++) {
                        JSONObject asset = assets.optJSONObject(i);
                        if (asset == null) continue;
                        String download = asset.optString("browser_download_url", "");
                        if (PatchUpdatePolicy.trustedDownload(download, tag)) {
                            preferences.edit().putString("pending_tag", tag)
                                    .putString("pending_url", download).apply();
                            main.post(new Runnable() {
                                @Override public void run() {
                                    Activity current = foreground.get();
                                    if (current != null) showIfSafe(current);
                                }
                            });
                            break;
                        }
                    }
                } catch (Exception ignored) {
                    // Optional connectivity must never affect opening or playing the app.
                } finally {
                    if (connection != null) connection.disconnect();
                    checking.set(false);
                }
            }
        }, "moviebox-patch-release-check").start();
    }

    private boolean safeToPrompt(Activity activity) {
        try {
            if (foreground.get() != activity || !PatchUpdatePolicy.eligibleActivity(activity.getClass().getName())
                    || activity.isFinishing() || activity.isDestroyed() || !activity.hasWindowFocus()
                    || activity.isInPictureInPictureMode() || activity.isInMultiWindowMode()
                    || SystemClock.uptimeMillis() - resumedAt < BROWSE_SETTLE_MS
                    || started.size() != 1 || !started.contains(activity)) return false;
            AudioManager audio = (AudioManager) activity.getSystemService(Context.AUDIO_SERVICE);
            if (audio == null || audio.isMusicActive()) return false;
            // Includes muted in-app/PIP video when a visible rendering surface exists.
            ArrayDeque<View> views = new ArrayDeque<>();
            views.add(activity.getWindow().getDecorView());
            int visited = 0;
            while (!views.isEmpty()) {
                if (++visited > 1600) return false;
                View view = views.removeFirst();
                if (!view.isAttachedToWindow() || !view.isShown()) continue;
                if (view instanceof SurfaceView || view instanceof TextureView) return false;
                if (view instanceof ViewGroup) {
                    ViewGroup group = (ViewGroup) view;
                    for (int i = 0; i < group.getChildCount(); i++) views.add(group.getChildAt(i));
                }
            }
            return true;
        } catch (RuntimeException uncertainState) {
            return false;
        }
    }

    private void showIfSafe(final Activity activity) {
        if (dialog != null || !preferences.getBoolean("enabled", true)) return;
        final String tag = preferences.getString("pending_tag", "");
        final String download = preferences.getString("pending_url", "");
        if (!PatchUpdatePolicy.shouldNotify(tag, preferences.getString("skipped_version", ""),
                System.currentTimeMillis(), preferences.getLong("later_until", 0))
                || !PatchUpdatePolicy.trustedDownload(download, tag) || !safeToPrompt(activity)) return;
        final CheckBox enabled = new CheckBox(activity);
        enabled.setText("Check for patch updates daily");
        enabled.setChecked(true);
        int padding = (int) (20 * activity.getResources().getDisplayMetrics().density);
        LinearLayout content = new LinearLayout(activity);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(padding, padding / 2, padding, 0);
        TextView message = new TextView(activity);
        message.setText("Independent MovieBox patch " + PatchUpdatePolicy.version(tag)
                + " is available on GitHub. Updating is optional. Download opens your browser; nothing is installed automatically.");
        content.addView(message);
        content.addView(enabled);
        postponeOnDismiss = true;
        dialog = new AlertDialog.Builder(activity).setTitle("Optional patch update")
                .setView(content)
                .setPositiveButton("Download", (which, button) -> {
                    saveChoice(enabled, false);
                    postpone();
                    try {
                        activity.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(download))
                                .addCategory(Intent.CATEGORY_BROWSABLE));
                    } catch (RuntimeException noBrowser) {
                        // Keep the notice optional even if no browser can open this URL.
                    }
                })
                .setNegativeButton("Later", (which, button) -> saveChoice(enabled, false))
                .setNeutralButton("Skip this version", (which, button) -> {
                    saveChoice(enabled, true);
                    preferences.edit().putString("skipped_version", PatchUpdatePolicy.version(tag)).apply();
                })
                .create();
        dialog.setCanceledOnTouchOutside(true);
        dialog.setCancelable(true);
        dialog.setOnDismissListener(which -> {
            preferences.edit().putBoolean("enabled", enabled.isChecked()).apply();
            if (postponeOnDismiss) postpone();
            dialog = null;
        });
        try {
            dialog.show();
        } catch (RuntimeException unavailableWindow) {
            dialog = null;
        }
    }

    private void saveChoice(CheckBox enabled, boolean skipped) {
        preferences.edit().putBoolean("enabled", enabled.isChecked()).apply();
        postponeOnDismiss = !skipped;
    }

    private void postpone() {
        preferences.edit().putLong("later_until", System.currentTimeMillis() + PatchUpdatePolicy.DAY_MS).apply();
    }

    @Override public void onActivityCreated(Activity activity, Bundle state) {}
    @Override public void onActivityStarted(Activity activity) { started.add(activity); }
    @Override public void onActivityResumed(Activity activity) {
        foreground = new WeakReference<>(activity);
        resumedAt = SystemClock.uptimeMillis();
        main.removeCallbacks(foregroundCheck);
        main.postDelayed(foregroundCheck, BROWSE_SETTLE_MS);
    }
    @Override public void onActivityPaused(Activity activity) {
        if (foreground.get() == activity) {
            foreground.clear();
            main.removeCallbacks(foregroundCheck);
            if (dialog != null) {
                // Navigating to playback cancels the notice without counting as Later.
                postponeOnDismiss = false;
                dialog.dismiss();
            }
        }
    }
    @Override public void onActivityStopped(Activity activity) { started.remove(activity); }
    @Override public void onActivitySaveInstanceState(Activity activity, Bundle state) {}
    @Override public void onActivityDestroyed(Activity activity) { started.remove(activity); }
}
