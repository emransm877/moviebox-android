package local.popupguard;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.view.inspector.WindowInspector;
import android.widget.TextView;
import java.util.ArrayDeque;

/** Only hides the identified update dialog; it does not intercept other dialogs. */
public final class GuardProvider extends ContentProvider {
    private static native int installNativeGuard();
    private static native int nativeGuardEvents();
    private boolean nativeReady;
    private int lastNativeEvents;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable scan = new Runnable() {
        @Override public void run() {
            try {
                if (nativeReady) {
                    int count = nativeGuardEvents();
                    if (count != lastNativeEvents) {
                        Log.i("PopupGuard", "Isolated startup fault handled: " + count);
                        lastNativeEvents = count;
                    }
                }
                for (View root : WindowInspector.getGlobalWindowViews()) {
                    if (root.getAlpha() == 0f || !root.isAttachedToWindow()) continue;
                    boolean title = false, message = false;
                    ArrayDeque<View> views = new ArrayDeque<>();
                    views.add(root);
                    int visited = 0;
                    while (!views.isEmpty() && visited++ < 1200) {
                        View view = views.removeFirst();
                        if (view instanceof TextView) {
                            String text = ((TextView) view).getText().toString();
                            title |= text.trim().equalsIgnoreCase("New Version Released");
                            message |= text.contains("recommend upgrading to the latest version")
                                    || text.contains("If the update fails, please uninstall");
                        }
                        if (view instanceof ViewGroup) {
                            ViewGroup group = (ViewGroup) view;
                            for (int i = 0; i < group.getChildCount(); i++) views.add(group.getChildAt(i));
                        }
                    }
                    if (title && message && root.getLayoutParams() instanceof WindowManager.LayoutParams) {
                        WindowManager.LayoutParams params = (WindowManager.LayoutParams) root.getLayoutParams();
                        // Never hide the activity's base window even if it contains matching text.
                        if (params.type != WindowManager.LayoutParams.TYPE_APPLICATION) continue;
                        params.flags |= WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                                | WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;
                        params.flags &= ~WindowManager.LayoutParams.FLAG_DIM_BEHIND;
                        params.dimAmount = 0f;
                        WindowManager manager = (WindowManager) root.getContext().getSystemService("window");
                        manager.updateViewLayout(root, params);
                        root.setAlpha(0f);
                        Log.i("PopupGuard", "Suppressed identified update dialog; video window unchanged");
                    }
                }
            } catch (Throwable error) {
                Log.w("PopupGuard", "Dialog scan failed", error);
            } finally {
                handler.postDelayed(this, 500);
            }
        }
    };
    @Override public boolean onCreate() {
        try {
            System.loadLibrary("popupguard");
            int result = installNativeGuard();
            nativeReady = result == 0;
            Log.i("PopupGuard", "Native startup guard status: " + result);
        } catch (Throwable error) {
            Log.w("PopupGuard", "Native startup guard unavailable", error);
        }
        Log.i("PopupGuard", "Guard initialized in " + getContext().getPackageName());
        handler.post(scan);
        return true;
    }
    @Override public Cursor query(Uri uri, String[] projection, String selection, String[] args, String sort) { return null; }
    @Override public String getType(Uri uri) { return null; }
    @Override public Uri insert(Uri uri, ContentValues values) { return null; }
    @Override public int delete(Uri uri, String where, String[] args) { return 0; }
    @Override public int update(Uri uri, ContentValues values, String where, String[] args) { return 0; }
}
