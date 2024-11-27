@echo off

REM 设置 cmd 编码为 UTF-8
chcp 65001 >nul

REM 设置Python解释器路径
set PYTHON_EXEC=runtime\python.exe

REM 获取传入的第一个参数作为脚本路径
set SCRIPT=%1

REM 检查是否传入参数
if "%SCRIPT%"=="" (
    echo 请提供脚本文件作为第一个参数。
    pause
    exit /b
)

REM 检查Python解释器是否存在
if not exist %PYTHON_EXEC% (
    echo 未找到 %PYTHON_EXEC%，请确保路径正确。
    pause
    exit /b
)

REM 检查脚本是否存在
if not exist %SCRIPT% (
    echo 未找到脚本 %SCRIPT%，请确保路径正确。
    pause
    exit /b
)

REM 执行Python脚本
%PYTHON_EXEC% %SCRIPT%

REM 等待用户查看输出
pause