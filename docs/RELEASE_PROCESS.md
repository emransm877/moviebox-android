# Android patch release checklist

The published patch and development source versions are recorded separately in
`release.json`. Upstream APK version fields are preserved and are not the patch
release number. Do not change package or signing identity for routine upgrades.

1. Run `python -m unittest discover -s tests -v` and `python tools/check_release.py`.
2. Build only from the pinned external source APK with the documented toolchain.
   Keep the proprietary input and signing keystore outside Git. Confirm applicable
   redistribution permissions for the derived artifact; MIT project source does
   not license upstream code or application assets.
3. Verify alignment and APK signature, compare signing-certificate digests with
   the previous release, and run the builder's `--upgrade-from` compatibility check.
4. Test the exact candidate APK on a real supported phone: fresh launch; browsing;
   playback; pause/resume; background/foreground; known update dialog; Back;
   optional notices deferred during video; Later/Skip/opt-out; and in-place upgrade
   with saved data retained. Record the device, Android version and APK SHA-256.
5. Keep unsupported or untested devices and behaviors explicit. Source compilation
   and synthetic-manifest tests do not certify protected-app runtime behavior.
6. Prepare release notes, artifact hashes and known issues. Discuss the concrete
   candidate with the maintainer before publishing; there is no automatic release
   publication workflow.
7. After approval, attach the exact reviewed APK and checksum to the release.
   Update `published_version`, declared assets and README together. Verify existing
   downloads with `python tools/check_release.py --online`.

Do not silently replace published APKs or create replacement signing keys. Never
commit an APK, original vendor payload, keystore or signing password to this repo.
