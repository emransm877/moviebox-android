# Local development

Clone this repository and work from its root. Development checks run locally by default; GitHub remains the source host and retains necessary production automation.

## Environment

Run `python tools/local_doctor.py` (`python3` on systems where that is the Python 3 command). This read-only preflight detects the host and basic tools; it does not install dependencies or certify a build. Use the project's supported runtime versions below and existing lockfiles. Do not upgrade dependencies just to run checks.

For Python, create an isolated environment with `python -m venv .venv`. Use `.venv/Scripts/python.exe` on Windows and `.venv/bin/python` on Linux/macOS for installation and checks (activation is optional). Replace `python` below with that interpreter. Existing pinned requirements remain authoritative. Where requirements contain ranges, exact historical dependency resolution is not guaranteed; record a tested lock separately before upgrading.

For Node projects with package-lock.json use `npm ci`; without a lockfile use `npm install` and review the generated lock before committing. Use the declared packageManager if present. Native SDKs and first dependency downloads need internet access. Local-first does not make external APIs or production services offline.

## Repository commands

Use Python 3.11+ and JDK 17 for source checks. Run `python -m unittest discover -s tests -v`, `python tools/check_release.py`, and `python tools/check_docs.py`. Rebuilding the patched APK additionally requires the exact reviewed external source APK, Android SDK/NDK tools and your external signing key: inspect `python tools/build.py --help` and the existing build documentation. Do not commit source APKs or signing material. A generic Gradle build is not applicable to this patch project.

## Existing hosted command reference

These are the pre-migration commands for reproducing checks locally. Use the correct host shell (PowerShell paths on Windows, Bash on Unix); install requirements from the workflow. Publishing commands are intentionally excluded.

### check.yml / unit-tests

```text
python -m unittest discover -s tests -v
python tools/check_release.py
python tools/check_docs.py
python - <<'PY'
from pathlib import Path
forbidden = {'.apk', '.aab', '.apks', '.keystore', '.jks', '.p12', '.pfx', '.dex', '.so', '.class'}
files = [p for p in Path('.').rglob('*') if p.is_file() and '.git' not in p.parts and p.suffix.lower() in forbidden]
assert not files, f'Private or binary artifacts must not be tracked: {files}'
PY

```


## Automation and releases

Development workflows are manual fallbacks; select Run workflow in GitHub only when local execution is impractical. Retained production workflows keep their existing triggers and approval gates. Existing release downloads are unaffected by changing development triggers. Manual workflow artifacts expire after the retention shown in each workflow and are not durable release downloads.

Before pushing a workflow change, inspect current branch protection/rulesets and preserve required check names or coordinate their replacement. A manual workflow does not automatically satisfy required PR checks. Never weaken protection merely to make a push pass.

Rollback: inspect the migration commit with `git show <migration-commit>`, then `git revert <migration-commit>` and push under normal repository policy. Reverting automatic triggers may start cloud jobs; review the resulting diff first. Avoid reverting later production state or historical statistics. Account billing and Actions permissions were not changed.

For a new project, choose its existing/native tooling, record supported runtime versions, commit an appropriate dependency lock and environment example without secrets, define local validation commands and platform limits, and classify any proposed cloud automation before adding it. Do not copy an unrelated stack's build script.
