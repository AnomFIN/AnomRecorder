"""Convert logo.png to Windows .ico format for application icon.

Usage:
    python scripts/create_icon.py
"""

from PIL import Image
from pathlib import Path


def create_icon():
    """Convert logo.png to app.ico."""
    logo_path = Path("logo.png")
    icon_path = Path("app.ico")
    
    if not logo_path.exists():
        print(f"Error: {logo_path} not found")
        return
    
    try:
        # Open logo
        img = Image.open(logo_path)
        
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create multiple sizes for Windows icon
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icon_images = []
        
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icon_images.append(resized)
        
        # Save as .ico
        icon_images[0].save(
            icon_path,
            format='ICO',
            sizes=sizes,
            append_images=icon_images[1:]
        )
        
        print(f"✓ Created {icon_path} with sizes: {sizes}")
        print(f"✓ Icon ready for Windows builds")
        
    except Exception as exc:
        print(f"Error creating icon: {exc}")


if __name__ == "__main__":
    create_icon()
