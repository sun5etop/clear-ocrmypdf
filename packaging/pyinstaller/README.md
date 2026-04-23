# PyInstaller packaging

This repository now supports a simple desktop build with bundled OCR runtimes.
There are now two Tesseract integration paths:

- `tesserocr` / `libtesseract` in-process OCR (`--ocr-engine tesserocr`)
- External Tesseract CLI fallback (`--ocr-engine tesseract`)

## Offline-only runtime layout

This packaging flow is intentionally offline-only. The repository does not
provide any script that downloads OCR assets or build dependencies from the
network. All runtime files must be prepared manually and copied into the
repository before building.

For an offline Windows build, vendor the wheel and language data into the repo:

```text
packaging/vendor/windows/
  tesserocr-2.9.1-cp311-cp311-win_amd64.whl
  tesserocr-2.9.1-cp312-cp312-win_amd64.whl
  tessdata/
    eng.traineddata
    osd.traineddata
    chi_sim.traineddata
```

Then stage runtime data and install the local wheel into `.venv`:

```bat
packaging\pyinstaller\install_windows_embedded_ocr.bat
```

The main build wrapper does this automatically unless you pass `--skip-install`.

Ghostscript and other optional binaries still live under `packaging/runtime/`:

```text
packaging/runtime/
  windows/
    tessdata/
      eng.traineddata
      osd.traineddata
      chi_sim.traineddata
    gs/
      bin/gswin64c.exe
  macos/
    tesseract/
      bin/tesseract
      tessdata/...
    gs/
      bin/gs
```

The app resolves bundled binaries in this order:

1. `OCRMYPDF_TESSERACT` / `OCRMYPDF_TESSDATA_PREFIX`
2. `OCRMYPDF_GS` / `OCRMYPDF_GHOSTSCRIPT` for Ghostscript
3. PyInstaller bundle root (`sys._MEIPASS`)
4. `ocrmypdf_runtime/` next to the packaged app
5. System `PATH`

The runtime resolver also supports the same pattern for `unpaper`, `pngquant`,
`jbig2`, and `verapdf` if you decide to ship those later.

## In-process OCR engine

If you want to avoid spawning `tesseract.exe`, install `tesserocr` and ship the
matching `libtesseract` runtime for your platform. On Windows, the vendored
wheel already contains the required `libtesseract.dll` and `libleptonica.dll`
for the matching Python ABI. The OCRmyPDF CLI now accepts:

```bash
uv run ocrmypdf --ocr-engine tesserocr input.pdf output.pdf
```

The in-process backend currently targets the default `fpdf2` rendering path.
If you need `--pdf-renderer sandwich`, OCRmyPDF still falls back to the external
Tesseract CLI backend.

## Build commands

Install desktop build tooling into `.venv` using your own offline wheelhouse or
internal package mirror. This repository does not automate dependency download.

Build the GUI app directly with PyInstaller:

```bash
uv run pyinstaller packaging/pyinstaller/ocrmypdf_gui.spec
```

Run the GUI from source:

```bash
uv run ocrmypdf-gui
```

Build the Windows bundle with runtime validation and zip packaging:

```bash
uv run python scripts/build_windows_gui.py --clean
```

On Windows, the wrapper batch file does the same thing using `.venv`:

```bat
packaging\pyinstaller\build_windows.bat
```

If you require PDF/A support in the packaged app, make Ghostscript mandatory:

```bash
uv run python scripts/build_windows_gui.py --clean --require-gs
```

## Important limitation

Bundling Tesseract removes the need for users to install `tesseract` separately.
Bundling Ghostscript also enables `pdfa*` output modes without a system install.
Other tools such as `unpaper`, `pngquant`, and `jbig2enc` remain optional unless
you rely on the features that need them.

## Vendored assets

The build expects these files to already exist inside the repository:

- `packaging/vendor/windows/tesserocr-*.whl`
- `packaging/vendor/windows/tessdata/*.traineddata`
- optionally `packaging/runtime/windows/gs/bin/gswin64c.exe`

How you obtain those files is outside the scope of this repository. Keep that
step separate from the build machine if you must guarantee no network access.
