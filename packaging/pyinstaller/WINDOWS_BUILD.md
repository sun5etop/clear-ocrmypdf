# Windows 从 0 开始打包指南

本文档说明如何在 Windows 上，从一个空白 Python 环境开始，将当前项目打包为可直接运行的 `.exe` 图形程序。

## 1. 前提说明

当前仓库已经集成了以下离线 OCR 运行时资源：

- `tesserocr`
- `libtesseract.dll`
- `libleptonica.dll`
- `tessdata/*.traineddata`

这意味着：

- 用户不需要单独安装 `Tesseract.exe`
- 打包后的程序可以直接使用内置 OCR 引擎

但需要注意：

- 如果目标机器完全离线，还需要提前准备 Python 依赖的离线 `wheelhouse`
- 如果需要 `pdfa` 输出，还要额外提供 `Ghostscript`

## 2. Python 版本要求

建议使用：

- 64 位 Python `3.12`

也支持：

- 64 位 Python `3.11`

原因是仓库当前已内置对应版本的 Windows `tesserocr` wheel：

- `cp311`
- `cp312`

## 3. 创建虚拟环境

在仓库根目录执行：

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
```

## 4. 安装 Python 依赖

### 4.1 联网环境

如果 Windows 机器可以联网，直接执行：

```bat
python -m pip install -r requirements.txt
```

### 4.2 离线环境

如果 Windows 机器完全离线，需要先在一台联网机器准备依赖包：

```bat
py -3.12 -m pip download -r requirements.txt -d wheelhouse
```

将 `wheelhouse\` 复制到离线 Windows 后执行：

```bat
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
```

## 5. 安装内置 OCR Runtime

仓库已经内置以下资源：

- `packaging\vendor\windows\tesserocr-*.whl`
- `packaging\vendor\windows\tessdata\*.traineddata`

执行下面的脚本：

```bat
packaging\pyinstaller\install_windows_embedded_ocr.bat
```

该脚本会：

1. 将本地 `tesserocr` wheel 安装到当前 `.venv`
2. 将 `tessdata` 复制到 `packaging\runtime\windows\tessdata\`

## 6. 可选：加入 Ghostscript

如果你只需要普通 `pdf` 输出，可以跳过这一步。

如果你要让打包后的 GUI 支持 `pdfa`，请准备：

```text
packaging\runtime\windows\gs\bin\gswin64c.exe
```

## 7. 开始打包

最简单的打包方式：

```bat
packaging\pyinstaller\build_windows.bat
```

如果必须要求支持 PDF/A：

```bat
packaging\pyinstaller\build_windows.bat --require-gs
```

## 8. 输出位置

打包完成后，产物位于：

- 目录：`dist\OCRmyPDF\`
- 压缩包：`dist\OCRmyPDF-windows.zip`

## 9. 建议先做自检

打包前建议先确认环境正常：

```bat
.venv\Scripts\python.exe -c "import ocrmypdf, tesserocr; print(ocrmypdf.__version__); print(tesserocr.tesseract_version())"
.venv\Scripts\python.exe -m PyInstaller --version
```

## 10. 最短流程总结

联网 Windows：

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
packaging\pyinstaller\install_windows_embedded_ocr.bat
packaging\pyinstaller\build_windows.bat
```

离线 Windows：

1. 先在联网机器准备 `wheelhouse`
2. 将仓库和 `wheelhouse` 一起复制到离线机器
3. 安装依赖
4. 执行 `install_windows_embedded_ocr.bat`
5. 执行 `build_windows.bat`
