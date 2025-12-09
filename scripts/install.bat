@echo off
REM Advanced DDoS Testing Framework - Installation Script for Windows
REM This script automates the installation process on Windows

setlocal enabledelayedexpansion

REM Configuration
set "FRAMEWORK_NAME=Advanced DDoS Testing Framework"
set "REPO_URL=https://github.com/ddos-framework/advanced-ddos-framework.git"
set "INSTALL_DIR=%USERPROFILE%\.ddos-framework"
set "PYTHON_MIN_VERSION=3.8"

REM Colors (if supported)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo %BLUE%================================%NC%
echo %BLUE%  %FRAMEWORK_NAME%%NC%
echo %BLUE%  Installation Script%NC%
echo %BLUE%================================%NC%
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo %YELLOW%[WARNING]%NC% Running as administrator. This is not recommended.
    echo %BLUE%[INFO]%NC% The script will prompt for elevation when needed.
    echo.
)

REM Step 1: Check Python installation
echo %GREEN%[STEP]%NC% Checking Python installation...

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[ERROR]%NC% Python not found. Please install Python %PYTHON_MIN_VERSION% or higher.
    echo %BLUE%[INFO]%NC% Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %BLUE%[INFO]%NC% Python %PYTHON_VERSION% found

REM Check Python version (simplified check)
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[ERROR]%NC% Python %PYTHON_VERSION% found, but %PYTHON_MIN_VERSION% or higher is required.
    pause
    exit /b 1
)

echo %BLUE%[INFO]%NC% Python version check passed

REM Step 2: Check pip installation
echo %GREEN%[STEP]%NC% Checking pip installation...

pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[ERROR]%NC% pip not found. Please install pip.
    pause
    exit /b 1
)

echo %BLUE%[INFO]%NC% pip found

REM Step 3: Check Git installation
echo %GREEN%[STEP]%NC% Checking Git installation...

git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %YELLOW%[WARNING]%NC% Git not found. Installing from GitHub may not work.
    echo %BLUE%[INFO]%NC% Download Git from: https://git-scm.com/download/win
    set "GIT_AVAILABLE=false"
) else (
    echo %BLUE%[INFO]%NC% Git found
    set "GIT_AVAILABLE=true"
)

REM Step 4: Check for Npcap
echo %GREEN%[STEP]%NC% Checking for Npcap installation...

if exist "C:\Windows\System32\Npcap\*" (
    echo %BLUE%[INFO]%NC% Npcap found
) else (
    echo %YELLOW%[WARNING]%NC% Npcap not found. Packet capture functionality may not work.
    echo %BLUE%[INFO]%NC% Download Npcap from: https://nmap.org/npcap/
    echo %BLUE%[INFO]%NC% Installation will continue, but some features may be limited.
)

REM Step 5: Create installation directory
echo %GREEN%[STEP]%NC% Creating installation directory...

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo %BLUE%[INFO]%NC% Created directory: %INSTALL_DIR%
) else (
    echo %BLUE%[INFO]%NC% Directory already exists: %INSTALL_DIR%
)

cd /d "%INSTALL_DIR%"

REM Step 6: Create virtual environment
echo %GREEN%[STEP]%NC% Creating virtual environment...

if exist "venv" (
    echo %BLUE%[INFO]%NC% Virtual environment already exists, updating...
) else (
    python -m venv venv
    echo %BLUE%[INFO]%NC% Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip setuptools wheel

REM Step 7: Download framework
echo %GREEN%[STEP]%NC% Downloading framework...

if "%GIT_AVAILABLE%"=="true" (
    if exist "advanced-ddos-framework" (
        echo %BLUE%[INFO]%NC% Framework directory exists, updating...
        cd advanced-ddos-framework
        git pull
        cd ..
    ) else (
        echo %BLUE%[INFO]%NC% Cloning framework repository...
        git clone %REPO_URL% advanced-ddos-framework
    )
) else (
    echo %YELLOW%[WARNING]%NC% Git not available. Please download the framework manually.
    echo %BLUE%[INFO]%NC% Download from: %REPO_URL%
    echo %BLUE%[INFO]%NC% Extract to: %INSTALL_DIR%\advanced-ddos-framework
    pause
    goto :install_framework
)

REM Step 8: Install framework
:install_framework
echo %GREEN%[STEP]%NC% Installing framework...

if not exist "advanced-ddos-framework" (
    echo %RED%[ERROR]%NC% Framework directory not found. Please download manually.
    pause
    exit /b 1
)

cd advanced-ddos-framework

REM Install framework
pip install -e .

if %errorLevel% neq 0 (
    echo %RED%[ERROR]%NC% Framework installation failed.
    pause
    exit /b 1
)

echo %BLUE%[INFO]%NC% Framework installed successfully

REM Step 9: Create launcher scripts
echo %GREEN%[STEP]%NC% Creating launcher scripts...

cd "%INSTALL_DIR%"

if not exist "bin" mkdir bin

REM Create main launcher
echo @echo off > bin\ddos-framework.bat
echo set "INSTALL_DIR=%INSTALL_DIR%" >> bin\ddos-framework.bat
echo call "%%INSTALL_DIR%%\venv\Scripts\activate.bat" >> bin\ddos-framework.bat
echo cd /d "%%INSTALL_DIR%%\advanced-ddos-framework" >> bin\ddos-framework.bat
echo python ddos.py %%* >> bin\ddos-framework.bat

REM Create CLI launcher
echo @echo off > bin\ddos-cli.bat
echo set "INSTALL_DIR=%INSTALL_DIR%" >> bin\ddos-cli.bat
echo call "%%INSTALL_DIR%%\venv\Scripts\activate.bat" >> bin\ddos-cli.bat
echo cd /d "%%INSTALL_DIR%%\advanced-ddos-framework" >> bin\ddos-cli.bat
echo python -m core.interfaces.cli %%* >> bin\ddos-cli.bat

REM Create web GUI launcher
echo @echo off > bin\ddos-web.bat
echo set "INSTALL_DIR=%INSTALL_DIR%" >> bin\ddos-web.bat
echo call "%%INSTALL_DIR%%\venv\Scripts\activate.bat" >> bin\ddos-web.bat
echo cd /d "%%INSTALL_DIR%%\advanced-ddos-framework" >> bin\ddos-web.bat
echo python -m core.interfaces.web_gui %%* >> bin\ddos-web.bat

REM Create API launcher
echo @echo off > bin\ddos-api.bat
echo set "INSTALL_DIR=%INSTALL_DIR%" >> bin\ddos-api.bat
echo call "%%INSTALL_DIR%%\venv\Scripts\activate.bat" >> bin\ddos-api.bat
echo cd /d "%%INSTALL_DIR%%\advanced-ddos-framework" >> bin\ddos-api.bat
echo python -m core.interfaces.api %%* >> bin\ddos-api.bat

echo %BLUE%[INFO]%NC% Launcher scripts created in %INSTALL_DIR%\bin\

REM Step 10: Add to PATH
echo %GREEN%[STEP]%NC% Setting up PATH...

REM Check if already in PATH
echo %PATH% | findstr /i "%INSTALL_DIR%\bin" >nul
if %errorLevel% neq 0 (
    echo %BLUE%[INFO]%NC% Adding to user PATH...
    
    REM Add to user PATH (requires setx)
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
    if not defined USER_PATH set "USER_PATH="
    
    REM Check if already in user PATH
    echo !USER_PATH! | findstr /i "%INSTALL_DIR%\bin" >nul
    if !errorLevel! neq 0 (
        if defined USER_PATH (
            setx PATH "!USER_PATH!;%INSTALL_DIR%\bin"
        ) else (
            setx PATH "%INSTALL_DIR%\bin"
        )
        echo %BLUE%[INFO]%NC% Added to user PATH. Please restart your command prompt.
    ) else (
        echo %BLUE%[INFO]%NC% Already in user PATH
    )
) else (
    echo %BLUE%[INFO]%NC% Already in current PATH
)

REM Step 11: Run basic tests
echo %GREEN%[STEP]%NC% Running basic tests...

cd "%INSTALL_DIR%\advanced-ddos-framework"
call "%INSTALL_DIR%\venv\Scripts\activate.bat"

REM Test framework import
python -c "import core; print('Framework import successful')" >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[ERROR]%NC% Framework import test failed
    goto :error_exit
) else (
    echo %GREEN%[SUCCESS]%NC% Framework import test passed
)

REM Test CLI
python ddos.py --help >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[ERROR]%NC% CLI test failed
    goto :error_exit
) else (
    echo %GREEN%[SUCCESS]%NC% CLI test passed
)

REM Step 12: Create desktop shortcuts (optional)
echo %GREEN%[STEP]%NC% Creating desktop shortcuts...

REM Create shortcut for CLI (requires PowerShell)
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\DDoS Framework CLI.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\bin\ddos-cli.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()}" >nul 2>&1

REM Create shortcut for Web GUI
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\DDoS Framework Web.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\bin\ddos-web.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()}" >nul 2>&1

echo %BLUE%[INFO]%NC% Desktop shortcuts created

REM Installation completed successfully
echo.
echo %GREEN%[SUCCESS]%NC% Installation completed successfully!
echo.
echo %BLUE%Next steps:%NC%
echo 1. Restart your command prompt to use the new PATH
echo 2. Test the installation: ddos-framework --help
echo 3. Start the web interface: ddos-web
echo 4. Read the documentation: %INSTALL_DIR%\advanced-ddos-framework\README.md
echo.
echo %YELLOW%Important:%NC%
echo - This framework is for educational and authorized testing only
echo - Always ensure you have permission before testing any systems
echo - Use only in controlled, isolated environments
echo.
echo %BLUE%Support:%NC%
echo - Documentation: https://ddos-framework.readthedocs.io/
echo - Issues: https://github.com/ddos-framework/advanced-ddos-framework/issues
echo - Email: support@ddos-framework.org
echo.

goto :end

:error_exit
echo.
echo %RED%[ERROR]%NC% Installation failed!
echo Please check the error messages above and try again.
echo.
echo %BLUE%Support:%NC%
echo - Issues: https://github.com/ddos-framework/advanced-ddos-framework/issues
echo - Email: support@ddos-framework.org
echo.
pause
exit /b 1

:end
pause