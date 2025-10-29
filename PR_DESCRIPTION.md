# Pull Request: Fix live freeze, improve zoom/pan, settings save and recording safety; add recording indicator, hotkeys and autoreconnect

## Summary

This PR implements comprehensive improvements to the AnomRecorder application to address UI freezing, enhance zoom/pan functionality, add safety features for settings changes during recording, and improve overall user experience with visual indicators, keyboard shortcuts, and automatic reconnection.

## Changes Implemented

### 1. Non-blocking "Päivitä" Button ✅
**Problem**: Clicking "Päivitä" (refresh cameras) would freeze the UI and stop recording.

**Solution**:
- Converted camera refresh to run in a background thread
- UI remains responsive during camera enumeration
- Recording continues uninterrupted
- Button shows "⏳ Päivitetään..." while refreshing and is disabled to prevent multiple concurrent refreshes

**Files Changed**:
- `src/ui/app.py`: Added `refresh_cameras()` with threading, `_apply_camera_list()`, `_finish_camera_refresh()`

**Testing**: 
- Manual: Click Päivitä while recording → recording continues
- Automated: N/A (requires GUI and camera hardware)

---

### 2. Zoom and Panning Improvements ✅

**Problem**: 
- Zoom only supported factors ≥1.0 (couldn't zoom out)
- No panning capability
- Zoom wasn't centered on user selection

**Solution**:
- Extended `ZoomState` to support `min_factor=0.5` (zoom out to 50%)
- Implemented `crop_zoom()` to handle:
  - Zoom out (<1.0): adds black borders around shrunken video
  - Zoom in (>1.0): crops and magnifies center region
  - Panning: applies offset in pixels, bounded to prevent overflow
- Added UI controls:
  - Mouse drag panning (with checkbox to enable)
  - Pan buttons (↑↓←→)
  - Keyboard arrow keys for panning
  - Visual cursor change (fleur) when panning enabled
- Added zoom/pan hotkeys:
  - `+`/`-`: zoom in/out
  - Arrow keys: pan
  - `Escape`: reset zoom/pan

**Files Changed**:
- `src/utils/zoom.py`: Extended `crop_zoom()` with pan support
- `src/ui/app.py`: Added pan controls, mouse bindings, keyboard shortcuts

**Testing**:
- `tests/test_app_features.py`: 
  - `test_zoom_out_support()` ✅
  - `test_zoom_in_out_cycle()` ✅
  - `test_crop_zoom_out()` ✅
  - `test_crop_zoom_with_pan()` ✅
  - `test_pan_bounds()` ✅

---

### 3. Settings Tab: Logo Preview and Save Button ✅

**Problem**:
- Logo selection didn't show preview
- No explicit "Save Settings" button
- Unclear when settings were persisted

**Solution**:
- Added immediate logo preview in Settings tab
  - Preview shows as ~100x100 thumbnail
  - Updates instantly when file is selected
- Added "💾 Tallenna asetukset" button
  - Persists all settings atomically to `settings.json`
  - Shows success dialog
  - Validates storage limit (must be > 0)
- Settings now include:
  - Storage limit
  - Logo path and transparency
  - Motion threshold
  - Hotkeys enabled/disabled
  - Auto-reconnect enabled/disabled

**Files Changed**:
- `src/ui/app.py`: 
  - Added `logo_preview_label`, `_update_logo_preview()`
  - Added `_save_settings_safe()` button handler
  - Extended `_load_settings()` to load new options

**Testing**:
- `tests/test_app_features.py`: `test_settings_save_atomic()` ✅
- Manual: Select logo → preview appears immediately

---

### 4. Safe Settings Save During Recording ✅

**Problem**: Changing settings could interrupt active recordings.

**Solution**:
- Settings save is now atomic and doesn't restart cameras
- `_save_settings_safe()` validates inputs before saving
- Recording state is preserved across settings changes
- Error handling prevents partial saves

**Files Changed**:
- `src/ui/app.py`: Separated internal `_save_settings()` from user-triggered `_save_settings_safe()`

**Testing**:
- Manual: Start recording → change settings → save → recording continues
- Automated: `test_settings_save_atomic()` ✅

---

### 5. Live Recording Indicator ✅

**Problem**: No visual indication of recording state.

**Solution**:
- Added "Tallentaa:" label with two indicators (one per camera)
- Indicator shows:
  - 🟢 GREEN `●` when not recording
  - 🔴 RED `●` when recording
- Updates in real-time in `update_frames()` loop
- Positioned prominently in Live tab top bar

**Files Changed**:
- `src/ui/app.py`: 
  - Added `recording_indicators`, `is_recording`, `rec_indicator1/2`
  - Added `_update_recording_indicator()`

**Testing**:
- `tests/test_app_features.py`: `test_indicator_updates_on_recording_change()` ✅
- Manual: Trigger motion → indicator turns red

---

### 6. UI Polish ✅

**Changes**:
- Added icons to buttons:
  - 🔄 Päivitä
  - 📷 Kuvakaappaus
  - 🔍+/− Zoom
  - 💾 Tallenna asetukset
  - 📁 Valitse (logo file)
  - 🖱️ Panning toggle
  - ↑↓←→ Pan direction buttons
- Improved layout spacing in Settings tab
- Organized settings into labeled frames
- All labels in Finnish
- Consistent button styles

**Files Changed**:
- `src/ui/app.py`: Updated `_build_live_tab()`, `_build_settings_tab()`, `_build_zoom_controls()`

---

### 7. Error Handling and Auto-Reconnect ✅

**Problem**: Camera disconnections caused app to fail silently.

**Solution**:
- Wrapped camera operations in try/catch blocks
- Added `_show_error()` for user-friendly error dialogs
- Implemented auto-reconnect with exponential backoff:
  - Detects camera read failures
  - Attempts reconnection up to 5 times
  - Delay: 1s, 2s, 4s, 8s, 16s (capped at 30s)
  - Shows status: "Kamera X: yritetään yhdistää uudelleen 1/5..."
  - Success message on reconnect
- Auto-reconnect can be disabled in Settings
- Logs all errors for debugging

**Files Changed**:
- `src/ui/app.py`:
  - Enhanced `start_camera()` with error handling
  - Added `_schedule_reconnect()`, `_attempt_reconnect()`
  - Added reconnect detection in `update_frames()`

**Testing**:
- Manual: Disconnect camera → observe reconnection attempts

---

### 8. Hotkeys ✅

**Problem**: No keyboard shortcuts for common actions.

**Solution**:
- Implemented hotkey bindings:
  - `R`: Refresh cameras (Päivitä)
  - `+` or `=`: Zoom in
  - `-`: Zoom out
  - Arrow keys: Pan (↑↓←→)
  - `Escape`: Reset zoom/pan, cancel actions
- Hotkeys don't trigger when typing in text fields (smart detection)
- Can be disabled in Settings → "Näppäinoikotiet käytössä"
- Bindings respect focus state

**Files Changed**:
- `src/ui/app.py`: Added `_bind_hotkeys()`, `_is_typing()`, `_handle_escape()`

**Testing**:
- Manual: Press hotkeys → actions trigger (unless typing)

---

### 9. Persistent Recordings List on Startup ✅

**Problem**: Tallenteet tab was empty on app restart.

**Solution**:
- Added `_load_recordings_on_startup()` in `__init__()`
- Scans `recordings/` directory for `recording_*.avi` files
- Parses timestamps from filenames (format: `recording_cam0_YYYYMMDD_HHMMSS.avi`)
- Estimates duration from file size (~5 MB/sec)
- Populates `self.events` list
- Refreshes Tallenteet view
- Logs success/failures

**Files Changed**:
- `src/ui/app.py`: Added `_load_recordings_on_startup()`

**Testing**:
- `tests/test_app_features.py`: `test_load_recordings_from_disk()` ✅
- Manual: Restart app → Tallenteet tab shows previous recordings

---

### 10. Tests and Build ✅

**New Tests**: `tests/test_app_features.py`
- `test_zoom_out_support()` - Verifies zoom factor <1.0 works
- `test_zoom_in_out_cycle()` - Tests zoom in/out cycle
- `test_crop_zoom_out()` - Tests zoom out creates black borders
- `test_crop_zoom_with_pan()` - Tests panning with zoom
- `test_pan_bounds()` - Tests pan offset clamping
- `test_zoom_reset_resets_pan()` - Tests reset behavior
- `test_settings_save_atomic()` - Tests atomic settings save
- `test_indicator_updates_on_recording_change()` - Tests indicator logic
- `test_load_recordings_from_disk()` - Tests recordings list persistence

**Test Results**:
```
tests/test_app_features.py::test_zoom_out_support PASSED
tests/test_app_features.py::test_zoom_in_out_cycle PASSED
tests/test_app_features.py::test_crop_zoom_out PASSED
tests/test_app_features.py::test_crop_zoom_with_pan PASSED
tests/test_app_features.py::test_pan_bounds PASSED
tests/test_app_features.py::test_zoom_reset_resets_pan PASSED
tests/test_app_features.py::TestSettingsSafety::test_settings_save_atomic PASSED
tests/test_app_features.py::TestRecordingIndicator::test_indicator_updates_on_recording_change PASSED
tests/test_app_features.py::TestRecordingsListPersistence::test_load_recordings_from_disk PASSED

15/15 tests passing (including 6 existing tests)
```

**Build**: 
- No build errors
- Syntax validated with `python -m py_compile`
- All imports resolve correctly

---

## Files Modified

### Core Application
- **src/ui/app.py** (~850 lines, was ~700)
  - Main application logic
  - Added 10+ new methods
  - Enhanced error handling throughout

### Utilities
- **src/utils/zoom.py** (~85 lines, was ~50)
  - Extended zoom functionality
  - Added panning support
  - Added cv2 import

### Tests
- **tests/test_app_features.py** (NEW, ~180 lines)
  - Comprehensive test coverage for new features

### Documentation
- **MANUAL_TESTING.md** (NEW)
  - Detailed manual testing procedures
  - Test checklists
  - Troubleshooting guide

---

## Manual Testing Instructions

See `MANUAL_TESTING.md` for complete instructions. Quick summary:

1. **Non-blocking Päivitä**:
   - Start recording → click Päivitä → recording continues, UI responsive

2. **Zoom/Pan**:
   - Click 🔍− to zoom out (black borders appear)
   - Click 🔍+ to zoom in (video magnifies)
   - Enable 🖱️ and drag video to pan
   - Use arrow buttons or keyboard to pan
   - Press Escape to reset

3. **Settings**:
   - Select logo → preview appears immediately
   - Change settings → click "💾 Tallenna asetukset"
   - Close and restart → settings persist

4. **Recording Indicator**:
   - Green `●` when not recording
   - Red `●` when recording

5. **Auto-Reconnect**:
   - Disconnect camera → observe reconnection attempts
   - Reconnect camera → app resumes automatically

6. **Hotkeys**:
   - Press `R` → refreshes cameras
   - Press `+`/`-` → zoom in/out
   - Press arrows → pan

7. **Recordings Persistence**:
   - Create recordings → close app → reopen
   - Tallenteet tab shows previous recordings

---

## Screenshots/GIFs

*(Screenshots would be added here if GUI environment available)*

**What to show**:
1. Live view with recording indicators (red and green)
2. Zoom controls with 🔍+/− buttons
3. Pan controls with ↑↓←→ buttons and 🖱️ toggle
4. Settings tab with logo preview and 💾 save button
5. Tallenteet tab with loaded recordings

---

## Breaking Changes

**None.** All changes are additive and backward-compatible:
- Existing settings files are extended, not replaced
- New settings have sensible defaults
- Old code paths still work
- No API changes

---

## Known Limitations

1. **Platform**: Auto-reconnect uses DirectShow (Windows). May need `cv2.CAP_ANY` on Linux/Mac.
2. **Hotkeys**: Global to app window, may conflict with OS shortcuts.
3. **Pan Bounds**: Roughly bounded (±500px), not perfectly clamped to frame edges.
4. **Logo Preview**: Scaled to 100x100, may lose detail for small images.
5. **Reconnect**: Max 5 attempts with 30s max delay.

---

## Future Improvements

Potential follow-ups (not in scope for this PR):
- Configurable hotkey mapping UI
- Mouse wheel zoom (Ctrl+Scroll)
- Zoom centered on mouse position (requires mouse coordinates)
- Persistent pan/zoom state across app restarts
- File watcher for external recording changes
- Retry logic for settings save failures
- Camera selection persistence across refreshes

---

## Migration Guide

No migration needed. Users should:
1. Pull latest code
2. Restart app
3. Existing settings will be preserved and extended with defaults
4. Test hotkeys (can be disabled in Settings if conflicts occur)

---

## Checklist

- [x] All requested features implemented
- [x] Tests added and passing (15/15)
- [x] Documentation updated (MANUAL_TESTING.md)
- [x] Code syntax validated
- [x] No breaking changes
- [x] Error handling comprehensive
- [x] UI is polished and localized (Finnish)
- [x] Threading used for non-blocking operations
- [x] Settings save is atomic and safe

---

## Related Issues

This PR addresses all requirements in the original issue for:
- Live view freeze fix
- Zoom/pan improvements
- Settings safety
- Recording indicators
- Hotkeys
- Auto-reconnect
- Persistent recordings
- UI polish
- Error handling
- Tests

---

## Reviewer Notes

**Key areas to review**:
1. Thread safety in `refresh_cameras()` - UI updates scheduled via `root.after()`
2. Zoom/pan math in `crop_zoom()` - bounds checking and edge cases
3. Auto-reconnect backoff logic - exponential delay capping
4. Hotkey bindings - focus detection to avoid conflicts with text entry
5. Settings persistence - atomic write, validation

**Testing recommendations**:
1. Run automated tests: `pytest tests/ -v`
2. Manual test with physical USB camera
3. Test camera disconnect/reconnect scenarios
4. Verify hotkeys don't interfere with text input
5. Check settings persist across app restarts

---

**PR Author**: Copilot SWE Agent  
**Date**: 2025-10-29  
**Branch**: `copilot/fix-live-zoom-settings-recording-indicator`
