# Icon Conversion Guide

## Converting logo.png to .ico

The `convert_icon.py` script converts the logo.png file to Windows .ico format for use in the packaged application.

### Usage

```bash
python convert_icon.py
```

This will create `logo.ico` with multiple sizes (16x16, 32x32, 48x48, 64x64, 128x128, 256x256) for optimal display at different resolutions.

### Build Integration

The icon is automatically used when building the Windows executable with `build.bat`:

```batch
build.bat
```

The resulting `dist\AnomRecorder.exe` will use the logo.ico as its application icon.

### Requirements

- Python 3.8+
- Pillow (already in requirements.txt)

### Notes

- If logo.png has transparency (RGBA), it will be converted to RGB with a white background
- The icon is optimized for Windows display
- Multiple sizes ensure crisp display in Windows Explorer, taskbar, and alt-tab switcher
