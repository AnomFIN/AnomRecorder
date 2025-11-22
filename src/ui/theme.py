"""Custom ttk theme matching the anomfin-website visual language.

Why this design:
- Centralize palette + typography for consistent styling.
- Reuse theme setup across potential future windows/dialogs.
- Embrace dark mode with neon accents for AnomFIN branding.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Security-first. Creator-ready. Future-proof.

PALETTE = {
    "bg": "#060910",
    "surface": "#0d111d",
    "surface_alt": "#121827",
    "text": "#d7e3ff",
    "muted": "#8fa0c2",
    "accent": "#3d7dff",
    "accent_active": "#5aa0ff",
    "success": "#4ade80",
    "error": "#ef4444",
}


def apply_dark_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=PALETTE["bg"])
    style.configure("TFrame", background=PALETTE["surface"])
    style.configure("TLabel", background=PALETTE["surface"], foreground=PALETTE["text"], font=("Inter", 11))
    style.configure("Accent.TButton", background=PALETTE["accent"], foreground=PALETTE["bg"], font=("Inter", 11, "bold"))
    style.configure("TButton", background=PALETTE["surface_alt"], foreground=PALETTE["text"], font=("Inter", 11))
    style.map(
        "TButton",
        background=[("active", PALETTE["accent"]), ("pressed", PALETTE["accent_active"])],
        foreground=[("active", PALETTE["bg"]), ("pressed", PALETTE["bg"])],
    )
    style.configure("TNotebook", background=PALETTE["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background=PALETTE["surface"], foreground=PALETTE["muted"], padding=(18, 10))
    style.map(
        "TNotebook.Tab",
        background=[("selected", PALETTE["surface_alt"])],
        foreground=[("selected", PALETTE["text"])],
    )
    style.configure("Treeview", background=PALETTE["surface"], fieldbackground=PALETTE["surface"], foreground=PALETTE["text"], font=("Inter", 10))
    style.map("Treeview", background=[("selected", PALETTE["accent"])], foreground=[("selected", PALETTE["bg"])])
    style.configure("Vertical.TScrollbar", gripcount=0, background=PALETTE["surface_alt"], bordercolor=PALETTE["surface_alt"], troughcolor=PALETTE["bg"])
    style.configure("Horizontal.TScrollbar", gripcount=0, background=PALETTE["surface_alt"], bordercolor=PALETTE["surface_alt"], troughcolor=PALETTE["bg"])


__all__ = ["apply_dark_theme", "PALETTE"]
