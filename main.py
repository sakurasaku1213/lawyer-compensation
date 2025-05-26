#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弁護士基準損害賠償計算システム - メインエントリーポイント

統合された起動システム:
- 依存関係の自動チェック・インストール
- 設定システムの初期化
- パフォーマンス監視の開始
- セキュリティシステムの起動
- エラーハンドリングの設定
- UIアプリケーションの起動
"""

import sys
import os
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
import argparse
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設定とユーティリティのインポート
try:
    from config.app_config import ConfigManager, get_config_manager
    from utils.error_handler import ErrorHandler, get_error_handler, handle_critical_error
    from utils.performance_monitor import PerformanceMonitor, get_performance_monitor
    from utils.security_manager import SecureDataManager, get_security_manager
    from dependency_manager import DependencyManager, quick_setup
except ImportError as e:
    print(f"❌ 重要なモジュールのインポートに失敗しました: {e}")
    print("dependency_manager.py を実行して依存関係をインストールしてください。")
    sys.exit(1)

class CompensationSystemLauncher:
    """統合システム起動クラス"""
    
    def __init__(self, args: Optional[argparse.Namespace] = None):
        self.args = args or argparse.Namespace()
        self.setup_complete = False
        self.components_initialized = False
        
        # 基本ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('system_startup.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("弁護士基準損害賠償計算システムを起動中...")
    
    def check_system_requirements(self) -> bool:
        """システム要件をチェック"""
        self.logger.info("🔍 システム要件をチェック中...")
        
        # Python バージョンチェック
        if sys.version_info < (3, 8):
            self.logger.error(f"Python 3.8以上が必要です (現在: {sys.version})")
            return False
        
        # 必要なディレクトリの作成
        required_dirs = [
            'config', 'database', 'logs', 'reports', 'exports', 'temp'
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            self.logger.debug(f"ディレクトリを確認/作成: {dir_path}")
        
        self.logger.info("✅ システム要件チェック完了")
        return True
    
    def setup_dependencies(self) -> bool:
        """依存関係をセットアップ"""
        if hasattr(self.args, 'skip_deps') and self.args.skip_deps:
            self.logger.info("⏭️  依存関係チェックをスキップします")
            return True
        
        self.logger.info("📦 依存関係をチェック中...")
        
        try:
            dm = DependencyManager()
            
            # 依存関係レポートを生成
            report = dm.generate_dependency_report()
            
            # 必須パッケージの不足をチェック
            if report["missing_required"]:
                self.logger.warning(f"不足している必須パッケージ: {report['missing_required']}")
                
                if hasattr(self.args, 'auto_install') and self.args.auto_install:
                    self.logger.info("自動インストールを実行中...")
                    success = dm.install_missing_packages()
                    if not success:
                        self.logger.error("❌ 依存関係のインストールに失敗しました")
                        return False
                else:
                    response = input("不足しているパッケージをインストールしますか？ (y/N): ")
                    if response.lower() in ['y', 'yes']:
                        success = dm.install_missing_packages()
                        if not success:
                            return False
                    else:
                        self.logger.error("必須パッケージが不足しています")
                        return False
            
            self.logger.info("✅ 依存関係チェック完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 依存関係チェックエラー: {e}")
            return False
    
    def initialize_configuration(self) -> bool:
        """設定システムを初期化"""
        self.logger.info("⚙️ 設定システムを初期化中...")
        
        try:
            self.config_manager = get_config_manager()
            
            # 設定の妥当性チェック
            if not self.config_manager.validate_config():
                self.logger.error("設定の妥当性チェックに失敗しました")
                return False
            
            # ログレベルを設定から更新
            log_level = getattr(logging, self.config_manager.config.logging.level.upper())
            logging.getLogger().setLevel(log_level)
            
            self.logger.info("✅ 設定システム初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 設定システム初期化エラー: {e}")
            return False
    
    def initialize_error_handling(self) -> bool:
        """エラーハンドリングシステムを初期化"""
        self.logger.info("🛡️ エラーハンドリングシステムを初期化中...")
        
        try:
            self.error_handler = get_error_handler()
            
            # グローバル例外ハンドラーを設定
            def global_exception_handler(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                
                self.logger.critical("未捕捉の例外が発生しました", 
                                   exc_info=(exc_type, exc_value, exc_traceback))
                self.error_handler.handle_exception(exc_value)
            
            sys.excepthook = global_exception_handler
            
            self.logger.info("✅ エラーハンドリングシステム初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ エラーハンドリングシステム初期化エラー: {e}")
            return False
    
    def initialize_performance_monitoring(self) -> bool:
        """パフォーマンス監視システムを初期化"""
        if hasattr(self.args, 'no_monitoring') and self.args.no_monitoring:
            self.logger.info("⏭️  パフォーマンス監視をスキップします")
            return True
        
        self.logger.info("📊 パフォーマンス監視システムを初期化中...")
        
        try:
            self.performance_monitor = get_performance_monitor()
            self.performance_monitor.start_monitoring()
            
            self.logger.info("✅ パフォーマンス監視システム初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ パフォーマンス監視システム初期化エラー: {e}")
            return False
    
    def initialize_security(self) -> bool:
        """セキュリティシステムを初期化"""
        if hasattr(self.args, 'no_security') and self.args.no_security:
            self.logger.info("⏭️  セキュリティシステムをスキップします")
            return True
        
        self.logger.info("🔒 セキュリティシステムを初期化中...")
        
        try:
            self.security_manager = get_security_manager()
            
            # デフォルトユーザーの権限設定（開発用）
            if hasattr(self.args, 'dev_mode') and self.args.dev_mode:
                from utils.security_manager import AccessType, SecurityLevel
                self.security_manager.access_control.grant_permission(
                    user_id="developer",
                    resource_pattern="*",
                    access_types=[AccessType.READ, AccessType.WRITE, AccessType.ADMIN],
                    security_level=SecurityLevel.RESTRICTED,
                    granted_by="system"
                )
                self.logger.info("開発者権限を設定しました")
            
            self.logger.info("✅ セキュリティシステム初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ セキュリティシステム初期化エラー: {e}")
            return False
    
    def launch_application(self) -> bool:
        """アプリケーションを起動"""
        self.logger.info("🚀 メインアプリケーションを起動中...")
        
        try:
            # UIモジュールのインポート（遅延インポート）
            try:
                from ui.modern_calculator_ui import ModernCompensationCalculator
            except ImportError as e:
                self.logger.error(f"UIモジュールのインポートに失敗: {e}")
                self.logger.info("依存関係を確認してください")
                return False
            
            # アプリケーションの作成と起動
            app = ModernCompensationCalculator()
            
            self.logger.info("✅ アプリケーションを起動しました")
            self.logger.info("📱 UIが表示されるまでお待ちください...")
            
            # メインループの開始
            app.run()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ アプリケーション起動エラー: {e}")
            self.error_handler.handle_exception(e)
            return False
    
    def cleanup(self):
        """システムクリーンアップ"""
        self.logger.info("🧹 システムクリーンアップを実行中...")
        
        try:
            # パフォーマンス監視の停止
            if hasattr(self, 'performance_monitor'):
                self.performance_monitor.stop_monitoring()
                self.performance_monitor.export_performance_report("logs/performance_report.json")
            
            # エラーレポートの出力
            if hasattr(self, 'error_handler'):
                self.error_handler.export_error_report("logs/error_report.json")
            
            # セキュリティレポートの出力
            if hasattr(self, 'security_manager'):
                summary = self.security_manager.access_control.get_security_summary()
                import json
                with open("logs/security_summary.json", 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info("✅ クリーンアップ完了")
            
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")
    
    def run(self) -> int:
        """メイン実行関数"""
        try:
            self.logger.info(f"{'='*60}")
            self.logger.info("弁護士基準損害賠償計算システム v2.0")
            self.logger.info(f"起動時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"{'='*60}")
            
            # 1. システム要件チェック
            if not self.check_system_requirements():
                return 1
            
            # 2. 依存関係セットアップ
            if not self.setup_dependencies():
                return 1
            
            # 3. 設定システム初期化
            if not self.initialize_configuration():
                return 1
            
            # 4. エラーハンドリング初期化
            if not self.initialize_error_handling():
                return 1
            
            # 5. パフォーマンス監視初期化
            if not self.initialize_performance_monitoring():
                return 1
            
            # 6. セキュリティシステム初期化
            if not self.initialize_security():
                return 1
            
            self.components_initialized = True
            self.logger.info("🎉 すべてのシステムコンポーネントの初期化が完了しました")
            
            # 7. アプリケーション起動
            if not self.launch_application():
                return 1
            
            return 0
            
        except KeyboardInterrupt:
            self.logger.info("ユーザーによって中断されました")
            return 0
        except Exception as e:
            self.logger.critical(f"致命的エラー: {e}")
            handle_critical_error(e)
            return 1
        finally:
            if self.components_initialized:
                self.cleanup()

def create_argument_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        description="弁護士基準損害賠償計算システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py                    # 通常起動
  python main.py --dev-mode         # 開発者モード
  python main.py --auto-install     # 自動依存関係インストール
  python main.py --no-monitoring    # 監視なしで起動
  python main.py --skip-deps        # 依存関係チェックスキップ
        """
    )
    
    parser.add_argument('--dev-mode', action='store_true',
                       help='開発者モードで起動（デバッグ機能有効）')
    parser.add_argument('--auto-install', action='store_true',
                       help='不足している依存関係を自動インストール')
    parser.add_argument('--skip-deps', action='store_true',
                       help='依存関係チェックをスキップ')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='パフォーマンス監視を無効化')
    parser.add_argument('--no-security', action='store_true',
                       help='セキュリティシステムを無効化')
    parser.add_argument('--config-file', type=str,
                       help='設定ファイルのパスを指定')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='ログレベルを指定')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0')
    
    return parser

def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # ランチャーを作成して実行
    launcher = CompensationSystemLauncher(args)
    exit_code = launcher.run()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
