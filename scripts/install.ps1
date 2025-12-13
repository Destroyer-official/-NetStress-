# NetStress Installation Script for Windows (PowerShell)
# This script automates the installation process on Windows

param(
    [switch]$SkipDependencies,
    [switch]$NativeEngine,
    [switch]$Force,
    [string]$InstallPath = "$env:USERPROFILE\.netstress"
)

# Configuration
$FrameworkName = "NetStress Power Trio"
$RepoUrl = "https://github.com/Destroyer-official/-NetStress-.git"
$PythonMinVersion = [Version]"3.8"

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Cyan"
    White = "White"
}

function Write-Header {
    Write-Host "================================" -ForegroundColor $Colors.Blue
    Write-Host "  $FrameworkName" -ForegroundColor $Colors.Blue
    Write-Host "  Installation Script" -ForegroundColor $Colors.Blue
    Write-Host "================================" -ForegroundColor $Colors.Blue
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor $Colors.Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-PythonVersion {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            return $false, $null
        }
        
        $versionString = ($pythonVersion -split " ")[1]
        $version = [Version]$versionString
        
        return ($version -ge $PythonMinVersion), $version
    }
    catch {
        return $false, $null
    }
}

function Install-Chocolatey {
    Write-Info "Installing Chocolatey package manager..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

function Install-Dependencies {
    Write-Step "Installing system dependencies..."
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Warning "Administrator privileges recommended for installing dependencies."
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Please run as Administrator for full installation."
            return $false
        }
    }
    
    # Install Chocolatey if not present
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Install-Chocolatey
    }
    
    # Install dependencies
    $dependencies = @("python", "git", "visualstudio2022buildtools", "npcap")
    
    foreach ($dep in $dependencies) {
        Write-Info "Installing $dep..."
        try {
            choco install $dep -y --no-progress
        }
        catch {
            Write-Warning "Failed to install $dep with Chocolatey. Please install manually."
        }
    }
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    return $true
}

function Install-Rust {
    Write-Step "Installing Rust..."
    
    if (Get-Command rustc -ErrorAction SilentlyContinue) {
        Write-Info "Rust already installed"
        return $true
    }
    
    try {
        # Download and install rustup
        $rustupUrl = "https://win.rustup.rs/x86_64"
        $rustupPath = "$env:TEMP\rustup-init.exe"
        
        Write-Info "Downloading Rust installer..."
        Invoke-WebRequest -Uri $rustupUrl -OutFile $rustupPath
        
        Write-Info "Installing Rust..."
        Start-Process -FilePath $rustupPath -ArgumentList "-y" -Wait
        
        # Add Rust to PATH
        $cargoPath = "$env:USERPROFILE\.cargo\bin"
        if ($env:Path -notlike "*$cargoPath*") {
            $env:Path += ";$cargoPath"
            [Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::User)
        }
        
        # Verify installation
        if (Get-Command rustc -ErrorAction SilentlyContinue) {
            Write-Success "Rust installed successfully"
            return $true
        }
        else {
            Write-Error "Rust installation verification failed"
            return $false
        }
    }
    catch {
        Write-Error "Failed to install Rust: $_"
        return $false
    }
}

function New-VirtualEnvironment {
    param([string]$Path)
    
    Write-Step "Creating virtual environment..."
    
    if (Test-Path "$Path\venv") {
        Write-Info "Virtual environment already exists"
        return $true
    }
    
    try {
        python -m venv "$Path\venv"
        Write-Success "Virtual environment created"
        return $true
    }
    catch {
        Write-Error "Failed to create virtual environment: $_"
        return $false
    }
}

function Invoke-InVirtualEnvironment {
    param(
        [string]$Path,
        [scriptblock]$ScriptBlock
    )
    
    $activateScript = "$Path\venv\Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        throw "Virtual environment not found at $Path"
    }
    
    # Save current execution policy
    $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
    
    try {
        # Temporarily allow script execution
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        
        # Activate virtual environment
        & $activateScript
        
        # Execute the script block
        & $ScriptBlock
    }
    finally {
        # Restore execution policy
        Set-ExecutionPolicy -ExecutionPolicy $currentPolicy -Scope CurrentUser -Force
        
        # Deactivate virtual environment
        if (Get-Command deactivate -ErrorAction SilentlyContinue) {
            deactivate
        }
    }
}

function Install-NetStress {
    param([string]$Path)
    
    Write-Step "Installing NetStress..."
    
    # Create installation directory
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
    
    # Clone or update repository
    $repoPath = "$Path\NetStress"
    if (Test-Path $repoPath) {
        Write-Info "Repository exists, updating..."
        Push-Location $repoPath
        try {
            git pull
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Info "Cloning repository..."
        git clone $RepoUrl $repoPath
    }
    
    # Install Python dependencies
    Invoke-InVirtualEnvironment -Path $Path -ScriptBlock {
        Push-Location $repoPath
        try {
            Write-Info "Upgrading pip..."
            python -m pip install --upgrade pip setuptools wheel
            
            Write-Info "Installing dependencies..."
            pip install -r requirements.txt
            
            if ($NativeEngine) {
                Write-Info "Installing native engine dependencies..."
                pip install maturin
            }
        }
        finally {
            Pop-Location
        }
    }
    
    return $true
}

function Build-NativeEngine {
    param([string]$Path)
    
    Write-Step "Building native engine..."
    
    $repoPath = "$Path\NetStress"
    $rustEnginePath = "$repoPath\native\rust_engine"
    
    if (-not (Test-Path $rustEnginePath)) {
        Write-Error "Rust engine source not found"
        return $false
    }
    
    Invoke-InVirtualEnvironment -Path $Path -ScriptBlock {
        Push-Location $rustEnginePath
        try {
            Write-Info "Building Rust engine with Windows features..."
            maturin develop --release --features "iocp"
            Write-Success "Native engine built successfully"
        }
        catch {
            Write-Error "Failed to build native engine: $_"
            throw
        }
        finally {
            Pop-Location
        }
    }
    
    return $true
}

function New-LauncherScripts {
    param([string]$Path)
    
    Write-Step "Creating launcher scripts..."
    
    $binPath = "$Path\bin"
    if (-not (Test-Path $binPath)) {
        New-Item -ItemType Directory -Path $binPath -Force | Out-Null
    }
    
    $repoPath = "$Path\NetStress"
    $venvPath = "$Path\venv"
    
    # Main launcher
    $mainScript = @"
@echo off
set "INSTALL_DIR=$Path"
call "$venvPath\Scripts\activate.bat"
cd /d "$repoPath"
python ddos.py %*
"@
    $mainScript | Out-File -FilePath "$binPath\netstress.bat" -Encoding ASCII
    
    # CLI launcher
    $cliScript = @"
@echo off
set "INSTALL_DIR=$Path"
call "$venvPath\Scripts\activate.bat"
cd /d "$repoPath"
python netstress_cli.py %*
"@
    $cliScript | Out-File -FilePath "$binPath\netstress-cli.bat" -Encoding ASCII
    
    # PowerShell launcher
    $psScript = @"
`$InstallDir = "$Path"
& "$venvPath\Scripts\Activate.ps1"
Set-Location "$repoPath"
python ddos.py `$args
"@
    $psScript | Out-File -FilePath "$binPath\netstress.ps1" -Encoding UTF8
    
    Write-Success "Launcher scripts created"
    return $true
}

function Add-ToPath {
    param([string]$Path)
    
    Write-Step "Adding to PATH..."
    
    $binPath = "$Path\bin"
    $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    
    if ($currentPath -notlike "*$binPath*") {
        $newPath = "$currentPath;$binPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::User)
        $env:Path = $newPath
        Write-Success "Added to user PATH"
    }
    else {
        Write-Info "Already in PATH"
    }
}

function New-DesktopShortcuts {
    param([string]$Path)
    
    Write-Step "Creating desktop shortcuts..."
    
    try {
        $WshShell = New-Object -comObject WScript.Shell
        
        # CLI shortcut
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\NetStress CLI.lnk")
        $Shortcut.TargetPath = "$Path\bin\netstress-cli.bat"
        $Shortcut.WorkingDirectory = $Path
        $Shortcut.Description = "NetStress Command Line Interface"
        $Shortcut.Save()
        
        Write-Success "Desktop shortcuts created"
    }
    catch {
        Write-Warning "Failed to create desktop shortcuts: $_"
    }
}

function Test-Installation {
    param([string]$Path)
    
    Write-Step "Testing installation..."
    
    $repoPath = "$Path\NetStress"
    
    try {
        Invoke-InVirtualEnvironment -Path $Path -ScriptBlock {
            Push-Location $repoPath
            try {
                # Test basic import
                python -c "import core; print('Framework import successful')"
                Write-Success "Framework import test passed"
                
                # Test CLI
                python ddos.py --help | Out-Null
                Write-Success "CLI test passed"
                
                if ($NativeEngine) {
                    # Test native engine
                    python -c "import netstress_engine; print('Native engine available')"
                    Write-Success "Native engine test passed"
                }
            }
            finally {
                Pop-Location
            }
        }
        
        return $true
    }
    catch {
        Write-Error "Installation test failed: $_"
        return $false
    }
}

function Write-CompletionMessage {
    param([string]$Path)
    
    Write-Host ""
    Write-Success "Installation completed successfully!"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor $Colors.Blue
    Write-Host "1. Restart your PowerShell/Command Prompt"
    Write-Host "2. Test the installation: netstress --help"
    Write-Host "3. Read the documentation: $Path\NetStress\README.md"
    Write-Host ""
    Write-Host "Important:" -ForegroundColor $Colors.Yellow
    Write-Host "- This framework is for educational and authorized testing only"
    Write-Host "- Always ensure you have permission before testing any systems"
    Write-Host "- Use only in controlled, isolated environments"
    Write-Host "- Run as Administrator for raw socket support"
    Write-Host ""
    Write-Host "Support:" -ForegroundColor $Colors.Blue
    Write-Host "- Documentation: https://github.com/Destroyer-official/-NetStress-"
    Write-Host "- Issues: https://github.com/Destroyer-official/-NetStress-/issues"
    Write-Host ""
}

# Main installation function
function Install-NetStressFramework {
    Write-Header
    
    # Check if running as administrator for better experience
    if (Test-Administrator) {
        Write-Info "Running as Administrator - full installation available"
    }
    else {
        Write-Warning "Not running as Administrator - some features may be limited"
    }
    
    # Check Python
    Write-Step "Checking Python installation..."
    $pythonOk, $pythonVersion = Test-PythonVersion
    
    if (-not $pythonOk) {
        if (-not $SkipDependencies) {
            Write-Info "Python not found or version too old. Installing dependencies..."
            if (-not (Install-Dependencies)) {
                Write-Error "Failed to install dependencies"
                return $false
            }
            
            # Re-check Python after installation
            $pythonOk, $pythonVersion = Test-PythonVersion
        }
        
        if (-not $pythonOk) {
            Write-Error "Python $PythonMinVersion or higher is required"
            Write-Info "Please install Python from https://python.org/downloads/"
            return $false
        }
    }
    
    Write-Success "Python $pythonVersion found"
    
    # Install Rust if native engine requested
    if ($NativeEngine) {
        if (-not (Install-Rust)) {
            Write-Error "Failed to install Rust"
            return $false
        }
    }
    
    # Create virtual environment
    if (-not (New-VirtualEnvironment -Path $InstallPath)) {
        Write-Error "Failed to create virtual environment"
        return $false
    }
    
    # Install NetStress
    if (-not (Install-NetStress -Path $InstallPath)) {
        Write-Error "Failed to install NetStress"
        return $false
    }
    
    # Build native engine if requested
    if ($NativeEngine) {
        if (-not (Build-NativeEngine -Path $InstallPath)) {
            Write-Warning "Failed to build native engine, continuing with Python-only mode"
        }
    }
    
    # Create launcher scripts
    New-LauncherScripts -Path $InstallPath
    
    # Add to PATH
    Add-ToPath -Path $InstallPath
    
    # Create desktop shortcuts
    New-DesktopShortcuts -Path $InstallPath
    
    # Test installation
    if (-not (Test-Installation -Path $InstallPath)) {
        Write-Warning "Installation test failed, but installation may still work"
    }
    
    # Show completion message
    Write-CompletionMessage -Path $InstallPath
    
    return $true
}

# Handle Ctrl+C
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Host "`nInstallation interrupted!" -ForegroundColor Red
}

# Main execution
try {
    if (-not (Install-NetStressFramework)) {
        Write-Error "Installation failed!"
        exit 1
    }
}
catch {
    Write-Error "Installation failed with error: $_"
    exit 1
}

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")