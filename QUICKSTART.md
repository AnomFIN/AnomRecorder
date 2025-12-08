# AnomRecorder - Quick Start Guide

## What is AnomRecorder?

AnomRecorder is a USB camera surveillance system for Windows that provides:
- Real-time viewing of 1-2 USB cameras
- Automatic motion and person detection
- Event-based recording
- Playback of recorded videos
- Screenshot capture
- Logo overlay support
- Local storage with automatic cleanup

**100% Offline** - No cloud connections, all data stays on your computer.

## Quick Start

### Option 1: Run from Python (Recommended)

1. Install dependencies with the automated installer:
   
   **Windows:**
   ```batch
   install_dependencies.bat
   ```
   
   **Linux/Mac/CLI:**
   ```bash
   python install.py
   ```
   
   The installer will:
   - Check system requirements
   - Install all dependencies
   - Test the installation
   - Automatically fix any errors
   - Verify the application works

2. Run the application:
   ```batch
   python usb_cam_viewer.py
   ```

### Option 2: Build Standalone .exe

1. Build the executable:
   ```batch
   build.bat
   ```

2. Run the program:
   ```
   dist\AnomRecorder.exe
   ```

## First Launch

When you first start AnomRecorder:

1. The camera window will open automatically
2. Your USB camera(s) will start streaming
3. Motion and person detection are enabled by default
4. Recording will start automatically when motion or a person is detected

## Main Controls

- **Start**: Begin camera streaming
- **Stop**: Stop camera streaming
- **Screenshot**: Save current frame from all cameras
- **Playback**: View recorded videos
- **Settings**: Configure application

## Settings Overview

### Camera Settings
- **Camera Indices**: Which USB cameras to use (0, 1, etc.)
- **Resolution**: Video resolution (default: 640x480)
- **FPS**: Frames per second (default: 30)

### Detection Settings
- **Motion Detection**: Enable/disable motion detection
- **Person Detection**: Enable/disable person detection (HOG-SVM)
- **Motion Threshold**: Sensitivity (lower = more sensitive)
- **Motion Min Area**: Minimum size for motion detection

### Recording Settings
- **Recording Duration**: How long to record after motion detected (seconds)
- **Max Storage**: Maximum disk space for recordings (GB)
- **Recordings Path**: Where to save recordings

### Logo Settings
- **Logo Path**: Path to your logo image file
- **Logo Position**: Corner placement (top-left, top-right, etc.)
- **Logo Scale**: Size of the logo (0.0 to 1.0)

## File Locations

- **Recordings**: Stored in `recordings/` folder
- **Screenshots**: Stored in `screenshots/` folder
- **Configuration**: Saved in `config.json`

## System Requirements

- Windows 10 or newer
- Python 3.8+ (for running from source)
- USB camera(s)
- 4GB RAM minimum
- Adequate disk space for recordings

## Troubleshooting

**Camera not detected?**
- Check USB connection
- Try different camera indices in Settings (0, 1, 2, etc.)
- Test camera with Windows Camera app first

**Person detection not working?**
- Ensure good lighting
- Person should be standing upright
- Increase resolution if needed

**Performance issues?**
- Lower the resolution
- Reduce FPS
- Disable person detection (CPU intensive)
- Use only one camera

## Privacy & Security

- ✓ No internet connection required
- ✓ No data sent to any servers
- ✓ All recordings stored locally
- ✓ No telemetry or analytics
- ✓ Open source - you can review the code

## Support

For issues or questions, please refer to the main README.md (Finnish documentation).

## License

Free to use and modify.
