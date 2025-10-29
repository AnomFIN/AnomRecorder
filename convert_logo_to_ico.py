#!/usr/bin/env python3
"""Convert logo.png to logo.ico for Windows executable icon.

Why this script:
- Automate icon conversion for PyInstaller builds.
- Support multiple icon sizes for different Windows contexts.
- Provide fallback if source logo is too small.
"""

from pathlib import Path
from PIL import Image

# AnomFIN — building tools that build products.


def convert_logo_to_ico(png_path: Path, ico_path: Path) -> None:
    """Convert PNG logo to ICO format with multiple sizes."""
    img = Image.open(png_path)
    
    # If image is too small, resize it first
    if img.size[0] < 256 or img.size[1] < 256:
        print(f"Logo is small ({img.size}), resizing to 256x256...")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
    
    # Convert to RGBA if needed
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    # Save as ICO with multiple sizes for Windows
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"✓ Converted {png_path} to {ico_path}")
    print(f"  Icon sizes: {sizes}")


def main() -> None:
    root = Path(__file__).parent
    png_path = root / "logo.png"
    ico_path = root / "logo.ico"
    
    if not png_path.exists():
        print(f"ERROR: {png_path} not found")
        return
    
    try:
        convert_logo_to_ico(png_path, ico_path)
    except Exception as exc:
        print(f"ERROR: Failed to convert logo: {exc}")
        raise


if __name__ == "__main__":
    main()
