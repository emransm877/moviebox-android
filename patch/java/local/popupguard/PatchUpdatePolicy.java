package local.popupguard;

import java.net.URI;
import java.net.URISyntaxException;

/** Platform-independent release validation and scheduling rules. */
public final class PatchUpdatePolicy {
    public static final String CURRENT_VERSION = "0.2.0";
    public static final String REPOSITORY = "emransm877/moviebox-android";
    public static final String API_URL = "https://api.github.com/repos/" + REPOSITORY + "/releases/latest";
    public static final String BROWSE_ACTIVITY = "com.transsion.subroom.activity.MainActivity";
    public static final long DAY_MS = 24L * 60 * 60 * 1000;

    private PatchUpdatePolicy() {}

    public static String version(String tag) {
        if (tag == null || !tag.matches("v?(0|[1-9][0-9]{0,8})\\.(0|[1-9][0-9]{0,8})\\.(0|[1-9][0-9]{0,8})")) return null;
        return tag.startsWith("v") ? tag.substring(1) : tag;
    }

    public static boolean newer(String candidate, String current) {
        String a = version(candidate), b = version(current);
        if (a == null || b == null) return false;
        String[] left = a.split("\\."), right = b.split("\\.");
        for (int i = 0; i < 3; i++) {
            int comparison = Integer.compare(Integer.parseInt(left[i]), Integer.parseInt(right[i]));
            if (comparison != 0) return comparison > 0;
        }
        return false;
    }

    public static boolean trustedRelease(String url, String tag) {
        return version(tag) != null && trustedPath(url, "/" + REPOSITORY + "/releases/tag/" + tag);
    }

    public static boolean trustedDownload(String url, String tag) {
        String release = version(tag);
        return release != null && trustedPath(url, "/" + REPOSITORY + "/releases/download/" + tag
                + "/MovieBox-Android-" + release + ".apk");
    }

    private static boolean trustedPath(String url, String path) {
        if (url == null) return false;
        try {
            URI uri = new URI(url);
            return "https".equals(uri.getScheme()) && "github.com".equals(uri.getHost())
                    && uri.getPort() == -1 && uri.getRawUserInfo() == null
                    && uri.getRawQuery() == null && uri.getRawFragment() == null
                    && path.equals(uri.getRawPath());
        } catch (URISyntaxException error) {
            return false;
        }
    }

    public static boolean checkDue(boolean enabled, long now, long lastCheck) {
        // Treat a backwards clock jump as one check, then establish a new baseline.
        return enabled && (lastCheck <= 0 || now < lastCheck || now - lastCheck >= DAY_MS);
    }

    public static boolean shouldNotify(String tag, String skipped, long now, long laterUntil) {
        String candidate = version(tag);
        return candidate != null && newer(candidate, CURRENT_VERSION)
                && !candidate.equals(version(skipped)) && now >= laterUntil;
    }

    public static boolean eligibleActivity(String className) {
        // An allowlist is deliberate: unknown screens and all player screens defer.
        return BROWSE_ACTIVITY.equals(className);
    }
}
