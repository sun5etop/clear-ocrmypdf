# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: CC-BY-SA-4.0

from __future__ import annotations

from pathlib import Path

from ocrmypdf.gui import (
    get_gui_ocr_kwargs,
    get_gui_runtime_hint,
    has_bundled_ghostscript,
    running_frozen_windows_bundle,
)


def test_running_frozen_windows_bundle_only_for_frozen_windows():
    assert running_frozen_windows_bundle(frozen=True, platform='win32') is True
    assert running_frozen_windows_bundle(frozen=False, platform='win32') is False
    assert running_frozen_windows_bundle(frozen=True, platform='darwin') is False


def test_gui_uses_tesserocr_in_frozen_windows_bundle():
    kwargs = get_gui_ocr_kwargs(output_type='pdf', frozen=True, platform='win32')

    assert kwargs == {'ocr_engine': 'tesserocr', 'pdf_renderer': 'auto'}


def test_gui_leaves_runtime_selection_alone_outside_frozen_windows():
    kwargs = get_gui_ocr_kwargs(output_type='pdfa', frozen=False, platform='win32')

    assert kwargs == {}


def test_has_bundled_ghostscript_detects_env_override(monkeypatch, tmp_path):
    ghostscript = tmp_path / 'gswin64c.exe'
    ghostscript.write_text('')
    monkeypatch.setenv('OCRMYPDF_GS', str(ghostscript))

    assert has_bundled_ghostscript() is True


def test_has_bundled_ghostscript_detects_bundle_layout(monkeypatch, tmp_path):
    ghostscript = tmp_path / 'ocrmypdf_runtime' / 'gs' / 'bin' / 'gswin64c.exe'
    ghostscript.parent.mkdir(parents=True)
    ghostscript.write_text('')
    monkeypatch.delenv('OCRMYPDF_GS', raising=False)
    monkeypatch.delenv('OCRMYPDF_GHOSTSCRIPT', raising=False)
    monkeypatch.setattr('sys.executable', str(tmp_path / 'OCRmyPDF.exe'))

    assert has_bundled_ghostscript() is True


def test_get_gui_runtime_hint_mentions_disabled_pdfa_without_ghostscript(monkeypatch):
    monkeypatch.setattr('ocrmypdf.gui.has_bundled_ghostscript', lambda: False)

    hint = get_gui_runtime_hint(frozen=True, platform='win32')

    assert '已禁用 PDF/A' in hint
