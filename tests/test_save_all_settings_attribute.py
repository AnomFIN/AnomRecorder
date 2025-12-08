"""Test that _save_all_settings attribute is correctly defined in CameraApp.

This test ensures that the AttributeError for the missing _save_all_settings
functionality has been resolved by verifying the method exists and follows
Pythonic conventions.
"""

import ast
import os


# Module-level constant for the app file path
APP_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'ui', 'app.py')


def _read_app_content() -> str:
    """Read the app.py file content."""
    with open(APP_FILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def test_save_all_settings_method_exists():
    """Test that _save_all_settings method is defined in CameraApp class."""
    content = _read_app_content()

    # Verify the method is defined
    assert 'def _save_all_settings(self)' in content, \
        "_save_all_settings method should be defined in CameraApp"


def test_save_all_settings_has_docstring():
    """Test that _save_all_settings method has a proper docstring."""
    content = _read_app_content()
    tree = ast.parse(content)

    # Find the _save_all_settings method
    found_method = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_save_all_settings':
            found_method = True
            # Check that it has a docstring
            if node.body and isinstance(node.body[0], ast.Expr):
                if isinstance(node.body[0].value, ast.Constant):
                    docstring = node.body[0].value.value
                    assert isinstance(docstring, str) and len(docstring) > 0, \
                        "_save_all_settings should have a non-empty docstring"
                    break
            else:
                raise AssertionError("_save_all_settings should have a docstring")

    assert found_method, "_save_all_settings method not found in AST"


def test_save_all_settings_is_referenced():
    """Test that _save_all_settings method is properly referenced in UI code."""
    content = _read_app_content()

    # Should be referenced as a button command
    assert 'command=self._save_all_settings' in content, \
        "_save_all_settings should be used as a button command"


def test_no_duplicate_save_buttons():
    """Test that there are no excessive duplicate save buttons in settings tab."""
    content = _read_app_content()

    # Count occurrences of save buttons in the settings tab
    save_button_count = content.count('text="Tallenna asetukset"')

    # There should be exactly 1 main save button in the settings tab
    assert save_button_count == 1, \
        f"Found {save_button_count} save buttons, expected exactly 1"
