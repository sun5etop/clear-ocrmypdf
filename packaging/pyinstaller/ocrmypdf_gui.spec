# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path
import platform
import os

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)


project_root = Path(SPECPATH).resolve().parents[1]
src_root = project_root / 'src'
runtime_root = project_root / 'packaging' / 'runtime'

system_name = {
    'Darwin': 'macos',
    'Windows': 'windows',
}.get(platform.system(), platform.system().lower())

datas = collect_data_files('ocrmypdf')
binaries = []

runtime_hooks = [str(project_root / 'packaging' / 'pyinstaller' / 'runtime_hook_tesserocr.py')]

try:
    datas += collect_data_files('tesserocr')
    binaries += collect_dynamic_libs('tesserocr')
except Exception:
    pass


def _is_executable_runtime_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() in {'.exe', '.dll', '.dylib', '.so'}:
        return True
    return 'bin' in path.parts or os.access(path, os.X_OK)


def _collect_runtime_entries(root: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    runtime_binaries: list[tuple[str, str]] = []
    runtime_datas: list[tuple[str, str]] = []
    if not root.exists():
        return runtime_binaries, runtime_datas

    for file in root.rglob('*'):
        if not file.is_file():
            continue
        destination = str(Path('ocrmypdf_runtime') / file.relative_to(root).parent)
        entry = (str(file), destination)
        if _is_executable_runtime_file(file):
            runtime_binaries.append(entry)
        else:
            runtime_datas.append(entry)
    return runtime_binaries, runtime_datas


for candidate in (runtime_root / 'common', runtime_root / system_name):
    new_binaries, new_datas = _collect_runtime_entries(candidate)
    binaries.extend(new_binaries)
    datas.extend(new_datas)

hiddenimports = collect_submodules('ocrmypdf')

a = Analysis(
    [str(src_root / 'ocrmypdf' / 'gui.py')],
    pathex=[str(src_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OCRmyPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OCRmyPDF',
)
