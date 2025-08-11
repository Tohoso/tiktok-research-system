"""
User-Agent管理モジュール
より自然なブラウザエージェントを提供
"""

import random
from typing import List


class UserAgentManager:
    """User-Agent管理クラス"""
    
    # 実際のブラウザのUser-Agentリスト（2024年版）
    DESKTOP_USER_AGENTS = [
        # Chrome (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        
        # Chrome (macOS)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        # Firefox (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
        
        # Firefox (macOS)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        
        # Safari (macOS)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        
        # Edge (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    ]
    
    MOBILE_USER_AGENTS = [
        # iPhone Safari
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        
        # iPhone Chrome
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.169 Mobile/15E148 Safari/604.1",
        
        # Android Chrome
        "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.193 Mobile Safari/537.36",
        
        # Android Firefox
        "Mozilla/5.0 (Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
        "Mozilla/5.0 (Mobile; rv:120.0) Gecko/120.0 Firefox/120.0",
    ]
    
    # TikTok特化User-Agent（実際のTikTokアプリのWebView）
    TIKTOK_OPTIMIZED_USER_AGENTS = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 musical_ly_2024120901 JsSdk/1.0 NetType/WIFI Channel/App Store ByteLocale/ja Region/JP RevealType/0 WKWebView/1",
        "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.144 Mobile Safari/537.36 musical_ly_2024120901 JsSdk/1.0 NetType/WIFI Channel/googleplay ByteLocale/ja Region/JP",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 musical_ly_2024111501 JsSdk/1.0 NetType/WIFI Channel/App Store ByteLocale/ja Region/JP",
    ]
    
    @classmethod
    def get_random_desktop_agent(cls) -> str:
        """ランダムなデスクトップUser-Agentを取得"""
        return random.choice(cls.DESKTOP_USER_AGENTS)
    
    @classmethod
    def get_random_mobile_agent(cls) -> str:
        """ランダムなモバイルUser-Agentを取得"""
        return random.choice(cls.MOBILE_USER_AGENTS)
    
    @classmethod
    def get_random_tiktok_agent(cls) -> str:
        """ランダムなTikTok最適化User-Agentを取得"""
        return random.choice(cls.TIKTOK_OPTIMIZED_USER_AGENTS)
    
    @classmethod
    def get_random_agent(cls, device_type: str = "desktop") -> str:
        """
        デバイスタイプに応じたランダムUser-Agentを取得
        
        Args:
            device_type: "desktop", "mobile", "tiktok"のいずれか
            
        Returns:
            User-Agent文字列
        """
        if device_type == "mobile":
            return cls.get_random_mobile_agent()
        elif device_type == "tiktok":
            return cls.get_random_tiktok_agent()
        else:
            return cls.get_random_desktop_agent()
    
    @classmethod
    def get_browser_headers(cls, user_agent: str) -> dict:
        """
        User-Agentに応じた自然なHTTPヘッダーを生成
        
        Args:
            user_agent: User-Agent文字列
            
        Returns:
            HTTPヘッダー辞書
        """
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # ブラウザ固有のヘッダーを追加
        if 'Chrome' in user_agent:
            headers.update({
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0' if 'Mobile' not in user_agent else '?1',
                'sec-ch-ua-platform': '"Windows"' if 'Windows' in user_agent else '"macOS"',
            })
        elif 'Firefox' in user_agent:
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ja-jp',
            })
        
        return headers

