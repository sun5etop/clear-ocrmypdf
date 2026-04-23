# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Fetch vendored offline Windows OCR assets into the repository."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = PROJECT_ROOT / 'packaging' / 'vendor' / 'windows'
TESSDATA_ROOT = VENDOR_ROOT / 'tessdata'

WHEELS = {
    'cp311': {
        'filename': 'tesserocr-2.9.1-cp311-cp311-win_amd64.whl',
        'url': 'https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/tesserocr-v2.9.1-tesseract-4.1.3/tesserocr-2.9.1-cp311-cp311-win_amd64.whl',
        'sha256': '453de95576f72dee2952f0b5d15c6fc4a7e1b2aec4ffb35a8a41847abc275c69',
    },
    'cp312': {
        'filename': 'tesserocr-2.9.1-cp312-cp312-win_amd64.whl',
        'url': 'https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/tesserocr-v2.9.1-tesseract-4.1.3/tesserocr-2.9.1-cp312-cp312-win_amd64.whl',
        'sha256': '21e27ae7d8265ea87954b12a8e0513a8b47165e4c8722d94833e9dfe689ddadb',
    },
}

TRAINEDDATA = {
    'eng': 'https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/eng.traineddata',
    'osd': 'https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/osd.traineddata',
    'chi_sim': 'https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/chi_sim.traineddata',
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, target.open('wb') as output:
        shutil.copyfileobj(response, output)


def fetch_wheels() -> None:
    for metadata in WHEELS.values():
        target = VENDOR_ROOT / metadata['filename']
        if target.exists() and sha256_file(target) == metadata['sha256']:
            print(f'Skipping existing wheel: {target.name}')
            continue
        print(f'Downloading wheel: {target.name}')
        download(metadata['url'], target)
        digest = sha256_file(target)
        if digest != metadata['sha256']:
            print(
                f"Warning: checksum mismatch for {target.name}: "
                f"expected {metadata['sha256']}, got {digest}"
            )


def fetch_tessdata() -> None:
    for lang, url in TRAINEDDATA.items():
        target = TESSDATA_ROOT / f'{lang}.traineddata'
        if target.exists() and target.stat().st_size > 0:
            print(f'Skipping existing traineddata: {target.name}')
            continue
        print(f'Downloading traineddata: {target.name}')
        download(url, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch vendored offline Windows OCR assets into packaging/vendor/windows."
    )
    parser.add_argument(
        '--only',
        choices=['wheels', 'tessdata', 'all'],
        default='all',
        help="Limit download scope.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.only in ('wheels', 'all'):
        fetch_wheels()
    if args.only in ('tessdata', 'all'):
        fetch_tessdata()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
