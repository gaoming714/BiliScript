@echo off

REM 设置 cmd 编码为 UTF-8
chcp 65001 >nul

REM 设置Python解释器路径
set PYTHON_EXEC=runtime\python.exe

REM 检查Python解释器是否存在
if not exist %PYTHON_EXEC% (
    echo 未找到 %PYTHON_EXEC%，请确保路径正确。
    pause
    exit /b
)

REM 执行Playwright安装
echo 正在安装Playwright需要的浏览器...
%PYTHON_EXEC% -m playwright install

REM 检查Playwright是否安装成功
if %errorlevel% neq 0 (
    echo Playwright安装失败，请检查错误信息。
    pause
    exit /b
)

echo Playwright安装完成！

REM 等待用户查看输出
pause