"""
A股模拟炒股系统 - 主程序入口
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.stock_app.cli import cli


if __name__ == '__main__':
    cli()
