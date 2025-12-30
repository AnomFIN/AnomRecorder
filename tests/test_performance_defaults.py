"""Test that performance-optimized defaults are correctly set."""

import json
from pathlib import Path


def test_default_resolution_is_lower():
    """Test that default resolution settings are lower for performance."""
    
    # Check config.json
    config_path = Path("config.json")
    assert config_path.exists(), "config.json should exist"
    
    config = json.loads(config_path.read_text())
    resolution = config.get("resolution", [])
    
    # Verify resolution is 480x360 or lower
    assert len(resolution) == 2, "Resolution should have width and height"
    assert resolution[0] <= 480, f"Width should be <= 480, got {resolution[0]}"
    assert resolution[1] <= 360, f"Height should be <= 360, got {resolution[1]}"
    
    # Verify person detection is disabled in config
    assert config.get("person_detection") is False, \
        "Person detection should be disabled in config.json"


def test_person_detection_default_in_code():
    """Test that person detection is initialized as False in the source code."""
    
    # Read the app.py source
    app_path = Path("src/ui/app.py")
    assert app_path.exists(), "src/ui/app.py should exist"
    
    app_source = app_path.read_text()
    
    # Look for the line where enable_person is initialized
    # It should be: self.enable_person = tk.BooleanVar(value=False)
    assert 'self.enable_person = tk.BooleanVar(value=False)' in app_source, \
        "Person detection should be initialized as False in app.py"


def test_camera_resolution_in_code():
    """Test that camera resolution is set to 480x360 in the source code."""
    
    # Read the app.py source
    app_path = Path("src/ui/app.py")
    assert app_path.exists(), "src/ui/app.py should exist"
    
    app_source = app_path.read_text()
    
    # Look for the resolution settings
    assert 'cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)' in app_source, \
        "Camera width should be set to 480 in app.py"
    assert 'cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)' in app_source, \
        "Camera height should be set to 360 in app.py"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

