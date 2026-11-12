# Findings and limits

## Reviewed target

The reviewed source package is `com.community.mbox.in.geobypass`, version
`4.0.03.0930.03`, version code `52120132`. Its pinned APK SHA-256 is recorded in
`project.json`. This project accepts only that artifact; it does not infer that
another APK with the same displayed version has equivalent behavior.

The original target already contains protected code, third-party libraries, and
prior modifications. The project's Android patches were built and observed as a
separate package, `com.community.mbox.in.popupfree`, to preserve isolation from the
source package.

## Update dialog

The observed forced-update prompt was a noncancelable application dialog titled
“New Version Released.” Back, outside touch, and picture-in-picture did not remove
it reliably. The patch's non-exported startup provider scans application window
views every 500 ms, with a bounded traversal per window. It requires both the
known title and one of the known upgrade messages.

Only a matching `TYPE_APPLICATION` dialog is changed. The provider removes dimming,
sets it non-focusable and non-touchable, and makes that window transparent. It
does not remove every dialog or alter the video activity's base window.

Earlier runtime evidence:

- Original prompt remained visible in picture-in-picture:
  `ev_e068a561f35a6ab2db1e01acfb8ed390b81b1dfad3273aefd1b3eb61d0b4c1ad`.
- Patched copy was observed playing without that prompt:
  `ev_89a4560bff85b0d80e22ead5ac8ff8765e35565fb79098d09c776feb07071af4`.

These observations concern specific sessions, not every future server response.
The English string match does not establish support for every translation.

## Protected startup behavior

The isolated clone initially encountered an ARM64 native startup fault: `SIGBUS`
at address `0xa01` on a non-main thread, with an invalid ordinary stack pointer.
The small native helper installs a raw kernel signal action using the existing
alternate stack. It exits only that narrowly identified faulting thread and
chains other faults to the prior handler. It does not broadly swallow crashes.

This low-level behavior is specific to the observed protected build and ARM64
runtime. It needs revalidation before supporting a new upstream artifact or
architecture.

## APK construction

The binary manifest receives a non-exported `ContentProvider`; the source package
reference is replaced by the same-length isolated package name. Existing resource
and loader package references are updated consistently. The provider is compiled
as a secondary DEX, and the ARM64 helper is added as a stored native library.

The protected source DEX has an intentionally nonstandard SHA-1 header. Normalizing
that field caused startup failures in earlier experiments. The build therefore
preserves bytes 12–31 and recalculates only Adler-32 after the same-length loader
package replacement. This exception applies only to the pinned input and is not
a recommendation for ordinary DEX rebuilding.

The resulting APK is zip-aligned for 16 KiB pages, signed with the caller's
external key, and verified with `apksigner` and independent manifest parsing.
The source version and SDK declarations are preserved. No permissions are added
or removed; the package-scoped receiver permission follows the package rename.
The private signing key is never rewritten. The runtime patch itself requires
ARM64 and API 29+.

## What is not established

- No comprehensive advertising removal was implemented or verified by this patch.
- The source APK's complete protected behavior, analytics, and network activity
  were not audited by this project.
- The renamed release artifact's label and signature can be verified statically;
  that does not replace an installation and playback check.
- Retaining a package and certificate permits an in-place update but cannot
  guarantee the upstream app will never change its own stored data.
