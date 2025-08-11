#!/usr/bin/env python3
"""
TikTok Scraper Debug Tool
取得されているデータの詳細を確認するためのデバッグツール
"""

import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper.scraperapi_client import ScraperAPIClient
from src.parser.tiktok_parser import TikTokParser
from src.utils.logger import setup_logging, get_logger

def debug_tiktok_scraping():
    """TikTokスクレイピングのデバッグ"""
    print("🔍 TikTok Scraper Debug Tool")
    print("=" * 50)
    
    # ログ設定
    setup_logging()
    logger = get_logger("DebugScraper")
    
    # ScraperAPIクライアントを初期化
    from src.utils.config import config
    api_key = config.get('scraper', {}).get('api_key')
    if not api_key:
        print("❌ APIキーが設定されていません")
        return
    
    api_client = ScraperAPIClient(api_key)
    parser = TikTokParser()
    
    try:
        print("📡 TikTok /exploreページにアクセス中...")
        
        # TikTok exploreページをスクレイピング
        url = "https://www.tiktok.com/explore"
        
        result = api_client.scrape(
            url=url,
            render_js=True,
            country_code='JP',
            device_type='desktop'
        )
        
        html_content = result['content']
        
        print(f"✅ HTMLコンテンツを取得 (サイズ: {len(html_content)} 文字)")
        
        # HTMLコンテンツをファイルに保存（デバッグ用）
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        
        with open(debug_dir / "tiktok_explore.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"💾 HTMLコンテンツを保存: {debug_dir / 'tiktok_explore.html'}")
        
        # HTMLを解析
        print("\n🔍 HTMLコンテンツの解析中...")
        videos = parser.parse_explore_page(html_content)
        
        print(f"📊 解析結果: {len(videos)}件の動画データを抽出")
        
        # 取得した動画データの詳細を表示
        if videos:
            print("\n📋 取得した動画データの詳細:")
            print("-" * 40)
            
            for i, video in enumerate(videos[:5], 1):  # 最初の5件を表示
                print(f"\n{i}. 動画ID: {video.video_id}")
                print(f"   URL: {video.url}")
                print(f"   タイトル: {video.title}")
                print(f"   再生数: {video.view_count}")
                print(f"   いいね数: {video.like_count}")
                print(f"   コメント数: {video.comment_count}")
                print(f"   投稿日時: {video.upload_date}")
                print(f"   作者: {video.author_username}")
                
            # 動画データをJSONで保存
            video_data = []
            for video in videos:
                video_dict = {
                    "video_id": video.video_id,
                    "url": video.url,
                    "title": video.title,
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "comment_count": video.comment_count,
                    "upload_date": video.upload_date.isoformat() if video.upload_date else None,
                    "author_username": video.author_username,
                    "author_verified": video.author_verified,
                    "collected_at": video.collected_at.isoformat() if video.collected_at else None
                }
                video_data.append(video_dict)
            
            with open(debug_dir / "extracted_videos.json", "w", encoding="utf-8") as f:
                json.dump(video_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 動画データを保存: {debug_dir / 'extracted_videos.json'}")
            
        else:
            print("❌ 動画データが取得できませんでした")
            
        # HTMLの構造を分析
        print("\n🔍 HTMLの構造分析:")
        print("-" * 40)
        
        # 基本的なHTML要素の確認
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # タイトル
        title = soup.find('title')
        print(f"ページタイトル: {title.text if title else 'なし'}")
        
        # メタ情報
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            print(f"説明: {meta_description.get('content', 'なし')}")
        
        # スクリプトタグの数
        scripts = soup.find_all('script')
        print(f"スクリプトタグ数: {len(scripts)}")
        
        # リンクの数
        links = soup.find_all('a')
        tiktok_links = [link for link in links if link.get('href') and 'tiktok.com' in link.get('href')]
        print(f"総リンク数: {len(links)}")
        print(f"TikTokリンク数: {len(tiktok_links)}")
        
        # 動画関連の要素
        video_elements = soup.find_all(['video', 'div'], class_=lambda x: x and 'video' in x.lower() if x else False)
        print(f"動画関連要素数: {len(video_elements)}")
        
        # JSON-LDデータの確認
        json_scripts = soup.find_all('script', type='application/ld+json')
        print(f"JSON-LDスクリプト数: {len(json_scripts)}")
        
        # JavaScript内のデータ確認
        js_data_scripts = [s for s in scripts if s.string and ('window.' in s.string or 'var ' in s.string)]
        print(f"データ含有JSスクリプト数: {len(js_data_scripts)}")
        
        print("\n📝 デバッグ情報の保存完了")
        print(f"📁 デバッグファイル: {debug_dir}/")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        api_client.close()

if __name__ == "__main__":
    debug_tiktok_scraping()

