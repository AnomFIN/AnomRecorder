"""
Tests for the installer auto-start functionality.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys


class TestInstallerAutoStart(unittest.TestCase):
    """Test the auto-start installation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock tkinter to avoid GUI dependencies in tests
        self.tk_mock = MagicMock()
        self.ttk_mock = MagicMock()
        self.messagebox_mock = MagicMock()
        self.scrolledtext_mock = MagicMock()
        
        sys.modules['tkinter'] = self.tk_mock
        sys.modules['tkinter.ttk'] = self.ttk_mock
        sys.modules['tkinter.messagebox'] = self.messagebox_mock
        sys.modules['tkinter.scrolledtext'] = self.scrolledtext_mock
        
        # Import after mocking
        import install
        self.install_module = install
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove mocked modules
        for module in ['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.scrolledtext']:
            if module in sys.modules:
                del sys.modules[module]
        # Remove install module
        if 'install' in sys.modules:
            del sys.modules['install']

    @patch('install.GUI_AVAILABLE', True)
    def test_auto_start_called_after_successful_check(self):
        """Test that auto_start_installation is scheduled after successful system check."""
        # Create a mock root
        root_mock = Mock()
        root_mock.after = Mock()
        
        # Create installer instance
        with patch('install.tk.Tk', return_value=root_mock):
            with patch.object(self.install_module.InstallerGUI, 'create_widgets'):
                installer = self.install_module.InstallerGUI(root_mock)
                installer.python_version_ok = True
                # Mock required GUI elements
                installer.progress_bar = Mock()
                installer.progress_label = Mock()
                installer.install_button = Mock()
                installer.log_text = Mock()
                
                # Call the completion method
                installer._complete_system_check()
                
                # Verify that auto_start_installation was scheduled
                root_mock.after.assert_called_with(300, installer.auto_start_installation)

    @patch('install.GUI_AVAILABLE', True)
    def test_auto_start_prevents_duplicate_runs(self):
        """Test that auto_start_installation prevents duplicate runs."""
        root_mock = Mock()
        
        with patch('install.tk.Tk', return_value=root_mock):
            with patch.object(self.install_module.InstallerGUI, 'create_widgets'):
                installer = self.install_module.InstallerGUI(root_mock)
                installer.python_version_ok = True
                installer._do_installation = Mock()
                installer.log_text = Mock()
                
                # First call should work
                installer.auto_start_installation()
                installer._do_installation.assert_called_once()
                
                # Second call should be blocked
                installer.auto_start_installation()
                installer._do_installation.assert_called_once()  # Still just once

    @patch('install.GUI_AVAILABLE', True)
    def test_auto_start_blocked_when_python_not_ok(self):
        """Test that auto_start_installation is blocked when Python version check fails."""
        root_mock = Mock()
        
        with patch('install.tk.Tk', return_value=root_mock):
            with patch.object(self.install_module.InstallerGUI, 'create_widgets'):
                installer = self.install_module.InstallerGUI(root_mock)
                installer.python_version_ok = False
                installer.installation_started = False
                installer._do_installation = Mock()
                
                # Call should be blocked
                installer.auto_start_installation()
                installer._do_installation.assert_not_called()

    @patch('install.GUI_AVAILABLE', True)
    def test_installation_started_flag_set_before_start(self):
        """Test that installation_started flag is set before calling _do_installation."""
        root_mock = Mock()
        
        with patch('install.tk.Tk', return_value=root_mock):
            with patch.object(self.install_module.InstallerGUI, 'create_widgets'):
                installer = self.install_module.InstallerGUI(root_mock)
                installer.python_version_ok = True
                installer.installation_started = False
                installer.log_text = Mock()
                
                # Track flag state when _do_installation is called
                flag_was_set = False
                
                def track_flag():
                    nonlocal flag_was_set
                    flag_was_set = installer.installation_started
                
                installer._do_installation = Mock(side_effect=track_flag)
                
                # Call auto_start
                installer.auto_start_installation()
                
                # Verify flag was True when _do_installation was called
                self.assertTrue(flag_was_set)

    @patch('install.GUI_AVAILABLE', True)
    def test_start_installation_prevents_duplicate_runs(self):
        """Test that start_installation method also prevents duplicate runs."""
        root_mock = Mock()
        root_mock.after = Mock()
        
        with patch('install.tk.Tk', return_value=root_mock):
            with patch.object(self.install_module.InstallerGUI, 'create_widgets'):
                installer = self.install_module.InstallerGUI(root_mock)
                installer.python_version_ok = True
                installer.installation_started = True  # Already started
                installer.log = Mock()
                
                # Call should be blocked and log a message
                installer.start_installation()
                installer.log.assert_called_with("Installation already running.")


if __name__ == '__main__':
    unittest.main()
