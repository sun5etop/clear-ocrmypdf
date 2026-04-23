# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Resolve bundled external runtimes for packaged desktop builds."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path

Environ = Mapping[str, str] | os._Environ  # pylint: disable=protected-access


def _iter_unique_paths(paths: Iterable[Path]) -> Iterator[Path]:
    seen: set[str] = set()
    for path in paths:
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        yield path


def _bundle_root_candidates(env: Environ | None = None) -> Iterator[Path]:
    if env is None:
        env = os.environ

    explicit_root = env.get('OCRMYPDF_BUNDLE_ROOT')
    if explicit_root:
        yield Path(explicit_root)

    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        yield Path(meipass)

    yield Path(sys.executable).resolve().parent

    package_root = Path(__file__).resolve().parent
    yield package_root
    yield package_root.parent
    yield package_root.parent.parent


def _candidate_runtime_dirs(env: Environ | None = None) -> Iterator[Path]:
    for root in _iter_unique_paths(_bundle_root_candidates(env)):
        yield root / 'ocrmypdf_runtime'
        yield root / 'runtime'
        yield root


PROGRAM_ALIASES: dict[str, tuple[str, ...]] = {
    'tesseract': ('tesseract', 'tesseract.exe'),
    'gs': ('gs', 'gswin64c', 'gswin64c.exe', 'gs.exe'),
    'gswin64c': ('gs', 'gswin64c', 'gswin64c.exe', 'gs.exe'),
    'unpaper': ('unpaper', 'unpaper.exe'),
    'pngquant': ('pngquant', 'pngquant.exe'),
    'jbig2': ('jbig2', 'jbig2.exe', 'jbig2enc', 'jbig2enc.exe'),
    'verapdf': ('verapdf', 'verapdf.exe'),
}

PROGRAM_ENV_OVERRIDES: dict[str, tuple[str, ...]] = {
    'tesseract': ('OCRMYPDF_TESSERACT',),
    'gs': ('OCRMYPDF_GS', 'OCRMYPDF_GHOSTSCRIPT'),
    'gswin64c': ('OCRMYPDF_GS', 'OCRMYPDF_GHOSTSCRIPT'),
    'unpaper': ('OCRMYPDF_UNPAPER',),
    'pngquant': ('OCRMYPDF_PNGQUANT',),
    'jbig2': ('OCRMYPDF_JBIG2',),
    'verapdf': ('OCRMYPDF_VERAPDF',),
}


def _program_candidates(program: str) -> tuple[str, ...]:
    return PROGRAM_ALIASES.get(program, (program,))


def resolve_program_path(program: str, env: Environ | None = None) -> Path | None:
    """Resolve a bundled executable path for an external program."""
    if env is None:
        env = os.environ

    for env_var in PROGRAM_ENV_OVERRIDES.get(program, ()):
        configured = env.get(env_var)
        if configured:
            candidate = Path(configured)
            if candidate.exists():
                return candidate

    names = _program_candidates(program)
    subdirs = ('', 'bin', program, f'{program}/bin')
    for runtime_dir in _candidate_runtime_dirs(env):
        for subdir in subdirs:
            for name in names:
                candidate = runtime_dir / subdir / name
                if candidate.exists():
                    return candidate
    return None


def _find_tessdata_root(executable: Path, env: Environ | None = None) -> Path | None:
    if env is None:
        env = os.environ

    explicit = env.get('OCRMYPDF_TESSDATA_PREFIX')
    if explicit and Path(explicit).exists():
        return Path(explicit)

    runtime_dirs = list(_candidate_runtime_dirs(env))
    candidates = [
        executable.parent / 'tessdata',
        executable.parent.parent / 'tessdata',
    ]
    for runtime_dir in runtime_dirs:
        candidates.extend(
            [
                runtime_dir / 'tessdata',
                runtime_dir / 'tesseract' / 'tessdata',
            ]
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def prepare_process_env(
    program: str, executable: Path | None, env: Environ | None = None
) -> dict[str, str]:
    """Create a subprocess environment for bundled runtimes."""
    base = dict(os.environ if env is None else env)

    path_prefixes: list[str] = []
    if executable is not None:
        path_prefixes.append(str(executable.parent))

    if program == 'tesseract' and executable is not None:
        tessdata_root = _find_tessdata_root(executable, base)
        if tessdata_root and not base.get('TESSDATA_PREFIX'):
            base['TESSDATA_PREFIX'] = str(tessdata_root)
        if tessdata_root is not None:
            path_prefixes.append(str(tessdata_root.parent))

    current_path = base.get('PATH', '')
    if path_prefixes:
        deduped = []
        seen = set()
        for entry in path_prefixes + ([current_path] if current_path else []):
            if not entry:
                continue
            key = os.path.normcase(entry)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)
        base['PATH'] = os.pathsep.join(deduped)

    return base
