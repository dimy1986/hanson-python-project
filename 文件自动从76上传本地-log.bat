@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ========== 获取昨天日期 ==========
for /f "tokens=* delims= " %%i in ('cscript //nologo "%~dp0getyesterday.vbs"') do set YESTERDAY=%%i

:: ========== 日志 ==========
set "LOG=%~dp0download_log.txt"
echo ============================== >> "%LOG%"
echo 开始时间：%date% %time% >> "%LOG%"
echo 目标日期：%YESTERDAY% >> "%LOG%"

:: ========== 配置 ==========
set "SERVER_IP=214.20.0.76"
set "SHARE_NAME=Users"
set "SUB_FOLDER=Administrator\guanzihao"
set "USERNAME=*****"
set "PASSWORD=****"
set "LOCAL_PATH=D:\BSN\CASH-HISTORY"
:: ===========================

echo 正在清理现有连接... >> "%LOG%"
net use * /delete /y >> "%LOG%" 2>&1
timeout /t 2 >nul

echo 正在连接共享 \\%SERVER_IP%\%SHARE_NAME%... >> "%LOG%"
net use Z: "\\%SERVER_IP%\%SHARE_NAME%" %PASSWORD% /user:%USERNAME% /persistent:no >> "%LOG%" 2>&1

if %errorlevel% neq 0 (
    echo 连接失败！ >> "%LOG%"
    echo 连接失败！
    pause
    exit /b
)

echo 连接成功！ >> "%LOG%"

:: ===== 昨天目录 =====
set "REMOTE_PATH=Z:\%SUB_FOLDER%\%YESTERDAY%"
set "LOCAL_TARGET=%LOCAL_PATH%\%YESTERDAY%"

:: 检查远程昨天目录
if not exist "%REMOTE_PATH%\" (
    echo 错误：找不到昨天目录 %REMOTE_PATH% >> "%LOG%"
    echo 错误：找不到昨天目录 %REMOTE_PATH%
    net use Z: /delete /y 2>nul
    pause
    exit /b
)

:: 创建本地昨天目录
if not exist "%LOCAL_TARGET%" mkdir "%LOCAL_TARGET%"

echo 正在复制 %REMOTE_PATH% 到 %LOCAL_TARGET%... >> "%LOG%"
xcopy "%REMOTE_PATH%\*" "%LOCAL_TARGET%\" /E /Y /I >> "%LOG%" 2>&1

if %errorlevel% equ 0 (
    echo 复制成功！ >> "%LOG%"
    echo 复制成功！
) else (
    echo 复制可能有问题，请检查 >> "%LOG%"
    echo 复制可能有问题，请检查
)

:: 断开连接
net use Z: /delete /y >> "%LOG%" 2>&1

echo 结束时间：%date% %time% >> "%LOG%"
echo 完成！ >> "%LOG%"
echo 完成！
pause