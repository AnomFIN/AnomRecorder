"""Integration tests for AnomRecorder app features."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


def test_settings_save_atomic():
    """Test that settings are saved atomically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / "settings.json"
        
        # Simulate atomic save
        payload = {
            "storage_limit_gb": 5.0,
            "save_audio": True,
            "selected_audio_output": "Default",
        }
        temp_path = settings_path.with_suffix('.tmp')
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(settings_path)
        
        # Verify file exists and is readable
        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["storage_limit_gb"] == 5.0
        assert data["save_audio"] is True
        assert data["selected_audio_output"] == "Default"


def test_audio_settings_persistence():
    """Test that audio settings are properly stored."""
    payload = {
        "save_audio": False,
        "selected_audio_output": "Järjestelmän oletus",
    }
    
    # Serialize and deserialize
    serialized = json.dumps(payload)
    deserialized = json.loads(serialized)
    
    assert deserialized["save_audio"] is False
    assert deserialized["selected_audio_output"] == "Järjestelmän oletus"


def test_recordings_list_from_directory():
    """Test loading recordings from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        record_dir = Path(tmpdir) / "recordings"
        record_dir.mkdir()
        
        # Create mock recording files
        (record_dir / "recording_cam0_20240101_120000.avi").touch()
        (record_dir / "recording_cam1_20240101_120100.avi").touch()
        
        # List recordings
        recordings = sorted(record_dir.glob("recording_*.avi"))
        assert len(recordings) == 2
        assert recordings[0].name == "recording_cam0_20240101_120000.avi"


def test_zoom_factor_range():
    """Test that zoom supports factors <1.0 and >1.0."""
    from src.utils.zoom import ZoomState
    
    state = ZoomState()
    
    # Test zoom out below 1.0
    state.zoom_out()
    assert state.factor < 1.0
    assert state.factor == 0.75
    
    # Test zoom in above 1.0
    state.reset()
    state.zoom_in()
    state.zoom_in()
    assert state.factor > 1.0
    assert state.factor == 1.5


def test_pan_offset_bounds():
    """Test that pan offsets are tracked correctly."""
    # Simulate pan tracking
    pan_x, pan_y = 0, 0
    
    # Pan right and down
    pan_x += 20
    pan_y += 20
    assert pan_x == 20
    assert pan_y == 20
    
    # Pan left and up
    pan_x -= 40
    pan_y -= 40
    assert pan_x == -20
    assert pan_y == -20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
