#!/usr/bin/env python3
"""
Integration test for the Windows installer components.
Tests that all installer files exist and have correct structure.
"""

import sys
from pathlib import Path

def test_installer_files_exist():
    """Verify all installer files are present"""
    required_files = [
        'install.bat',
        'install.ps1',
        'install.py',
        'install_dependencies.bat',
        'run.bat',
        'requirements.txt',
        'WINDOWS_INSTALLER.md'
    ]
    
    project_root = Path(__file__).parent
    missing = []
    
    for file in required_files:
        if not (project_root / file).exists():
            missing.append(file)
    
    if missing:
        print(f"✗ Missing files: {', '.join(missing)}")
        return False
    
    print(f"✓ All required installer files present ({len(required_files)} files)")
    return True

def test_installer_scripts_syntax():
    """Verify installer scripts have valid syntax"""
    print("\n=== Syntax Validation ===")
    
    # Test Python script
    try:
        import py_compile
        py_compile.compile('install.py', doraise=True)
        print("✓ install.py has valid Python syntax")
    except py_compile.PyCompileError as e:
        print(f"✗ install.py syntax error: {e}")
        return False
    
    # Test PowerShell script exists and is readable
    ps_script = Path('install.ps1')
    if ps_script.exists():
        content = ps_script.read_text(encoding='utf-8')
        if 'param(' in content and 'function' in content:
            print("✓ install.ps1 structure looks valid")
        else:
            print("✗ install.ps1 may have structural issues")
            return False
    
    # Test batch files exist and contain expected commands
    for bat_file in ['install.bat', 'run.bat', 'install_dependencies.bat']:
        bat_path = Path(bat_file)
        if bat_path.exists():
            content = bat_path.read_text()
            if '@echo off' in content:
                print(f"✓ {bat_file} has valid batch structure")
            else:
                print(f"✗ {bat_file} missing batch header")
                return False
    
    return True

def test_installer_logging():
    """Test that logging configuration works"""
    print("\n=== Logging Test ===")
    
    try:
        import logging
        from datetime import datetime
        
        test_log = Path('test_installer_validation.log')
        
        # Create logger like in install.py
        logger = logging.getLogger('test_installer')
        handler = logging.FileHandler(test_log, encoding='utf-8')
        handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Test logging
        logger.info("Test message")
        logger.warning("Test warning")
        
        # Verify log was written
        if test_log.exists():
            content = test_log.read_text()
            if 'Test message' in content and 'Test warning' in content:
                print("✓ Logging functionality works correctly")
                test_log.unlink()  # Clean up
                return True
            else:
                print("✗ Log file doesn't contain expected content")
                test_log.unlink()
                return False
        else:
            print("✗ Log file was not created")
            return False
            
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False

def test_documentation():
    """Verify installer documentation is comprehensive"""
    print("\n=== Documentation Check ===")
    
    doc_file = Path('WINDOWS_INSTALLER.md')
    if not doc_file.exists():
        print("✗ WINDOWS_INSTALLER.md not found")
        return False
    
    content = doc_file.read_text()
    
    required_sections = [
        '## Overview',
        '## Features',
        '## Installation Methods',
        '## Troubleshooting',
        '## System Requirements',
        '## Logging'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"✗ Documentation missing sections: {', '.join(missing_sections)}")
        return False
    
    print(f"✓ Documentation contains all required sections")
    
    # Check documentation quality by verifying key content is present
    quality_checks = {
        'installation_methods': 'Method 1:' in content and 'Method 2:' in content,
        'troubleshooting': 'Troubleshooting' in content,
        'examples': '```' in content,  # Code examples present
        'comprehensive': len(content) > 3000  # Reasonable minimum length
    }
    
    quality_issues = [k for k, v in quality_checks.items() if not v]
    if quality_issues:
        print(f"⚠ Documentation quality concerns: {', '.join(quality_issues)}")
    else:
        print(f"✓ Documentation is comprehensive and well-structured ({len(content)} characters)")
    
    return True

def test_gitignore():
    """Verify .gitignore excludes installer artifacts"""
    print("\n=== .gitignore Check ===")
    
    gitignore = Path('.gitignore')
    if not gitignore.exists():
        print("✗ .gitignore not found")
        return False
    
    content = gitignore.read_text()
    
    required_entries = [
        '*.log',
        '.venv/'
    ]
    
    missing = []
    for entry in required_entries:
        if entry not in content:
            missing.append(entry)
    
    if missing:
        print(f"✗ .gitignore missing entries: {', '.join(missing)}")
        return False
    
    print("✓ .gitignore properly configured for installer artifacts")
    return True

def main():
    """Run all installer validation tests"""
    print("=" * 60)
    print("AnomRecorder Windows Installer Validation")
    print("=" * 60)
    
    tests = [
        ("File Existence", test_installer_files_exist),
        ("Script Syntax", test_installer_scripts_syntax),
        ("Logging", test_installer_logging),
        ("Documentation", test_documentation),
        (".gitignore", test_gitignore)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print('='*60)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All installer validation tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
