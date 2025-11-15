@echo off
chcp 65001 > nul
echo ========================================
echo Agent股票交易模拟系统 - 快速启动
echo ========================================
echo.

echo [0/4] 检查环境配置...
if not exist .env (
    echo ✗ 未找到.env文件
    echo.
    echo 请先配置环境变量：
    echo 1. 复制 .env.example 为 .env
    echo 2. 编辑 .env 文件，填入真实的API密钥
    echo.
    pause
    exit /b 1
)
echo ✓ .env文件存在
echo.

echo [1/4] 测试API连接...
python test_api.py
if errorlevel 1 (
    echo.
    echo ✗ API测试失败，请检查配置
    pause
    exit /b 1
)

echo.
echo [2/4] 测试数据库...
python test_data.py
if errorlevel 1 (
    echo.
    echo ✗ 数据库测试失败，请检查数据
    pause
    exit /b 1
)

echo.
echo [3/4] 安装依赖...
pip install python-dotenv -q
echo ✓ 依赖已安装
echo.

echo [4/4] 启动MVP模拟...
echo 提示: 完整模拟需要30-60分钟，可按Ctrl+C中断
echo.
pause

python run_mvp.py

echo.
echo ========================================
echo 模拟完成！查看results文件夹获取报告
echo ========================================
pause
