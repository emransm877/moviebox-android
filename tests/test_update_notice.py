"""Policy execution and patch compatibility checks; no APK is built or signed."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def java_tool(name):
    home = os.getenv('JAVA_HOME')
    if home:
        candidate = Path(home) / 'bin' / (name + ('.exe' if os.name == 'nt' else ''))
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


class UpdatePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.javac, cls.java = java_tool('javac'), java_tool('java')
        if not cls.javac or not cls.java:
            raise unittest.SkipTest('JDK required for actual Java policy tests')
        cls.directory = tempfile.TemporaryDirectory(prefix='moviebox-policy-tests-')
        cls.addClassCleanup(cls.directory.cleanup)
        subprocess.run([cls.javac, '-d', cls.directory.name,
            str(ROOT / 'patch/java/local/popupguard/PatchUpdatePolicy.java'),
            str(ROOT / 'tests/java/PatchUpdatePolicyChecks.java')], check=True, capture_output=True, text=True)

    def check_group(self, group):
        subprocess.run([self.java, '-cp', self.directory.name, 'PatchUpdatePolicyChecks', group],
                       check=True, capture_output=True, text=True)

    def test_numeric_stable_version_comparison(self):
        self.check_group('versions')

    def test_only_exact_https_repository_release_asset_is_accepted(self):
        self.check_group('urls')

    def test_daily_schedule_and_disabled_preference(self):
        self.check_group('schedule')

    def test_later_skip_and_installed_version_suppress_notice(self):
        self.check_group('choices')

    def test_only_reviewed_browse_activity_is_eligible(self):
        self.check_group('activity')


class UpdateCompatibilityTests(unittest.TestCase):
    def test_patch_version_matches_notice_version(self):
        config = json.loads((ROOT / 'project.json').read_text())
        source = (ROOT / 'patch/java/local/popupguard/PatchUpdatePolicy.java').read_text()
        self.assertEqual(re.search(r'CURRENT_VERSION = "([^"]+)"', source).group(1), config['patch_version'])

    def test_reviewed_native_startup_guard_is_unchanged(self):
        source = (ROOT / 'patch/native/startup-guard.c').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),
                         '4e8d240e7cdc63cbac3e333252b3bbe3389785b7aa321cb1b396c2ebe76537eb')


if __name__ == '__main__':
    unittest.main()
