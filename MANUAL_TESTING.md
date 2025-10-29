# Manual Testing Guide

This guide provides step-by-step instructions for manually testing the comprehensive improvements to AnomRecorder.

## Prerequisites

- Python 3.8+ installed
- USB camera connected (or two cameras for dual-camera testing)
- All dependencies installed: `pip install -r requirements.txt`

## Test Scenarios

### 1. Non-blocking Camera Refresh

**Steps:**
1. Start the application: `python -m src.index`
2. Start a recording (enable motion detection or manually trigger)
3. Verify the recording indicator turns red and shows "● Tallentaa"
4. Click the "Päivitä" button
5. Observe that the UI remains responsive
6. Verify that recording continues without interruption
7. Check the status message shows "Päivitetään kameralistaa..."

**Expected Result:** ✅ Camera list refreshes without stopping recording or freezing UI

### 2. Enhanced Zoom and Pan

**Zoom Out Test:**
1. Select a camera from the list
2. Click the "-" button multiple times
3. Observe zoom level drops below 1.0x (to 0.75x, 0.5x)
4. Verify padded black borders appear around the zoomed-out image

**Zoom In Test:**
1. Click the "+" button multiple times
2. Observe zoom level increases above 1.0x (to 1.25x, 1.5x, etc.)
3. Verify the image crops to show detail

**Pan Test:**
1. Zoom in to at least 2.0x
2. Press arrow keys (↑↓←→) or click pan buttons
3. Observe the view pans in the correct direction
4. Try to pan beyond bounds and verify it stops at limits
5. Click "Reset" to return to center

**Ctrl+Wheel Test:**
1. Hold Ctrl and scroll mouse wheel
2. Verify zoom changes incrementally

**Expected Result:** ✅ All zoom and pan operations work smoothly with proper bounds

### 3. Settings Management

**Logo Preview Test:**
1. Go to Asetukset (Settings) tab
2. Click "Valitse" (Choose) under Logo
3. Select an image file (PNG, JPG, etc.)
4. Verify a small preview appears immediately next to the file path
5. Change transparency slider and observe changes in live view

**Save Settings Test:**
1. Modify any setting (storage limit, motion threshold, transparency)
2. Start a recording if not already recording
3. Click "Tallenna asetukset" button
4. Verify green checkmark appears: "✓ Asetukset tallennettu"
5. Verify recording continues uninterrupted
6. Close and restart the application
7. Verify all settings are restored from settings.json

**Expected Result:** ✅ Settings save atomically without interrupting recording

### 4. Hotkeys

**Test Each Hotkey:**
1. Press `R` → Verify camera list refreshes
2. Press `+` → Verify active camera zooms in
3. Press `-` → Verify active camera zooms out
4. Press `↑` → Verify camera view pans up
5. Press `↓` → Verify camera view pans down
6. Press `←` → Verify camera view pans left
7. Press `→` → Verify camera view pans right
8. Hold `Ctrl` and scroll wheel → Verify zoom changes

**Hotkey Display Test:**
1. Go to Asetukset tab
2. Locate "Pikanäppäimet" section
3. Verify all hotkeys are listed in Finnish

**Expected Result:** ✅ All hotkeys work and are documented in UI

### 5. Recordings Management

**Load Existing Test:**
1. Close the application
2. Manually place some .avi files in the `recordings/` directory
3. Start the application
4. Go to Tallenteet (Recordings) tab
5. Verify all existing recordings appear in the list

**Delete Single Recording:**
1. Select one recording from the list
2. Click "Poista valittu" (Delete selected)
3. Confirm the dialog
4. Verify the recording is removed from both list and disk

**Delete Multiple Recordings:**
1. Hold Ctrl and click multiple recordings to select them
2. Click "Poista valittu"
3. Confirm the deletion count matches
4. Verify all selected recordings are removed

**Delete All:**
1. Click "Poista kaikki" (Delete all)
2. Confirm the warning dialog
3. Verify all recordings are removed

**Expected Result:** ✅ Recording management works with proper confirmations

### 6. Recording Indicator

**Test Indicator States:**
1. Start the application with no motion
2. Verify indicator shows green "● Ei tallenna"
3. Enable motion detection and trigger motion
4. Verify indicator turns red "● Tallentaa"
5. Wait for motion to stop and post-recording delay
6. Verify indicator returns to green

**Expected Result:** ✅ Indicator accurately reflects recording state in real-time

### 7. Camera Autoreconnect

**Disconnect Test:**
1. Start the application with a camera connected
2. Start recording or live view
3. Physically disconnect the USB camera
4. Observe the application notices the disconnection
5. Wait and observe reconnection attempts
6. Verify status shows retry count

**Reconnect Test:**
1. While reconnection is attempting, plug the camera back in
2. Verify camera reconnects on next attempt
3. Verify live view resumes
4. Check status shows "Yhdistetty" (Connected)

**Disable Autoreconnect:**
1. Go to Asetukset tab
2. Uncheck "Automaattinen uudelleenyhdistäminen"
3. Save settings
4. Disconnect camera
5. Verify no reconnection attempts occur

**Expected Result:** ✅ Autoreconnect works with exponential backoff and can be disabled

### 8. Windows Icon

**Build Test (Windows only):**
1. Install PyInstaller: `pip install pyinstaller`
2. Build the executable: `pyinstaller AnomRecorder.spec`
3. Navigate to `dist/` folder
4. Verify `AnomRecorder.exe` exists
5. Right-click the .exe and check Properties
6. Verify the icon appears in the properties dialog
7. Create a shortcut on desktop
8. Verify the icon appears on the shortcut

**Icon Regeneration:**
1. Modify `logo.png` if desired
2. Run: `python scripts/create_icon.py`
3. Verify `app.ico` is updated
4. Rebuild with PyInstaller

**Expected Result:** ✅ Windows executable has proper icon

### 9. UI and Localization

**Visual Inspection:**
1. Check all text is in Finnish
2. Verify spacing between elements is consistent
3. Check button alignments
4. Verify color coding (red for recording, green for not recording)
5. Check that pan buttons show arrow symbols (↑↓←→)

**Window Resize:**
1. Drag window corners to resize
2. Verify all controls remain visible
3. Verify video area scales appropriately
4. Make window very small, verify controls don't overlap
5. Maximize window, verify layout looks good

**Expected Result:** ✅ UI is polished and fully localized to Finnish

### 10. Error Handling

**Invalid Logo:**
1. Try to select an invalid/corrupted image file as logo
2. Verify error is caught gracefully
3. Check log for warning message

**Storage Limit:**
1. Set storage limit to a very small value (e.g., 0.01 GB)
2. Create recordings until limit is exceeded
3. Verify oldest recordings are automatically deleted
4. Check log for deletion messages

**Camera Error:**
1. Select a camera index that doesn't exist (if possible)
2. Verify error message appears
3. Verify application doesn't crash

**Expected Result:** ✅ All errors handled gracefully with Finnish messages

## Performance Testing

1. Run with two cameras simultaneously
2. Enable both motion and person detection
3. Record for extended period (10+ minutes)
4. Verify no memory leaks (use Task Manager/Activity Monitor)
5. Verify frame rate remains stable
6. Check CPU usage is reasonable

## Regression Testing

Run the existing automated tests:
```bash
pytest tests/ -v
```

All 21 tests should pass:
- 4 humanize tests
- 6 zoom tests
- 4 hotkey tests
- 7 reconnect tests

## Final Checklist

- [ ] All manual test scenarios completed
- [ ] All automated tests pass
- [ ] No console errors during normal operation
- [ ] Settings persist across restarts
- [ ] Recordings directory created automatically
- [ ] Windows icon visible in built executable
- [ ] UI text is in Finnish
- [ ] Recording safety verified (Päivitä and Tallenna don't stop recording)

## Reporting Issues

If any test fails:
1. Note the exact steps to reproduce
2. Check console output for error messages
3. Check logs in the application
4. Verify settings.json for corruption
5. Report issue with full details

---

**Testers:** Please initial or check off each test as completed. Report any anomalies immediately.
