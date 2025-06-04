# 弁護士基準損害賠償計算システム v2.0

## 概要

このシステムは、交通事故等の損害賠償計算を弁護士基準で自動化する専門的なアプリケーションです。モダンなGUIインターフェースを提供し、正確で効率的な損害賠償計算を支援します。

## 主な機能

### 📊 損害賠償計算
- **弁護士基準による正確な計算**: 業界標準の計算式を使用
- **リアルタイム計算**: 入力値の変更に応じて即座に結果を更新
- **包括的な損害項目**: 治療費、慰謝料、逸失利益等を網羅

### 💼 案件管理
- **案件データベース**: SQLiteによる安全なデータ保存
- **案件履歴管理**: 過去の計算結果の検索・参照
- **データエクスポート**: PDF・Excel形式での出力

### 🎨 ユーザーインターフェース
- **モダンなUI**: CustomTkinterによる美しいインターフェース
- **直感的操作**: ユーザーフレンドリーなデザイン
- **レスポンシブ設計**: 様々な画面サイズに対応

### 🔒 セキュリティ・安定性
- **統合エラーハンドリング**: 堅牢なエラー処理システム
- **パフォーマンス監視**: リアルタイムシステム監視
- **セキュリティ管理**: データの安全性確保

## 最新の改善事項 (v2.0)

### 🎯 ユーザーエクスペリエンス向上
- **入力時エラー表示の改善**: 案件番号・依頼者氏名入力時の即座エラー表示を抑制
- **スマートな入力制御**: `auto_calculate`機能による柔軟な入力制御
- **作業効率向上**: ストレスフリーな入力環境の実現

### 🔧 システム安定性向上
- **循環インポート問題の解決**: モジュール間の依存関係を最適化
- **モデル統一**: データモデルの一貫性確保
- **エラー処理強化**: より堅牢なエラーハンドリング

## システム要件

### 動作環境
- **OS**: Windows 10/11
- **Python**: 3.8以上
- **メモリ**: 4GB以上推奨
- **ストレージ**: 500MB以上の空き容量

### 必要パッケージ
```
customtkinter>=5.0.0
tkinter
sqlite3
pandas
openpyxl
reportlab
pillow
python-dateutil
decimal
```

## インストール

### 1. リポジトリのクローン
```bash
git clone https://github.com/[your-username]/lawyer-compensation-calculator.git
cd lawyer-compensation-calculator
```

### 2. 仮想環境の作成（推奨）
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. アプリケーションの起動
```bash
python main.py
```

## 使用方法

### 基本的な操作手順

1. **新規案件の作成**
   - アプリケーション起動後、「新規案件」ボタンをクリック
   - 案件番号と依頼者氏名を入力

2. **基本情報の入力**
   - 被害者情報（年齢、職業、年収等）
   - 事故情報（事故日、症状固定日等）
   - 治療情報（治療期間、治療費等）

3. **計算結果の確認**
   - 入力内容に基づいて自動計算される損害賠償額を確認
   - 各項目の詳細な内訳を参照

4. **結果の保存・出力**
   - 計算結果をデータベースに保存
   - PDF・Excel形式でのレポート出力

## プロジェクト構造

```
lawyer-compensation-calculator/
├── main.py                     # メインアプリケーション
├── requirements.txt            # 依存関係
├── README.md                  # このファイル
├── COMPLETION_REPORT.md       # 実装完了報告
│
├── ui/                        # ユーザーインターフェース
│   └── modern_calculator_ui.py
│
├── models/                    # データモデル
│   ├── __init__.py
│   └── case_data.py
│
├── database/                  # データベース管理
│   ├── __init__.py
│   └── db_manager.py
│
├── calculation/               # 計算エンジン
│   ├── __init__.py
│   └── compensation_engine.py
│
├── config/                    # 設定管理
│   ├── __init__.py
│   ├── app_config.py
│   └── app_config.json
│
├── utils/                     # ユーティリティ
│   ├── __init__.py
│   ├── error_handler.py
│   ├── performance_monitor.py
│   └── security_manager.py
│
├── reports/                   # レポート生成
│   ├── __init__.py
│   ├── pdf_generator.py
│   └── excel_generator.py
│
└── tests/                     # テストファイル
    └── test_functionality.py
```

### Configuration file path
Utilities in `reports/` read settings from `config/app_config.json` by default.
Set the environment variable `APP_CONFIG_PATH` to point to another JSON file if you
need to override this location.

## 開発

### 開発環境のセットアップ
1. 上記のインストール手順を実行
2. 開発用の追加パッケージをインストール：
   ```bash
   pip install pytest pytest-cov black flake8
   ```

### テストの実行
```bash
python -m pytest tests/
```

### コードフォーマット
```bash
black . --line-length 100
```

## 貢献

プルリクエストや課題報告を歓迎します。貢献する前に、以下をご確認ください：

1. コードスタイルガイドラインに従う
2. 適切なテストを追加する
3. ドキュメントを更新する

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は`LICENSE`ファイルを参照してください。

## 変更履歴

### v2.0 (2025-05-27)
- ✨ 入力時エラー表示の改善
- 🔧 システム安定性向上
- 🐛 循環インポート問題の解決
- 📈 ユーザーエクスペリエンス向上

### v1.0 (初期バージョン)
- 基本的な損害賠償計算機能
- データベース連携
- PDF・Excel出力機能

## サポート

質問や問題がございましたら、GitHubのIssuesページにてお気軽にお問い合わせください。

---

**開発**: 法務システム開発チーム  
**最終更新**: 2025年5月27日
