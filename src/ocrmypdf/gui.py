# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF 的简易 Tk 桌面界面。"""

from __future__ import annotations

import logging
import os
import queue
import threading
import sys
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    BooleanVar,
    StringVar,
    Tk,
    filedialog,
    messagebox,
)
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import ocrmypdf
from ocrmypdf import ExitCode


class QueueLogHandler(logging.Handler):
    """Send log lines from the worker thread to the GUI."""

    def __init__(self, log_queue: queue.Queue[str]):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:  # pragma: no cover - logging fallback
            message = record.getMessage()
        self.log_queue.put(message)


class OcrmypdfGui(Tk):
    """用于常见 OCRmyPDF 任务的简易桌面应用。"""

    def __init__(self):
        super().__init__()
        self.title("OCRmyPDF 桌面版")
        self.geometry("760x560")
        self.minsize(680, 500)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.input_path = StringVar()
        self.output_path = StringVar()
        self.language = StringVar(value='eng')
        self.output_type = StringVar(value='pdf')
        self.mode = StringVar(value='skip')
        self.status = StringVar(value='就绪')
        self.runtime_hint = StringVar(value=get_gui_runtime_hint())

        self.rotate_pages = BooleanVar(value=True)
        self.deskew = BooleanVar(value=False)

        self._build()
        self._configure_runtime_options()
        self.after(100, self._drain_logs)

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=BOTH, expand=True)

        ttk.Label(root, text="输入文件").grid(row=0, column=0, sticky='w')
        ttk.Entry(root, textvariable=self.input_path).grid(
            row=1, column=0, sticky='ew', padx=(0, 8)
        )
        ttk.Button(root, text="浏览...", command=self._select_input).grid(
            row=1, column=1, sticky='ew'
        )

        ttk.Label(root, text="输出文件").grid(row=2, column=0, sticky='w', pady=(12, 0))
        ttk.Entry(root, textvariable=self.output_path).grid(
            row=3, column=0, sticky='ew', padx=(0, 8)
        )
        ttk.Button(root, text="另存为...", command=self._select_output).grid(
            row=3, column=1, sticky='ew'
        )

        options = ttk.LabelFrame(root, text="选项", padding=12)
        options.grid(row=4, column=0, columnspan=2, sticky='nsew', pady=(16, 0))

        ttk.Label(options, text="语言").grid(row=0, column=0, sticky='w')
        ttk.Entry(options, textvariable=self.language, width=18).grid(
            row=1, column=0, sticky='w', padx=(0, 12)
        )

        ttk.Label(options, text="输出类型").grid(row=0, column=1, sticky='w')
        self.output_type_combo = ttk.Combobox(
            options,
            textvariable=self.output_type,
            values=('pdf', 'pdfa'),
            state='readonly',
            width=12,
        )
        self.output_type_combo.grid(row=1, column=1, sticky='w', padx=(0, 12))

        ttk.Label(options, text="处理模式").grid(row=0, column=2, sticky='w')
        ttk.Combobox(
            options,
            textvariable=self.mode,
            values=('skip', 'force', 'redo'),
            state='readonly',
            width=12,
        ).grid(row=1, column=2, sticky='w')

        ttk.Checkbutton(
            options, text="自动旋转页面", variable=self.rotate_pages
        ).grid(row=2, column=0, sticky='w', pady=(12, 0))
        ttk.Checkbutton(options, text="纠偏", variable=self.deskew).grid(
            row=2, column=1, sticky='w', pady=(12, 0)
        )
        ttk.Label(
            options,
            textvariable=self.runtime_hint,
            wraplength=560,
        ).grid(row=3, column=0, columnspan=3, sticky='w', pady=(12, 0))

        controls = ttk.Frame(root)
        controls.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(16, 0))
        self.start_button = ttk.Button(controls, text="开始 OCR", command=self.start)
        self.start_button.pack(side=LEFT)
        ttk.Button(controls, text="清空日志", command=self._clear_log).pack(
            side=LEFT, padx=(8, 0)
        )
        ttk.Label(controls, textvariable=self.status).pack(side=RIGHT)

        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(12, 0))

        self.log_widget = ScrolledText(root, height=16, state='disabled')
        self.log_widget.grid(row=7, column=0, columnspan=2, sticky='nsew', pady=(12, 0))

        root.columnconfigure(0, weight=1)
        root.rowconfigure(7, weight=1)

    def _select_input(self) -> None:
        selected = filedialog.askopenfilename(
            title="选择输入 PDF 或图片",
            filetypes=[
                ("PDF 和图片", "*.pdf *.png *.jpg *.jpeg *.tif *.tiff *.bmp"),
                ("所有文件", "*.*"),
            ],
        )
        if not selected:
            return
        self.input_path.set(selected)
        if not self.output_path.get():
            output = str(Path(selected).with_name(Path(selected).stem + '_ocr.pdf'))
            self.output_path.set(output)

    def _select_output(self) -> None:
        selected = filedialog.asksaveasfilename(
            title="选择输出 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 文件", "*.pdf")],
        )
        if selected:
            self.output_path.set(selected)

    def _append_log(self, message: str) -> None:
        self.log_widget.configure(state='normal')
        self.log_widget.insert(END, message.rstrip() + '\n')
        self.log_widget.see(END)
        self.log_widget.configure(state='disabled')

    def _clear_log(self) -> None:
        self.log_widget.configure(state='normal')
        self.log_widget.delete('1.0', END)
        self.log_widget.configure(state='disabled')

    def _drain_logs(self) -> None:
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(message)
        self.after(100, self._drain_logs)

    def _set_busy(self, busy: bool) -> None:
        if busy:
            self.start_button.configure(state='disabled')
            self.progress.start(10)
        else:
            self.start_button.configure(state='normal')
            self.progress.stop()

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            return

        input_path = Path(self.input_path.get()).expanduser()
        output_path = Path(self.output_path.get()).expanduser()
        if not input_path.exists():
            messagebox.showerror("输入无效", "输入文件不存在。")
            return
        if not output_path.parent.exists():
            messagebox.showerror("输出无效", "输出目录不存在。")
            return

        self._clear_log()
        self._set_busy(True)
        self.status.set("运行中")
        self.worker = threading.Thread(
            target=self._run_ocr, args=(input_path, output_path), daemon=True
        )
        self.worker.start()

    def _run_ocr(self, input_path: Path, output_path: Path) -> None:
        logger = logging.getLogger('ocrmypdf')
        handler = QueueLogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter('%(message)s'))

        old_handlers = list(logger.handlers)
        old_level = logger.level
        old_propagate = logger.propagate

        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        logger.propagate = False

        try:
            ocr_kwargs = get_gui_ocr_kwargs(
                output_type=self.output_type.get(),
                frozen=getattr(sys, 'frozen', False),
                platform=sys.platform,
            )
            exit_code = ocrmypdf.ocr(
                input_path,
                output_path,
                language=[
                    lang.strip()
                    for lang in self.language.get().replace('+', ',').split(',')
                    if lang.strip()
                ]
                or ['eng'],
                output_type=self.output_type.get(),
                mode=self.mode.get(),
                rotate_pages=self.rotate_pages.get(),
                deskew=self.deskew.get(),
                optimize=0,
                progress_bar=False,
                use_threads=True,
                **ocr_kwargs,
            )
            if exit_code == ExitCode.ok:
                self.log_queue.put(f"处理完成：{output_path}")
                self.after(0, lambda: self.status.set("已完成"))
            else:
                self.log_queue.put(f"OCR 失败，退出码：{exit_code}")
                self.after(0, lambda: self.status.set("失败"))
        except Exception as exc:  # pragma: no cover - GUI error path
            self.log_queue.put(f"错误：{exc}")
            self.after(0, lambda: self.status.set("失败"))
        finally:
            logger.handlers = old_handlers
            logger.setLevel(old_level)
            logger.propagate = old_propagate
            self.after(0, lambda: self._set_busy(False))

    def _configure_runtime_options(self) -> None:
        if not running_frozen_windows_bundle(
            frozen=getattr(sys, 'frozen', False), platform=sys.platform
        ):
            return
        if not has_bundled_ghostscript():
            self.output_type_combo.configure(values=('pdf',))
            if self.output_type.get() != 'pdf':
                self.output_type.set('pdf')


def main() -> None:
    _configure_tk_runtime()
    app = OcrmypdfGui()
    app.mainloop()


def running_frozen_windows_bundle(*, frozen: bool, platform: str) -> bool:
    """Return True when the GUI is running from a packaged Windows app."""
    return frozen and platform == 'win32'


def get_gui_ocr_kwargs(
    *, output_type: str, frozen: bool, platform: str
) -> dict[str, str]:
    """Return OCR settings that are safe for the desktop GUI runtime."""
    del output_type
    kwargs: dict[str, str] = {}
    if running_frozen_windows_bundle(frozen=frozen, platform=platform):
        # The Windows bundle ships libtesseract/tesserocr, but not tesseract.exe.
        kwargs['ocr_engine'] = 'tesserocr'
        kwargs['pdf_renderer'] = 'auto'
    return kwargs


def has_bundled_ghostscript() -> bool:
    """Return True when the packaged Windows app can find gswin64c.exe."""
    for env_var in ('OCRMYPDF_GS', 'OCRMYPDF_GHOSTSCRIPT'):
        configured = os.environ.get(env_var)
        if configured and Path(configured).is_file():
            return True

    bundle_roots: list[Path] = []
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        bundle_roots.append(Path(meipass))
    bundle_roots.append(Path(sys.executable).resolve().parent)

    for root in bundle_roots:
        for relative in (
            Path('ocrmypdf_runtime/gs/bin/gswin64c.exe'),
            Path('runtime/gs/bin/gswin64c.exe'),
            Path('gs/bin/gswin64c.exe'),
        ):
            if (root / relative).is_file():
                return True
    return False


def get_gui_runtime_hint(*, frozen: bool | None = None, platform: str | None = None) -> str:
    """Return the hint text shown in the desktop GUI."""
    if frozen is None:
        frozen = getattr(sys, 'frozen', False)
    if platform is None:
        platform = sys.platform

    if not running_frozen_windows_bundle(frozen=frozen, platform=platform):
        return "提示：桌面打包版默认使用内置 libtesseract，并避免调用外部 tesseract.exe。"
    if has_bundled_ghostscript():
        return "提示：当前打包版使用内置 libtesseract；已检测到 Ghostscript，可输出 PDF/A。"
    return "提示：当前打包版使用内置 libtesseract；未检测到 Ghostscript，已禁用 PDF/A。"


def _configure_tk_runtime() -> None:
    """Point tkinter to a usable Tcl/Tk runtime when Python cannot find one."""
    if os.environ.get('TCL_LIBRARY') and os.environ.get('TK_LIBRARY'):
        return

    python_root = Path(sys.executable).resolve().parents[1]
    uv_python_root = Path(sys.base_prefix)
    candidates = [
        (
            uv_python_root / 'lib' / 'tcl8.6',
            uv_python_root / 'lib' / 'tk8.6',
        ),
        (
            python_root / 'lib' / 'tcl8.6',
            python_root / 'lib' / 'tk8.6',
        ),
        (
            Path('/opt/homebrew/opt/tcl-tk@8/lib/tcl8.6'),
            Path('/opt/homebrew/opt/tcl-tk@8/lib/tk8.6'),
        ),
        (
            Path('/opt/homebrew/Cellar/tcl-tk@8/8.6.17/lib/tcl8.6'),
            Path('/opt/homebrew/Cellar/tcl-tk@8/8.6.17/lib/tk8.6'),
        ),
        (
            Path('/opt/homebrew/opt/tcl-tk/lib/tcl9.0'),
            Path('/opt/homebrew/opt/tcl-tk/lib/tk9.0'),
        ),
        (
            Path('/opt/homebrew/Cellar/tcl-tk/9.0.3/lib/tcl9.0'),
            Path('/opt/homebrew/Cellar/tcl-tk/9.0.3/lib/tk9.0'),
        ),
    ]

    for tcl_dir, tk_dir in candidates:
        if (tcl_dir / 'init.tcl').exists() and (tk_dir / 'tk.tcl').exists():
            os.environ.setdefault('TCL_LIBRARY', str(tcl_dir))
            os.environ.setdefault('TK_LIBRARY', str(tk_dir))
            return


if __name__ == '__main__':
    main()
