<!-- SPDX-FileCopyrightText: 2014 Julien Pfefferkorn -->
<!-- SPDX-FileCopyrightText: 2015 James R. Barlow -->
<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->

<img src="docs/images/logo.svg" width="240" alt="OCRmyPDF">

# OCRmyPDF

OCRmyPDF adds an OCR text layer to scanned PDF files so they can be searched or copy-pasted.

```bash
ocrmypdf                      # command line entry point
   -l eng+fra                 # multiple languages
   --rotate-pages             # fix page rotation
   --deskew                   # deskew crooked pages
   --output-type pdf          # regular PDF output
   input_scanned.pdf
   output_searchable.pdf
```

## Main features

- Generates searchable PDF output from scanned PDF or image input
- Preserves original embedded image resolution when possible
- Supports multi-language OCR with Tesseract language packs
- Can rotate, deskew, optimize, and validate output
- Scales to large multi-page document batches

## Installation

Supported platforms include Linux, Windows, macOS, and FreeBSD.

Typical package-manager installs:

| Operating system | Install command |
| --- | --- |
| Debian / Ubuntu | `apt install ocrmypdf` |
| Fedora | `dnf install ocrmypdf` |
| macOS (Homebrew) | `brew install ocrmypdf` |
| FreeBSD | `pkg install py-ocrmypdf` |

For this repository, prefer the local docs under `docs/` and the offline packaging guides under `packaging/pyinstaller/`.

## Documentation

Local documentation entry points:

- `docs/index.md`
- `docs/installation.md`
- `docs/languages.md`
- `packaging/pyinstaller/README.md`
- `packaging/pyinstaller/WINDOWS_BUILD.md`

Built-in help is also available:

```bash
ocrmypdf --help
```

## Plugins

OCRmyPDF supports plugin-based OCR backends and processing extensions. This fork also includes:

- in-process `tesserocr` / `libtesseract` support
- Tk desktop GUI support
- offline Windows PyInstaller packaging helpers

## Requirements

In addition to Python, OCRmyPDF may require external runtimes such as Ghostscript and Tesseract, depending on the selected OCR and output mode. This fork also supports bundled offline runtimes for desktop packaging.

## License

The OCRmyPDF software is licensed under the Mozilla Public License 2.0 (MPL-2.0).
