#!/usr/bin/env python3
"""
Test script for AnomRecorder
Tests configuration, storage management, and basic imports
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✓ NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print(f"✓ Pillow (PIL) imported")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False
    
    try:
        import tkinter as tk
        print(f"✓ Tkinter imported")
    except ImportError as e:
        print(f"✗ Tkinter import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        # Import Config class from main module
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from usb_cam_viewer import Config
        
        config = Config()
        print(f"✓ Config loaded successfully")
        print(f"  - Camera indices: {config.get('camera_indices')}")
        print(f"  - Resolution: {config.get('resolution')}")
        print(f"  - FPS: {config.get('fps')}")
        print(f"  - Motion detection: {config.get('motion_detection')}")
        print(f"  - Person detection: {config.get('person_detection')}")
        print(f"  - Max storage: {config.get('max_storage_gb')} GB")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def test_storage_manager():
    """Test storage manager"""
    print("\nTesting storage manager...")
    try:
        from usb_cam_viewer import Config, StorageManager
        
        config = Config()
        storage = StorageManager(config)
        
        # Create recordings directory
        os.makedirs(config.get("recordings_path"), exist_ok=True)
        
        size = storage.get_directory_size()
        print(f"✓ Storage manager initialized")
        print(f"  - Current recordings size: {size:.2f} GB")
        return True
    except Exception as e:
        print(f"✗ Storage manager test failed: {e}")
        return False

def test_camera_capture_init():
    """Test camera capture initialization (without opening camera)"""
    print("\nTesting camera capture initialization...")
    try:
        from usb_cam_viewer import Config, CameraCapture
        
        config = Config()
        # Don't actually open the camera, just test initialization
        camera = CameraCapture(0, config)
        print(f"✓ Camera capture object created")
        print(f"  - HOG detector initialized: {camera.hog is not None}")
        return True
    except Exception as e:
        print(f"✗ Camera capture init failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("AnomRecorder Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Storage Manager", test_storage_manager),
        ("Camera Capture Init", test_camera_capture_init),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
