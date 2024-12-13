@echo off

REM Set cmd encoding to UTF-8
chcp 65001 >nul

REM Set Python interpreter path
set PYTHON_EXEC=runtime\python.exe

REM Check if the Python interpreter exists
if not exist %PYTHON_EXEC% (
    echo %PYTHON_EXEC% not found, please ensure the path is correct.
    pause
    exit /b
)

REM Install the browsers needed for Playwright
echo Installing the necessary browsers for Playwright...
%PYTHON_EXEC% -m playwright install

REM Check if Playwright installation was successful
if %errorlevel% neq 0 (
    echo Playwright installation failed, please check the error message.
    pause
    exit /b
)

echo Playwright installation complete!

REM Wait for the user to view the output
pause
