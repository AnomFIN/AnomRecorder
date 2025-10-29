#!/usr/bin/env python
"""Convert logo.png to icon format for Windows packaging.

This script converts the logo.png file to .ico format for use as the
application icon in Windows builds created with PyInstaller.
"""

from pathlib import Path
from PIL import Image


def main():
    logo_path = Path(__file__).parent / "logo.png"
    icon_path = Path(__file__).parent / "logo.ico"
    
    if not logo_path.exists():
        print(f"Error: {logo_path} not found")
        return 1
    
    try:
        img = Image.open(logo_path)
        
        # Convert to RGB if needed (ICO doesn't support RGBA well)
        if img.mode != 'RGB':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            else:
                background.paste(img)
            img = background
        
        # Create multiple sizes for better display at different resolutions
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(icon_path, format='ICO', sizes=sizes)
        
        print(f"✓ Icon created: {icon_path}")
        print(f"  Sizes: {', '.join(f'{w}x{h}' for w, h in sizes)}")
        return 0
    
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    exit(main())
