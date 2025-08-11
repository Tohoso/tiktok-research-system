#!/usr/bin/env python3
"""
既存の成功データを詳細分析するスクリプト
"""

import sys
import os
import json
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.logger import get_logger

def analyze_existing_html_data():
    """既存のHTMLデータを詳細分析"""
    logger = get_logger("AnalyzeExistingData")
    
    logger.info("="*60)
    logger.info("既存データの詳細分析開始")
    logger.info("="*60)
    
    # 既存のHTMLファイルを分析
    html_files = [
        "debug/tiktok_explore_strategy_1.html",
        "debug/tiktok_explore_strategy_2.html", 
        "debug/tiktok_explore_strategy_3.html"
    ]
    
    all_videos = []
    
    for i, html_file in enumerate(html_files, 1):
        if not os.path.exists(html_file):
            logger.warning(f"ファイルが見つかりません: {html_file}")
            continue
            
        logger.info(f"\n--- 戦略{i}のHTMLファイル分析: {html_file} ---")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            logger.info(f"ファイルサイズ: {len(html_content)} 文字")
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 詳細分析
            videos = analyze_html_content(soup, f"戦略{i}", logger)
            all_videos.extend(videos)
            
        except Exception as e:
            logger.error(f"ファイル分析エラー {html_file}: {e}")
    
    # 全体統計
    logger.info(f"\n{'='*60}")
    logger.info(f"全体統計")
    logger.info(f"{'='*60}")
    logger.info(f"総動画数: {len(all_videos)}")
    
    # 抽出方法別統計
    extraction_methods = {}
    for video in all_videos:
        method = video.get('extraction_method', 'unknown')
        extraction_methods[method] = extraction_methods.get(method, 0) + 1
    
    logger.info("抽出方法別統計:")
    for method, count in extraction_methods.items():
        logger.info(f"  {method}: {count}件")
    
    # 有効な動画ID（数値）の統計
    valid_video_ids = [v for v in all_videos if v.get('video_id', '').isdigit()]
    logger.info(f"有効な動画ID（数値）: {len(valid_video_ids)}件")
    
    # 結果を保存
    output_file = "debug/existing_data_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_videos': len(all_videos),
            'valid_video_ids': len(valid_video_ids),
            'extraction_methods': extraction_methods,
            'all_videos': all_videos,
            'valid_videos': valid_video_ids
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n分析結果を保存: {output_file}")
    
    # 有効な動画の詳細表示
    if valid_video_ids:
        logger.info(f"\n有効な動画の詳細（最初の5件）:")
        for i, video in enumerate(valid_video_ids[:5]):
            logger.info(f"\n--- 動画 {i+1} ---")
            logger.info(f"ID: {video.get('video_id')}")
            logger.info(f"URL: {video.get('url')}")
            logger.info(f"作者: {video.get('author_username', 'N/A')}")
            logger.info(f"説明: {video.get('description', video.get('text_content', 'N/A'))[:100]}...")
            logger.info(f"抽出方法: {video.get('extraction_method')}")
    
    logger.info(f"\n{'='*60}")
    logger.info("既存データの詳細分析完了")
    logger.info(f"{'='*60}")

def analyze_html_content(soup, strategy_name, logger):
    """HTMLコンテンツを詳細分析"""
    videos = []
    
    # 1. 動画リンクの検索
    video_links = soup.find_all('a', href=re.compile(r'/video/\d+'))
    logger.info(f"動画リンク: {len(video_links)}件")
    
    for link in video_links:
        video_data = extract_from_video_link(link, strategy_name)
        if video_data:
            videos.append(video_data)
    
    # 2. data-e2e属性の検索
    recommend_items = soup.find_all(attrs={'data-e2e': 'recommend-list-item'})
    logger.info(f"recommend-list-item: {len(recommend_items)}件")
    
    for item in recommend_items:
        video_data = extract_from_recommend_item(item, strategy_name)
        if video_data:
            videos.append(video_data)
    
    # 3. JavaScriptデータの検索
    script_tags = soup.find_all('script')
    logger.info(f"scriptタグ: {len(script_tags)}件")
    
    json_scripts = 0
    for script in script_tags:
        if script.string and ('{' in script.string or '[' in script.string):
            json_scripts += 1
            try:
                # JSONデータの抽出を試行
                script_content = script.string.strip()
                
                # window.__INITIAL_STATE__ パターン
                if 'window.__INITIAL_STATE__' in script_content:
                    logger.info("window.__INITIAL_STATE__ を発見")
                    json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', script_content, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            script_videos = extract_from_initial_state(data, strategy_name)
                            videos.extend(script_videos)
                            logger.info(f"INITIAL_STATE から {len(script_videos)} 件の動画データを抽出")
                        except json.JSONDecodeError:
                            pass
                
                # その他のJSONパターン
                elif script_content.startswith('{') or script_content.startswith('['):
                    try:
                        data = json.loads(script_content)
                        script_videos = extract_from_script_data(data, strategy_name)
                        videos.extend(script_videos)
                        if script_videos:
                            logger.info(f"スクリプトデータから {len(script_videos)} 件の動画データを抽出")
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                continue
    
    logger.info(f"JSON形式のスクリプト: {json_scripts}件")
    
    # 4. その他のパターン検索
    # TikTok特有のクラス名やID
    tiktok_elements = soup.find_all(class_=re.compile(r'(video|item|card|post)', re.I))
    logger.info(f"TikTok関連要素: {len(tiktok_elements)}件")
    
    # 重複除去
    unique_videos = remove_duplicate_videos(videos)
    logger.info(f"{strategy_name}: {len(unique_videos)}件の一意な動画データを抽出")
    
    return unique_videos

def extract_from_video_link(link, strategy_name):
    """動画リンクから動画データを抽出"""
    try:
        href = link.get('href', '')
        
        # 動画IDを抽出
        video_id_match = re.search(r'/video/(\d+)', href)
        if not video_id_match:
            return None
        
        video_id = video_id_match.group(1)
        
        # 作者情報を抽出
        author_username = ''
        if '/@' in href:
            author_match = re.search(r'/@([\w.-]+)', href)
            if author_match:
                author_username = author_match.group(1)
        
        # 親要素から追加情報を抽出
        parent = link.parent
        text_content = parent.get_text(strip=True) if parent else ''
        
        return {
            'video_id': video_id,
            'url': f"https://www.tiktok.com{href}" if href.startswith('/') else href,
            'author_username': author_username,
            'text_content': text_content,
            'extraction_method': f'video_link_{strategy_name}',
            'strategy': strategy_name
        }
        
    except Exception as e:
        return None

def extract_from_recommend_item(item, strategy_name):
    """recommend-list-item要素から動画データを抽出"""
    try:
        # 動画リンクを検索
        link = item.find('a', href=True)
        if not link:
            return None
        
        href = link['href']
        
        # 動画IDを抽出
        video_id_match = re.search(r'/video/(\d+)', href)
        if not video_id_match:
            return None
        
        video_id = video_id_match.group(1)
        
        # 作者情報を抽出
        author_link = item.find('a', href=re.compile(r'/@[\w.-]+'))
        author_username = ''
        if author_link:
            author_match = re.search(r'/@([\w.-]+)', author_link['href'])
            if author_match:
                author_username = author_match.group(1)
        
        # テキストコンテンツを抽出
        text_content = item.get_text(strip=True)
        
        return {
            'video_id': video_id,
            'url': f"https://www.tiktok.com{href}" if href.startswith('/') else href,
            'author_username': author_username,
            'text_content': text_content,
            'extraction_method': f'recommend_item_{strategy_name}',
            'strategy': strategy_name
        }
        
    except Exception as e:
        return None

def extract_from_initial_state(data, strategy_name):
    """INITIAL_STATEデータから動画データを抽出"""
    videos = []
    
    try:
        def search_video_data(obj, path=""):
            if isinstance(obj, dict):
                # 動画データの可能性があるキーを検索
                for key, value in obj.items():
                    if key in ['itemList', 'items', 'videoList', 'videos', 'data', 'list']:
                        if isinstance(value, list):
                            for item in value:
                                if is_video_item(item):
                                    video_data = extract_video_from_item(item, strategy_name)
                                    if video_data:
                                        videos.append(video_data)
                        else:
                            search_video_data(value, f"{path}.{key}")
                    elif key in ['aweme_id', 'video_id', 'id'] and isinstance(value, (str, int)):
                        # 単一の動画IDの場合
                        if str(value).isdigit():
                            videos.append({
                                'video_id': str(value),
                                'url': f"https://www.tiktok.com/video/{value}",
                                'extraction_method': f'initial_state_{strategy_name}',
                                'strategy': strategy_name
                            })
                    else:
                        search_video_data(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_video_data(item, f"{path}[{i}]")
        
        search_video_data(data)
        
    except Exception as e:
        pass
    
    return videos

def extract_from_script_data(data, strategy_name):
    """スクリプトデータから動画データを抽出"""
    videos = []
    
    try:
        def search_video_data(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['itemList', 'items', 'videoList', 'videos', 'data']:
                        if isinstance(value, list):
                            for item in value:
                                if is_video_item(item):
                                    video_data = extract_video_from_item(item, strategy_name)
                                    if video_data:
                                        videos.append(video_data)
                        else:
                            search_video_data(value, f"{path}.{key}")
                    else:
                        search_video_data(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_video_data(item, f"{path}[{i}]")
        
        search_video_data(data)
        
    except Exception as e:
        pass
    
    return videos

def is_video_item(item):
    """アイテムが動画データかどうかを判定"""
    if not isinstance(item, dict):
        return False
    
    # 動画データの特徴的なキーをチェック
    video_keys = ['id', 'aweme_id', 'video_id', 'desc', 'author', 'stats']
    return any(key in item for key in video_keys)

def extract_video_from_item(item, strategy_name):
    """動画アイテムから動画データを抽出"""
    try:
        video_id = item.get('id') or item.get('aweme_id') or item.get('video_id')
        if not video_id:
            return None
        
        author = item.get('author', {})
        stats = item.get('stats', {})
        
        return {
            'video_id': str(video_id),
            'url': f"https://www.tiktok.com/@{author.get('unique_id', 'unknown')}/video/{video_id}",
            'description': item.get('desc', ''),
            'author_username': author.get('unique_id', ''),
            'author_display_name': author.get('nickname', ''),
            'view_count': stats.get('play_count'),
            'like_count': stats.get('digg_count'),
            'comment_count': stats.get('comment_count'),
            'share_count': stats.get('share_count'),
            'create_time': item.get('create_time'),
            'extraction_method': f'script_data_{strategy_name}',
            'strategy': strategy_name
        }
        
    except Exception as e:
        return None

def remove_duplicate_videos(videos):
    """重複する動画を除去"""
    seen_ids = set()
    unique_videos = []
    
    for video in videos:
        video_id = video.get('video_id')
        if video_id and video_id not in seen_ids:
            unique_videos.append(video)
            seen_ids.add(video_id)
    
    return unique_videos

if __name__ == "__main__":
    analyze_existing_html_data()

