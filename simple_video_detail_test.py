#!/usr/bin/env python3
"""
Simple Video Detail Test for TikTok Research System
既存のScraperAPIClientを使用したシンプルなテスト
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scraper.scraperapi_client import ScraperAPIClient
from src.utils.logger import get_logger


def test_simple_video_detail():
    """シンプルな動画詳細取得テスト"""
    logger = get_logger("SimpleVideoDetailTest")
    
    # APIキーを取得
    api_key = os.getenv('SCRAPERAPI_KEY')
    if not api_key:
        print("❌ SCRAPERAPI_KEY環境変数が設定されていません")
        return
    
    # テスト用動画URL
    test_url = "https://www.tiktok.com/@_quietlydope/video/7535094688726945079"
    
    logger.info("シンプルな動画詳細取得テストを開始")
    
    try:
        # ScraperAPIClientを初期化
        client = ScraperAPIClient(api_key)
        
        logger.info(f"テスト対象URL: {test_url}")
        
        # 基本的なスクレイピング（JavaScript実行なし）
        print("\n=== 基本スクレイピング（JavaScript実行なし） ===")
        response = client.scrape(
            url=test_url,
            render_js=False,
            country_code='JP',
            premium=True
        )
        
        if response and response.get('status_code') == 200:
            content = response.get('content', '')
            print(f"✅ 基本スクレイピング成功")
            print(f"コンテンツサイズ: {len(content):,}文字")
            
            # HTMLファイルに保存
            os.makedirs('debug', exist_ok=True)
            with open('debug/simple_basic_content.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("HTMLを保存: debug/simple_basic_content.html")
            
            # 基本的な情報抽出
            basic_info = extract_basic_info(content)
            print(f"基本情報: {basic_info}")
        else:
            print(f"❌ 基本スクレイピング失敗: {response}")
        
        time.sleep(5)  # 待機
        
        # JavaScript実行ありのスクレイピング
        print("\n=== JavaScript実行ありスクレイピング ===")
        response_js = client.scrape(
            url=test_url,
            render_js=True,
            country_code='JP',
            premium=True
        )
        
        if response_js and response_js.get('status_code') == 200:
            content_js = response_js.get('content', '')
            print(f"✅ JavaScript実行スクレイピング成功")
            print(f"コンテンツサイズ: {len(content_js):,}文字")
            
            # HTMLファイルに保存
            with open('debug/simple_js_content.html', 'w', encoding='utf-8') as f:
                f.write(content_js)
            print("HTMLを保存: debug/simple_js_content.html")
            
            # 詳細情報抽出
            detailed_info = extract_detailed_info(content_js)
            print(f"詳細情報: {detailed_info}")
            
            # JSONファイルに保存
            with open('debug/simple_extracted_info.json', 'w', encoding='utf-8') as f:
                json.dump(detailed_info, f, ensure_ascii=False, indent=2)
            print("詳細情報を保存: debug/simple_extracted_info.json")
        else:
            print(f"❌ JavaScript実行スクレイピング失敗: {response_js}")
        
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")
        print(f"❌ テスト実行エラー: {e}")


def extract_basic_info(html_content: str) -> dict:
    """基本情報を抽出"""
    import re
    
    info = {}
    
    try:
        # タイトル抽出
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            info['title'] = title_match.group(1).strip()
        
        # メタタグから情報抽出
        og_title = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if og_title:
            info['og_title'] = og_title.group(1)
        
        og_description = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if og_description:
            info['og_description'] = og_description.group(1)
        
        # 動画ID抽出
        video_id_match = re.search(r'/video/(\d+)', html_content)
        if video_id_match:
            info['video_id'] = video_id_match.group(1)
        
        # 基本的な統計情報パターン
        like_pattern = re.search(r'(\d+(?:\.\d+)?[KMB]?)\s*(?:likes?|いいね)', html_content, re.IGNORECASE)
        if like_pattern:
            info['like_count_text'] = like_pattern.group(1)
        
        view_pattern = re.search(r'(\d+(?:\.\d+)?[KMB]?)\s*(?:views?|再生)', html_content, re.IGNORECASE)
        if view_pattern:
            info['view_count_text'] = view_pattern.group(1)
        
    except Exception as e:
        info['extraction_error'] = str(e)
    
    return info


def extract_detailed_info(html_content: str) -> dict:
    """詳細情報を抽出"""
    import re
    import json
    
    info = {}
    
    try:
        # SIGI_STATE抽出
        sigi_pattern = r'window\[\'SIGI_STATE\'\]\s*=\s*({.+?});'
        sigi_match = re.search(sigi_pattern, html_content, re.DOTALL)
        
        if sigi_match:
            try:
                sigi_data = json.loads(sigi_match.group(1))
                info['sigi_state_found'] = True
                info['sigi_keys'] = list(sigi_data.keys()) if isinstance(sigi_data, dict) else []
                
                # ItemModuleから情報抽出
                if 'ItemModule' in sigi_data:
                    item_module = sigi_data['ItemModule']
                    info['item_module_keys'] = list(item_module.keys()) if isinstance(item_module, dict) else []
                    
                    # 最初の動画データを取得
                    for video_id, video_data in item_module.items():
                        if isinstance(video_data, dict):
                            info['video_data'] = {
                                'desc': video_data.get('desc'),
                                'createTime': video_data.get('createTime'),
                                'stats': video_data.get('stats'),
                                'author': video_data.get('author', {}).get('uniqueId') if video_data.get('author') else None
                            }
                            break
                
                # UserModuleから情報抽出
                if 'UserModule' in sigi_data:
                    user_module = sigi_data['UserModule']
                    if 'users' in user_module:
                        info['user_module_found'] = True
                        info['user_count'] = len(user_module['users'])
            
            except json.JSONDecodeError as e:
                info['sigi_parse_error'] = str(e)
        else:
            info['sigi_state_found'] = False
        
        # Universal Data抽出
        universal_pattern = r'window\[\'__UNIVERSAL_DATA_FOR_REHYDRATION__\'\]\s*=\s*({.+?});'
        universal_match = re.search(universal_pattern, html_content, re.DOTALL)
        
        if universal_match:
            try:
                universal_data = json.loads(universal_match.group(1))
                info['universal_data_found'] = True
                info['universal_keys'] = list(universal_data.keys()) if isinstance(universal_data, dict) else []
            except json.JSONDecodeError as e:
                info['universal_parse_error'] = str(e)
        else:
            info['universal_data_found'] = False
        
        # JSON-LD抽出
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>([^<]+)</script>'
        json_ld_matches = re.findall(json_ld_pattern, html_content, re.IGNORECASE)
        
        if json_ld_matches:
            info['json_ld_found'] = True
            info['json_ld_count'] = len(json_ld_matches)
            
            for i, json_ld_content in enumerate(json_ld_matches):
                try:
                    json_ld_data = json.loads(json_ld_content)
                    if isinstance(json_ld_data, dict) and json_ld_data.get('@type') == 'VideoObject':
                        info['json_ld_video_object'] = {
                            'name': json_ld_data.get('name'),
                            'description': json_ld_data.get('description'),
                            'uploadDate': json_ld_data.get('uploadDate'),
                            'interactionStatistic': json_ld_data.get('interactionStatistic')
                        }
                        break
                except json.JSONDecodeError:
                    continue
        else:
            info['json_ld_found'] = False
        
        # 基本情報も含める
        basic_info = extract_basic_info(html_content)
        info.update(basic_info)
        
    except Exception as e:
        info['detailed_extraction_error'] = str(e)
    
    return info


if __name__ == "__main__":
    test_simple_video_detail()

