"""
测试下载页面功能的脚本
验证导入和基本功能是否正常
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有必要的导入"""
    print("测试导入模块...")
    
    try:
        from src.stock_app.data_downloader import DataDownloader
        print("✅ DataDownloader 导入成功")
    except Exception as e:
        print(f"❌ DataDownloader 导入失败: {e}")
        return False
    
    try:
        from src.stock_app.database import Database
        print("✅ Database 导入成功")
    except Exception as e:
        print(f"❌ Database 导入失败: {e}")
        return False
    
    try:
        import streamlit as st
        print("✅ Streamlit 导入成功")
    except Exception as e:
        print(f"❌ Streamlit 导入失败: {e}")
        return False
    
    try:
        from visualization import app
        print("✅ visualization.app 导入成功")
    except Exception as e:
        print(f"❌ visualization.app 导入失败: {e}")
        return False
    
    return True

def test_downloader():
    """测试下载器基本功能"""
    print("\n测试DataDownloader基本功能...")
    
    try:
        from src.stock_app.data_downloader import DataDownloader
        downloader = DataDownloader()
        print("✅ DataDownloader 初始化成功")
        
        # 测试获取股票列表（不实际下载）
        print("注意：实际使用时会调用外部API获取股票列表")
        return True
    except Exception as e:
        print(f"❌ DataDownloader 测试失败: {e}")
        return False

def test_database():
    """测试数据库基本功能"""
    print("\n测试Database基本功能...")
    
    try:
        from src.stock_app.database import Database
        db = Database()
        print("✅ Database 初始化成功")
        print(f"✅ 数据库路径: {db.db_path}")
        return True
    except Exception as e:
        print(f"❌ Database 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("股票下载功能测试")
    print("=" * 60)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 导入测试失败，请检查依赖")
        return
    
    # 测试下载器
    if not test_downloader():
        print("\n❌ 下载器测试失败")
        return
    
    # 测试数据库
    if not test_database():
        print("\n❌ 数据库测试失败")
        return
    
    print("\n" + "=" * 60)
    print("✅ 所有基本测试通过！")
    print("=" * 60)
    print("\n使用方法:")
    print("1. 运行: python run_visualization.py")
    print("2. 在浏览器中访问: http://localhost:8501")
    print("3. 选择导航菜单中的 '⬇️ 下载股票数据'")
    print("\n详细使用说明请查看: visualization/DOWNLOAD_GUIDE.md")

if __name__ == "__main__":
    main()
