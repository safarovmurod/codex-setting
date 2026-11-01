"""Exercise repair of interrupted Windows runtime preparation without running a runtime."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'scripts' / 'Prepare-RecoveryPackage.ps1'


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(os.name == 'nt' and shutil.which('powershell.exe'), 'Windows PowerShell required')
class RecoveryPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex-setting-repair-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'recovery'
        self.root.mkdir()
        self.fixture = self.base / 'release.zip'
        self.files = {
            'payload/runtime/python.exe': b'fixture-python-not-executed',
            'payload/runtime/pythonw.exe': b'fixture-pythonw-not-executed',
            'payload/app/src/auto_resume.py': b'# fixture, never imported\n',
        }
        self.write_zip(self.fixture, self.files)
        self.expected = hashlib.sha256(self.fixture.read_bytes()).hexdigest()
        self.archive = self.root / 'release.zip'
        self.package = self.root / 'package'

    @staticmethod
    def write_zip(path, files):
        with zipfile.ZipFile(path, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data)

    def prepare(self, download=None, expected=None, success=True):
        # Mock only the download cmdlet. All hashing, ZIP validation, extraction,
        # boundary checks, backups and swaps execute in real Windows PowerShell.
        script = "\n".join([
            "$ErrorActionPreference='Stop'",
            '$global:RepairTestArchive=' + ps_quote(download or self.fixture),
            'function global:Invoke-WebRequest { param($Uri,$OutFile,[switch]$UseBasicParsing,$TimeoutSec) Copy-Item -LiteralPath $global:RepairTestArchive -Destination $OutFile }',
            '& ' + ps_quote(HELPER) + ' -RecoveryRoot ' + ps_quote(self.root)
            + " -ArchiveName 'release.zip' -DownloadUrl 'https://fixture.invalid/release.zip' -Sha256 "
            + ps_quote(expected or self.expected),
        ])
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script],
                                capture_output=True, text=True, timeout=45,
                                env={k:v for k,v in os.environ.items() if k.lower() != 'psmodulepath'})
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.root.glob('.prepare-*')), [], 'Staging files were not cleaned')
        return result

    def assert_package(self):
        for name, content in self.files.items():
            self.assertEqual((self.package / name).read_bytes(), content)

    def test_incomplete_existing_package_is_rebuilt_from_verified_cache(self):
        shutil.copyfile(self.fixture, self.archive)
        (self.package / 'payload/runtime').mkdir(parents=True)
        (self.package / 'payload/runtime/python.exe').write_bytes(b'interrupted-copy')
        self.prepare()
        self.assert_package()
        backups = list((self.root / 'backups').glob('package-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'payload/runtime/python.exe').read_bytes(), b'interrupted-copy')

    def test_partial_download_is_replaced_and_complete_package_installed(self):
        self.archive.write_bytes(b'partial-download')
        self.prepare()
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(), self.expected)
        self.assert_package()

    def test_unchanged_package_is_not_replaced_on_repeat(self):
        self.prepare()
        target = self.package / 'payload/runtime/python.exe'
        previous_mtime = target.stat().st_mtime_ns
        self.prepare()
        self.assert_package()
        self.assertEqual(target.stat().st_mtime_ns, previous_mtime)
        self.assertFalse((self.root / 'backups').exists())

    def test_failed_download_digest_preserves_previous_archive_and_package(self):
        self.archive.write_bytes(b'previous-partial-download')
        self.package.mkdir()
        sentinel = self.package / 'keep.txt'
        sentinel.write_bytes(b'previous-owned-package')
        invalid = self.base / 'invalid.zip'
        invalid.write_bytes(b'broken-replacement')
        self.prepare(download=invalid, success=False)
        self.assertEqual(self.archive.read_bytes(), b'previous-partial-download')
        self.assertEqual(sentinel.read_bytes(), b'previous-owned-package')

    def test_zip_escape_is_rejected_before_any_package_swap(self):
        malicious = self.base / 'malicious.zip'
        self.write_zip(malicious, {**self.files, '../escape.txt': b'escape'})
        expected = hashlib.sha256(malicious.read_bytes()).hexdigest()
        self.prepare(download=malicious, expected=expected, success=False)
        self.assertFalse((self.root / 'escape.txt').exists())
        self.assertFalse(self.package.exists())
        self.assertFalse(self.archive.exists())

    def test_incomplete_release_is_rejected_before_package_swap(self):
        incomplete = self.base / 'incomplete.zip'
        self.write_zip(incomplete, {'payload/runtime/python.exe': b'incomplete'})
        expected = hashlib.sha256(incomplete.read_bytes()).hexdigest()
        self.prepare(download=incomplete, expected=expected, success=False)
        self.assertFalse(self.package.exists())
        self.assertFalse(self.archive.exists())


if __name__ == '__main__':
    unittest.main()
