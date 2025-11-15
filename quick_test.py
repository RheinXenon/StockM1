"""
快速测试脚本 - 验证环境和基本功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console

console = Console()


def test_imports():
    """测试依赖包导入"""
    console.print("\n[bold cyan]1. 测试依赖包导入...[/bold cyan]")
    
    try:
        import akshare
        console.print("  ✓ akshare 导入成功")
    except ImportError:
        console.print("  ✗ akshare 导入失败，请运行: pip install akshare")
        return False
    
    try:
        import pandas
        console.print("  ✓ pandas 导入成功")
    except ImportError:
        console.print("  ✗ pandas 导入失败")
        return False
    
    try:
        import click
        console.print("  ✓ click 导入成功")
    except ImportError:
        console.print("  ✗ click 导入失败")
        return False
    
    try:
        from rich import console as rich_console
        console.print("  ✓ rich 导入成功")
    except ImportError:
        console.print("  ✗ rich 导入失败")
        return False
    
    return True


def test_modules():
    """测试项目模块"""
    console.print("\n[bold cyan]2. 测试项目模块...[/bold cyan]")
    
    try:
        from src.stock_app.database import Database
        console.print("  ✓ database 模块导入成功")
        
        # 测试数据库初始化
        db = Database()
        db.close()
        console.print("  ✓ 数据库初始化成功")
    except Exception as e:
        console.print(f"  ✗ database 模块测试失败: {e}")
        return False
    
    try:
        from src.stock_app.data_downloader import DataDownloader
        console.print("  ✓ data_downloader 模块导入成功")
    except Exception as e:
        console.print(f"  ✗ data_downloader 模块测试失败: {e}")
        return False
    
    try:
        from src.stock_app.trading_engine import TradingEngine
        console.print("  ✓ trading_engine 模块导入成功")
    except Exception as e:
        console.print(f"  ✗ trading_engine 模块测试失败: {e}")
        return False
    
    try:
        from src.stock_app.portfolio import Portfolio
        console.print("  ✓ portfolio 模块导入成功")
    except Exception as e:
        console.print(f"  ✗ portfolio 模块测试失败: {e}")
        return False
    
    return True


def test_data_download():
    """测试数据下载（获取股票列表）"""
    console.print("\n[bold cyan]3. 测试数据获取...[/bold cyan]")
    
    try:
        from src.stock_app.data_downloader import DataDownloader
        
        downloader = DataDownloader()
        console.print("  正在获取股票列表...")
        
        stock_list = downloader.get_stock_list()
        
        if not stock_list.empty:
            console.print(f"  ✓ 成功获取 {len(stock_list)} 只股票信息")
            console.print(f"  示例: {stock_list.head(3).to_dict('records')}")
            return True
        else:
            console.print("  ✗ 股票列表为空")
            return False
            
    except Exception as e:
        console.print(f"  ✗ 数据获取失败: {e}")
        console.print("  提示: 这可能是网络问题，不影响系统使用")
        return False


def main():
    """主测试流程"""
    console.print("[bold green]开始测试A股模拟炒股系统...[/bold green]")
    
    # 测试依赖包
    if not test_imports():
        console.print("\n[bold red]依赖包测试失败！请安装缺失的依赖包。[/bold red]")
        console.print("运行命令: pip install -r requirements.txt")
        return
    
    # 测试项目模块
    if not test_modules():
        console.print("\n[bold red]项目模块测试失败！[/bold red]")
        return
    
    # 测试数据下载
    test_data_download()
    
    console.print("\n[bold green]测试完成！[/bold green]")
    console.print("\n[bold cyan]下一步操作：[/bold cyan]")
    console.print("1. 下载历史数据: python main.py download-indices")
    console.print("2. 下载股票数据: python main.py download-stocks --limit 10")
    console.print("3. 创建模拟账户: python main.py create-account 我的账户")
    console.print("4. 开始模拟交易: python main.py load-account 我的账户")
    console.print("\n更多信息请查看 README.md")


if __name__ == '__main__':
    main()
