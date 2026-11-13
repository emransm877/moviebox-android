# MovieBox (No Force Update & Adds)

An independent, patch-only Android project for a specific MovieBox APK. The built
app is named **MovieBox** in the launcher and uses package
`com.community.mbox.in.popupfree`.

The requested project title is retained verbatim. **This patch suppresses one
identified forced-update dialog; general advertising removal is not implemented
or verified.** “Adds” in the title must not be read as a verified ad-blocking claim.

## Download and install

[**Download signed Android APK**](https://github.com/emransm877/moviebox-android/releases/latest/download/MovieBox-Android-0.2.0.apk)

On an Android 10+ ARM64 phone, download the APK, open it and allow installation
from your browser or file manager when Android asks. No compiler or PC is needed.
The launcher name is **MovieBox**. This is an independent sideloaded build,
not the official app or a Google Play release. A matching `.sha256` file is
provided in Releases.

The patch targets ARM64 Android 10+; other architectures and older Android
versions are unsupported even if the original manifest permits installation.
Newer OS versions, 16 KB page-size devices and other manufacturers have not all
been tested. The renamed APK is signature-verified but still needs an additional
on-device check. Do not treat a download link as universal device certification.

For an update, keep the existing app installed: Android preserves data only when
its package and signing certificate match. An official MovieBox installation uses
a different package, so this copy installs separately. A differently signed copy
of the same patched package cannot be updated with this APK without resolving the
signing identity; do not uninstall it merely to bypass that error.

## What it changes

| Behavior | Status |
|---|---|
| “New Version Released” forced-update dialog | Matches the known English title and upgrade message, makes that dialog invisible, and lets input reach the underlying app |
| Separate package | Keeps the patched copy separate from the source package |
| Launcher label | Exactly `MovieBox` |
| ARM64 clone startup fault | Narrow workaround for the observed `SIGBUS` at address `0xa01` on a non-main thread |
| Advertising SDKs, banners, video ads | No general removal performed by this patch |
| Login, memberships, service access | No changes made by this patch |
| Patch update notice (0.2.0) | Optional daily GitHub release check; Download, Later, Skip, and a disable switch |

The dialog guard and native helper previously worked during an observed playback
session and were confirmed by the user. The renamed release build is verified
statically; it needs an additional on-device check after installation. A future
server change, translated prompt, or different APK may require a new investigation.

The 0.2.0 notice implementation has source and compile validation, not on-device
validation. Its release check runs in a background thread at most once per day
while the app is used. It contacts only the public GitHub releases API for
`emransm877/moviebox-android`; it sends no MovieBox credentials or phone identifier.
It accepts only a newer stable patch version and an exact HTTPS APK asset URL in
that repository. It never downloads or installs an APK itself.

The notice is dismissible with Back, outside touch, **Later** (24 hours), or
**Skip this version**. **Download** opens the validated GitHub asset in a browser.
Uncheck **Check for patch updates daily** in the notice to disable further checks.
That preference is local to the patched app; there is no integration into the
original app's settings screen, and this build does not add a re-enable screen.

Prompts are allowed only on the reviewed main browsing activity, after it settles
and has focus. Player/detail/splash/unknown activities, other started activities,
picture-in-picture, multiwindow, active music, and visible video surfaces defer
the notice. These conservative checks need runtime validation on the actual
protected app; uncertainty defers rather than showing a prompt.

## Supported input

Only the reviewed upstream artifact is accepted. Obtain it separately; it is not
distributed in this repository.

| Field | Required value |
|---|---|
| Source package | `com.community.mbox.in.geobypass` |
| Source version | `4.0.03.0930.03` (`52120132`) |
| Source APK SHA-256 | `600d34e28e424278ee18e4ea2c486b15b17c97e58625c9ca2410e4ef7e4c38e3` |
| Patched package | `com.community.mbox.in.popupfree` |
| Runtime supported by the patch | ARM64 Android 10 / API 29 or newer |

The input's existing SDK declarations and permission set are preserved; its
package-scoped receiver permission is renamed to match the isolated package. The patch's
API-29 runtime requirement is stricter than the source APK's declared minimum.
This is not a general-purpose APK patcher.

## Requirements

- Python 3.10 or newer; the tooling uses only the standard library.
- A full JDK 17, including `javac`.
- Android SDK Platform `android-35` and Build Tools `35.0.0` (`d8`, `zipalign`, `apksigner`).
- Zig `0.13.0`, used to compile the small ARM64 helper without installing an NDK.
- The supported source APK and a signing keystore, both stored outside this repository.

No SDK, compiler, original APK, signing key, or third-party runtime binary is
included. Tool versions are pinned in the documented build; byte-identical output
across different toolchains is not guaranteed.

## Build

From this repository on Windows PowerShell:

```powershell
python tools/build.py `
  --apk "D:\Private\moviebox-original.apk" `
  --android-sdk "$env:ANDROID_HOME" `
  --java-home "$env:JAVA_HOME" `
  --zig "D:\Tools\zig\zig.exe" `
  --keystore "D:\Private\moviebox-signing.keystore" `
  --alias "YOUR_KEY_ALIAS" `
  --upgrade-from "D:\Private\previous-patched-copy.apk" `
  --output-dir "D:\Builds\MovieBoxAndroid"
```

`--upgrade-from` is recommended when replacing an existing patched installation.
The builder checks that the package, signing-certificate digest, and version code
permit that in-place upgrade. Omit it only for a new installation signed with your
own key. A new key cannot update someone else's signed copy while retaining its data.

The builder prompts for passwords without echoing them. For noninteractive builds,
supply `MOVIEBOX_KEYSTORE_PASSWORD` and `MOVIEBOX_KEY_PASSWORD` through your local
environment or secret manager. Do not put their values in source, command-line
arguments, shell history, CI configuration, or the repository.

Keep the private keystore backed up outside Git. For a new installation you can
create your own key with `keytool -genkeypair`; let it prompt for its password.
Never replace the signing key for an existing patched installation.

The external output directory receives:

- `MovieBox-Android-0.2.0.apk` — the signed derived APK.
- `build-report.json` — package, launcher label, preserved metadata, certificate digest, checksums, and verification results.
- `SHA256SUMS.txt` — the APK checksum.
- `build-logs/` — compiler and verification logs.

Build outputs, source APKs, and keystores remain outside the publishable source
tree. The signed convenience APK is attached separately to Releases. The MIT
license covers the independently authored patch/tooling, not the upstream
application or third-party components in that APK.

## Install or update

Review `build-report.json`, then connect an authorized Android device with USB
debugging enabled:

```powershell
adb -d install -r --no-incremental "D:\Builds\MovieBoxAndroid\MovieBox-Android-0.2.0.apk"
adb -d shell am start -n com.community.mbox.in.popupfree/com.transsion.subroom.activity.SplashActivity
```

The launcher should show **MovieBox**. The `-r` update preserves app data when the
package and signing identity match. Do not uninstall a working copy to resolve a
signature mismatch: rebuild with its original key instead.

After installation, check opening the app, browsing, starting a video, returning
from the background, and the update-dialog behavior. Static verification alone
does not establish successful runtime playback on every device.

## Verify the source tooling

```powershell
python -m unittest discover -s tests -v
```

CI tests use a small synthetic manifest, not a proprietary application. An optional
local integration test also checks the real manifest when `MOVIEBOX_SOURCE_APK`
points to your external supported source APK.

## Implementation and provenance

See [the findings](docs/REVERSE_ENGINEERING.md) for the evidence boundary and the
reason the original protected DEX header's nonstandard SHA-1 bytes are preserved.
See [third-party notices](THIRD_PARTY_NOTICES.md) for distribution boundaries.

This project is not affiliated with or endorsed by MovieBox, its developers, or
its service operators. MovieBox names and application assets belong to their
respective owners. The MIT license applies only to the patch source and tooling
authored for this project, not to the original or derived application.
