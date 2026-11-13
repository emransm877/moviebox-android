import local.popupguard.PatchUpdatePolicy;

/** Runs the actual shared policy without Android stubs or a proprietary APK. */
public final class PatchUpdatePolicyChecks {
    static void expect(boolean condition) {
        if (!condition) throw new AssertionError("Policy regression");
    }
    public static void main(String[] args) {
        String group = args[0];
        if (group.equals("versions")) {
            expect(PatchUpdatePolicy.newer("v0.3.0", "0.2.0"));
            expect(PatchUpdatePolicy.newer("0.10.0", "0.9.0"));
            expect(PatchUpdatePolicy.newer("1.0.0", "0.99.99"));
            expect(!PatchUpdatePolicy.newer("v0.2.0", "0.2.0"));
            expect(!PatchUpdatePolicy.newer("0.1.0", "0.2.0"));
            for (String invalid : new String[]{"0.3.0-beta", "0.3.0+build", "01.3.0", "0.3", "9999999999.0.0", "v0.3.0/evil", ""}) {
                expect(PatchUpdatePolicy.version(invalid) == null);
                expect(!PatchUpdatePolicy.newer(invalid, "0.2.0"));
            }
        } else if (group.equals("urls")) {
            String base = "https://github.com/emransm877/moviebox-android/releases/";
            String valid = base + "download/v0.3.0/MovieBox-Android-0.3.0.apk";
            expect(PatchUpdatePolicy.trustedDownload(valid, "v0.3.0"));
            expect(PatchUpdatePolicy.trustedRelease(base + "tag/v0.3.0", "v0.3.0"));
            for (String invalid : new String[]{valid.replace("https:", "http:"),
                    valid.replace("github.com", "github.com.evil.test"),
                    valid.replace("github.com/", "github.com@evil.test/"),
                    valid.replace("emransm877/", "somebody/"),
                    valid.replace("moviebox-android/", "another-repo/"),
                    valid.replace("0.3.0.apk", "0.2.0.apk"), valid + "?redirect=evil", valid + "#fragment",
                    valid.replace("github.com/", "github.com:444/"),
                    valid.replace("MovieBox-Android", "../MovieBox-Android"),
                    valid.replace("MovieBox-Android", "%4dovieBox-Android")}) {
                expect(!PatchUpdatePolicy.trustedDownload(invalid, "v0.3.0"));
            }
            expect(!PatchUpdatePolicy.trustedRelease("https://evil.test/releases/tag/v0.3.0", "v0.3.0"));
        } else if (group.equals("schedule")) {
            long day = PatchUpdatePolicy.DAY_MS;
            expect(PatchUpdatePolicy.checkDue(true, day * 4, 0));
            expect(PatchUpdatePolicy.checkDue(true, day * 4, day * 3));
            expect(!PatchUpdatePolicy.checkDue(true, day * 4 - 1, day * 3));
            expect(!PatchUpdatePolicy.checkDue(false, day * 4, 0));
            expect(PatchUpdatePolicy.checkDue(true, day, day * 2));
        } else if (group.equals("choices")) {
            expect(PatchUpdatePolicy.shouldNotify("v0.3.0", "", 100, 0));
            expect(!PatchUpdatePolicy.shouldNotify("v0.3.0", "0.3.0", 100, 0));
            expect(!PatchUpdatePolicy.shouldNotify("v0.3.0", "", 100, 101));
            expect(PatchUpdatePolicy.shouldNotify("v0.4.0", "0.3.0", 100, 0));
            expect(!PatchUpdatePolicy.shouldNotify("v0.2.0", "", 100, 0));
        } else if (group.equals("activity")) {
            expect(PatchUpdatePolicy.eligibleActivity("com.transsion.subroom.activity.MainActivity"));
            for (String screen : new String[]{"com.transsion.subroom.activity.SplashActivity",
                    "com.transsion.moviedetail.activity.MovieDetailActivity",
                    "com.transsion.postdetail.ui.activity.LocalVideoDetailActivity", "unknown.Player", ""}) {
                expect(!PatchUpdatePolicy.eligibleActivity(screen));
            }
        } else throw new AssertionError("Unknown group");
    }
}
