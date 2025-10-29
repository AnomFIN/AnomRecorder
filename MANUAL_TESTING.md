# Manual Testing Guide for AnomRecorder Features

This guide covers manual testing for the new features in this PR.

## Prerequisites
- Install dependencies: `pip install -r requirements.txt`
- Run the app: `python -m src.index`
- Have at least one USB camera connected

## 1. Non-blocking "Päivitä" Button

### Test Steps:
1. Start the app and go to Live view
2. Select a camera and start viewing (motion/person detection enabled)
3. Start recording by triggering motion (wave hand in front of camera)
4. While recording is active (red indicator visible), click "🔄 Päivitä"
5. Observe the button text changes to "⏳ Päivitetään..." and is disabled
6. **Expected**: 
   - UI remains responsive
   - Recording continues (red indicator stays red)
   - Camera list refreshes in background
   - Button returns to "🔄 Päivitä" when complete

### Pass Criteria:
- ✅ UI doesn't freeze
- ✅ Recording continues without interruption
- ✅ Camera list updates successfully

## 2. Zoom and Panning

### Test Steps:

#### Zoom Out (< 1.0x):
1. Select a camera in Live view
2. Click "🔍−" button multiple times
3. **Expected**: 
   - Zoom level shows 0.75x, 0.5x (minimum)
   - Video shrinks with black borders
   - Zoom label updates

#### Zoom In (> 1.0x):
1. Click "🔍+" button multiple times
2. **Expected**:
   - Zoom level shows 1.25x, 1.5x, up to 4.0x
   - Video crops to center, magnified
   - Zoom label updates

#### Panning with Mouse:
1. Set zoom to 2.0x or higher
2. Check "🖱️" checkbox to enable panning
3. Click and drag on the video area
4. **Expected**:
   - Cursor changes to "fleur" (cross-arrows)
   - Video pans as you drag
   - Panning is bounded (can't pan infinitely)

#### Panning with Buttons:
1. Set zoom to 2.0x
2. Click the arrow buttons (↑↓←→) next to Pan label
3. **Expected**: Video pans in the direction of the button

#### Panning with Keyboard:
1. Set zoom to 2.0x
2. Press arrow keys on keyboard
3. **Expected**: Video pans (if not typing in a text field)

#### Reset:
1. After zooming and panning, click "Reset"
2. **Expected**: 
   - Zoom returns to 1.0x
   - Pan offset resets to center
   
#### Hotkeys:
1. Press `+` or `=` key → zoom in on camera 1
2. Press `-` key → zoom out on camera 1
3. Press `Escape` → reset all zoom/pan
4. **Expected**: Hotkeys work (unless typing in text field)

### Pass Criteria:
- ✅ Zoom out to 0.5x works (black borders)
- ✅ Zoom in to 4.0x works (magnified, cropped)
- ✅ Mouse panning works when enabled
- ✅ Button panning works
- ✅ Keyboard panning works
- ✅ Panning is bounded
- ✅ Reset returns to 1.0x with no pan
- ✅ Hotkeys work

## 3. Settings Tab: Logo Preview and Save Button

### Test Steps:

#### Logo Preview:
1. Go to Settings tab
2. Click "📁 Valitse" button to select a logo file
3. Choose a PNG/JPG image
4. **Expected**:
   - File path appears in text field
   - Logo preview shows immediately in "Esikatselu:" area
   - Preview is scaled to fit ~100x100 pixels

#### Settings Save:
1. Change storage limit to 10 GB
2. Adjust logo transparency slider
3. Adjust motion threshold
4. Check/uncheck hotkeys and autoreconnect options
5. Click "💾 Tallenna asetukset"
6. **Expected**:
   - Success dialog: "Asetukset tallennettu onnistuneesti!"
   - Settings persist to `settings.json`
   - No interruption to active recording

#### Verify Persistence:
1. Close and restart the app
2. Go to Settings tab
3. **Expected**: All settings are restored (storage limit, logo path, etc.)

### Pass Criteria:
- ✅ Logo preview shows immediately on file selection
- ✅ Save button persists all settings
- ✅ Save doesn't stop recording
- ✅ Settings persist across app restarts

## 4. Recording Indicator

### Test Steps:
1. Start the app and go to Live view
2. Select camera(s)
3. Enable motion detection
4. Observe the "Tallentaa:" indicators next to camera controls
5. Trigger motion (wave hand)
6. **Expected**:
   - Indicator turns RED when recording starts
   - Indicator stays RED while recording
   - Indicator turns GREEN when recording stops (5 sec after motion ends)

### Pass Criteria:
- ✅ Indicator is GREEN when not recording
- ✅ Indicator is RED when recording
- ✅ Indicator updates in real-time

## 5. Error Handling and Auto-Reconnect

### Test Steps:

#### Camera Disconnect:
1. Start viewing a camera
2. Physically disconnect the USB camera
3. **Expected**:
   - Error is logged
   - Status shows reconnection attempts (1/5, 2/5, ...)
   - App attempts to reconnect with exponential backoff

#### Camera Reconnect:
1. Plug the camera back in during reconnection attempts
2. **Expected**:
   - Camera reconnects automatically
   - Status shows "Kamera X: yhdistetty uudelleen!"
   - Live view resumes

#### Disable Auto-Reconnect:
1. Go to Settings → uncheck "Automaattinen yhdistäminen uudelleen"
2. Click "💾 Tallenna asetukset"
3. Disconnect camera
4. **Expected**: No reconnection attempts

### Pass Criteria:
- ✅ Auto-reconnect attempts with backoff
- ✅ Successful reconnection on camera return
- ✅ Auto-reconnect can be disabled
- ✅ Error messages are user-friendly

## 6. Hotkeys

### Test Steps:
1. Go to Live view
2. Press `R` → **Expected**: Camera refresh triggered
3. Press `+` → **Expected**: Zoom in on camera 1
4. Press `-` → **Expected**: Zoom out on camera 1
5. Press arrow keys → **Expected**: Pan camera 1
6. Press `Escape` → **Expected**: Reset zoom/pan, disable panning
7. Click in a text field (Settings tab), press `R` → **Expected**: Types "R", doesn't refresh
8. Go to Settings, uncheck "Näppäinoikotiet käytössä" → **Expected**: Hotkeys disabled

### Pass Criteria:
- ✅ R = refresh cameras
- ✅ +/- = zoom in/out
- ✅ Arrows = pan
- ✅ Escape = reset
- ✅ Hotkeys don't trigger when typing in text fields
- ✅ Hotkeys can be disabled in Settings

## 7. Persistent Recordings List

### Test Steps:

#### Generate Recordings:
1. Start app, trigger some recordings (motion detection)
2. Wait for recordings to complete
3. Go to Tallenteet tab → recordings should appear

#### Test Persistence:
1. Close the app completely
2. Restart the app
3. Go to Tallenteet tab immediately
4. **Expected**: Previous recordings are listed (loaded from disk)

#### Verify File Format:
1. Check that recordings directory contains `.avi` files
2. Files should be named like `recording_cam0_20231027_143000.avi`
3. **Expected**: Files are parsed and displayed with timestamp

### Pass Criteria:
- ✅ Recordings list is populated on app startup
- ✅ Timestamps are parsed correctly from filenames
- ✅ All previous recordings are shown

## 8. UI Polish

### Visual Inspection:
1. Check all tabs (Live, Tallenteet, Asetukset)
2. **Expected**:
   - Icons visible: 🔄📷🔍💾🖱️↑↓←→
   - Finnish labels throughout
   - Proper spacing and alignment
   - Buttons are clearly labeled
   - Recording indicators visible and prominent

### Pass Criteria:
- ✅ UI is polished and professional
- ✅ All text is in Finnish
- ✅ Icons enhance usability
- ✅ Layout is clean and organized

## Summary Checklist

After completing all tests above, verify:

- [ ] Päivitä button doesn't freeze UI or stop recording
- [ ] Zoom works for factors <1.0 and >1.0
- [ ] Pan works with mouse, buttons, and keyboard
- [ ] Logo preview shows immediately on selection
- [ ] Settings save button works without stopping recording
- [ ] Recording indicator shows red/green correctly
- [ ] Auto-reconnect works when camera disconnects
- [ ] Hotkeys work and can be disabled
- [ ] Recordings list persists across app restarts
- [ ] All tests pass: `pytest tests/ -v`

## Test Results

Date: ___________
Tester: ___________

| Feature | Pass | Fail | Notes |
|---------|------|------|-------|
| Non-blocking Päivitä | ☐ | ☐ | |
| Zoom <1.0 | ☐ | ☐ | |
| Zoom >1.0 | ☐ | ☐ | |
| Mouse pan | ☐ | ☐ | |
| Button pan | ☐ | ☐ | |
| Keyboard pan | ☐ | ☐ | |
| Logo preview | ☐ | ☐ | |
| Settings save | ☐ | ☐ | |
| Recording indicator | ☐ | ☐ | |
| Auto-reconnect | ☐ | ☐ | |
| Hotkeys | ☐ | ☐ | |
| Recordings persistence | ☐ | ☐ | |

## Known Limitations

1. Hotkeys are global to the app window (may conflict with OS hotkeys)
2. Auto-reconnect has a maximum of 5 attempts
3. Pan offset is roughly bounded (±500 pixels)
4. Logo preview is scaled to ~100x100 (may lose quality for small icons)
5. Camera refresh uses DirectShow (Windows) - may need CAP_ANY on other platforms

## Troubleshooting

**Q: Päivitä button seems to hang**
A: Check if camera is physically connected and responding. Thread may be waiting for camera probe timeout.

**Q: Zoom/pan not working**
A: Ensure a camera is selected and displaying video. Zoom/pan only affects active video streams.

**Q: Hotkeys not working**
A: Check Settings → "Näppäinoikotiet käytössä" is checked. Don't type in text fields.

**Q: Recordings not loading on startup**
A: Check `recordings/` directory exists and contains `recording_*.avi` files. Check file permissions.

**Q: Auto-reconnect failing**
A: Camera may be in use by another app, or driver may be stuck. Try manual Päivitä or restart app.
