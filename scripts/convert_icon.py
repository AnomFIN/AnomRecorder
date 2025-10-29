#!/usr/bin/env python3
"""Convert logo.png to icon formats for packaging.

Requires: pip install pillow
"""

from pathlib import Path
from PIL import Image


def convert_logo_to_icons():
    """Convert logo.png to .ico and .icns formats."""
    logo_path = Path(__file__).parent.parent / "logo.png"
    
    if not logo_path.exists():
        print(f"Error: {logo_path} not found")
        return False
    
    try:
        img = Image.open(logo_path)
        
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create .ico for Windows (multiple sizes)
        ico_path = logo_path.with_suffix('.ico')
        img.save(
            ico_path,
            format='ICO',
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )
        print(f"✓ Created {ico_path}")
        
        # Create .icns for macOS (requires pillow-icns or manual conversion)
        # Note: Full .icns support requires additional tools or libraries
        # For basic support, we'll create a PNG at standard icon size
        icns_temp = logo_path.parent / "logo_256.png"
        img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
        img_256.save(icns_temp)
        print(f"✓ Created {icns_temp} (for .icns conversion)")
        print("  Note: Convert to .icns using 'png2icns' or macOS iconutil")
        print("  Example: png2icns logo.icns logo_256.png")
        
        return True
        
    except Exception as exc:
        print(f"Error converting icon: {exc}")
        return False


if __name__ == "__main__":
    import sys
    success = convert_logo_to_icons()
    sys.exit(0 if success else 1)
