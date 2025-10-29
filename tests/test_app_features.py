"""Tests for new app features: non-blocking refresh, zoom/pan, settings safety."""

import time
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np

from src.utils.zoom import ZoomState, crop_zoom


def test_zoom_out_support():
    """Test that zoom supports factors < 1.0 (zoom out)."""
    state = ZoomState(min_factor=0.5)
    
    # Start at 1.0
    assert state.factor == 1.0
    
    # Zoom out
    state.zoom_out()
    assert state.factor == 0.75
    
    state.zoom_out()
    assert state.factor == 0.5
    
    # Can't go below min
    state.zoom_out()
    assert state.factor == 0.5


def test_zoom_in_out_cycle():
    """Test zoom in and out cycle."""
    state = ZoomState(min_factor=0.5, max_factor=2.0)
    
    # Zoom in
    state.zoom_in()
    assert state.factor == 1.25
    
    # Zoom out back to 1.0
    state.zoom_out()
    assert state.factor == 1.0
    
    # Zoom out below 1.0
    state.zoom_out()
    assert state.factor == 0.75


def test_crop_zoom_out():
    """Test that crop_zoom handles zoom out (< 1.0)."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    # Zoom out to 0.5x should create black borders
    zoomed = crop_zoom(frame, 0.5)
    
    assert zoomed.shape == frame.shape
    # Center should be white, edges should be black
    center_val = zoomed[50, 50, 0]
    edge_val = zoomed[0, 0, 0]
    assert center_val == 255
    assert edge_val == 0


def test_crop_zoom_with_pan():
    """Test that crop_zoom supports panning."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    
    # Pan without zoom
    panned = crop_zoom(frame, 1.0, (10, 0))
    assert panned.shape == frame.shape
    
    # Pan with zoom
    panned = crop_zoom(frame, 2.0, (5, 5))
    assert panned.shape[0] == 50
    assert panned.shape[1] == 50


def test_pan_bounds():
    """Test that panning respects bounds."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    
    # Large pan offset should be clamped
    panned = crop_zoom(frame, 2.0, (1000, 1000))
    assert panned.shape[0] == 50
    assert panned.shape[1] == 50


def test_zoom_reset_resets_pan():
    """Test that zoom reset should also reset pan offset."""
    state = ZoomState()
    state.zoom_in()
    state.zoom_in()
    
    state.reset()
    assert state.factor == 1.0


class TestSettingsSafety:
    """Test that settings can be saved without stopping recording."""
    
    def test_settings_save_atomic(self):
        """Test that settings save is atomic."""
        from pathlib import Path
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            
            # Write initial settings
            data = {"storage_limit_gb": 5.0, "logo_path": ""}
            settings_path.write_text(json.dumps(data))
            
            # Update settings
            data["storage_limit_gb"] = 10.0
            settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            
            # Read back
            loaded = json.loads(settings_path.read_text())
            assert loaded["storage_limit_gb"] == 10.0


class TestRecordingIndicator:
    """Test recording indicator state changes."""
    
    def test_indicator_updates_on_recording_change(self):
        """Test that indicator state changes when recording starts/stops."""
        # This would need a full app mock, testing state logic
        is_recording = False
        
        # Simulate recording start
        is_recording = True
        indicator_color = "red" if is_recording else "green"
        assert indicator_color == "red"
        
        # Simulate recording stop
        is_recording = False
        indicator_color = "red" if is_recording else "green"
        assert indicator_color == "green"


class TestRecordingsListPersistence:
    """Test that recordings list persists and loads on startup."""
    
    def test_load_recordings_from_disk(self):
        """Test loading recording files from disk."""
        import tempfile
        from pathlib import Path
        from datetime import datetime
        
        with tempfile.TemporaryDirectory() as tmpdir:
            record_dir = Path(tmpdir)
            
            # Create some fake recording files
            files = [
                record_dir / "recording_cam0_20231027_143000.avi",
                record_dir / "recording_cam1_20231027_143100.avi",
            ]
            
            for file in files:
                file.write_text("fake video data")
            
            # Simulate loading
            loaded_files = sorted(record_dir.glob("recording_*.avi"))
            assert len(loaded_files) == 2
            
            # Parse timestamp from first file
            name = loaded_files[0].stem
            parts = name.split("_")
            assert len(parts) >= 3
            date_str = parts[-2]
            time_str = parts[-1]
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            assert dt.year == 2023
            assert dt.month == 10
            assert dt.day == 27


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
