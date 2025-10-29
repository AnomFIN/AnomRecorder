# Feature Implementation Guide

This document describes the new features implemented in this PR.

## Priority A - Critical Fixes

### 1. Non-Blocking Camera Refresh
The "Päivitä" (Refresh) button now runs camera detection in a background thread to prevent UI freezing.

**Implementation**:
- Uses Python threading for background camera detection
- Updates UI via `root.after()` to maintain thread safety
- Shows toast notifications for success/error
- Prevents multiple simultaneous refresh operations

**User Experience**:
- UI remains responsive during refresh
- Status messages show progress
- Active recordings continue uninterrupted

### 2. Safe Settings Save
Settings can be saved without stopping active recordings.

**Implementation**:
- Settings save only writes to JSON file
- Does not modify camera capture or recording state
- "Tallenna asetukset" button provides explicit save action

**Settings Saved**:
- Storage limit (GB)
- Logo path and transparency
- Motion detection threshold
- Autoreconnect preference

### 3. Persistent Recordings List
Recordings are loaded from disk on startup and monitored continuously.

**Implementation**:
- Scans `./recordings/` directory on startup
- Parses timestamps from filenames (YYYYMMDD_HHMMSS format)
- File watcher checks for new files every 5 seconds
- Multi-select delete with confirmation dialogs
- Safe deletion (attempts send2trash on Windows)

## Priority B - Important Features

### 4. Zoom and Panning
Enhanced zoom supporting both zoom in (>1.0) and zoom out (<1.0) with panning.

**Zoom Features**:
- Range: 0.5x to 4.0x (step 0.25x)
- Zoom out adds black padding around image
- Zoom in crops to center
- Reset button returns to 1.0x

**Pan Features**:
- Pan buttons: ← ↑ ↓ →
- Keyboard arrows for panning
- Pan offsets constrained to ±1.0 (frame boundaries)
- Pan resets with zoom reset

**Tests**:
- 5 comprehensive tests for zoom/pan bounds and behavior
- All tests passing

### 5. Live Recording Indicator
Visual indicators show recording status for each camera.

**Implementation**:
- Canvas widgets with colored dots
- Red = recording, Green = idle
- Tooltips on hover: "Tallentaa" / "Ei tallenna"
- Updates in real-time during frame loop

**Accessibility**:
- Hover tooltips with Finnish text
- Status updates in status bar
- Clear visual distinction (red/green)

### 6. Logo Preview
Settings tab shows immediate preview of selected logo.

**Implementation**:
- Uses cv2 to read image
- Resizes to max 200x100 for preview
- Updates immediately on file selection
- Handles RGBA and RGB formats

### 7. Hotkeys
Keyboard shortcuts for common operations.

**Hotkey Mappings**:
- `+` / `-`: Zoom in/out
- Arrow keys: Pan view
- `Esc`: Reset zoom and pan
- `R`: Refresh cameras
- `Space`: Reserved for future recording toggle

**Documentation**:
- Listed in Settings tab under "Pikanäppäimet"
- Finnish descriptions
- Applies to active camera

### 8. Camera Autoreconnect
Automatically attempts to reconnect cameras on failure.

**Implementation**:
- Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s (max 60s)
- Up to 6 attempts per cycle
- Resets on successful reconnect
- Settings toggle to enable/disable

**User Feedback**:
- Status messages during reconnection attempts
- Toast notifications on success/failure
- Saved to settings.json

## Usage Examples

### Using Hotkeys
1. Start the application
2. Select a camera
3. Press `+` to zoom in, `-` to zoom out
4. Use arrow keys to pan around
5. Press `Esc` to reset view
6. Press `R` to refresh camera list

### Managing Recordings
1. Go to "Tallenteet" tab
2. Existing recordings load automatically
3. Select one or more recordings (Ctrl+Click for multi-select)
4. Click "Poista valittu" to delete selected
5. Or "Poista kaikki" to clear all

### Configuring Autoreconnect
1. Go to "Asetukset" tab
2. Toggle "Kameran automaattinen uudelleenyhdistäminen"
3. Click "Tallenna asetukset" to persist
4. Camera will now auto-reconnect on failure

## Technical Notes

### Thread Safety
- Camera refresh uses daemon threads
- UI updates via `root.after(0, callback)`
- Recording state never modified by settings

### Performance
- Background operations don't block UI
- File watcher runs every 5 seconds (configurable)
- Zoom/pan calculations optimized with numpy

### Testing
- 9 unit tests (all passing)
- Tests cover zoom, pan, humanize utilities
- UI tests skipped (require display)

## Future Enhancements

Potential improvements for future versions:
- Mouse wheel zoom
- Click-and-drag panning
- Customizable hotkeys in Settings
- Manual recording start/stop
- Configurable file watcher interval
- Recording metadata editing
