# Vendored Windows OCR runtime assets

Place offline Windows OCR assets here so the build machine does not need network access.

Expected files:

```text
packaging/vendor/windows/
  tesserocr-<version>-cp311-cp311-win_amd64.whl
  or
  tesserocr-<version>-cp312-cp312-win_amd64.whl
  tessdata/
    eng.traineddata
    osd.traineddata
    chi_sim.traineddata   # optional but recommended for Chinese OCR
```

Install them into `.venv` on Windows with:

```bat
packaging\pyinstaller\install_windows_embedded_ocr.bat
```
