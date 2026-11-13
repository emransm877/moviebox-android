# Changelog

## 0.2.0 (source prepared; on-device validation pending)

- Add an optional daily check for stable releases of this independent patch on its GitHub repository.
- Offer Download, Later, Skip this version, and disabling checks; never auto-download or install.
- Defer notices during playback or uncertain activity states; preserve the original update-dialog guard and native startup helper.
- Validate version ordering and exact repository HTTPS release/download URLs; add executable Java policy tests.

## 0.1.0

- Package the reviewed update-dialog guard and narrow ARM64 startup helper as a patch-only project.
- Set the application and inherited launcher label to exactly `MovieBox`.
- Preserve `com.community.mbox.in.popupfree` and support checking signing identity against an existing patched APK.
- Add external-input, external-key builds, metadata/signature/alignment verification, and checksum reports.
- State explicitly that comprehensive advertising removal is not implemented or verified.
