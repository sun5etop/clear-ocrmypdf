# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to libtesseract through tesserocr."""

from __future__ import annotations

import logging
import math
import os
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image
from packaging.version import Version

from ocrmypdf._exec.tesseract import TesseractVersion, ThresholdingMethod
from ocrmypdf.exceptions import MissingDependencyError, TesseractConfigError
from ocrmypdf.hocrtransform.hocr_parser import HocrParser
from ocrmypdf.models.ocr_element import OcrElement
from ocrmypdf.pluginspec import OrientationConfidence

log = logging.getLogger(__name__)

_IMPORT_ERROR: Exception | None = None

try:
    import tesserocr as _tesserocr
except Exception as exc:  # pragma: no cover - depends on local install
    _tesserocr = None
    _IMPORT_ERROR = exc


def available() -> bool:
    """Return True if the tesserocr binding is importable."""
    return _tesserocr is not None


def _require_tesserocr():
    if _tesserocr is None:  # pragma: no cover - depends on local install
        raise MissingDependencyError(
            "The in-process libtesseract backend requires the 'tesserocr' package. "
            "Install it first, or use the external tesseract CLI backend."
        ) from _IMPORT_ERROR
    return _tesserocr


def version() -> Version:
    module = _require_tesserocr()
    raw = module.tesseract_version().splitlines()[0].strip()
    if raw.lower().startswith('tesseract '):
        raw = raw.split(' ', 1)[1].strip()
    return TesseractVersion(raw)


def has_thresholding() -> bool:
    return version() >= Version('5.0')


def _tessdata_prefix() -> str | None:
    explicit = (
        os.environ.get('OCRMYPDF_TESSDATA_PREFIX')
        or os.environ.get('TESSDATA_PREFIX')
        or None
    )
    if explicit:
        return explicit

    candidates = [
        '/opt/homebrew/share/tessdata',
        '/usr/local/share/tessdata',
        '/usr/share/tessdata',
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def _lang_spec(languages: list[str]) -> str:
    return '+'.join(languages) if languages else 'eng'


def get_languages() -> set[str]:
    module = _require_tesserocr()
    tessdata = _tessdata_prefix()
    try:
        _path, langs = module.get_languages(tessdata)
    except Exception as exc:
        raise MissingDependencyError(
            "libtesseract could not report installed languages. "
            "Check that tessdata is available and matches the bundled runtime."
        ) from exc
    return set(langs)


def _api_kwargs(languages: list[str], engine_mode: int | None, pagesegmode: int | None):
    kwargs: dict[str, Any] = {
        'lang': _lang_spec(languages),
    }
    tessdata = _tessdata_prefix()
    if tessdata:
        kwargs['path'] = tessdata
    if engine_mode is not None:
        kwargs['oem'] = engine_mode
    if pagesegmode is not None:
        kwargs['psm'] = pagesegmode
    return kwargs


def _apply_variables(
    api,
    *,
    thresholding: ThresholdingMethod,
    user_words,
    user_patterns,
    tessconfig: list[str],
) -> None:
    if thresholding != ThresholdingMethod.AUTO and has_thresholding():
        if api.SetVariable('thresholding_method', str(int(thresholding))) is False:
            raise TesseractConfigError('thresholding_method')

    if user_words:
        if api.SetVariable('user_words_file', os.fspath(user_words)) is False:
            raise TesseractConfigError('user_words_file')
    if user_patterns:
        if api.SetVariable('user_patterns_file', os.fspath(user_patterns)) is False:
            raise TesseractConfigError('user_patterns_file')

    for config in tessconfig:
        ok = api.ReadConfigFile(config)
        if ok is False:
            raise TesseractConfigError(config)


def get_orientation(
    input_file: Path,
    engine_mode: int | None,
    timeout: float,
    omp_thread_limit: int | None = None,
) -> OrientationConfidence:
    del timeout, omp_thread_limit  # timeouts are not supported in-process
    module = _require_tesserocr()

    kwargs = _api_kwargs(['osd'], engine_mode, getattr(module.PSM, 'OSD_ONLY', 0))
    with module.PyTessBaseAPI(**kwargs) as api:
        api.SetImageFile(os.fspath(input_file))
        result = api.DetectOrientationScript()
        return OrientationConfidence(
            angle=int(result.get('orient_deg', 0)),
            confidence=float(result.get('orient_conf', 0.0)),
        )


def get_deskew(
    input_file: Path,
    languages: list[str],
    engine_mode: int | None,
    timeout: float,
    omp_thread_limit: int | None = None,
) -> float:
    del timeout, omp_thread_limit  # timeouts are not supported in-process
    module = _require_tesserocr()

    psm_auto = getattr(module.PSM, 'AUTO_OSD', getattr(module.PSM, 'AUTO', 3))
    kwargs = _api_kwargs(languages, engine_mode, psm_auto)
    with module.PyTessBaseAPI(**kwargs) as api:
        api.SetImageFile(os.fspath(input_file))
        api.Recognize()
        it = api.AnalyseLayout()
        if it is None:
            return 0.0
        _orientation, _direction, _order, deskew_angle = it.Orientation()
        return 180 / math.pi * float(deskew_angle)


def _null_page_from_image(input_file: Path, page_number: int = 0) -> OcrElement:
    with Image.open(input_file) as im:
        width, height = im.size
        dpi_info = im.info.get('dpi', (72, 72))
        dpi = dpi_info[0] if isinstance(dpi_info, tuple) else dpi_info
        if not dpi or dpi <= 0:
            dpi = 72.0

    from ocrmypdf.models.ocr_element import BoundingBox, OcrClass

    return OcrElement(
        ocr_class=OcrClass.PAGE,
        bbox=BoundingBox(left=0, top=0, right=width, bottom=height),
        dpi=float(dpi),
        page_number=page_number,
    )


def _page_geometry(input_file: Path) -> tuple[float, int, int]:
    with Image.open(input_file) as im:
        width, height = im.size
        dpi_info = im.info.get('dpi', (72, 72))
        dpi = dpi_info[0] if isinstance(dpi_info, tuple) else dpi_info
        if not dpi or dpi <= 0:
            dpi = 72.0
    return float(dpi), width, height


def generate_ocr(
    *,
    input_file: Path,
    languages: list[str],
    engine_mode: int | None,
    tessconfig: list[str],
    timeout: float,
    pagesegmode: int | None,
    thresholding: ThresholdingMethod,
    user_words,
    user_patterns,
    page_number: int = 0,
) -> tuple[OcrElement, str]:
    del timeout  # timeouts are not supported in-process
    module = _require_tesserocr()

    kwargs = _api_kwargs(languages, engine_mode, pagesegmode)
    fallback_dpi, fallback_width, fallback_height = _page_geometry(input_file)
    with module.PyTessBaseAPI(**kwargs) as api:
        _apply_variables(
            api,
            thresholding=thresholding,
            user_words=user_words,
            user_patterns=user_patterns,
            tessconfig=tessconfig,
        )
        api.SetImageFile(os.fspath(input_file))
        text_content = api.GetUTF8Text() or ''

        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            hocr_path = Path(tmpdir) / 'page.hocr'
            hocr_content = api.GetHOCRText(page_number)
            hocr_path.write_text(hocr_content, encoding='utf-8')
            with suppress(Exception):
                api.Clear()
            try:
                page = HocrParser(hocr_path).parse()
            except Exception:
                log.exception("Failed to parse hOCR from libtesseract backend")
                page = _null_page_from_image(input_file, page_number=page_number)

    if page.dpi is None or page.dpi <= 0:
        page.dpi = fallback_dpi
    if page.bbox is None:
        from ocrmypdf.models.ocr_element import BoundingBox

        page.bbox = BoundingBox(
            left=0, top=0, right=fallback_width, bottom=fallback_height
        )
    page.page_number = page_number
    return page, text_content
