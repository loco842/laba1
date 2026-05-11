"""Modern, minimalist tkinter GUI for BeatVideoCutter (dark theme)."""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from .config import Config
from .editor import run_edit
from .theme import PALETTE, apply_dark_theme, style_text_widget


APP_TITLE = "BeatVideoCutter"


class BeatVideoCutterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x720")
        self.minsize(820, 640)

        self._queue: "queue.Queue[tuple]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._cancel_flag = threading.Event()

        self.style = apply_dark_theme(self)

        self._build_ui()
        self.after(100, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- UI ----------

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=(24, 20, 24, 16))
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text="BeatVideoCutter", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Автоматический видеомонтаж в такт музыке",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        ttk.Separator(outer, orient="horizontal").pack(fill="x", pady=(0, 16))

        # ----- Files -----
        ttk.Label(outer, text="ИСХОДНЫЕ ФАЙЛЫ", style="Section.TLabel").pack(anchor="w")
        files = ttk.Frame(outer)
        files.pack(fill="x", pady=(8, 18))
        files.columnconfigure(1, weight=1)

        self.var_video_dir = tk.StringVar()
        self.var_audio = tk.StringVar()
        self.var_output = tk.StringVar(value=os.path.abspath("output.mp4"))

        self._row_path(files, "Папка с видео",  self.var_video_dir, self._browse_video_dir, row=0)
        self._row_path(files, "Аудиофайл",      self.var_audio,     self._browse_audio,     row=1)
        self._row_path(files, "Файл результата", self.var_output,    self._browse_output,    row=2)

        # ----- Parameters -----
        ttk.Label(outer, text="ПАРАМЕТРЫ МОНТАЖА", style="Section.TLabel").pack(anchor="w")
        params = ttk.Frame(outer)
        params.pack(fill="x", pady=(8, 14))
        for c in (1, 3):
            params.columnconfigure(c, weight=1, uniform="p")

        self.var_clip_duration = tk.DoubleVar(value=2.0)
        self.var_beat_divider  = tk.IntVar(value=1)
        self.var_min_remains   = tk.DoubleVar(value=0.5)
        self.var_width         = tk.StringVar(value="")
        self.var_height        = tk.StringVar(value="")
        self.var_fps           = tk.IntVar(value=30)
        self.var_keep_audio    = tk.BooleanVar(value=False)
        self.var_audio_mix     = tk.DoubleVar(value=0.2)
        self.var_codec_v       = tk.StringVar(value="libx264")
        self.var_codec_a       = tk.StringVar(value="aac")
        self.var_preset        = tk.StringVar(value="medium")
        self.var_bitrate       = tk.StringVar(value="")
        self.var_fit_mode      = tk.StringVar(value="loop")
        self.var_seed          = tk.StringVar(value="")

        rows = [
            ("Длина фрагмента, сек",        self.var_clip_duration, "entry"),
            ("Делитель битов",              self.var_beat_divider,  "entry"),
            ("Мин. остаток, сек",           self.var_min_remains,   "entry"),
            ("FPS",                         self.var_fps,           "entry"),
            ("Ширина",                      self.var_width,         "entry"),
            ("Высота",                      self.var_height,        "entry"),
            ("Подгонка длины",              self.var_fit_mode,      "fit"),
            ("Seed (опц.)",                 self.var_seed,          "entry"),
            ("Видеокодек",                  self.var_codec_v,       "entry"),
            ("Аудиокодек",                  self.var_codec_a,       "entry"),
            ("Preset",                      self.var_preset,        "preset"),
            ("Битрейт (напр. 4M)",          self.var_bitrate,       "entry"),
        ]

        for i, (label, var, kind) in enumerate(rows):
            r, c = divmod(i, 2)
            ttk.Label(params, text=label, style="Dim.TLabel").grid(
                row=r, column=c * 2, sticky="w", padx=(0, 10), pady=5,
            )
            if kind == "fit":
                w = ttk.Combobox(
                    params, textvariable=var, values=("loop", "speed", "trim"),
                    state="readonly",
                )
            elif kind == "preset":
                w = ttk.Combobox(
                    params, textvariable=var,
                    values=("ultrafast", "superfast", "veryfast", "faster",
                            "fast", "medium", "slow", "slower", "veryslow"),
                    state="readonly",
                )
            else:
                w = ttk.Entry(params, textvariable=var)
            w.grid(row=r, column=c * 2 + 1, sticky="we", padx=(0, 24 if c == 0 else 0), pady=5)

        # checkbox + mix ratio
        audio_row = ttk.Frame(outer)
        audio_row.pack(fill="x", pady=(2, 12))
        ttk.Checkbutton(
            audio_row,
            text="Сохранять оригинальный звук видео (микшировать с музыкой)",
            variable=self.var_keep_audio,
        ).pack(side="left")
        ttk.Label(audio_row, text="  Доля музыки", style="Dim.TLabel").pack(side="left", padx=(18, 6))
        ttk.Entry(audio_row, textvariable=self.var_audio_mix, width=6).pack(side="left")

        ttk.Separator(outer, orient="horizontal").pack(fill="x", pady=(4, 14))

        # ----- Control row -----
        ctrl = ttk.Frame(outer)
        ctrl.pack(fill="x")
        self.btn_start = ttk.Button(ctrl, text="Старт", style="Accent.TButton", command=self._on_start)
        self.btn_start.pack(side="left")
        self.btn_cancel = ttk.Button(ctrl, text="Отмена", command=self._on_cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=(10, 0))

        self.var_status = tk.StringVar(value="Готов к работе")
        ttk.Label(ctrl, textvariable=self.var_status, style="Faint.TLabel").pack(side="right")

        self.progress = ttk.Progressbar(outer, mode="determinate", maximum=1000)
        self.progress.pack(fill="x", pady=(14, 14))

        # ----- Log -----
        ttk.Label(outer, text="ЖУРНАЛ", style="Section.TLabel").pack(anchor="w")
        log_wrap = tk.Frame(outer, bg=PALETTE["bg"], highlightthickness=0)
        log_wrap.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(log_wrap, height=10, wrap="word", state="disabled")
        style_text_widget(self.log)
        sb = ttk.Scrollbar(log_wrap, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

    def _row_path(self, parent, label, var, cmd, row) -> None:
        ttk.Label(parent, text=label, style="Dim.TLabel").grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=5,
        )
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="we", pady=5)
        ttk.Button(parent, text="Обзор", command=cmd).grid(
            row=row, column=2, padx=(10, 0), pady=5,
        )

    # ---------- Browsers ----------

    def _browse_video_dir(self) -> None:
        p = filedialog.askdirectory(title="Выберите папку с видео")
        if p:
            self.var_video_dir.set(p)

    def _browse_audio(self) -> None:
        p = filedialog.askopenfilename(
            title="Выберите аудиофайл",
            filetypes=[
                ("Аудиофайлы", "*.wav *.mp3 *.aac *.flac *.ogg *.m4a"),
                ("Все файлы", "*.*"),
            ],
        )
        if p:
            self.var_audio.set(p)

    def _browse_output(self) -> None:
        p = filedialog.asksaveasfilename(
            title="Куда сохранить результат",
            defaultextension=".mp4",
            initialfile="output.mp4",
            filetypes=[("MP4", "*.mp4"), ("Все файлы", "*.*")],
        )
        if p:
            self.var_output.set(p)

    # ---------- Run / cancel ----------

    def _collect_config(self) -> Config:
        def _opt_int(s: str):
            s = (s or "").strip()
            return int(s) if s else None

        def _opt_str(s: str):
            s = (s or "").strip()
            return s or None

        seed_str = (self.var_seed.get() or "").strip()
        seed = int(seed_str) if seed_str else None

        return Config(
            video_input_dir=self.var_video_dir.get().strip(),
            audio_file=self.var_audio.get().strip(),
            output_file=self.var_output.get().strip() or "output.mp4",
            clip_duration=float(self.var_clip_duration.get()),
            beat_divider=int(self.var_beat_divider.get()),
            min_clip_remains=float(self.var_min_remains.get()),
            output_width=_opt_int(self.var_width.get()),
            output_height=_opt_int(self.var_height.get()),
            output_fps=int(self.var_fps.get()),
            keep_original_audio=bool(self.var_keep_audio.get()),
            audio_mix_ratio=float(self.var_audio_mix.get()),
            codec_video=self.var_codec_v.get().strip() or "libx264",
            codec_audio=self.var_codec_a.get().strip() or "aac",
            preset=self.var_preset.get().strip() or "medium",
            bitrate=_opt_str(self.var_bitrate.get()),
            length_fit_mode=self.var_fit_mode.get() or "loop",
            random_seed=seed,
        )

    def _on_start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        try:
            cfg = self._collect_config()
            cfg.validate()
        except Exception as e:
            messagebox.showerror("Ошибка параметров", str(e))
            return

        self._cancel_flag.clear()
        self._clear_log()
        self._log(f"Старт. Видео: {cfg.video_input_dir}")
        self._log(f"Аудио: {cfg.audio_file}")
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.var_status.set("Работаю…")
        self.progress.configure(value=0)

        self._worker = threading.Thread(target=self._run_pipeline, args=(cfg,), daemon=True)
        self._worker.start()

    def _on_cancel(self) -> None:
        if self._worker and self._worker.is_alive():
            self._cancel_flag.set()
            self.var_status.set("Останавливаю…")

    def _run_pipeline(self, cfg: Config) -> None:
        def progress_cb(pct: float, msg: str):
            self._queue.put(("progress", pct, msg))

        def cancel_check() -> bool:
            return self._cancel_flag.is_set()

        try:
            result = run_edit(cfg, progress=progress_cb, cancel_check=cancel_check)
            self._queue.put(("done", result))
        except Exception as e:
            tb = traceback.format_exc()
            self._queue.put(("error", str(e), tb))

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self._queue.get_nowait()
                kind = item[0]
                if kind == "progress":
                    _, pct, msg = item
                    self.progress.configure(value=max(0, min(1000, int(pct * 1000))))
                    self.var_status.set(msg)
                    self._log(msg)
                elif kind == "done":
                    _, result = item
                    self.progress.configure(value=1000)
                    self.var_status.set("Готово")
                    self._log(
                        f"Готово. Файл: {result.output_path}\n"
                        f"Длительность: {result.duration:.2f}с | "
                        f"Сегментов: {result.n_segments} | "
                        f"BPM: {result.tempo:.1f}"
                        + (" (fallback)" if result.used_fallback_beats else "")
                    )
                    self.btn_start.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                    messagebox.showinfo("Готово", f"Видео сохранено:\n{result.output_path}")
                elif kind == "error":
                    _, msg, tb = item
                    self.var_status.set("Ошибка")
                    self._log(f"ОШИБКА: {msg}\n{tb}")
                    self.btn_start.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                    messagebox.showerror("Ошибка", msg)
        except queue.Empty:
            pass
        finally:
            self.after(120, self._poll_queue)

    # ---------- Logging ----------

    def _log(self, msg: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _on_close(self) -> None:
        if self._worker and self._worker.is_alive():
            self._cancel_flag.set()
        self.destroy()


def main() -> None:
    app = BeatVideoCutterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
