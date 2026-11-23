"""Read-only environment preflight; never installs dependencies or starts builds."""
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
missing = []
print('Platform:', platform.system(), platform.machine())
print('Python:', platform.python_version())

def require(tool):
    found = shutil.which(tool)
    print(tool + ':', 'available' if found else 'MISSING')
    if not found:
        missing.append(tool)
    return found

require('git')
for package in [root / 'package.json', root / 'frontend/package.json', root / 'proxy/package.json']:
    if package.exists():
        require('node')
        data = json.loads(package.read_text(encoding='utf-8-sig'))
        manager = data.get('packageManager', 'npm').split('@')[0]
        require(manager)
        print('Package:', package.relative_to(root), 'engines:', data.get('engines', 'not pinned'))
        print('Scripts:', ', '.join(data.get('scripts', {})) or 'none')
        print('Lockfile:', 'present' if any((package.parent / n).exists() for n in ['package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lock', 'bun.lockb']) else 'MISSING; install resolution is not fully reproducible')
for requirements in root.glob('*requirements*.txt'):
    print('Dependencies:', requirements.name, '(use an isolated virtual environment)')
if (root / 'gradlew').exists():
    require('java')
    if not require('javac'):
        print('Android builds need a full JDK, not just a JRE.')
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    local = root / 'local.properties'
    configured = local.exists() and any(line.strip().startswith('sdk.dir=') for line in local.read_text(encoding='utf-8').splitlines())
    if sdk and pathlib.Path(sdk).is_dir():
        print('Android SDK: environment configured; verify required SDK/build-tools versions in LOCAL_DEVELOPMENT.md')
    elif configured:
        print('Android SDK: local.properties configured; Gradle must validate the path')
    else:
        missing.append('Android SDK configuration')
        print('Android SDK: MISSING; set ANDROID_HOME or local.properties sdk.dir')
    print('Gradle wrapper: use gradlew.bat on Windows; bash gradlew on Linux/macOS')
if (root / 'Core/Package.swift').exists():
    require('swift')
    print('Apple SDK builds require macOS + Xcode. Other hosts can edit source; use the existing manual Mac workflow if necessary.')
if (root / 'build.ps1').exists():
    print('Windows packaging:', 'supported host' if sys.platform == 'win32' else 'requires Windows; use a compatible machine or existing manual workflow')
print('Preflight:', 'missing: ' + ', '.join(sorted(set(missing))) if missing else 'basic tools found; dependency installation and application tests still required')
sys.exit(1 if missing else 0)
