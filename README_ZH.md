# OCRmyPDF 中文说明

OCRmyPDF 用于给扫描版 PDF 增加 OCR 文本层，使文档可以被搜索、复制和索引。

```bash
ocrmypdf                      # 命令行入口
   -l eng+chi_sim             # 支持多语言
   --rotate-pages             # 自动旋转页面
   --deskew                   # 页面纠偏
   --output-type pdf          # 输出普通 PDF
   input_scanned.pdf
   output_searchable.pdf
```

## 主要能力

- 将扫描 PDF 或图片转换为可搜索 PDF
- 尽量保留原始图像分辨率
- 支持 Tesseract 语言包的多语言 OCR
- 支持旋转、纠偏、优化与输出校验
- 可用于大批量多页文档处理

## 安装方式

支持 Linux、Windows、macOS 和 FreeBSD。

常见安装方式：

| 系统 | 命令 |
| --- | --- |
| Debian / Ubuntu | `apt install ocrmypdf` |
| Fedora | `dnf install ocrmypdf` |
| macOS (Homebrew) | `brew install ocrmypdf` |
| FreeBSD | `pkg install py-ocrmypdf` |

如果你正在使用这个仓库的离线桌面版能力，请优先查看本地文档：

- `docs/index.md`
- `docs/installation.md`
- `docs/languages.md`
- `packaging/pyinstaller/README.md`
- `packaging/pyinstaller/WINDOWS_BUILD.md`

## 帮助与文档

命令行帮助：

```bash
ocrmypdf --help
```

本仓库不再在说明文档中依赖外部网址，主要资料请直接查看仓库内 `docs/` 与 `packaging/` 目录。

## 本分支附加能力

- 进程内 `tesserocr` / `libtesseract` OCR 支持
- Tk 图形界面
- Windows 离线 PyInstaller 打包支持

## 依赖说明

除 Python 外，根据输出模式和 OCR 引擎配置，可能仍需要 Ghostscript 或 Tesseract 运行时。本分支支持将这些运行时以离线方式随桌面程序一起分发。

## 许可证

OCRmyPDF 软件采用 MPL-2.0 许可证。
