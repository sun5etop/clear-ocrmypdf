# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: CC-BY-SA-4.0

from __future__ import annotations

import os
from pathlib import Path

from ocrmypdf._runtime import prepare_process_env, resolve_program_path


def test_resolve_bundled_tesseract_from_bundle_root(monkeypatch, tmp_path):
    runtime = tmp_path / 'ocrmypdf_runtime' / 'tesseract'
    executable = runtime / 'bin' / 'tesseract.exe'
    tessdata = runtime / 'tessdata'
    executable.parent.mkdir(parents=True)
    tessdata.mkdir(parents=True)
    executable.write_text('')

    monkeypatch.setenv('OCRMYPDF_BUNDLE_ROOT', str(tmp_path))

    resolved = resolve_program_path('tesseract')

    assert resolved == executable


def test_prepare_process_env_sets_tessdata_prefix(monkeypatch, tmp_path):
    runtime = tmp_path / 'ocrmypdf_runtime' / 'tesseract'
    executable = runtime / 'bin' / 'tesseract'
    tessdata = runtime / 'tessdata'
    executable.parent.mkdir(parents=True)
    tessdata.mkdir(parents=True)
    executable.write_text('')

    monkeypatch.setenv('PATH', '/usr/bin')
    env = prepare_process_env('tesseract', executable, {'PATH': '/usr/bin'})

    assert Path(env['TESSDATA_PREFIX']) == tessdata
    assert env['PATH'].split(os.pathsep)[0] == str(executable.parent)


def test_env_override_wins(monkeypatch, tmp_path):
    direct = tmp_path / 'custom' / 'tesseract.exe'
    direct.parent.mkdir(parents=True)
    direct.write_text('')
    monkeypatch.setenv('OCRMYPDF_TESSERACT', str(direct))

    resolved = resolve_program_path('tesseract')

    assert resolved == direct


def test_resolve_bundled_ghostscript_from_bundle_root(monkeypatch, tmp_path):
    runtime = tmp_path / 'ocrmypdf_runtime' / 'gs'
    executable = runtime / 'bin' / 'gswin64c.exe'
    executable.parent.mkdir(parents=True)
    executable.write_text('')

    monkeypatch.setenv('OCRMYPDF_BUNDLE_ROOT', str(tmp_path))

    resolved = resolve_program_path('gs')

    assert resolved == executable


def test_prepare_process_env_for_ghostscript_preserves_path_prefix(monkeypatch, tmp_path):
    runtime = tmp_path / 'ocrmypdf_runtime' / 'gs'
    executable = runtime / 'bin' / 'gs'
    executable.parent.mkdir(parents=True)
    executable.write_text('')

    monkeypatch.setenv('PATH', '/usr/bin')
    env = prepare_process_env('gs', executable, {'PATH': '/usr/bin'})

    assert 'TESSDATA_PREFIX' not in env
    assert env['PATH'].split(os.pathsep)[0] == str(executable.parent)
