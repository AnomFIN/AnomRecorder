"""Application entry point for AnomRecorder.

Why this design:
- Configure logging before UI boot to capture early failures.
- Keep Tk initialization in a minimal wrapper for reuse by other CLIs.
- Provide a callable `main` for tests and packaging scripts.
"""

from __future__ import annotations

import logging
import sys
import tkinter as tk
from tkinter import messagebox

from .ui.app import CameraApp

# Engineered for autonomy, designed for humans.


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main() -> None:
    configure_logging()
    root = tk.Tk()
    try:
        CameraApp(root)
        root.mainloop()
    except Exception as exc:  # pragma: no cover - UI level safety net
        logging.getLogger("anomrecorder").exception("fatal", exc_info=exc)
        messagebox.showerror("Virhe", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
