#!/usr/bin/env python3
"""
TikTok Research System - Demo Mode
APIキーなしでもシステムの動作確認ができるデモモード
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.database import DatabaseManager
from src.filter.video_filter import VideoFilter
from src.parser.video_data import VideoData
from src.utils.logger import setup_logging, get_logger

def load_demo_data():
    """デモデータを読み込み"""
    demo_file = Path("data/demo_trending_videos.json")
    
    if not demo_file.exists():
        print("❌ デモデータが見つかりません。先にデモデータを生成してください。")
        print("   python demo_data_generator.py")
        return None
    
    with open(demo_file, "r", encoding="utf-8") as f:
        return json.load(f)

def convert_to_video_data(video_dict):
    """辞書データをVideoDataオブジェクトに変換"""
    return VideoData(
        video_id=video_dict["video_id"],
        url=video_dict["url"],
        title=video_dict["title"],
        view_count=video_dict["view_count"],
        like_count=video_dict.get("like_count", 0),
        comment_count=video_dict.get("comment_count", 0),
        upload_date=datetime.fromisoformat(video_dict["upload_date"]),
        author_username=video_dict["author_username"],
        author_verified=video_dict.get("author_verified", False),
        collected_at=datetime.fromisoformat(video_dict["collected_at"])
    )

def demo_video_collection():
    """デモモードでの動画収集シミュレーション"""
    print("🎬 TikTok Research System - デモモード")
    print("=" * 60)
    
    # ログ設定
    setup_logging()
    logger = get_logger("DemoMode")
    
    # デモデータを読み込み
    print("📂 デモデータを読み込み中...")
    demo_data = load_demo_data()
    if not demo_data:
        return
    
    # システムコンポーネントを初期化
    print("🔧 システムコンポーネントを初期化中...")
    db = DatabaseManager(":memory:")  # メモリ内データベース
    video_filter = VideoFilter()
    
    # デモ動画データを変換
    print("🔄 動画データを変換中...")
    videos = [convert_to_video_data(v) for v in demo_data["videos"]]
    
    print(f"✅ {len(videos)}件の動画データを読み込みました")
    print()
    
    # フィルタリングのデモ
    print("🔍 フィルタリング実行中...")
    print("-" * 40)
    
    # 1. 50万再生以上フィルタ
    high_view_videos = video_filter.filter_by_views(videos, min_views=500000)
    print(f"📊 50万再生以上: {len(high_view_videos)}件")
    
    # 2. 24時間以内フィルタ
    recent_videos = video_filter.filter_by_date(
        high_view_videos, 
        start_date=datetime.now() - timedelta(hours=24)
    )
    print(f"⏰ 24時間以内: {len(recent_videos)}件")
    
    # 3. トレンドフィルタ適用
    trending_videos = video_filter.apply_trending_filter(
        videos,
        min_views=500000,
        hours_ago=24
    )
    print(f"🔥 トレンド動画: {len(trending_videos)}件")
    print()
    
    # データベース保存のデモ
    print("💾 データベース保存中...")
    for video in trending_videos:
        db.save_video(video)
    
    # 統計情報を表示
    stats = db.get_statistics()
    print("📈 データベース統計:")
    print(f"   総動画数: {stats['total_videos']}件")
    print(f"   平均再生数: {stats['avg_views']:,.0f}")
    print(f"   最高再生数: {stats['max_views']:,}")
    print()
    
    # トップ動画を表示
    print("🏆 トップ5動画:")
    print("-" * 40)
    top_videos = sorted(trending_videos, key=lambda x: x.view_count, reverse=True)[:5]
    
    for i, video in enumerate(top_videos, 1):
        hours_ago = (datetime.now() - video.upload_date).total_seconds() / 3600
        print(f"{i}. {video.title}")
        print(f"   👀 {video.view_count:,}回再生 | ❤️ {video.like_count:,} | ⏰ {hours_ago:.1f}時間前")
        print(f"   👤 @{video.author_username}")
        print()
    
    # 検索デモ
    print("🔍 検索機能デモ:")
    print("-" * 40)
    search_results = db.search_videos(min_views=1000000)  # 100万再生以上
    print(f"100万再生以上の動画: {len(search_results)}件")
    
    if search_results:
        mega_viral = search_results[0]
        print(f"最高再生数動画: {mega_viral.title}")
        print(f"再生数: {mega_viral.view_count:,}")
    
    print()
    print("✅ デモモード実行完了！")
    print("🚀 実際のAPIキーを設定すれば、リアルタイムでTikTokデータを収集できます。")

def demo_system_monitoring():
    """システム監視のデモ"""
    print("\n🖥️  システム監視デモ:")
    print("-" * 40)
    
    from src.monitor.system_monitor import SystemMonitor
    
    monitor = SystemMonitor()
    system_stats = monitor.get_system_stats()
    
    print(f"CPU使用率: {system_stats['cpu_percent']:.1f}%")
    print(f"メモリ使用率: {system_stats['memory_percent']:.1f}%")
    print(f"ディスク使用率: {system_stats['disk_percent']:.1f}%")

if __name__ == "__main__":
    try:
        demo_video_collection()
        demo_system_monitoring()
    except KeyboardInterrupt:
        print("\n\n⏹️  デモモードを中断しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

