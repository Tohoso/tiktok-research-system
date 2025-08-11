#!/usr/bin/env python3
"""
Enhanced TikTok Scraper Debug Tool
改良版TikTokスクレイピングデバッグツール

新機能:
- User-Agentローテーション
- プロキシローテーション  
- 人間らしいアクセスパターン
- 詳細な統計情報
"""

import sys
import os
import time
import random

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper.scraperapi_client import ScraperAPIClient
from src.parser.tiktok_parser import TikTokParser
from src.utils.logger import setup_logging, get_logger
from src.utils.config import config


def enhanced_debug_tiktok_scraping():
    """改良版TikTokスクレイピングデバッグ"""
    
    print("🚀 Enhanced TikTok Scraper Debug Tool")
    print("=" * 60)
    
    # ログ設定
    setup_logging()
    logger = get_logger("EnhancedDebugScraper")
    
    # ScraperAPIクライアントを初期化（改良版）
    from src.utils.config import config
    api_key = config.get('scraper', {}).get('api_key')
    if not api_key:
        print("❌ APIキーが設定されていません")
        return
    
    # 改良版クライアント設定
    api_client = ScraperAPIClient(
        api_key=api_key,
        enable_proxy_rotation=True,
        enable_request_throttling=True,
        device_type="tiktok"  # TikTok最適化User-Agent使用
    )
    parser = TikTokParser()
    
    try:
        print("📊 初期統計情報:")
        initial_stats = api_client.get_stats()
        print(f"  デバイスタイプ: {initial_stats['device_type']}")
        print(f"  User-Agent: {initial_stats['current_user_agent'][:80]}...")
        print()
        
        # 複数の戦略でテスト
        test_strategies = [
            {
                "name": "戦略1: TikTok最適化 + 日本プロキシ",
                "params": {
                    "device_type": "tiktok",
                    "country_code": "JP",
                    "render_js": True,
                    "premium": True,
                    "rotate_user_agent": True,
                    "use_proxy_rotation": True
                }
            },
            {
                "name": "戦略2: モバイル + シンガポールプロキシ",
                "params": {
                    "device_type": "mobile",
                    "country_code": "SG", 
                    "render_js": True,
                    "premium": True,
                    "rotate_user_agent": True,
                    "use_proxy_rotation": True
                }
            },
            {
                "name": "戦略3: デスクトップ + アメリカプロキシ",
                "params": {
                    "device_type": "desktop",
                    "country_code": "US",
                    "render_js": True,
                    "premium": True,
                    "rotate_user_agent": True,
                    "use_proxy_rotation": True
                }
            }
        ]
        
        results = []
        
        for i, strategy in enumerate(test_strategies, 1):
            print(f"🧪 {strategy['name']}")
            print("-" * 50)
            
            try:
                # TikTok exploreページをスクレイピング
                url = "https://www.tiktok.com/explore"
                
                print(f"📡 アクセス中: {url}")
                print(f"   パラメータ: {strategy['params']}")
                
                # リクエスト実行
                start_time = time.time()
                result = api_client.scrape(url=url, **strategy['params'])
                end_time = time.time()
                
                html_content = result['content']
                response_time = end_time - start_time
                
                print(f"✅ レスポンス受信 (時間: {response_time:.2f}秒)")
                print(f"   サイズ: {len(html_content)} 文字")
                print(f"   ステータス: {result.get('status_code', 'N/A')}")
                
                # HTMLコンテンツを保存
                debug_dir = "debug"
                os.makedirs(debug_dir, exist_ok=True)
                
                html_file = f"{debug_dir}/tiktok_explore_strategy_{i}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"💾 HTMLコンテンツを保存: {html_file}")
                
                # HTMLコンテンツの解析
                print("🔍 HTMLコンテンツの解析中...")
                videos = parser.parse_videos(html_content)
                
                print(f"📊 解析結果: {len(videos)}件の動画データを抽出")
                
                # 詳細分析
                analysis = analyze_html_content(html_content)
                print("🔍 HTML構造分析:")
                for key, value in analysis.items():
                    print(f"   {key}: {value}")
                
                # 結果を記録
                strategy_result = {
                    "strategy": strategy['name'],
                    "response_time": response_time,
                    "content_size": len(html_content),
                    "video_count": len(videos),
                    "status_code": result.get('status_code'),
                    "analysis": analysis,
                    "success": len(html_content) > 100 and "Page not available" not in html_content
                }
                results.append(strategy_result)
                
                # 成功した場合は詳細情報を表示
                if strategy_result["success"] and videos:
                    print("🎯 取得した動画の詳細:")
                    for j, video in enumerate(videos[:3], 1):  # 最初の3件のみ表示
                        print(f"   動画{j}:")
                        print(f"     ID: {video.video_id}")
                        print(f"     URL: {video.url}")
                        print(f"     再生数: {video.view_count}")
                        print(f"     投稿日時: {video.created_at}")
                
                print()
                
            except Exception as e:
                print(f"❌ エラーが発生: {e}")
                strategy_result = {
                    "strategy": strategy['name'],
                    "success": False,
                    "error": str(e)
                }
                results.append(strategy_result)
                print()
            
            # 戦略間の待機時間（人間らしいアクセス）
            if i < len(test_strategies):
                wait_time = random.uniform(10, 30)
                print(f"⏳ 次の戦略まで {wait_time:.1f}秒待機...")
                time.sleep(wait_time)
        
        # 最終統計情報
        print("📈 最終統計情報:")
        final_stats = api_client.get_stats()
        
        if "proxy_stats" in final_stats:
            proxy_stats = final_stats["proxy_stats"]
            print(f"  プロキシ統計:")
            print(f"    総プロキシ数: {proxy_stats.get('total_proxies', 0)}")
            print(f"    総リクエスト数: {proxy_stats.get('total_requests', 0)}")
            print(f"    成功率: {proxy_stats.get('overall_success_rate', 0):.2%}")
        
        if "throttle_stats" in final_stats:
            throttle_stats = final_stats["throttle_stats"]
            print(f"  リクエスト制御統計:")
            print(f"    総リクエスト数: {throttle_stats.get('total_requests', 0)}")
            print(f"    平均待機時間: {throttle_stats.get('average_wait_time', 0):.2f}秒")
            print(f"    時間制限内リクエスト: {throttle_stats.get('hourly_requests', 0)}/{throttle_stats.get('hourly_limit', 0)}")
        
        # 結果サマリー
        print("\n🎯 戦略別結果サマリー:")
        print("-" * 60)
        successful_strategies = [r for r in results if r.get("success", False)]
        
        if successful_strategies:
            print(f"✅ 成功した戦略: {len(successful_strategies)}/{len(results)}")
            
            best_strategy = max(successful_strategies, key=lambda x: x.get("video_count", 0))
            print(f"🏆 最も効果的な戦略: {best_strategy['strategy']}")
            print(f"   取得動画数: {best_strategy.get('video_count', 0)}件")
            print(f"   レスポンス時間: {best_strategy.get('response_time', 0):.2f}秒")
            
            # 推奨設定
            print("\n💡 推奨設定:")
            if best_strategy.get("video_count", 0) > 0:
                print("  ✅ この設定で実際の収集を実行することを推奨")
                print(f"  📋 設定: {best_strategy['strategy']}")
            else:
                print("  ⚠️  動画データの取得はできませんでしたが、アクセス自体は成功")
                print("  💭 TikTokの表示制限やJavaScript依存が原因の可能性")
        else:
            print("❌ すべての戦略が失敗しました")
            print("💡 考えられる原因:")
            print("   - TikTokのボット検出システム")
            print("   - 地域制限")
            print("   - APIキーの制限")
            print("   - ネットワーク接続の問題")
        
        # デバッグファイルの保存
        debug_summary_file = f"{debug_dir}/debug_summary.txt"
        with open(debug_summary_file, 'w', encoding='utf-8') as f:
            f.write("Enhanced TikTok Scraper Debug Summary\n")
            f.write("=" * 50 + "\n\n")
            
            for result in results:
                f.write(f"Strategy: {result['strategy']}\n")
                f.write(f"Success: {result.get('success', False)}\n")
                if result.get('success'):
                    f.write(f"Video Count: {result.get('video_count', 0)}\n")
                    f.write(f"Response Time: {result.get('response_time', 0):.2f}s\n")
                    f.write(f"Content Size: {result.get('content_size', 0)} chars\n")
                else:
                    f.write(f"Error: {result.get('error', 'Unknown')}\n")
                f.write("\n")
        
        print(f"📝 デバッグサマリーを保存: {debug_summary_file}")
        print(f"📁 デバッグファイル: {debug_dir}/")
        
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
        logger.error(f"Debug scraping failed: {e}", exc_info=True)
    
    finally:
        api_client.close()


def analyze_html_content(html_content: str) -> dict:
    """HTMLコンテンツの詳細分析"""
    from bs4 import BeautifulSoup
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        analysis = {
            "ページタイトル": soup.title.string if soup.title else "なし",
            "スクリプトタグ数": len(soup.find_all('script')),
            "総リンク数": len(soup.find_all('a')),
            "TikTokリンク数": len([a for a in soup.find_all('a', href=True) if 'tiktok.com' in a['href']]),
            "動画関連要素数": len(soup.find_all(['video', 'div'], class_=lambda x: x and 'video' in str(x).lower())),
            "JSON-LDスクリプト数": len(soup.find_all('script', type='application/ld+json')),
            "データ含有JSスクリプト数": len([s for s in soup.find_all('script') if s.string and ('window.' in s.string or 'data' in s.string.lower())]),
            "フォーム数": len(soup.find_all('form')),
            "画像数": len(soup.find_all('img')),
            "メタタグ数": len(soup.find_all('meta')),
        }
        
        # 特定のキーワードをチェック
        content_lower = html_content.lower()
        keywords = ['explore', 'fyp', 'for you', 'trending', 'video', 'tiktok']
        for keyword in keywords:
            analysis[f"'{keyword}'含有"] = keyword in content_lower
        
        return analysis
        
    except Exception as e:
        return {"エラー": str(e)}


if __name__ == "__main__":
    enhanced_debug_tiktok_scraping()

