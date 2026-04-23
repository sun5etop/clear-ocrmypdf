# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Install vendored Windows tesserocr assets into the active environment."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = PROJECT_ROOT / 'packaging' / 'vendor' / 'windows'
RUNTIME_ROOT = PROJECT_ROOT / 'packaging' / 'runtime' / 'windows'
TESSDATA_DEST = RUNTIME_ROOT / 'tessdata'


def wheel_tag() -> str:
    major, minor = sys.version_info[:2]
    return f'cp{major}{minor}'


def find_wheel() -> Path:
    tag = wheel_tag()
    wheels = sorted(VENDOR_ROOT.glob(f'tesserocr-*-{tag}-{tag}-win_amd64.whl'))
    if not wheels:
        raise SystemExit(
            f"No vendored Windows wheel found for {tag}. "
            f"Expected one under {VENDOR_ROOT}"
        )
    return wheels[-1]


def ensure_tessdata() -> None:
    source = VENDOR_ROOT / 'tessdata'
    if not source.exists():
        raise SystemExit(
            f"Missing vendored tessdata under {source}. "
            "Place traineddata files there before running this installer."
        )
    TESSDATA_DEST.mkdir(parents=True, exist_ok=True)
    for traineddata in source.glob('*.traineddata'):
        shutil.copy2(traineddata, TESSDATA_DEST / traineddata.name)


def install_wheel(wheel: Path) -> None:
    cmd = [sys.executable, '-m', 'pip', 'install', '--force-reinstall', str(wheel)]
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install vendored Windows tesserocr runtime assets."
    )
    parser.add_argument(
        '--skip-pip',
        action='store_true',
        help="Only stage tessdata into packaging/runtime/windows without installing the wheel.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_tessdata()
    wheel = find_wheel()
    print(f'Using vendored wheel: {wheel}')
    if not args.skip_pip:
        install_wheel(wheel)
    print(f'Staged tessdata at: {TESSDATA_DEST}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
