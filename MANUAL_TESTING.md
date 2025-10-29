# Manual Testing Guide for UI Improvements

This guide outlines how to manually verify all the UI improvements in this PR.

## Prerequisites
- USB camera connected
- Python environment with all dependencies installed
- Run: `python -m src.index`

## Test Scenarios

### 1. Recording Indicator
**Test**: Verify the recording indicator works correctly

**Steps**:
1. Start the application
2. Select a camera from the dropdown
3. Observe the top-left corner of the Live tab
4. Look for the indicator: `● Ei tallenna` in green

**Expected Result**:
- Green indicator shows "● Ei tallenna" when not recording
- When motion/person is detected, indicator changes to "● Tallentaa" in red
- Indicator updates automatically

**Visual Check**:
- Color changes from green to red
- Text changes appropriately
- Positioned at top-left, before camera dropdowns

---

### 2. Zoom Out (<1.0x)
**Test**: Verify zoom out functionality works

**Steps**:
1. Start camera feed in Live tab
2. Click the `-` button under "Zoom 1" multiple times
3. Observe the zoom level label
4. Watch the video feed

**Expected Result**:
- Zoom level goes to 0.75x, 0.5x (stops at 0.5x minimum)
- Video feed shows black borders around the original frame
- Label shows current zoom level (e.g., "0.5x")

**Visual Check**:
- Black borders appear around video when zoomed out
- Image stays centered
- Clicking `-` at minimum doesn't break anything

---

### 3. Pan Controls
**Test**: Verify panning works with buttons and keyboard

**Steps**:
1. Start camera feed in Live tab
2. Click `+` to zoom in (e.g., to 2.0x)
3. Click the arrow buttons (←↑↓→) next to zoom controls
4. Also try pressing arrow keys on keyboard
5. Observe video movement

**Expected Result**:
- Clicking arrow buttons pans the view in that direction
- Keyboard arrows also pan the active camera
- Panning is smooth and bounded (doesn't go outside frame)
- Both camera 1 and camera 2 can be panned independently

**Visual Check**:
- Video content moves in the correct direction
- Can reach all corners of the zoomed frame
- Panning stops at edges (doesn't show invalid regions)

---

### 4. Logo Preview in Settings
**Test**: Verify logo preview appears immediately

**Steps**:
1. Go to Settings tab (Asetukset)
2. Click "Valitse" under the Logo section
3. Select an image file (PNG/JPG)
4. Look for the preview below the file path

**Expected Result**:
- Logo preview appears immediately after selection
- Preview shows a scaled-down version of the logo
- No need to save or reload to see the preview
- Text changes from "Ei logoa valittu" to showing the image

**Visual Check**:
- Preview image is visible and recognizable
- Preview is reasonable size (not too large)
- If logo can't be loaded, error message is clear

---

### 5. "Tallenna asetukset" Button
**Test**: Verify explicit save button works

**Steps**:
1. Go to Settings tab
2. Change logo transparency slider
3. Notice settings are NOT auto-saved
4. Click "Tallenna asetukset" button
5. If recording is active, test the confirmation dialog

**Expected Result**:
- Button is visible at bottom of Settings
- Clicking it saves all settings
- Success message appears: "Asetukset tallennettu onnistuneesti!"
- If recording, confirmation dialog asks before saving
- Recording continues uninterrupted after save

**Visual Check**:
- Button has accent styling (stands out)
- Success dialog appears
- No errors in console/logs

---

### 6. "Päivitä" Button Safety
**Test**: Verify refresh doesn't break recording

**Steps**:
1. Start camera feed in Live tab
2. Wait for or trigger recording (move in front of camera)
3. Verify recording indicator is red
4. Click "Päivitä" button while recording
5. Observe recording continues

**Expected Result**:
- Camera list refreshes
- Recording does NOT stop
- Recording indicator stays red
- Video feed continues without interruption
- Status message updates to show camera names

**Visual Check**:
- No visible disruption in video feed
- Recording indicator doesn't turn green
- No error dialogs appear

---

### 7. Error Handling Tests

#### Test 7a: Disconnect Camera While Running
**Steps**:
1. Start camera feed
2. Physically disconnect USB camera
3. Observe behavior

**Expected Result**:
- Error message appears (Finnish)
- Application doesn't crash
- Status text shows error
- Can reconnect camera and continue

#### Test 7b: Invalid Logo File
**Steps**:
1. Go to Settings
2. Try to select a non-image file as logo
3. Or select a corrupted image

**Expected Result**:
- Error dialog appears in Finnish
- Application doesn't crash
- Can try selecting a different file

#### Test 7c: Snapshot Without Camera
**Steps**:
1. Don't start any camera
2. Click "Kuvakaappaus" button

**Expected Result**:
- Info dialog: "Ei kuvaa tallennettavana"
- No error, just informative message

---

### 8. Layout and Polish
**Test**: Verify UI improvements

**Visual Checks**:
- Pan buttons (←↑↓→) are visible and aligned in zoom control rows
- Recording indicator is prominent at top-left
- Settings tab has proper spacing:
  - Logo row with file picker
  - Preview below logo row
  - Transparency slider in its own row
  - Motion threshold in separate frame
  - "Tallenna asetukset" button at bottom
- All text is in Finnish
- No layout overflow or clipping
- Dark theme is preserved

---

## Regression Tests

### Test R1: Normal Recording Flow
**Steps**:
1. Select camera
2. Enable motion/person detection
3. Trigger detection
4. Verify recording starts and stops normally
5. Check recordings in Tallenteet tab

**Expected Result**: Everything works as before

### Test R2: Playback
**Steps**:
1. Record some video
2. Go to Tallenteet tab
3. Select a recording
4. Click Play
5. Try different speeds (0.5x, 1x, 2x)

**Expected Result**: Playback works normally

### Test R3: Settings Persistence
**Steps**:
1. Change settings and save
2. Close application
3. Restart application
4. Verify settings are loaded

**Expected Result**: Settings persist across restarts

---

## Success Criteria
- All new features work as described
- No regressions in existing features
- No error dialogs during normal operation
- Application remains responsive
- All text is in Finnish
- UI is polished and professional

## Notes for Testers
- Test with both 1 and 2 cameras if possible
- Test with different zoom levels
- Test panning at different zoom levels
- Try switching tabs while recording
- Test all error scenarios safely
- Check logs for any warnings/errors
