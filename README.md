# TikTok Research System

TikTokの/exploreページから24時間以内・日本・50万再生以上の動画を自動収集するシステムです。

## 🎯 主な機能

- **自動動画収集**: TikTokのおすすめ欄から動画を自動収集
- **高度なフィルタリング**: 再生数、投稿日時、地域による精密フィルタリング
- **データベース管理**: SQLiteによる効率的なデータ保存・検索
- **システム監視**: リアルタイムパフォーマンス監視とアラート
- **CLI インターフェース**: コマンドラインからの簡単操作

## 📋 要件

- Python 3.8以上
- ScraperAPI アカウント（APIキーが必要）
- 十分なディスク容量（動画データ保存用）

## 🚀 インストール

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd tiktok_research_system
```

### 2. 依存関係をインストール

```bash
pip install -r requirements.txt
```

### 3. パッケージをインストール

```bash
pip install -e .
```

### 4. 設定ファイルを編集

```bash
cp config/config.yaml config/config_local.yaml
# config_local.yaml を編集してAPIキーを設定
```

## ⚙️ 設定

### ScraperAPI設定

1. [ScraperAPI](https://www.scraperapi.com/) でアカウントを作成
2. APIキーを取得
3. `config/config_local.yaml` の `scraper.api_key` に設定

```yaml
scraper:
  api_key: "YOUR_SCRAPERAPI_KEY_HERE"
```

### その他の設定

- `filter.min_views`: 最小再生数（デフォルト: 500,000）
- `filter.time_range_hours`: 収集対象時間範囲（デフォルト: 24時間）
- `tiktok.country_code`: 対象国コード（デフォルト: JP）

## 📖 使用方法

### コマンドライン操作

#### トレンド動画を収集

```bash
# 基本的な収集（100件、50万再生以上、24時間以内）
python -m src.main collect

# カスタム設定で収集
python -m src.main collect --count 200 --min-views 1000000 --hours 12
```

#### 動画を検索

```bash
# 50万再生以上の動画を検索
python -m src.main search --min-views 500000

# 特定の作成者の動画を検索
python -m src.main search --author username

# 24時間以内の動画を検索
python -m src.main search --hours 24
```

#### 統計情報を表示

```bash
python -m src.main stats
```

#### 接続テスト

```bash
python -m src.main test
```

#### データ管理

```bash
# 古いデータを削除（30日以前）
python -m src.main cleanup --days 30

# データベースをバックアップ
python -m src.main backup backup/tiktok_videos_backup.db
```

### プログラムから使用

```python
from src.main import TikTokResearchApp

# アプリケーションを初期化
app = TikTokResearchApp(config_path="config/config_local.yaml")

# トレンド動画を収集
result = app.collect_trending_videos(
    target_count=100,
    min_views=500000,
    hours_ago=24
)

print(f"収集完了: {result['collected_count']}件")

# 動画を検索
search_result = app.search_videos(min_views=500000, limit=50)
print(f"検索結果: {search_result['count']}件")

# リソースを解放
app.close()
```

## 📊 データ構造

### 動画データ

```json
{
  "video_id": "7123456789",
  "url": "https://www.tiktok.com/@user/video/7123456789",
  "title": "動画タイトル",
  "description": "動画説明",
  "author_username": "username",
  "author_display_name": "表示名",
  "author_verified": true,
  "view_count": 1000000,
  "like_count": 50000,
  "comment_count": 1000,
  "share_count": 500,
  "upload_date": "2024-01-01T12:00:00",
  "hashtags": ["トレンド", "人気"],
  "mentions": ["user1", "user2"]
}
```

## 🔧 開発

### テストの実行

```bash
# 全テストを実行
python -m pytest tests/

# 特定のテストを実行
python -m pytest tests/test_video_filter.py

# カバレッジ付きでテスト実行
python -m pytest tests/ --cov=src
```

### ログの確認

```bash
# リアルタイムでログを確認
tail -f logs/tiktok_research.log

# エラーログのみを確認
grep ERROR logs/tiktok_research.log
```

## 📈 監視とメンテナンス

### システム状態の確認

```bash
# システム状態を確認
python -m src.main stats

# 接続テスト
python -m src.main test
```

### 定期メンテナンス

```bash
# 週次バックアップ
python -m src.main backup "backup/weekly_$(date +%Y%m%d).db"

# 月次クリーンアップ
python -m src.main cleanup --days 30
```

## ⚠️ 注意事項

### 法的考慮事項

- TikTokの利用規約を遵守してください
- 商用利用前に法務部門にご相談ください
- 個人情報保護法（GDPR等）への配慮が必要です

### 技術的制約

- ScraperAPIの利用制限に注意してください
- 大量リクエスト時はレート制限が適用されます
- TikTokの仕様変更により動作しなくなる可能性があります

### パフォーマンス

- 初回実行時は動画収集に時間がかかります
- データベースサイズが大きくなると検索が遅くなる場合があります
- 定期的なデータクリーンアップを推奨します

## 🐛 トラブルシューティング

### よくある問題

#### APIキーエラー

```
Error: Invalid API key
```

**解決方法**: `config/config_local.yaml` でAPIキーが正しく設定されているか確認

#### 接続エラー

```
Error: Connection timeout
```

**解決方法**: 
- インターネット接続を確認
- ScraperAPIの利用制限を確認
- `scraper.timeout` 設定を増加

#### データベースエラー

```
Error: Database is locked
```

**解決方法**:
- 他のプロセスがデータベースを使用していないか確認
- データベースファイルの権限を確認

### ログレベルの変更

デバッグ情報を詳しく見たい場合:

```yaml
logging:
  level: "DEBUG"
```

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください:

- エラーメッセージ
- 実行したコマンド
- 設定ファイル（APIキーは除く）
- ログファイル（`logs/tiktok_research.log`）

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🔄 更新履歴

### v1.0.0 (2024-01-01)
- 初回リリース
- 基本的な動画収集機能
- データベース管理機能
- CLI インターフェース

