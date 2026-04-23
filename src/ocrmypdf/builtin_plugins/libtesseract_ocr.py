# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Built-in OCR engine using libtesseract via tesserocr."""

from __future__ import annotations

import logging

from ocrmypdf import hookimpl
from ocrmypdf._exec import tesserocr
from ocrmypdf.exceptions import BadArgsError, MissingDependencyError
from ocrmypdf.pluginspec import OcrEngine

log = logging.getLogger(__name__)


def can_handle_options(options) -> bool:
    """Return True if the libtesseract backend can handle the requested options."""
    if options is None:
        return True
    if getattr(options, 'ocr_engine', 'auto') == 'none':
        return False
    if getattr(options, 'pdf_renderer', 'auto') == 'sandwich':
        return False
    return True


class LibtesseractOcrEngine(OcrEngine):
    """Implements OCR using libtesseract loaded in-process."""

    @staticmethod
    def version():
        return str(tesserocr.version())

    @staticmethod
    def creator_tag(options):
        return f"OCRmyPDF libtesseract OCR {LibtesseractOcrEngine.version()}"

    def __str__(self):
        return f"libtesseract OCR {LibtesseractOcrEngine.version()}"

    @staticmethod
    def languages(options):
        return tesserocr.get_languages()

    @staticmethod
    def get_orientation(input_file, options):
        return tesserocr.get_orientation(
            input_file,
            engine_mode=options.tesseract.oem,
            timeout=options.tesseract.non_ocr_timeout,
            omp_thread_limit=options.tesseract.omp_thread_limit,
        )

    @staticmethod
    def get_deskew(input_file, options) -> float:
        return tesserocr.get_deskew(
            input_file,
            languages=options.languages,
            engine_mode=options.tesseract.oem,
            timeout=options.tesseract.non_ocr_timeout,
            omp_thread_limit=options.tesseract.omp_thread_limit,
        )

    @staticmethod
    def supports_generate_ocr() -> bool:
        return True

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        raise NotImplementedError(
            "The in-process libtesseract backend uses generate_ocr() directly "
            "and does not provide an hOCR file backend."
        )

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        raise NotImplementedError(
            "The in-process libtesseract backend does not provide Tesseract's "
            "text-only PDF renderer. Use --pdf-renderer fpdf2/auto."
        )

    @staticmethod
    def generate_ocr(input_file, options, page_number: int = 0):
        return tesserocr.generate_ocr(
            input_file=input_file,
            languages=options.languages,
            engine_mode=options.tesseract.oem,
            tessconfig=options.tesseract.config,
            timeout=options.tesseract.timeout,
            pagesegmode=options.tesseract.pagesegmode,
            thresholding=options.tesseract.thresholding,
            user_words=options.tesseract.user_words,
            user_patterns=options.tesseract.user_patterns,
            page_number=page_number,
        )


@hookimpl
def check_options(options):
    """Validate explicit libtesseract requests and unsupported combinations."""
    selected_engine = getattr(options, 'ocr_engine', 'auto')
    if selected_engine not in ('auto', 'tesseract', 'tesserocr'):
        return

    if selected_engine == 'tesserocr' and not tesserocr.available():
        raise MissingDependencyError(
            "The requested OCR engine 'tesserocr' is unavailable. "
            "Install the Python package 'tesserocr' together with libtesseract."
        )

    if not can_handle_options(options):
        if selected_engine == 'tesserocr':
            raise BadArgsError(
                "The in-process libtesseract backend does not support "
                "--pdf-renderer sandwich. Use --pdf-renderer fpdf2/auto instead."
            )
        return

    if selected_engine == 'tesserocr' and tesserocr.version() == tesserocr.TesseractVersion('5.4.0'):
        raise MissingDependencyError(
            "libtesseract 5.4.0 is not supported due to regressions in this version. "
            "Please upgrade to a newer or supported older version."
        )


@hookimpl
def get_ocr_engine(options):
    """Return the in-process libtesseract engine when available and suitable."""
    if options is not None:
        selected_engine = getattr(options, 'ocr_engine', 'auto')
        if selected_engine not in ('auto', 'tesseract', 'tesserocr'):
            return None
        if not can_handle_options(options):
            return None
        if selected_engine == 'tesserocr' and not tesserocr.available():
            return None

    if not tesserocr.available():
        return None
    return LibtesseractOcrEngine()
