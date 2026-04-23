# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: CC-BY-SA-4.0

from __future__ import annotations

from pathlib import Path

from scripts.build_windows_gui import find_runtime
from scripts.install_windows_embedded_ocr import find_wheel


def test_find_runtime_prefers_windows_over_common(monkeypatch, tmp_path):
    project_root = tmp_path
    runtime_root = project_root / 'packaging' / 'runtime'
    common = runtime_root / 'common' / 'tessdata'
    windows = runtime_root / 'windows' / 'tessdata'
    common.parent.mkdir(parents=True)
    windows.parent.mkdir(parents=True)
    common.mkdir()
    windows.mkdir()

    monkeypatch.setattr('scripts.build_windows_gui.RUNTIME_ROOT', runtime_root)

    assert find_runtime('tessdata') == windows


def test_find_runtime_falls_back_to_common(monkeypatch, tmp_path):
    runtime_root = tmp_path / 'packaging' / 'runtime'
    common = runtime_root / 'common' / 'gs' / 'bin' / 'gswin64c.exe'
    common.parent.mkdir(parents=True)
    common.write_text('')

    monkeypatch.setattr('scripts.build_windows_gui.RUNTIME_ROOT', runtime_root)

    assert find_runtime('gs/bin/gswin64c.exe') == common


def test_find_wheel_uses_matching_python_abi(monkeypatch, tmp_path):
    vendor_root = tmp_path / 'packaging' / 'vendor' / 'windows'
    vendor_root.mkdir(parents=True)
    wheel = vendor_root / 'tesserocr-2.9.1-cp312-cp312-win_amd64.whl'
    wheel.write_text('')

    monkeypatch.setattr('scripts.install_windows_embedded_ocr.VENDOR_ROOT', vendor_root)
    monkeypatch.setattr('scripts.install_windows_embedded_ocr.wheel_tag', lambda: 'cp312')

    assert find_wheel() == wheel
