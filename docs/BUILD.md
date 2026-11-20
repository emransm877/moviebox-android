# Build the reviewed Android patch

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

See [the findings](REVERSE_ENGINEERING.md) for the evidence boundary and the
reason the original protected DEX header's nonstandard SHA-1 bytes are preserved.
See [third-party notices](../THIRD_PARTY_NOTICES.md) for distribution boundaries.

This project is not affiliated with or endorsed by MovieBox, its developers, or
its service operators. MovieBox names and application assets belong to their
respective owners. The MIT license applies only to the patch source and tooling
authored for this project, not to the original or derived application.
