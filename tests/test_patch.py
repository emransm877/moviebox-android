"""Small manifest/DEX invariants; proprietary fixtures are not committed."""
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from axml import NO, OLD, NEW, manifest_summary, patch_manifest
from build import assemble, validate_source, verify_manifest


def synthetic_manifest():
    strings = []
    def index(text):
        if text not in strings:
            strings.append(text)
        return strings.index(text)
    android = index('http://schemas.android.com/apk/res/android')
    def start(tag, attributes=None):
        name = index(tag)
        attrs = []
        for key, value in (attributes or {}).items():
            key_index = index(key)
            if isinstance(value, str):
                raw, kind, data = index(value), 3, index(value)
            else:
                raw, kind, data = NO, 0x10, int(value)
            attrs.append(struct.pack('<IIIHBBI', android, key_index, raw, 8, 0, kind, data))
        data = b''.join(attrs)
        return (struct.pack('<HHIII', 0x102, 16, 36 + len(data), 0, NO)
            + struct.pack('<IIHHHHHH', NO, name, 20, 20, len(attrs), 0, 0, 0) + data)
    def end(tag):
        return struct.pack('<HHIII', 0x103, 16, 24, 0, NO) + struct.pack('<II', NO, index(tag))
    body = [start('manifest', {'package': OLD, 'versionCode': 52120132, 'versionName': '4.0.03.0930.03'}),
        start('uses-sdk', {'minSdkVersion': 23, 'targetSdkVersion': 35}), end('uses-sdk'),
        start('uses-permission', {'name': 'android.permission.INTERNET'}), end('uses-permission'),
        start('application', {'label': 'Original label'}),
        start('activity', {'name': 'com.example.SplashActivity'}), start('intent-filter'),
        start('action', {'name': 'android.intent.action.MAIN'}), end('action'),
        start('category', {'name': 'android.intent.category.LAUNCHER'}), end('category'),
        end('intent-filter'), end('activity'), end('application'), end('manifest')]
    values, offsets = bytearray(), []
    for text in strings:
        offsets.append(len(values))
        encoded = text.encode('utf-8')
        values += bytes([len(text), len(encoded)]) + encoded + b'\0'
    values += b'\0' * (-len(values) % 4)
    beginning = 28 + 4 * len(strings)
    pool = struct.pack('<HHIIIIII', 1, 28, beginning + len(values), len(strings), 0, 0x100, beginning, 0)
    pool += struct.pack('<' + 'I' * len(offsets), *offsets) + values
    resources = struct.pack('<HHI', 0x180, 8, 8 + 4 * len(strings)) + bytes(4 * len(strings))
    chunks = pool + resources + b''.join(body)
    return struct.pack('<HHI', 3, 8, 8 + len(chunks)) + chunks


class ManifestTests(unittest.TestCase):
    def test_exact_launcher_label_and_isolated_package(self):
        source = synthetic_manifest()
        before = manifest_summary(source)
        after = manifest_summary(patch_manifest(source))
        self.assertEqual(before['package'], OLD)
        self.assertEqual(after['package'], NEW)
        self.assertEqual(after['label'], 'MovieBox')
        self.assertEqual(after['launchers'][0]['label'], 'MovieBox')
        verify_manifest(before, after)

    def test_provider_is_not_exported_and_permissions_are_unchanged(self):
        source = synthetic_manifest()
        before, after = manifest_summary(source), manifest_summary(patch_manifest(source))
        self.assertEqual(after['permissions'], before['permissions'])
        provider = next(p for p in after['providers'] if p['name'] == 'local.popupguard.GuardProvider')
        self.assertFalse(provider['exported'])
        self.assertEqual(provider['authorities'], NEW + '.popupguard.init')

    def test_verifier_rejects_wrong_launcher_label(self):
        source = synthetic_manifest()
        before, after = manifest_summary(source), manifest_summary(patch_manifest(source))
        after['launchers'][0]['label'] = 'MovieBox Popup Test'
        with self.assertRaisesRegex(ValueError, 'launcher'):
            verify_manifest(before, after)

    def test_permission_rename_is_allowed_but_new_permissions_are_rejected(self):
        source = synthetic_manifest()
        before, after = manifest_summary(source), manifest_summary(patch_manifest(source))
        before['permissions'].append(OLD + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION')
        after['permissions'].append(NEW + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION')
        verify_manifest(before, after)
        after['permissions'].append('android.permission.READ_CONTACTS')
        with self.assertRaisesRegex(ValueError, 'permission'):
            verify_manifest(before, after)


class ConstructionTests(unittest.TestCase):
    def test_preserves_protected_sha1_and_only_normalises_adler32(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            manifest = synthetic_manifest()
            protected = bytearray(112) + OLD.encode() + b'protected-payload'
            protected[:8] = b'dex\n035\0'
            protected[12:32] = bytes(range(20))
            original, output, dex, library = [folder / name for name in ['source.apk', 'output.apk', 'guard.dex', 'guard.so']]
            dex.write_bytes(b'new-secondary-dex')
            library.write_bytes(b'new-native-helper')
            with zipfile.ZipFile(original, 'w') as archive:
                archive.writestr('AndroidManifest.xml', manifest)
                archive.writestr('classes.dex', protected)
                archive.writestr('resources.arsc', OLD.encode())
                archive.writestr('META-INF/OLD.SF', b'old-signature')
                archive.writestr('META-INF/services/example.Provider', b'preserved-service')
            assemble(original, output, dex, library)
            with zipfile.ZipFile(output) as archive:
                rebuilt = archive.read('classes.dex')
                self.assertEqual(rebuilt[12:32], protected[12:32])
                self.assertEqual(struct.unpack_from('<I', rebuilt, 8)[0], zlib.adler32(rebuilt[12:]) & 0xffffffff)
                self.assertIn(NEW.encode(), rebuilt)
                self.assertNotIn(OLD.encode(), rebuilt)
                self.assertNotIn('META-INF/OLD.SF', archive.namelist())
                self.assertEqual(archive.read('META-INF/services/example.Provider'), b'preserved-service')

    def test_rejects_unreviewed_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'unsupported.apk'
            path.write_bytes(b'not-the-reviewed-upstream')
            with self.assertRaisesRegex(ValueError, 'Unsupported source APK'):
                validate_source(path)

    def test_project_metadata_does_not_claim_verified_ad_removal(self):
        project = json.loads((ROOT / 'project.json').read_text())
        self.assertEqual(project['launcher_label'], 'MovieBox')
        self.assertEqual(project['title'], 'MovieBox (No Force Update & Adds)')
        self.assertIn('not implemented', project['scope']['advertising_removal'])


@unittest.skipUnless(os.getenv('MOVIEBOX_SOURCE_APK'), 'External proprietary fixture is not configured')
class ExternalArtifactTests(unittest.TestCase):
    def test_pinned_real_manifest(self):
        source = Path(os.environ['MOVIEBOX_SOURCE_APK'])
        before = validate_source(source)
        with zipfile.ZipFile(source) as archive:
            after = manifest_summary(patch_manifest(archive.read('AndroidManifest.xml')))
        verify_manifest(before, after)
        self.assertEqual(after['launchers'][0]['label'], 'MovieBox')


if __name__ == '__main__':
    unittest.main()
