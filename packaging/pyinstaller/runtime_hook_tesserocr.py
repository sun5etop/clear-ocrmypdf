# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""PyInstaller runtime hook for bundled libtesseract/tesserocr assets."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _candidate_dirs(bundle_root: Path) -> list[Path]:
    return [
        bundle_root,
        bundle_root / 'tesserocr',
        bundle_root / 'ocrmypdf_runtime',
        bundle_root / 'ocrmypdf_runtime' / 'tesserocr',
    ]


bundle_root = Path(getattr(sys, '_MEIPASS', Path(sys.executable).resolve().parent))

for directory in _candidate_dirs(bundle_root):
    if directory.exists() and hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(str(directory))
        except OSError:
            pass

tessdata_candidates = [
    bundle_root / 'ocrmypdf_runtime' / 'tessdata',
    bundle_root / 'ocrmypdf_runtime' / 'tesserocr' / 'tessdata',
    bundle_root / 'tessdata',
]

for tessdata in tessdata_candidates:
    if tessdata.exists():
        os.environ.setdefault('TESSDATA_PREFIX', str(tessdata))
        os.environ.setdefault('OCRMYPDF_TESSDATA_PREFIX', str(tessdata))
        break
