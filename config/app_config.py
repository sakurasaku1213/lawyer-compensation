#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アプリケーション設定管理システム
設定の読み込み、保存、検証を統一的に管理
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import os

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

@dataclass
class DatabaseConfig:
    """データベース設定"""
    db_path: str = "compensation_cases.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    backup_retention_days: int = 30
    auto_optimize: bool = True
    connection_timeout: float = 30.0
    
@dataclass
class UIConfig:
    """UI設定"""
    theme: str = "light"
    language: str = "ja"
    window_width: int = 1200
    window_height: int = 800
    font_size: int = 10
    enable_tooltips: bool = True
    auto_save_interval: int = 300  # 秒

@dataclass
class CalculationConfig:
    """計算設定"""
    default_standard: str = "弁護士基準"
    enable_auto_calculation: bool = True
    precision_digits: int = 0
    rounding_method: str = "round"  # round, floor, ceil
    validation_enabled: bool = True

@dataclass
class LoggingConfig:
    """ログ設定"""
    level: str = "INFO"
    file_enabled: bool = True
    file_path: str = "logs/app.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    console_enabled: bool = True

@dataclass
class SecurityConfig:
    """セキュリティ設定"""
    enable_data_encryption: bool = False
    backup_encryption: bool = False
    session_timeout: int = 3600  # 秒
    max_login_attempts: int = 3

@dataclass
class AppConfig:
    """アプリケーション全体設定"""
    version: str = "1.0.0"
    app_name: str = "弁護士基準損害賠償計算システム"
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    calculation: CalculationConfig = field(default_factory=CalculationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # カスタム設定
    custom_settings: Dict[str, Any] = field(default_factory=dict)

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "config/app_config.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._config: Optional[AppConfig] = None
        
        # 設定ディレクトリを作成
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 設定を読み込み
        self.load_config()
    
    def load_config(self) -> AppConfig:
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                
                # バージョンチェックと移行処理
                config_dict = self._migrate_config_if_needed(config_dict)
                
                # 設定オブジェクトを作成
                self._config = self._dict_to_config(config_dict)
                self.logger.info(f"設定ファイルを読み込みました: {self.config_path}")
            else:
                # デフォルト設定で初期化
                self._config = AppConfig()
                self.save_config()
                self.logger.info("デフォルト設定で初期化しました")
                
        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
            self._config = AppConfig()
            
        return self._config
    
    def save_config(self) -> bool:
        """設定ファイルを保存"""
        try:
            if self._config is None:
                self._config = AppConfig()
            
            # 更新日時を設定
            self._config.last_updated = datetime.now().isoformat()
            
            # 設定を辞書に変換
            config_dict = asdict(self._config)
            
            # JSONファイルに保存
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"設定ファイルを保存しました: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
            return False
    
    def get_config(self) -> AppConfig:
        """現在の設定を取得"""
        if self._config is None:
            self.load_config()
        return self._config
    
    def update_config(self, **kwargs) -> bool:
        """設定を更新"""
        try:
            if self._config is None:
                self.load_config()
            
            # ネストした設定の更新
            for key, value in kwargs.items():
                if hasattr(self._config, key):
                    if isinstance(value, dict):
                        # セクション設定の更新
                        section = getattr(self._config, key)
                        for sub_key, sub_value in value.items():
                            if hasattr(section, sub_key):
                                setattr(section, sub_key, sub_value)
                    else:
                        setattr(self._config, key, value)
                else:
                    # カスタム設定に追加
                    self._config.custom_settings[key] = value
            
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"設定更新エラー: {e}")
            return False
    
    def get_setting(self, key: str, section: str = None, default=None) -> Any:
        """特定の設定値を取得"""
        try:
            if self._config is None:
                self.load_config()
            
            if section:
                section_obj = getattr(self._config, section, None)
                if section_obj:
                    return getattr(section_obj, key, default)
            else:
                return getattr(self._config, key, default)
                
        except Exception as e:
            self.logger.error(f"設定取得エラー: {e}")
        
        return default
    
    def set_setting(self, key: str, value: Any, section: str = None) -> bool:
        """特定の設定値を設定"""
        try:
            if self._config is None:
                self.load_config()
            
            if section:
                section_obj = getattr(self._config, section, None)
                if section_obj and hasattr(section_obj, key):
                    setattr(section_obj, key, value)
                    return self.save_config()
            else:
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
                    return self.save_config()
                else:
                    self._config.custom_settings[key] = value
                    return self.save_config()
                    
        except Exception as e:
            self.logger.error(f"設定設定エラー: {e}")
        
        return False
    
    def reset_to_defaults(self, section: str = None) -> bool:
        """設定をデフォルトにリセット"""
        try:
            if section:
                # 特定セクションのみリセット
                if hasattr(AppConfig, section):
                    default_section = getattr(AppConfig(), section)
                    setattr(self._config, section, default_section)
            else:
                # 全設定をリセット
                self._config = AppConfig()
            
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"設定リセットエラー: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """設定の妥当性を検証"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            if self._config is None:
                self.load_config()
            
            # データベース設定の検証
            if self._config.database.backup_interval_hours < 1:
                validation_result['errors'].append("バックアップ間隔は1時間以上である必要があります")
                validation_result['valid'] = False
            
            if self._config.database.backup_retention_days < 1:
                validation_result['errors'].append("バックアップ保持期間は1日以上である必要があります")
                validation_result['valid'] = False
            
            # UI設定の検証
            if self._config.ui.window_width < 800:
                validation_result['warnings'].append("ウィンドウ幅が小さすぎる可能性があります")
            
            if self._config.ui.window_height < 600:
                validation_result['warnings'].append("ウィンドウ高さが小さすぎる可能性があります")
            
            # 計算設定の検証
            if self._config.calculation.precision_digits < 0:
                validation_result['errors'].append("精度桁数は0以上である必要があります")
                validation_result['valid'] = False
            
            # ログ設定の検証
            log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self._config.logging.level not in log_levels:
                validation_result['errors'].append(f"ログレベルは{log_levels}のいずれかである必要があります")
                validation_result['valid'] = False
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"設定検証エラー: {str(e)}")
        
        return validation_result
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """辞書から設定オブジェクトを作成"""
        try:
            # 各セクションを安全に作成
            database_config = DatabaseConfig(**config_dict.get('database', {}))
            ui_config = UIConfig(**config_dict.get('ui', {}))
            calculation_config = CalculationConfig(**config_dict.get('calculation', {}))
            logging_config = LoggingConfig(**config_dict.get('logging', {}))
            security_config = SecurityConfig(**config_dict.get('security', {}))
            
            return AppConfig(
                version=config_dict.get('version', '1.0.0'),
                app_name=config_dict.get('app_name', '弁護士基準損害賠償計算システム'),
                last_updated=config_dict.get('last_updated', datetime.now().isoformat()),
                database=database_config,
                ui=ui_config,
                calculation=calculation_config,
                logging=logging_config,
                security=security_config,
                custom_settings=config_dict.get('custom_settings', {})
            )
        except Exception as e:
            self.logger.error(f"設定オブジェクト作成エラー: {e}")
            return AppConfig()
    
    def _migrate_config_if_needed(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """設定のバージョン移行処理"""
        current_version = config_dict.get('version', '0.0.0')
        
        # バージョン固有の移行処理をここに追加
        if current_version < '1.0.0':
            # 1.0.0への移行処理
            self.logger.info(f"設定を{current_version}から1.0.0に移行します")
            config_dict['version'] = '1.0.0'
        
        return config_dict
    
    def export_config(self, export_path: str) -> bool:
        """設定をエクスポート"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            if self._config is None:
                self.load_config()
            
            config_dict = asdict(self._config)
            config_dict['export_date'] = datetime.now().isoformat()
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"設定をエクスポートしました: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定エクスポートエラー: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """設定をインポート"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                self.logger.error(f"インポートファイルが見つかりません: {import_path}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # バージョンチェックと移行
            config_dict = self._migrate_config_if_needed(config_dict)
            
            # 設定を更新
            self._config = self._dict_to_config(config_dict)
            
            # 保存
            if self.save_config():
                self.logger.info(f"設定をインポートしました: {import_path}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"設定インポートエラー: {e}")
            return False

# グローバル設定管理インスタンス
_config_manager = None

def get_config_manager() -> ConfigManager:
    """設定管理インスタンスを取得（シングルトンパターン）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> AppConfig:
    """現在の設定を取得（便利関数）"""
    return get_config_manager().get_config()

def save_config() -> bool:
    """設定を保存（便利関数）"""
    return get_config_manager().save_config()
