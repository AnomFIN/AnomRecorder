# Manual Test Checklist for PR: Fix live freeze, improve zoom/pan, settings save and recording safety

## Priority A — Critical Fixes

### 1. Non-blocking "Päivitä" Button
- [ ] Start the application
- [ ] Click "Päivitä" button while live view is active
- [ ] Verify the UI remains responsive (not frozen)
- [ ] Verify status message shows "Päivitetään kameroita..."
- [ ] Start a recording (trigger motion detection)
- [ ] Click "Päivitä" while recording
- [ ] Verify recording continues (red indicator stays on)
- [ ] Verify no errors shown in UI or console

### 2. Settings Save Safety
- [ ] Start a recording
- [ ] Go to "Asetukset" tab
- [ ] Change any setting (e.g., storage limit, logo alpha)
- [ ] Click "Tallenna asetukset"
- [ ] Verify recording continues (check red indicator in Live tab)
- [ ] Verify success message shown: "Asetukset tallennettu ja otettu käyttöön"
- [ ] Restart application and verify settings persisted

### 3. Persistent Recordings List & Deletion
- [ ] Close and restart application
- [ ] Go to "Tallenteet" tab
- [ ] Verify existing recordings appear in list
- [ ] Create a new recording (trigger motion)
- [ ] Verify new recording appears automatically (filesystem watcher)
- [ ] Select one or more recordings
- [ ] Click "Poista valitut"
- [ ] Confirm deletion
- [ ] On Windows: Check Recycle Bin for deleted files
- [ ] On Linux/macOS: Check Trash for deleted files
- [ ] Verify recordings removed from list
- [ ] Verify disk usage updated

## Priority B — Important Features

### 4. Zoom & Panning

#### Zoom Out (< 1.0x)
- [ ] Start live view with camera
- [ ] Click "-" button in Zoom controls multiple times
- [ ] Verify zoom label shows 0.75x, then 0.5x (minimum)
- [ ] Verify video shows with black padding around edges
- [ ] Click "Reset" and verify zoom returns to 1.0x

#### Zoom In (> 1.0x)
- [ ] Click "+" button multiple times
- [ ] Verify zoom label increases: 1.25x, 1.5x, etc.
- [ ] Verify video is cropped and centered
- [ ] Verify maximum zoom is 4.0x

#### Panning
- [ ] Set zoom to 2.0x or higher
- [ ] Click pan arrows (↑ ↓ ← →)
- [ ] Verify video content shifts in corresponding direction
- [ ] Use keyboard arrow keys to pan
- [ ] Verify pan works with keyboard

### 5. Live Recording Indicator
- [ ] View "Live" tab with no motion
- [ ] Verify indicator shows "● Ei tallenna" in green
- [ ] Trigger motion detection (wave hand in front of camera)
- [ ] Verify indicator changes to "● Tallentaa" in red
- [ ] Wait for motion to stop (5+ seconds)
- [ ] Verify indicator returns to "● Ei tallenna" in green

### 6. Audio Settings

#### UI Elements
- [ ] Go to "Asetukset" tab
- [ ] Verify "Ääniasetukset" section exists
- [ ] Verify "Tallenna ääntä?" checkbox present
- [ ] Verify "Äänilähtö" dropdown present
- [ ] Verify "Tallenna asetukset" button present

#### Persistence
- [ ] Toggle "Tallenna ääntä?" off
- [ ] Select different audio output
- [ ] Click "Tallenna asetukset"
- [ ] Restart application
- [ ] Verify settings persisted (checkbox and dropdown)

#### Apply While Recording
- [ ] Start a recording
- [ ] Change audio settings
- [ ] Click "Tallenna asetukset"
- [ ] Verify recording continues (check indicator)
- [ ] Verify success message shown

### 7. Hotkeys
- [ ] Press 'R' key → Verify camera refresh triggered
- [ ] Press '+' key → Verify active camera zooms in
- [ ] Press '-' key → Verify active camera zooms out
- [ ] Press Up/Down/Left/Right arrows → Verify panning
- [ ] Press Escape → Verify application closes (with confirmation)

### 8. Camera Autoreconnect

#### Enable/Disable
- [ ] Go to "Asetukset" tab
- [ ] Verify "Kameran autoyhdistys" section exists
- [ ] Check "Yhdistä automaattisesti uudelleen katkoksen jälkeen"
- [ ] Click "Tallenna asetukset"

#### Test Reconnection (if possible)
- [ ] Enable autoreconnect
- [ ] Start live view
- [ ] Physically disconnect USB camera (if safe to do so)
- [ ] Verify status message shows disconnection
- [ ] Reconnect USB camera
- [ ] Wait ~1-5 seconds
- [ ] Verify camera reconnects automatically
- [ ] Verify status shows "Kamera X yhdistetty uudelleen"

### 9. Resizable Window
- [ ] Drag window edges to resize
- [ ] Verify minimum size: 1024x600 (cannot resize smaller)
- [ ] Verify maximum size: 2560x1440 (cannot resize larger)
- [ ] Verify controls remain visible at all sizes
- [ ] Verify video content scales appropriately

## Priority C — Polish & Packaging

### 10. UI Polish
- [ ] Review all Finnish labels for correctness
- [ ] Verify button tooltips (hover for hints if implemented)
- [ ] Verify consistent spacing and alignment
- [ ] Verify dark theme applied throughout

### 11. App Icon (for packaged builds)
- [ ] Build executable (use build script if available)
- [ ] Verify .exe/.app shows logo.png as icon
- [ ] (If not working, note: icon conversion script needed)

### 12. Tests
- [ ] Run: `python -m pytest tests/ -v`
- [ ] Verify all 12+ tests pass
- [ ] Check test coverage report

## Additional Verification

### Error Handling
- [ ] Try to delete recording that doesn't exist
- [ ] Try to save invalid settings (e.g., negative storage limit)
- [ ] Verify Finnish error messages shown
- [ ] Verify no crashes, only user-friendly messages

### Performance
- [ ] Run with 2 cameras simultaneously
- [ ] Verify UI remains responsive
- [ ] Verify recording works on both cameras
- [ ] Check CPU/memory usage is reasonable

### Cross-Platform (if applicable)
- [ ] Test on Windows
- [ ] Test on Linux
- [ ] Test on macOS
- [ ] Note any platform-specific issues

## Test Results Summary

Date: ___________
Tester: ___________

Total Tests: _____ / _____
Pass: _____
Fail: _____
Notes:

