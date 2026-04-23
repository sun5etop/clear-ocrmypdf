# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Build the Windows OCRmyPDF desktop bundle with PyInstaller."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE = PROJECT_ROOT / 'packaging' / 'pyinstaller' / 'ocrmypdf_gui.spec'
DIST_DIR = PROJECT_ROOT / 'dist'
BUILD_DIR = PROJECT_ROOT / 'build'
RUNTIME_ROOT = PROJECT_ROOT / 'packaging' / 'runtime'
VENDOR_ROOT = PROJECT_ROOT / 'packaging' / 'vendor' / 'windows'
INSTALL_SCRIPT = PROJECT_ROOT / 'scripts' / 'install_windows_embedded_ocr.py'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the OCRmyPDF Windows GUI bundle."
    )
    parser.add_argument(
        '--require-gs',
        action='store_true',
        help="Fail if Ghostscript is not bundled. Use this when PDF/A output must work.",
    )
    parser.add_argument(
        '--skip-zip',
        action='store_true',
        help="Do not create a zip archive after PyInstaller finishes.",
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help="Delete build/ and dist/ before building.",
    )
    parser.add_argument(
        '--python',
        type=Path,
        default=Path(sys.executable),
        help="Python interpreter to use for invoking PyInstaller.",
    )
    parser.add_argument(
        '--skip-install',
        action='store_true',
        help="Skip local installation of the vendored tesserocr wheel before building.",
    )
    return parser.parse_args()


def runtime_candidates(relative_path: str) -> list[Path]:
    return [
        RUNTIME_ROOT / 'windows' / relative_path,
        RUNTIME_ROOT / 'common' / relative_path,
    ]


def find_runtime(relative_path: str) -> Path | None:
    for candidate in runtime_candidates(relative_path):
        if candidate.exists():
            return candidate
    return None


def validate_runtime(require_gs: bool) -> None:
    tessdata = find_runtime('tessdata')
    ghostscript = find_runtime('gs/bin/gswin64c.exe')
    vendored_wheels = sorted(VENDOR_ROOT.glob('tesserocr-*-win_amd64.whl'))

    if not vendored_wheels:
        raise SystemExit(
            "Missing vendored tesserocr wheel: expected one under "
            "packaging/vendor/windows/"
        )
    if tessdata is None:
        raise SystemExit(
            "Missing bundled tessdata: expected "
            "packaging/runtime/windows/tessdata/ "
            "or packaging/runtime/common/tessdata/"
        )
    if require_gs and ghostscript is None:
        raise SystemExit(
            "Missing bundled Ghostscript: expected "
            "packaging/runtime/windows/gs/bin/gswin64c.exe "
            "or packaging/runtime/common/gs/bin/gswin64c.exe"
        )

    print(f'Using vendored tesserocr wheel: {vendored_wheels[-1]}')
    print(f'Using bundled tessdata:   {tessdata}')
    if ghostscript is not None:
        print(f'Using bundled Ghostscript: {ghostscript}')
    else:
        print('Ghostscript not bundled: GUI build will work, but PDF/A output will not.')


def install_embedded_ocr(python: Path) -> None:
    cmd = [str(python), str(INSTALL_SCRIPT)]
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def run_pyinstaller(python: Path) -> None:
    cmd = [str(python), '-m', 'PyInstaller', '--noconfirm', str(SPEC_FILE)]
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def make_zip() -> Path:
    bundle_dir = DIST_DIR / 'OCRmyPDF'
    if not bundle_dir.exists():
        raise SystemExit(f"Expected bundle output at {bundle_dir}, but it was not created.")

    archive_base = DIST_DIR / 'OCRmyPDF-windows'
    archive = shutil.make_archive(str(archive_base), 'zip', root_dir=bundle_dir.parent, base_dir=bundle_dir.name)
    return Path(archive)


def main() -> int:
    args = parse_args()

    if args.clean:
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        shutil.rmtree(DIST_DIR, ignore_errors=True)

    if not args.skip_install:
        install_embedded_ocr(args.python)

    validate_runtime(require_gs=args.require_gs)
    run_pyinstaller(args.python)

    if not args.skip_zip:
        archive = make_zip()
        print(f'Created archive: {archive}')

    print(f'Bundle ready: {DIST_DIR / "OCRmyPDF"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
