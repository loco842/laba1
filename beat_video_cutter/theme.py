"""Dark, minimalist theme for the BeatVideoCutter GUI.

Pure tkinter/ttk — no extra dependencies. Restyles the built-in 'clam'
theme to look modern: deep gray/black surfaces, subtle borders, no
pop-out 3D effects.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


PALETTE = {
    "bg":          "#0f0f10",
    "surface":     "#161618",
    "surface_2":   "#1c1c1f",
    "border":      "#2a2a2e",
    "border_soft": "#202024",
    "text":        "#e6e6e6",
    "text_dim":    "#9aa0a6",
    "text_faint":  "#6b7075",
    "accent":      "#e6e6e6",
    "accent_hover":"#ffffff",
    "danger":      "#e06c75",
    "progress":    "#8a8a8a",
    "field":       "#1f1f22",
    "field_focus": "#26262a",
    "select_bg":   "#3a3a3f",
}

FONT_FAMILY = "TkDefaultFont"


def apply_dark_theme(root: tk.Misc) -> ttk.Style:
    """Apply the dark theme to the given root and return the configured Style."""

    p = PALETTE
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=p["bg"])
    try:
        root.option_add("*Background", p["bg"])
        root.option_add("*Foreground", p["text"])
        root.option_add("*selectBackground", p["select_bg"])
        root.option_add("*selectForeground", p["text"])
        root.option_add("*insertBackground", p["text"])
        root.option_add("*highlightThickness", 0)
        root.option_add("*Font", (FONT_FAMILY, 10))
    except tk.TclError:
        pass

    style.configure(".",
        background=p["bg"],
        foreground=p["text"],
        fieldbackground=p["field"],
        bordercolor=p["border"],
        lightcolor=p["border"],
        darkcolor=p["border"],
        troughcolor=p["surface_2"],
        focuscolor=p["border"],
        font=(FONT_FAMILY, 10),
    )

    style.configure("TFrame", background=p["bg"])
    style.configure("Surface.TFrame", background=p["surface"])
    style.configure("Card.TFrame", background=p["surface"], relief="flat")

    style.configure("TLabel", background=p["bg"], foreground=p["text"])
    style.configure("Dim.TLabel", background=p["bg"], foreground=p["text_dim"])
    style.configure("Faint.TLabel", background=p["bg"], foreground=p["text_faint"])
    style.configure("Header.TLabel",
        background=p["bg"], foreground=p["text"],
        font=(FONT_FAMILY, 16, "bold"),
    )
    style.configure("Sub.TLabel",
        background=p["bg"], foreground=p["text_dim"],
        font=(FONT_FAMILY, 10),
    )
    style.configure("Section.TLabel",
        background=p["bg"], foreground=p["text_dim"],
        font=(FONT_FAMILY, 9, "bold"),
    )

    style.configure("TLabelframe",
        background=p["bg"], foreground=p["text_dim"],
        bordercolor=p["border_soft"], lightcolor=p["border_soft"], darkcolor=p["border_soft"],
        relief="solid", borderwidth=1,
    )
    style.configure("TLabelframe.Label",
        background=p["bg"], foreground=p["text_dim"],
        font=(FONT_FAMILY, 9, "bold"),
        padding=(6, 0),
    )

    style.configure("TButton",
        background=p["surface_2"], foreground=p["text"],
        bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"],
        focusthickness=0, relief="flat", padding=(14, 8),
    )
    style.map("TButton",
        background=[("active", p["border"]), ("pressed", p["border_soft"]), ("disabled", p["surface"])],
        foreground=[("disabled", p["text_faint"])],
        bordercolor=[("active", p["border"])],
    )

    style.configure("Accent.TButton",
        background=p["text"], foreground=p["bg"],
        bordercolor=p["text"], lightcolor=p["text"], darkcolor=p["text"],
        focusthickness=0, relief="flat", padding=(16, 9),
        font=(FONT_FAMILY, 10, "bold"),
    )
    style.map("Accent.TButton",
        background=[("active", p["accent_hover"]), ("pressed", p["text_dim"]), ("disabled", p["surface_2"])],
        foreground=[("disabled", p["text_faint"]), ("!disabled", p["bg"])],
    )

    style.configure("TEntry",
        fieldbackground=p["field"], background=p["field"],
        foreground=p["text"], insertcolor=p["text"],
        bordercolor=p["border_soft"], lightcolor=p["border_soft"], darkcolor=p["border_soft"],
        padding=6,
    )
    style.map("TEntry",
        fieldbackground=[("focus", p["field_focus"])],
        bordercolor=[("focus", p["border"])],
        lightcolor=[("focus", p["border"])],
        darkcolor=[("focus", p["border"])],
    )

    style.configure("TCombobox",
        fieldbackground=p["field"], background=p["surface_2"],
        foreground=p["text"], arrowcolor=p["text_dim"],
        bordercolor=p["border_soft"], lightcolor=p["border_soft"], darkcolor=p["border_soft"],
        padding=5,
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", p["field"]), ("focus", p["field_focus"])],
        foreground=[("readonly", p["text"])],
        bordercolor=[("focus", p["border"])],
        arrowcolor=[("active", p["text"])],
    )
    try:
        root.option_add("*TCombobox*Listbox*Background", p["surface_2"])
        root.option_add("*TCombobox*Listbox*Foreground", p["text"])
        root.option_add("*TCombobox*Listbox*selectBackground", p["select_bg"])
        root.option_add("*TCombobox*Listbox*selectForeground", p["text"])
    except tk.TclError:
        pass

    style.configure("TCheckbutton",
        background=p["bg"], foreground=p["text"],
        indicatorbackground=p["field"], indicatorforeground=p["text"],
        focuscolor=p["bg"],
        padding=4,
    )
    style.map("TCheckbutton",
        background=[("active", p["bg"])],
        foreground=[("disabled", p["text_faint"])],
        indicatorbackground=[("selected", p["text"]), ("pressed", p["text_dim"])],
        indicatorforeground=[("selected", p["bg"])],
    )

    style.configure("Horizontal.TProgressbar",
        background=p["progress"], troughcolor=p["surface_2"],
        bordercolor=p["surface_2"], lightcolor=p["progress"], darkcolor=p["progress"],
        thickness=6,
    )

    style.configure("Vertical.TScrollbar",
        background=p["surface_2"], troughcolor=p["bg"],
        bordercolor=p["bg"], arrowcolor=p["text_dim"],
        lightcolor=p["surface_2"], darkcolor=p["surface_2"],
    )
    style.map("Vertical.TScrollbar",
        background=[("active", p["border"])],
        arrowcolor=[("active", p["text"])],
    )

    style.configure("TSeparator", background=p["border_soft"])

    return style


def style_text_widget(widget: tk.Text) -> None:
    """Apply dark styling to a plain tk.Text widget (no ttk equivalent)."""
    p = PALETTE
    widget.configure(
        bg=p["surface"],
        fg=p["text"],
        insertbackground=p["text"],
        selectbackground=p["select_bg"],
        selectforeground=p["text"],
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=p["border_soft"],
        highlightcolor=p["border"],
        padx=10,
        pady=8,
        font=(FONT_FAMILY, 10),
    )
