@echo off
REM ===========================================================================
REM  Alavette Form V1.0 - Windows GUI release builder
REM  ---------------------------------------------------------------------------
REM  Produces a distributable onedir GUI bundle for Windows 10/11 under
REM  dist\Alavette-Form\.  The bundle is launched by Alavette-Form.exe.
REM
REM  Usage:
REM     build_release.bat            Build the GUI release
REM     build_release.bat clean      Remove build/ and dist/ before building
REM     build_release.bat probe      After building, run the package probe
REM                                  (--internal-package-import-probe) to
REM                                  verify frozen-only imports load cleanly.
REM
REM  Prerequisites:
REM     * Windows 10 or Windows 11
REM     * Python 3.10 - 3.12 x64 (https://www.python.org/downloads/windows/)
REM     * Project dependencies from requirements.txt installed
REM       (install_env.bat handles this in a fresh venv)
REM ===========================================================================

setlocal enableextensions
set "PROJ_ROOT=%~dp0"
set "PROJ_ROOT=%PROJ_ROOT:~0,-1%"
cd /d "%PROJ_ROOT%"

set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=build"

REM --- Locate Python ---------------------------------------------------------
where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
    ) else (
        echo [ERROR] Neither py nor python is on PATH.
        echo         Install Python 3.10-3.12 from https://www.python.org/downloads/windows/
        exit /b 1
    )
)

REM --- Activate the local venv if present (matches install_env.bat layout) ---
if exist "%PROJ_ROOT%\.venv\Scripts\activate.bat" (
    call "%PROJ_ROOT%\.venv\Scripts\activate.bat"
    set "PYTHON_CMD=python"
)

echo [build] Using interpreter:
%PYTHON_CMD% --version

REM --- Ensure build dependencies are present --------------------------------
%PYTHON_CMD% -m pip install --upgrade pip >nul
%PYTHON_CMD% -m pip install "pyinstaller>=6.19.0" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.  Run install_env.bat first or
    echo         install requirements.txt in this environment.
    exit /b 1
)

REM --- Optional clean pass ---------------------------------------------------
if /i "%ACTION%"=="clean" (
    echo [build] Cleaning previous build artifacts ...
    if exist "%PROJ_ROOT%\build" rmdir /s /q "%PROJ_ROOT%\build"
    if exist "%PROJ_ROOT%\dist" rmdir /s /q "%PROJ_ROOT%\dist"
    set "ACTION=build"
)

if /i not "%ACTION%"=="build" if /i not "%ACTION%"=="probe" (
    echo [ERROR] Unknown action: %ACTION%
    echo         Valid actions: ^(empty^), clean, probe
    exit /b 1
)

REM --- Run PyInstaller -------------------------------------------------------
echo [build] Running PyInstaller with Alavette-Form_V1.0.spec ...
%PYTHON_CMD% -m PyInstaller --noconfirm --clean --log-level WARN ^
    "%PROJ_ROOT%\Alavette-Form_V1.0.spec"
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed.  Re-run without --log-level WARN for details.
    exit /b 1
)

set "DIST_DIR=%PROJ_ROOT%\dist\Alavette-Form"
if not exist "%DIST_DIR%\Alavette-Form.exe" (
    echo [ERROR] Build completed but %DIST_DIR%\Alavette-Form.exe is missing.
    exit /b 1
)

echo.
echo [build] Release bundle created at:
echo         %DIST_DIR%
echo         Launch with Alavette-Form.exe

REM --- Optional frozen-import probe ----------------------------------------
if /i "%ACTION%"=="probe" (
    echo.
    echo [build] Running frozen package import probe ...
    "%DIST_DIR%\Alavette-Form.exe" --internal-package-import-probe
    if %errorlevel% neq 0 (
        echo [ERROR] Frozen package probe failed.  See the bundle log for details.
        exit /b 1
    )
    echo [build] Frozen package probe succeeded.
)

endlocal
exit /b 0
