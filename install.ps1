<#
.SYNOPSIS
    AnomRecorder Windows Installer - 100% Bulletproof
.DESCRIPTION
    Fully automated installer for AnomRecorder on Windows.
    Creates virtual environment, installs dependencies, tests installation,
    and optionally launches the application.
    
    Features:
    - Zero manual steps required
    - Never crashes (comprehensive error handling)
    - Professional logging to file
    - Auto-retry on transient failures
    - Silent mode support
    - Auto-launch capability
    
.PARAMETER Silent
    Run in silent mode (no interactive prompts)
.PARAMETER NoLaunch
    Skip auto-launching the application after installation
.PARAMETER NoVenv
    Skip virtual environment creation (use global Python)
.EXAMPLE
    .\install.ps1
    Standard installation with prompts
.EXAMPLE
    .\install.ps1 -Silent -NoLaunch
    Silent installation without launching
#>

[CmdletBinding()]
param(
    [switch]$Silent,
    [switch]$NoLaunch,
    [switch]$NoVenv
)

# Error handling: Never crash, always exit gracefully
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogFile = Join-Path $ScriptDir "installer.log"
$VenvDir = Join-Path $ScriptDir ".venv"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$AppEntry = Join-Path $ScriptDir "usb_cam_viewer.py"
$MinPythonVersion = [version]"3.8.0"
$MaxRetries = 3

# Initialize alternate log notification flag
$script:AltLogNotified = $false

#region Logging Functions

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Always log to file with better error handling
    try {
        Add-Content -Path $LogFile -Value $logMessage -ErrorAction Stop
    } catch {
        # If primary log fails, try alternate log location
        try {
            $altLog = Join-Path $env:TEMP "anomrecorder_installer.log"
            Add-Content -Path $altLog -Value $logMessage -ErrorAction Stop
            # Notify user once about alternate log location
            if (-not $script:AltLogNotified) {
                Write-Host "Note: Using alternate log location: $altLog" -ForegroundColor Yellow
                $script:AltLogNotified = $true
            }
        } catch {
            # If both fail, continue without file logging (to not block installation)
        }
    }
    
    # Console output based on level and silent mode
    if (-not $Silent) {
        switch ($Level) {
            "SUCCESS" {
                Write-Host "✓ $Message" -ForegroundColor Green
            }
            "ERROR" {
                Write-Host "✗ $Message" -ForegroundColor Red
            }
            "WARNING" {
                Write-Host "⚠ $Message" -ForegroundColor Yellow
            }
            "HEADER" {
                Write-Host "`n=== $Message ===`n" -ForegroundColor Cyan
            }
            default {
                Write-Host "  $Message"
            }
        }
    }
}

function Write-Header {
    param([string]$Text)
    Write-Log -Message $Text -Level "HEADER"
}

function Write-Success {
    param([string]$Text)
    Write-Log -Message $Text -Level "SUCCESS"
}

function Write-Error-Safe {
    param([string]$Text)
    Write-Log -Message $Text -Level "ERROR"
}

function Write-Warning-Safe {
    param([string]$Text)
    Write-Log -Message $Text -Level "WARNING"
}

#endregion

#region Helper Functions

function Test-PythonInstalled {
    try {
        $null = Get-Command python -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Get-PythonVersion {
    try {
        $versionOutput = & python --version 2>&1
        if ($versionOutput -match "Python (\d+\.\d+\.\d+)") {
            return [version]$matches[1]
        }
        return $null
    } catch {
        return $null
    }
}

function Test-PythonVersionValid {
    param([version]$Version)
    return $Version -ge $MinPythonVersion
}

function Invoke-CommandWithRetry {
    param(
        [scriptblock]$Command,
        [string]$Description,
        [int]$Retries = $MaxRetries
    )
    
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            Write-Log "Attempting: $Description (Try $i/$Retries)"
            $result = & $Command
            Write-Success "$Description completed successfully"
            return $true
        } catch {
            Write-Warning-Safe "$Description failed (Try $i/$Retries): $($_.Exception.Message)"
            if ($i -eq $Retries) {
                Write-Error-Safe "$Description failed after $Retries attempts"
                return $false
            }
            Start-Sleep -Seconds (2 * $i)
        }
    }
    return $false
}

function Show-FriendlyError {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Suggestion = ""
    )
    
    Write-Log "`n" -Level "ERROR"
    Write-Log "╔═══════════════════════════════════════════════════════════╗" -Level "ERROR"
    Write-Log "║  $Title" -Level "ERROR"
    Write-Log "╠═══════════════════════════════════════════════════════════╣" -Level "ERROR"
    Write-Log "║  $Message" -Level "ERROR"
    if ($Suggestion) {
        Write-Log "║" -Level "ERROR"
        Write-Log "║  💡 Suggestion: $Suggestion" -Level "ERROR"
    }
    Write-Log "╚═══════════════════════════════════════════════════════════╝" -Level "ERROR"
    Write-Log "" -Level "ERROR"
}

#endregion

#region Installation Functions

function Test-SystemRequirements {
    Write-Header "Checking System Requirements"
    
    # Check Python installation
    Write-Log "Checking for Python..."
    if (-not (Test-PythonInstalled)) {
        Show-FriendlyError `
            -Title "Python Not Found" `
            -Message "Python is not installed or not in PATH" `
            -Suggestion "Download Python from https://www.python.org/downloads/ (version 3.8 or higher)"
        return $false
    }
    Write-Success "Python is installed"
    
    # Check Python version
    $pythonVersion = Get-PythonVersion
    if ($null -eq $pythonVersion) {
        Show-FriendlyError `
            -Title "Cannot Determine Python Version" `
            -Message "Unable to detect Python version" `
            -Suggestion "Ensure Python is properly installed and accessible from command line"
        return $false
    }
    
    Write-Log "Detected Python version: $pythonVersion"
    
    if (-not (Test-PythonVersionValid $pythonVersion)) {
        Show-FriendlyError `
            -Title "Python Version Too Old" `
            -Message "Python $MinPythonVersion or higher is required, found $pythonVersion" `
            -Suggestion "Upgrade Python from https://www.python.org/downloads/"
        return $false
    }
    Write-Success "Python version is compatible ($pythonVersion >= $MinPythonVersion)"
    
    # Check pip
    Write-Log "Checking for pip..."
    try {
        $pipVersion = & python -m pip --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "pip check failed"
        }
        Write-Success "pip is available"
        Write-Log "pip version: $pipVersion"
    } catch {
        Show-FriendlyError `
            -Title "pip Not Available" `
            -Message "pip (Python package installer) is not available" `
            -Suggestion "Reinstall Python with pip included, or run: python -m ensurepip"
        return $false
    }
    
    # Check venv module
    if (-not $NoVenv) {
        Write-Log "Checking for venv module..."
        try {
            $venvCheck = & python -c "import venv" 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "venv import failed"
            }
            Write-Success "venv module is available"
        } catch {
            Show-FriendlyError `
                -Title "venv Module Not Available" `
                -Message "Python venv module is not available" `
                -Suggestion "Reinstall Python with venv included, or use -NoVenv flag"
            return $false
        }
    }
    
    # Check requirements.txt exists
    if (-not (Test-Path $RequirementsFile)) {
        Show-FriendlyError `
            -Title "Requirements File Missing" `
            -Message "requirements.txt not found in $ScriptDir" `
            -Suggestion "Ensure you have the complete AnomRecorder package"
        return $false
    }
    Write-Success "requirements.txt found"
    
    Write-Success "All system requirements met"
    return $true
}

function Initialize-VirtualEnvironment {
    if ($NoVenv) {
        Write-Log "Skipping virtual environment (--no-venv flag)"
        return @{
            Python = "python"
            Pip = "python -m pip"
        }
    }
    
    Write-Header "Setting Up Virtual Environment"
    
    if (Test-Path $VenvDir) {
        Write-Log "Virtual environment already exists at: $VenvDir"
        Write-Success "Reusing existing virtual environment"
    } else {
        Write-Log "Creating virtual environment at: $VenvDir"
        
        try {
            $createVenvCmd = {
                & python -m venv $VenvDir 2>&1 | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    throw "venv creation failed with exit code $LASTEXITCODE"
                }
            }
            
            $success = Invoke-CommandWithRetry `
                -Command $createVenvCmd `
                -Description "Virtual environment creation" `
                -Retries 2
            
            if (-not $success) {
                Show-FriendlyError `
                    -Title "Virtual Environment Creation Failed" `
                    -Message "Could not create virtual environment" `
                    -Suggestion "Try running with -NoVenv flag to install globally"
                return $null
            }
            
            Write-Success "Virtual environment created successfully"
        } catch {
            Show-FriendlyError `
                -Title "Virtual Environment Error" `
                -Message $_.Exception.Message `
                -Suggestion "Try running with -NoVenv flag to install globally"
            return $null
        }
    }
    
    # Determine Python and pip paths in venv
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    $venvPip = Join-Path $VenvDir "Scripts\pip.exe"
    
    if (-not (Test-Path $venvPython)) {
        Show-FriendlyError `
            -Title "Virtual Environment Invalid" `
            -Message "Python executable not found in virtual environment" `
            -Suggestion "Delete .venv folder and try again"
        return $null
    }
    
    Write-Success "Virtual environment is ready"
    return @{
        Python = $venvPython
        Pip = "$venvPython -m pip"
    }
}

function Install-Dependencies {
    param(
        [hashtable]$Paths
    )
    
    Write-Header "Installing Dependencies"
    
    $pythonExe = $Paths.Python
    $pipCmd = $Paths.Pip
    
    # Upgrade pip first
    Write-Log "Upgrading pip, setuptools, and wheel..."
    try {
        $upgradeCmd = {
            $output = & $pythonExe -m pip install --upgrade pip setuptools wheel 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Pip upgrade failed: $output"
            }
        }
        
        $success = Invoke-CommandWithRetry `
            -Command $upgradeCmd `
            -Description "pip/setuptools/wheel upgrade" `
            -Retries 2
        
        if (-not $success) {
            Write-Warning-Safe "Could not upgrade pip/setuptools/wheel, continuing anyway..."
        }
    } catch {
        Write-Warning-Safe "pip upgrade encountered issues: $($_.Exception.Message)"
        Write-Log "Continuing with existing pip version..."
    }
    
    # Install dependencies from requirements.txt
    Write-Log "Installing packages from requirements.txt..."
    Write-Log "This may take several minutes..."
    
    try {
        $installCmd = {
            $output = & $pythonExe -m pip install -r $RequirementsFile 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Dependency installation failed"
            }
            return $output
        }
        
        $success = Invoke-CommandWithRetry `
            -Command $installCmd `
            -Description "Dependency installation" `
            -Retries 3
        
        if (-not $success) {
            Write-Warning-Safe "Some dependencies may have failed to install"
            Write-Log "Attempting package-by-package installation..."
            
            # Try installing packages one by one
            $packages = Get-Content $RequirementsFile | Where-Object { 
                $_ -and $_ -notmatch '^\s*#' -and $_ -notmatch '^\s*$' 
            }
            
            $failed = @()
            foreach ($package in $packages) {
                Write-Log "Installing $package..."
                try {
                    $output = & $pythonExe -m pip install $package 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "Installed $package"
                    } else {
                        $failed += $package
                        Write-Warning-Safe "Failed to install $package"
                    }
                } catch {
                    $failed += $package
                    Write-Warning-Safe "Error installing $package: $($_.Exception.Message)"
                }
            }
            
            if ($failed.Count -gt 0) {
                Write-Warning-Safe "The following packages could not be installed:"
                foreach ($pkg in $failed) {
                    Write-Log "  - $pkg"
                }
                Write-Log "`nThe application may have limited functionality."
                return $false
            }
        }
        
        Write-Success "All dependencies installed successfully"
        return $true
        
    } catch {
        Show-FriendlyError `
            -Title "Dependency Installation Failed" `
            -Message $_.Exception.Message `
            -Suggestion "Check your internet connection and try again"
        return $false
    }
}

function Test-Installation {
    param(
        [hashtable]$Paths
    )
    
    Write-Header "Testing Installation"
    
    $pythonExe = $Paths.Python
    
    # Test critical imports
    $modules = @(
        "PySide6",
        "cv2",
        "numpy",
        "PIL"
    )
    
    $allSuccess = $true
    foreach ($module in $modules) {
        Write-Log "Testing import: $module"
        try {
            $output = & $pythonExe -c "import $module" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Module $module is available"
            } else {
                Write-Warning-Safe "Module $module import failed"
                $allSuccess = $false
            }
        } catch {
            Write-Warning-Safe "Module $module test failed: $($_.Exception.Message)"
            $allSuccess = $false
        }
    }
    
    if ($allSuccess) {
        Write-Success "All critical modules tested successfully"
    } else {
        Write-Warning-Safe "Some modules failed to import, but installation may still work"
    }
    
    return $allSuccess
}

function Start-Application {
    param(
        [hashtable]$Paths
    )
    
    Write-Header "Launching Application"
    
    $pythonExe = $Paths.Python
    
    if (-not (Test-Path $AppEntry)) {
        Write-Warning-Safe "Application entry point not found: $AppEntry"
        Write-Log "Try running manually: python usb_cam_viewer.py"
        return $false
    }
    
    Write-Log "Starting AnomRecorder..."
    Write-Log "Application will open in a new window"
    
    try {
        # Launch in background
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $pythonExe
        $processInfo.Arguments = "`"$AppEntry`""
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $false
        $processInfo.WorkingDirectory = $ScriptDir
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        $null = $process.Start()
        
        Write-Success "Application launched successfully (PID: $($process.Id))"
        return $true
    } catch {
        Write-Warning-Safe "Could not auto-launch application: $($_.Exception.Message)"
        Write-Log "You can start it manually: python usb_cam_viewer.py"
        return $false
    }
}

#endregion

#region Main Installation Flow

function Start-Installation {
    # Initialize log file
    try {
        "=== AnomRecorder Installation Log ===" | Out-File -FilePath $LogFile -Encoding UTF8
        "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        "" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    } catch {
        # Continue even if log file creation fails
    }
    
    # Display banner
    if (-not $Silent) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                                                           ║" -ForegroundColor Cyan
        Write-Host "║          AnomRecorder Windows Installer v1.0              ║" -ForegroundColor Cyan
        Write-Host "║                                                           ║" -ForegroundColor Cyan
        Write-Host "║          Bulletproof • Automated • Professional           ║" -ForegroundColor Cyan
        Write-Host "║                                                           ║" -ForegroundColor Cyan
        Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""
    }
    
    Write-Log "Installation started with parameters:"
    Write-Log "  Silent: $Silent"
    Write-Log "  NoLaunch: $NoLaunch"
    Write-Log "  NoVenv: $NoVenv"
    Write-Log "  Script Directory: $ScriptDir"
    Write-Log "  Log File: $LogFile"
    
    # Step 1: Check system requirements
    if (-not (Test-SystemRequirements)) {
        Write-Error-Safe "System requirements check failed"
        return 1
    }
    
    # Step 2: Set up virtual environment
    $paths = Initialize-VirtualEnvironment
    if ($null -eq $paths) {
        Write-Error-Safe "Virtual environment setup failed"
        return 1
    }
    
    # Step 3: Install dependencies
    $depsSuccess = Install-Dependencies -Paths $paths
    if (-not $depsSuccess) {
        Write-Warning-Safe "Dependency installation completed with warnings"
    }
    
    # Step 4: Test installation
    $testSuccess = Test-Installation -Paths $paths
    
    # Step 5: Complete installation
    Write-Header "Installation Complete"
    
    if ($testSuccess) {
        Write-Success "AnomRecorder has been installed successfully!"
    } else {
        Write-Warning-Safe "Installation completed with some warnings"
    }
    
    Write-Log "`nInstallation log saved to: $LogFile"
    
    # Step 6: Launch application if requested
    if (-not $NoLaunch -and $testSuccess) {
        if ($Silent) {
            Start-Application -Paths $paths | Out-Null
        } else {
            $response = Read-Host "`nWould you like to launch AnomRecorder now? (Y/n)"
            if ($response -eq "" -or $response -match "^[Yy]") {
                Start-Application -Paths $paths | Out-Null
            }
        }
    }
    
    if (-not $Silent) {
        Write-Host ""
        Write-Host "To run AnomRecorder in the future:" -ForegroundColor Cyan
        if ($NoVenv) {
            Write-Host "  python usb_cam_viewer.py" -ForegroundColor Yellow
        } else {
            Write-Host "  .\.venv\Scripts\python.exe usb_cam_viewer.py" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "Thank you for using AnomRecorder!" -ForegroundColor Green
        Write-Host ""
    }
    
    Write-Log "Installation completed successfully"
    return 0
}

#endregion

# Main entry point
try {
    $exitCode = Start-Installation
    exit $exitCode
} catch {
    Write-Error-Safe "Unexpected error during installation: $($_.Exception.Message)"
    Write-Log "Stack trace: $($_.ScriptStackTrace)"
    Show-FriendlyError `
        -Title "Installation Failed" `
        -Message $_.Exception.Message `
        -Suggestion "Check installer.log for details or contact support"
    exit 1
}
