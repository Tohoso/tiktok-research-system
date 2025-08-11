#!/usr/bin/env python3
"""
Demo data generator for TikTok Research System
APIキーなしでもシステムの動作確認ができるデモデータを生成
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# デモ用の動画データを生成
def generate_demo_videos(count=50):
    """デモ用の動画データを生成"""
    demo_videos = []
    
    # 日本のトレンドハッシュタグ例
    hashtags = [
        "#おすすめ", "#fyp", "#viral", "#japan", "#tokyo", "#trending",
        "#dance", "#music", "#funny", "#cute", "#food", "#travel",
        "#fashion", "#beauty", "#lifestyle", "#comedy", "#art", "#anime"
    ]
    
    # ユーザー名例
    usernames = [
        "tiktok_user_jp", "viral_creator", "trend_master", "japan_tiktoker",
        "creative_soul", "dance_queen", "music_lover", "funny_guy",
        "cute_content", "food_blogger", "travel_vlogger", "fashion_icon"
    ]
    
    for i in range(count):
        # ランダムな再生数（10万〜500万）
        view_count = random.randint(100000, 5000000)
        
        # 24時間以内のランダムな投稿時間
        hours_ago = random.randint(1, 24)
        upload_time = datetime.now() - timedelta(hours=hours_ago)
        
        # エンゲージメント率を再生数に基づいて計算
        engagement_rate = random.uniform(0.02, 0.15)  # 2-15%
        like_count = int(view_count * engagement_rate)
        comment_count = int(like_count * random.uniform(0.05, 0.2))
        share_count = int(like_count * random.uniform(0.1, 0.3))
        
        video = {
            "video_id": f"demo_{i+1:03d}",
            "url": f"https://tiktok.com/@{random.choice(usernames)}/video/demo_{i+1:03d}",
            "title": f"トレンド動画 #{i+1} {random.choice(hashtags)}",
            "description": f"日本で人気のトレンド動画です！ {random.choice(hashtags)} {random.choice(hashtags)}",
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "upload_date": upload_time.isoformat(),
            "author_username": random.choice(usernames),
            "author_display_name": f"TikToker {i+1}",
            "author_verified": random.choice([True, False]),
            "author_follower_count": random.randint(1000, 1000000),
            "duration": random.randint(15, 60),  # 15-60秒
            "hashtags": random.sample(hashtags, random.randint(2, 5)),
            "region": "JP",
            "language": "ja",
            "collected_at": datetime.now().isoformat(),
            "trending_score": random.uniform(0.5, 1.0)
        }
        
        demo_videos.append(video)
    
    return demo_videos

def save_demo_data():
    """デモデータをJSONファイルに保存"""
    # 50万再生以上の動画を25件生成
    trending_videos = []
    for i in range(25):
        view_count = random.randint(500000, 5000000)  # 50万〜500万再生
        hours_ago = random.randint(1, 24)
        upload_time = datetime.now() - timedelta(hours=hours_ago)
        
        engagement_rate = random.uniform(0.05, 0.2)  # 高エンゲージメント
        like_count = int(view_count * engagement_rate)
        comment_count = int(like_count * random.uniform(0.1, 0.3))
        
        video = {
            "video_id": f"trending_{i+1:03d}",
            "url": f"https://tiktok.com/@viral_creator_{i+1}/video/trending_{i+1:03d}",
            "title": f"🔥 バイラル動画 #{i+1} - {view_count:,}回再生",
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "upload_date": upload_time.isoformat(),
            "author_username": f"viral_creator_{i+1}",
            "author_verified": True,
            "region": "JP",
            "collected_at": datetime.now().isoformat()
        }
        trending_videos.append(video)
    
    # デモデータを保存
    demo_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_videos": len(trending_videos),
            "criteria": {
                "min_views": 500000,
                "region": "JP",
                "time_range": "24h"
            }
        },
        "videos": trending_videos
    }
    
    # データディレクトリを作成
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # JSONファイルに保存
    with open(data_dir / "demo_trending_videos.json", "w", encoding="utf-8") as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ デモデータを生成しました: {len(trending_videos)}件の動画")
    print(f"📁 保存場所: {data_dir / 'demo_trending_videos.json'}")
    
    # 統計情報を表示
    total_views = sum(v["view_count"] for v in trending_videos)
    avg_views = total_views // len(trending_videos)
    max_views = max(v["view_count"] for v in trending_videos)
    min_views = min(v["view_count"] for v in trending_videos)
    
    print(f"\n📊 統計情報:")
    print(f"   総再生数: {total_views:,}")
    print(f"   平均再生数: {avg_views:,}")
    print(f"   最高再生数: {max_views:,}")
    print(f"   最低再生数: {min_views:,}")
    
    return demo_data

if __name__ == "__main__":
    print("🎬 TikTok Research System - デモデータ生成")
    print("=" * 50)
    
    demo_data = save_demo_data()
    
    print(f"\n🚀 デモモードでシステムを実行するには:")
    print(f"   python demo_mode.py")

