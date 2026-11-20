# Android installation and troubleshooting

This patch supports a specific upstream APK and ARM64 Android 10+ devices. A
released APK is an independently signed sideload, not an official Google Play
build. Manufacturer/OS combinations and 16 KB page-size devices are not all tested.

| Problem | What to do |
| --- | --- |
| Installation says signatures conflict | Keep the working app installed. Compare the package and signing certificate. The same patched package needs its original signing identity for an in-place update; uninstalling can erase its data. |
| Device is incompatible | Check Android version and ARM64 support. Do not assume the upstream manifest's lower minimum SDK is sufficient for this patch. |
| Android shows an installation warning | Confirm the GitHub repository, downloaded release and SHA-256. Review its limitations. Do not disable Play Protect or other security protections. |
| Update dialog reappears | Record the release, prompt language and exact text. The patch targets one known English dialog; a changed or translated prompt needs investigation. |
| Ads still appear | General advertising removal is not implemented or verified by this patch. |
| No optional patch update notice appears | Notices are limited to settled browsing activities, can be skipped/disabled, and are deferred during playback or uncertain activity state. They are not mandatory. |
| App shows the upstream version rather than 0.2.0 | The project release tag describes the patch. Upstream manifest version fields are preserved, so those fields alone do not identify the patched APK. Use its release-file hash and signing identity. |

The patched package is `com.community.mbox.in.popupfree`; it installs separately
from the reviewed source package. Source APKs and signing keys stay outside Git.
The project's MIT license covers independent patch/tooling source, not the full
derived APK. See [third-party notices](../THIRD_PARTY_NOTICES.md).

Use [the bug form](https://github.com/emransm877/moviebox-android/issues/new/choose).
Include the downloaded patch release, Android version, model, whether it was a
fresh install or update, and reproducible steps. Do not attach original APKs,
private keys, passwords, accounts, signed media URLs, device serials or full logs.
