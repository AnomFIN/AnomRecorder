"""Test that autoreconnect_var attribute is correctly used in the code."""

import ast
import os


def test_no_enable_autoreconnect_references():
    """Test that there are no references to the old enable_autoreconnect attribute."""
    app_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'ui', 'app.py')
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that enable_autoreconnect is not referenced anywhere
    assert 'enable_autoreconnect' not in content, \
        "Found reference to deprecated 'enable_autoreconnect' attribute"


def test_autoreconnect_var_is_used():
    """Test that autoreconnect_var is consistently used in the code."""
    app_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'ui', 'app.py')
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the Python file as AST
    tree = ast.parse(content)
    
    # Find the CameraApp class
    camera_app_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'CameraApp':
            camera_app_class = node
            break
    
    assert camera_app_class is not None, "CameraApp class not found"
    
    # Verify autoreconnect_var is defined somewhere in the class
    # (It's defined in _build_settings_tab which is called from __init__)
    assert 'self.autoreconnect_var' in content, \
        "autoreconnect_var should be defined in the CameraApp class"
    
    # Verify it's assigned as a BooleanVar
    assert 'self.autoreconnect_var = tk.BooleanVar' in content, \
        "autoreconnect_var should be initialized as a BooleanVar"


def _get_method_source(content: str, tree: ast.AST, method_name: str) -> str:
    """Helper function to extract method source code using AST parsing."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return ast.get_source_segment(content, node) or ""
    return ""


def test_autoreconnect_usage_in_methods():
    """Test that autoreconnect_var is used correctly in relevant methods."""
    app_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'ui', 'app.py')
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    # Check that _schedule_reconnect uses autoreconnect_var.get()
    schedule_method = _get_method_source(content, tree, '_schedule_reconnect')
    assert schedule_method, "_schedule_reconnect method not found"
    assert 'self.autoreconnect_var.get()' in schedule_method, \
        "_schedule_reconnect should use autoreconnect_var.get()"
    
    # Check that _try_autoreconnect uses autoreconnect_var.get()
    try_method = _get_method_source(content, tree, '_try_autoreconnect')
    assert try_method, "_try_autoreconnect method not found"
    assert 'self.autoreconnect_var.get()' in try_method, \
        "_try_autoreconnect should use autoreconnect_var.get()"
