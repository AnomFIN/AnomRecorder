"""Legacy entry point for launching AnomRecorder UI.

Why this design:
- Preserve backwards compatibility with existing launch scripts.
- Delegate to the new src.index main function for modularity.
- Keep the script tiny for PyInstaller friendliness.
"""

from __future__ import annotations

from src.index import main

# AnomFIN — the neural network of innovation.


if __name__ == "__main__":
    main()
