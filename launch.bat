@echo off

REM Set cmd encoding to UTF-8
chcp 65001 >nul

REM Set Python interpreter path
set PYTHON_EXEC=runtime\python.exe

REM Get the first argument as the script path
set SCRIPT=%1

REM Check if the parameter is provided
if "%SCRIPT%"=="" (
    echo Please provide the script file as the first parameter.
    pause
    exit /b
)

REM Check if the Python interpreter exists
if not exist %PYTHON_EXEC% (
    echo %PYTHON_EXEC% not found, please ensure the path is correct.
    pause
    exit /b
)

REM Check if the script exists
if not exist %SCRIPT% (
    echo Script %SCRIPT% not found, please ensure the path is correct.
    pause
    exit /b
)

REM Execute the Python script
%PYTHON_EXEC% %SCRIPT%

REM Wait for user to view the output
pause
