@echo off
REM TVB Test Runner (Windows)
setlocal

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

echo ================================================
echo  TVB Unit Tests
echo ================================================
echo.

set "PYTHONPATH=%CD%\python;%PYTHONPATH%"

python -m unittest discover tests/ -v

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% equ 0 (
    echo [OK] All tests passed
) else (
    echo [FAIL] Some tests failed
)

exit /b %EXIT_CODE%
