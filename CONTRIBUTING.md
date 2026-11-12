# Contributing

This is a patch-only project. Keep the upstream APK, generated APKs, signing
keys, certificate passwords, phone data and runtime captures outside the repo.
Use the exact input artifact identified in the README and preserve package and
certificate compatibility when preparing an update for an existing installation.

Run the source/manifest regression tests before submitting a change. Describe
which checks were static and which were observed on Android. Do not claim that
all advertising is removed: that is not implemented or verified by this patch.

Keep startup-fault handling narrowly scoped to the documented fault and thread.
Do not change login, membership or service-access behavior.
