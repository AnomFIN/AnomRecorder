#!/usr/bin/env python3
"""
Simple test to verify usb_cam_viewer.py has all required imports and can be parsed.
This test does not require a display or camera hardware.
"""

import ast
import sys


def test_syntax():
    """Test that the file has valid Python syntax"""
    print("Testing Python syntax...")
    try:
        with open('usb_cam_viewer.py', 'r') as f:
            code = f.read()
        compile(code, 'usb_cam_viewer.py', 'exec')
        print("✓ Syntax check passed")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False


def test_required_imports():
    """Test that all required imports are present in the file"""
    print("\nTesting required imports...")
    
    with open('usb_cam_viewer.py', 'r') as f:
        tree = ast.parse(f.read())
    
    # Extract all imports
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ''
            for alias in node.names:
                full_name = f'{module}.{alias.name}' if module else alias.name
                imports.add(full_name)
    
    # Check for critical imports that were previously missing
    required = {
        'tkinter.filedialog': 'Used in _choose_logo method',
        'tkinter.simpledialog': 'Used in add_event_note method',
    }
    
    all_ok = True
    for req, usage in required.items():
        if req in imports:
            print(f"✓ {req} is imported ({usage})")
        else:
            print(f"✗ {req} is NOT imported but {usage}")
            all_ok = False
    
    return all_ok


def test_import_statements():
    """Test that the required dependencies are in the import statements"""
    print("\nTesting module dependencies...")
    
    with open('usb_cam_viewer.py', 'r') as f:
        code = f.read()
    
    required_modules = {
        'numpy': 'import numpy as np',
        'PIL': 'from PIL import Image, ImageTk',
        'cv2': 'import cv2',
        'tkinter': 'import tkinter as tk',
    }
    
    all_ok = True
    for module, expected_import in required_modules.items():
        if expected_import in code or f'import {module}' in code:
            print(f"✓ {module} import found")
        else:
            print(f"✗ {module} import NOT found")
            all_ok = False
    
    return all_ok


def main():
    """Run all tests"""
    print("=" * 60)
    print("USB Camera Viewer Import Tests")
    print("=" * 60)
    
    tests = [
        test_syntax,
        test_required_imports,
        test_import_statements,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {len(results) - sum(results)} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
