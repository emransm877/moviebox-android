"""Rebuild the supported external APK with the patch and an external signing key."""
from __future__ import annotations
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib

from axml import NEW, OLD, manifest_summary, patch_manifest, replace_package

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'project.json').read_text(encoding='utf-8'))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def validate_source(path):
    digest = sha256(path)
    if digest != CONFIG['supported_source_sha256']:
        raise ValueError('Unsupported source APK. Its SHA-256 does not match the reviewed upstream artifact.')
    with zipfile.ZipFile(path) as archive:
        if 'classes2.dex' in archive.namelist():
            raise ValueError('The source already contains a secondary DEX; supply the supported original APK.')
        summary = manifest_summary(archive.read('AndroidManifest.xml'))
    if summary['package'] != OLD:
        raise ValueError('Source package does not match the supported artifact.')
    return summary


def assemble(source, output, dex, native_library):
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(output, 'w') as patched:
        for member in original.infolist():
            name = member.filename
            if name.startswith('META-INF/') and name.upper().endswith(('.RSA', '.DSA', '.EC', '.SF', '.MF')):
                continue
            data = original.read(name)
            if name == 'AndroidManifest.xml':
                data = patch_manifest(data, CONFIG['launcher_label'])
            elif name == 'resources.arsc':
                data = replace_package(data)
            elif name.endswith('.dex'):
                data = bytearray(replace_package(data))
                # SecShell deliberately uses a nonstandard SHA-1 header here.
                # Preserving bytes 12:32 is essential to this reviewed input.
                struct.pack_into('<I', data, 8, zlib.adler32(data[12:]) & 0xffffffff)
                data = bytes(data)
            patched.writestr(member, data)
        for name, path, compression in [
            ('classes2.dex', dex, zipfile.ZIP_DEFLATED),
            ('lib/arm64-v8a/libpopupguard.so', native_library, zipfile.ZIP_STORED),
        ]:
            member = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = compression
            member.external_attr = 0o644 << 16
            patched.writestr(member, Path(path).read_bytes())


def manifest_from_apk(path):
    with zipfile.ZipFile(path) as archive:
        return manifest_summary(archive.read('AndroidManifest.xml'))


def certificate_digest(text):
    match = re.search(r'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F:]+)', text)
    if not match:
        raise ValueError('apksigner did not report the signing certificate digest.')
    return match.group(1).replace(':', '').lower()


def verify_manifest(before, after):
    if after['package'] != NEW or after['label'] != CONFIG['launcher_label']:
        raise ValueError('Output package or application label is incorrect.')
    if not after['launchers'] or any(x['label'] != CONFIG['launcher_label'] for x in after['launchers']):
        raise ValueError('A launcher component does not display the requested MovieBox label.')
    for key in ['versionCode', 'versionName', 'minSdkVersion', 'targetSdkVersion']:
        if before.get(key) != after.get(key):
            raise ValueError(f'Unexpected change to {key}.')
    expected_permissions = [name.replace(OLD, NEW) if name else name for name in before['permissions']]
    if expected_permissions != after['permissions']:
        raise ValueError('Unexpected permission addition or removal.')
    providers = [provider for provider in after['providers'] if provider.get('name') == CONFIG['java_provider']]
    if len(providers) != 1 or providers[0].get('exported') is not False:
        raise ValueError('The injected provider must be present once and remain non-exported.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', required=True, type=Path, help='Supported original APK, outside this repository')
    parser.add_argument('--keystore', required=True, type=Path, help='Private signing keystore outside this repository')
    parser.add_argument('--alias', required=True, help='Signing key alias')
    parser.add_argument('--output-dir', required=True, type=Path, help='Output directory outside this repository')
    parser.add_argument('--android-sdk', type=Path, default=os.getenv('ANDROID_HOME') or os.getenv('ANDROID_SDK_ROOT'))
    parser.add_argument('--java-home', type=Path, default=os.getenv('JAVA_HOME'))
    parser.add_argument('--zig', type=Path, default=shutil.which('zig'))
    parser.add_argument('--build-tools-version', default='35.0.0')
    parser.add_argument('--platform', default='android-35')
    parser.add_argument('--upgrade-from', type=Path, help='Existing patched APK whose package/certificate must match')
    args = parser.parse_args(argv)
    for name in ['apk', 'keystore', 'output_dir']:
        if getattr(args, name).resolve().is_relative_to(ROOT):
            parser.error(f'--{name.replace("_", "-")} must point outside the publishable source tree.')
    before = validate_source(args.apk)
    for name in ['android_sdk', 'java_home', 'zig']:
        if not getattr(args, name):
            parser.error(f'--{name.replace("_", "-")} is required (or configure its environment default).')
    suffix = '.exe' if os.name == 'nt' else ''
    java = args.java_home / 'bin' / ('java' + suffix)
    javac = args.java_home / 'bin' / ('javac' + suffix)
    android_jar = args.android_sdk / 'platforms' / args.platform / 'android.jar'
    build_tools = args.android_sdk / 'build-tools' / args.build_tools_version
    apksigner = build_tools / 'lib' / 'apksigner.jar'
    zipalign = build_tools / ('zipalign' + suffix)
    for tool in [java, javac, args.zig, android_jar, apksigner, zipalign, build_tools / 'lib' / 'd8.jar', args.keystore]:
        if not tool.is_file():
            parser.error(f'Required external file was not found: {tool}')
    env = os.environ.copy()
    if not env.get('MOVIEBOX_KEYSTORE_PASSWORD'):
        env['MOVIEBOX_KEYSTORE_PASSWORD'] = getpass.getpass('Keystore password: ')
    if not env.get('MOVIEBOX_KEY_PASSWORD'):
        env['MOVIEBOX_KEY_PASSWORD'] = getpass.getpass('Key password (Enter to reuse keystore password): ') or env['MOVIEBOX_KEYSTORE_PASSWORD']
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logs = args.output_dir / 'build-logs'
    logs.mkdir(exist_ok=True)

    def run(name, command):
        result = subprocess.run([str(part) for part in command], env=env, capture_output=True, text=True, errors='replace')
        log = result.stdout + result.stderr
        (logs / (name + '.log')).write_text(log, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'{name} failed. Inspect {logs / (name + ".log")}')
        return log

    with tempfile.TemporaryDirectory(prefix='moviebox-patch-') as directory:
        work = Path(directory)
        classes, dex = work / 'classes', work / 'dex'
        classes.mkdir()
        dex.mkdir()
        native = work / 'libpopupguard.so'
        print('Compiling the reviewed ARM64 startup helper and dialog provider…')
        run('native-compile', [args.zig, 'cc', '-target', 'aarch64-linux-android', '-shared', '-fPIC', '-O2',
            '-nostdlib', '-fno-stack-protector', '-Wl,-z,max-page-size=16384', '-Wl,-z,noexecstack',
            '-Wl,-soname,libpopupguard.so', '-o', native, ROOT / 'patch/native/startup-guard.c'])
        run('java-compile', [javac, '-source', '8', '-target', '8', '-classpath', android_jar,
            '-d', classes, *sorted((ROOT / 'patch/java').rglob('*.java'))])
        run('dex-compile', [java, '-Xmx512m', '-cp', build_tools / 'lib/d8.jar', 'com.android.tools.r8.D8',
            '--lib', android_jar, '--min-api', '29', '--output', dex, *sorted(classes.rglob('*.class'))])
        unsigned, aligned = work / 'unsigned.apk', work / 'aligned.apk'
        assemble(args.apk, unsigned, dex / 'classes.dex', native)
        run('alignment', [zipalign, '-P', '16', '-f', '4', unsigned, aligned])
        signed = work / 'signed.apk'
        print('Signing with the external keystore and verifying metadata…')
        run('sign', [java, '-jar', apksigner, 'sign', '--ks', args.keystore, '--ks-key-alias', args.alias,
            '--ks-pass', 'env:MOVIEBOX_KEYSTORE_PASSWORD', '--key-pass', 'env:MOVIEBOX_KEY_PASSWORD',
            '--v4-signing-enabled', 'false', '--out', signed, aligned])
        signer = run('signature-verification', [java, '-jar', apksigner, 'verify', '--verbose', '--print-certs', signed])
        run('alignment-verification', [zipalign, '-c', '-P', '16', '4', signed])
        after = manifest_from_apk(signed)
        verify_manifest(before, after)
        digest = certificate_digest(signer)
        compatible = None
        if args.upgrade_from:
            old = manifest_from_apk(args.upgrade_from)
            old_signer = run('upgrade-baseline-verification', [java, '-jar', apksigner, 'verify', '--print-certs', args.upgrade_from])
            compatible = (old['package'] == after['package'] and certificate_digest(old_signer) == digest
                          and after['versionCode'] >= old['versionCode'])
            if not compatible:
                raise ValueError('Output does not preserve the baseline package/signing identity for an in-place upgrade.')
        output = args.output_dir / ('MovieBox-Android-' + CONFIG['patch_version'] + '.apk')
        shutil.copyfile(signed, output)
    report = {'project': CONFIG['title'], 'patch_version': CONFIG['patch_version'],
        'source_sha256': sha256(args.apk), 'output_file': output.name, 'output_sha256': sha256(output),
        'signer_certificate_sha256': digest, 'upgrade_identity_verified': compatible,
        'manifest': after, 'advertising_removal': 'Not implemented or verified by this patch',
        'validation': {'apksigner': 'passed', 'zipalign_16k': 'passed', 'metadata': 'passed'},
        'runtime_tested_for_this_build': False}
    (args.output_dir / 'build-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (args.output_dir / 'SHA256SUMS.txt').write_text(f'{report["output_sha256"]}  {output.name}\n', encoding='utf-8')
    print(f'Built: {output}\nPackage: {after["package"]}\nLauncher label: {after["label"]}\nSHA-256: {report["output_sha256"]}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, zipfile.BadZipFile) as error:
        raise SystemExit(str(error))
