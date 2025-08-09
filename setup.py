#!/usr/bin/env python3
"""
TikTok Research System Setup Script
M3 Mac (Apple Silicon) 対応
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Python バージョンチェック"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11以上が必要です")
        print(f"現在のバージョン: {sys.version}")
        return False
    print(f"✅ Python バージョン: {sys.version}")
    return True

def check_platform():
    """プラットフォームチェック"""
    system = platform.system()
    machine = platform.machine()
    print(f"✅ プラットフォーム: {system} {machine}")
    
    if system == "Darwin" and machine == "arm64":
        print("✅ M3 Mac (Apple Silicon) 環境を検出")
        return True
    else:
        print(f"⚠️  想定環境: macOS arm64, 検出環境: {system} {machine}")
        return True  # 他の環境でも続行

def install_dependencies():
    """依存関係のインストール"""
    print("\n📦 依存関係をインストール中...")
    
    try:
        # pip のアップグレード
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip をアップグレードしました")
        
        # requirements.txt からインストール
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ 依存関係をインストールしました")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依存関係のインストールに失敗: {e}")
        return False

def create_config_files():
    """設定ファイルの作成"""
    print("\n⚙️  設定ファイルを作成中...")
    
    # .env ファイルの作成
    env_file = Path("config/.env")
    if not env_file.exists():
        env_content = """# TikTok Research System Configuration

# ScraperAPI Settings
SCRAPERAPI_KEY=your_scraperapi_key_here
SCRAPERAPI_BASE_URL=http://api.scraperapi.com

# TikTok Settings
TIKTOK_EXPLORE_URL=https://www.tiktok.com/explore
TARGET_COUNTRY=JP
MIN_VIEWS=500000
TIME_RANGE_HOURS=24

# System Settings
MAX_RETRIES=3
REQUEST_TIMEOUT=60
RATE_LIMIT_DELAY=2

# Data Storage
DATA_DIR=data
LOG_DIR=logs
DATABASE_FILE=data/tiktok_videos.db

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
"""
        env_file.write_text(env_content)
        print("✅ .env ファイルを作成しました")
    
    # config.yaml ファイルの作成
    config_file = Path("config/config.yaml")
    if not config_file.exists():
        config_content = """# TikTok Research System Configuration

scraper:
  api_key: ${SCRAPERAPI_KEY}
  base_url: ${SCRAPERAPI_BASE_URL}
  timeout: 60
  max_retries: 3
  rate_limit_delay: 2

tiktok:
  explore_url: ${TIKTOK_EXPLORE_URL}
  country_code: ${TARGET_COUNTRY}
  render_js: true
  device_type: desktop

filters:
  min_views: ${MIN_VIEWS}
  time_range_hours: ${TIME_RANGE_HOURS}
  exclude_duplicates: true

storage:
  database_file: ${DATABASE_FILE}
  data_dir: ${DATA_DIR}
  backup_enabled: true

monitoring:
  enabled: ${ENABLE_MONITORING}
  log_level: ${LOG_LEVEL}
  log_dir: ${LOG_DIR}
  alert_on_errors: true

scheduler:
  enabled: false
  interval_minutes: 60
  max_concurrent_jobs: 1
"""
        config_file.write_text(config_content)
        print("✅ config.yaml ファイルを作成しました")

def create_directories():
    """必要なディレクトリの作成"""
    print("\n📁 ディレクトリを作成中...")
    
    directories = [
        "data/raw",
        "data/processed", 
        "data/reports",
        "logs/scraper",
        "logs/system",
        "tests/unit",
        "tests/integration"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ ディレクトリを作成しました")

def create_gitignore():
    """gitignore ファイルの作成"""
    gitignore_content = """# TikTok Research System .gitignore

# Environment variables
.env
config/.env

# API Keys
**/api_keys.txt
**/secrets.json

# Data files
data/
logs/
*.db
*.sqlite

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
.pytest_cache/
htmlcov/

# Logs
*.log
"""
    
    Path(".gitignore").write_text(gitignore_content)
    print("✅ .gitignore ファイルを作成しました")

def main():
    """メイン実行関数"""
    print("🚀 TikTok Research System セットアップを開始します\n")
    
    # Python バージョンチェック
    if not check_python_version():
        sys.exit(1)
    
    # プラットフォームチェック
    check_platform()
    
    # 依存関係のインストール
    if not install_dependencies():
        sys.exit(1)
    
    # 設定ファイルの作成
    create_config_files()
    
    # ディレクトリの作成
    create_directories()
    
    # gitignore の作成
    create_gitignore()
    
    print("\n🎉 セットアップが完了しました!")
    print("\n📋 次のステップ:")
    print("1. config/.env ファイルでScraperAPI キーを設定")
    print("2. python src/main.py でシステムを実行")
    print("3. python -m pytest tests/ でテストを実行")
    
    print("\n⚠️  重要:")
    print("- ScraperAPI のアカウント作成とAPI キー取得が必要です")
    print("- 利用規約を確認し、法的リスクを理解してください")

if __name__ == "__main__":
    main()

