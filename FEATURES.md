# UI & Stability Improvements - User Guide

This document describes the new features and improvements added to AnomRecorder.

## New Features

### 1. Recording Indicator
- A live recording indicator is now displayed at the top-left of the Live view
- **Green (● Ei tallenna)**: No active recording
- **Red (● Tallentaa)**: Recording is active
- Updates automatically as recording starts and stops

### 2. Enhanced Zoom Controls

#### Zoom Out Support
- You can now zoom out below 1.0x to see the entire frame with black borders
- Zoom range: 0.5x - 4.0x (previously 1.0x - 4.0x)
- Use the `-` button to zoom out, `+` to zoom in, and `Reset` to return to 1.0x

#### Pan Controls
- Pan the zoomed view using:
  - **Arrow buttons**: ←↑↓→ buttons next to each zoom control
  - **Keyboard arrows**: Use arrow keys on your keyboard to pan
  - The active camera view will pan when using keyboard arrows
- Panning is bounded to keep the content within frame edges
- Works seamlessly while recording

### 3. Settings Tab Improvements

#### Logo Preview
- When you select a logo file, it now shows immediately in the Settings tab
- Preview displays the logo at a reasonable size
- No need to navigate away to see the logo

#### Explicit Save Button
- New **"Tallenna asetukset"** button to save all settings
- Settings are no longer auto-saved when you adjust sliders
- If recording is active, you'll be asked to confirm before saving
- Saving settings is safe and won't interrupt an active recording

### 4. Improved "Päivitä" Button
- The Päivitä (Refresh) button is now non-blocking
- It will not stop active cameras unnecessarily
- If recording is active and no cameras are found, it won't stop the cameras
- Better error messages if camera refresh fails

### 5. Better Error Handling
- All camera and I/O operations now have proper error handling
- User-friendly error messages in Finnish
- Errors are logged for troubleshooting
- The application continues running even if one operation fails

## Usage Tips

### Zooming and Panning
1. Select a zoom level using the +/- buttons
2. If zoomed in (>1.0x), use pan controls to move around:
   - Click arrow buttons next to zoom controls
   - Or use keyboard arrow keys
3. Press `Reset` to return to center at 1.0x zoom

### Safe Settings Changes
1. Make your desired changes in the Settings tab (logo, transparency, motion threshold, storage limit)
2. Click **"Tallenna asetukset"** when ready to save
3. If recording is active, you'll see a confirmation dialog
4. Settings will be applied without interrupting recording

### Recording Workflow
1. Watch the recording indicator at the top-left of Live view
2. Green means ready to record (waiting for motion/person detection)
3. Red means actively recording
4. You can safely:
   - Change zoom and pan
   - Navigate between tabs
   - Adjust settings (with explicit save)
   - Click Päivitä to refresh cameras

## Troubleshooting

### Camera Issues
- If a camera fails to start, you'll see an error message in Finnish
- Check USB connection and try Päivitä
- Error details are logged for debugging

### Settings Not Saving
- Make sure to click "Tallenna asetukset" after making changes
- If recording is active, confirm the dialog to proceed
- Check logs if save fails

### Zoom/Pan Not Working
- Ensure a camera is active and displaying video
- Keyboard arrows work on the active camera view
- Reset zoom if the view seems stuck

## Technical Notes

### Recording Safety
- All major operations are now safe during active recording
- Refresh cameras won't stop recording if cameras are found
- Settings save doesn't restart camera streams
- Frame processing errors are handled per-camera without crashing

### Error Logging
All errors are logged with details for troubleshooting. Check application logs if you encounter issues.
