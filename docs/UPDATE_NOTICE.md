# Optional patch release notice (0.2.0)

This notice concerns releases of the independent patch repository, not the
upstream MovieBox application's update service. It does not change the existing
forced-update dialog matcher or the ARM64 startup helper.

## Reviewed activity boundary

The pinned original APK's binary manifest declares
`com.transsion.subroom.activity.MainActivity` and
`com.transsion.subroom.activity.SplashActivity`; recovered DEX class metadata
also includes the main activity and separate movie-detail/video-detail classes.
Only the exact main activity is allowlisted. Splash, detail, player, and unknown
activities are excluded. Static names alone cannot prove every playback path.

`PatchUpdateNotice` therefore also requires a resumed, focused, settled activity,
exactly one started activity, no picture-in-picture or multiwindow mode, no active
music, and no visible `SurfaceView` or `TextureView`. A bounded view scan that
cannot establish safety defers. A pause dismisses the notice without treating
navigation as a user choice. No player activity is modified or launched.

These are conservative safeguards. Actual playback, silent video, background
playback, picture-in-picture, rotations, and prompt dismissal still need a device
test of this protected APK; no device was connected for source validation.

## Release trust and scheduling

- Background request: `https://api.github.com/repos/emransm877/moviebox-android/releases/latest`.
- Standard HTTPS certificate validation; API redirects are not followed.
- Stable numeric version tags only (`0.3.0` or `v0.3.0`), strictly newer than the
  patch's compiled version. Drafts and prereleases are ignored.
- The release page must belong to the exact repository and tag. Its asset must
  be exactly `https://github.com/emransm877/moviebox-android/releases/download/TAG/MovieBox-Android-VERSION.apk`.
  Userinfo, custom ports, queries, fragments, encoded/alternate paths, other
  repositories, and other hosts fail validation.
- Response size is bounded to 256 KiB; connect/read waits are limited and an
  additional body-reading deadline applies. Failures do not affect playback.
- Attempts, including offline/rate-limited attempts, are limited to daily while
  the app runs. No alarms, service, wake lock, or runtime permission are added.
- No MovieBox account data, device ID, or signing secret is sent to GitHub.

The latest public release observed during source review was `v0.1.0`, with the
expected APK asset naming. Version 0.2.0 correctly ignores that older release.
A future-update flow is covered by policy fixtures, not a fabricated public release.

## Choices and private preferences

The framework dialog is cancelable by Back or outside touch. Later and ordinary
dismissal postpone for 24 hours. Skip stores the normalized version; a later
newer version can still be offered. Download opens the validated URL through a
browser intent and postpones the notice. The patch has no file downloader,
installer invocation, or automatic installation path.

The checkbox stores an `enabled` preference in the patched app's private
`moviebox_patch_updates` preferences. Unchecking disables subsequent checks and
notices. This minimal integration has no separate settings/re-enable screen;
the checkbox is available only when a new release notice is shown.

## Validation boundary

The source tests execute the actual platform-independent Java policy for version
ordering, release/download URL validation, daily scheduling, skip/later choices,
and the activity allowlist. Other tests verify project version consistency and
the unchanged native helper hash. The full Android Java source compiles against
API 35 with JDK 17, targeting Java 8.

The 0.2.0 APK was rebuilt and signed with the same certificate as 0.1.0; signature
verification, 16 KiB ZIP alignment, Java compilation and 15 source tests passed.
Its original manifest, protected payload and native helper were preserved.
No phone was connected for this revision, so runtime UI, installation and
protected-app compatibility remain separate checks before claiming device support.
