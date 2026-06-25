@echo off
setlocal enabledelayedexpansion

REM Change directory to the project root (parent of the 'packaging' folder)
cd /d "%~dp0\.."

echo ========================================
echo PCD Visualizer Distribution Build Process
echo Building GUI Application
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Extract application metadata from config.py
for /f "tokens=*" %%i in ('python -c "import sys; sys.path.insert(0, '.'); import config; print(config.APP_NAME)"') do set APP_NAME=%%i
for /f "tokens=*" %%i in ('python -c "import sys; sys.path.insert(0, '.'); import config; print(config.APP_VERSION)"') do set APP_VERSION=%%i
for /f "tokens=*" %%i in ('python -c "import sys; sys.path.insert(0, '.'); import config; print(config.ORGANIZATION_NAME)"') do set ORGANIZATION_NAME=%%i
for /f "tokens=*" %%i in ('python -c "import sys; sys.path.insert(0, '.'); import config; print(config.EXECUTABLE_NAME)"') do set EXECUTABLE_NAME=%%i
for /f "tokens=*" %%i in ('python -c "import sys; sys.path.insert(0, '.'); import config; print(config.INSTALLER_BASENAME)"') do set INSTALLER_BASENAME=%%i
echo Detected APP_NAME: %APP_NAME%
echo Detected APP_VERSION: %APP_VERSION%
echo Detected ORGANIZATION_NAME: %ORGANIZATION_NAME%
echo Detected EXECUTABLE_NAME: %EXECUTABLE_NAME%
echo Detected INSTALLER_BASENAME: %INSTALLER_BASENAME%

REM Install/update dependencies from the new requirements file
echo Installing dependencies for PCD Visualizer...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo Installing PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller!
    pause
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist\%EXECUTABLE_NAME%.exe del /q dist\%EXECUTABLE_NAME%.exe
if exist dist\%INSTALLER_BASENAME%_v%APP_VERSION%.exe del /q dist\%INSTALLER_BASENAME%_v%APP_VERSION%.exe

REM Check entry point
echo Checking entry point...
if not exist pcd_visualizer.py (
    echo ERROR: pcd_visualizer.py not found!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Building %EXECUTABLE_NAME% executable...
echo ========================================
pyinstaller packaging/visualizer.spec

REM Check if executable was created
if not exist "dist\%EXECUTABLE_NAME%.exe" (
    echo.
    echo ERROR: Executable build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)

REM Get file size
for %%A in ("dist\%EXECUTABLE_NAME%.exe") do set exe_size=%%~zA
set /a exe_size_mb=!exe_size!/1024/1024

echo.
echo ========================================
echo Executable built successfully!
echo Location: dist\%EXECUTABLE_NAME%.exe
echo Size: !exe_size_mb! MB
echo ========================================

REM Build installer if Inno Setup is available
echo.
echo ========================================
echo Building installer...
echo ========================================

REM Check if Inno Setup is installed
set "INNO_PATH="
for %%i in ("C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "C:\Program Files\Inno Setup 6\ISCC.exe") do (
    if exist "%%i" set "INNO_PATH=%%~i"
)

if defined INNO_PATH (
    echo Found Inno Setup at: "!INNO_PATH!"
    if exist packaging/visualizer_installer.iss (
        "!INNO_PATH!" /DAppName="!APP_NAME!" /DAppVersion="!APP_VERSION!" /DAppPublisher="!ORGANIZATION_NAME!" /DExecutableName="!EXECUTABLE_NAME!" /DInstallerBaseName="!INSTALLER_BASENAME!" "packaging/visualizer_installer.iss"
        
        if exist "dist\!INSTALLER_BASENAME!_v!APP_VERSION!.exe" (
            for %%A in ("dist\!INSTALLER_BASENAME!_v!APP_VERSION!.exe") do set installer_size=%%~zA
            set /a installer_size_mb=!installer_size!/1024/1024
            
            echo.
            echo ========================================
            echo Installer created successfully!
            echo Location: dist\!INSTALLER_BASENAME!_v!APP_VERSION!.exe
            echo Size: !installer_size_mb! MB
            echo ========================================
        ) else (
            echo ERROR: Installer creation failed!
        )
    ) else (
        echo visualizer_installer.iss not found. Skipping installer creation.
    )
) else (
    echo Inno Setup not found. Skipping installer creation.
)

echo.
echo ========================================
echo Build process completed!
echo ========================================
echo.
pause