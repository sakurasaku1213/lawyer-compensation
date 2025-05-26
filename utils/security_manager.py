#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セキュリティ・データ保護システム

機能:
- データ暗号化・復号化
- アクセス制御とユーザー認証
- 機密データの安全な保存
- 監査ログの記録
- データ完整性の検証
- セキュリティアラート
"""

import hashlib
import hmac
import secrets
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecurityLevel(Enum):
    """セキュリティレベル"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class AccessType(Enum):
    """アクセス種別"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

@dataclass
class SecurityEvent:
    """セキュリティイベント"""
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    resource: str
    action: str
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserPermission:
    """ユーザー権限"""
    user_id: str
    resource_pattern: str
    access_types: List[AccessType]
    security_level: SecurityLevel
    expires_at: Optional[datetime] = None
    granted_by: Optional[str] = None
    granted_at: datetime = field(default_factory=datetime.now)

class DataEncryption:
    """データ暗号化クラス"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if master_key:
            self.key = self._derive_key(master_key)
        else:
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
        self.logger.info("データ暗号化システムを初期化しました")
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """パスワードからキーを導出"""
        if salt is None:
            salt = b"compensation_system_salt"  # 本番環境では動的に生成
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt_data(self, data: Union[str, dict, list]) -> str:
        """データを暗号化"""
        try:
            if isinstance(data, (dict, list)):
                data = json.dumps(data, ensure_ascii=False)
            
            encrypted = self.cipher.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            self.logger.error(f"データ暗号化エラー: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """データを復号化"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            self.logger.error(f"データ復号化エラー: {e}")
            raise
    
    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """JSON データを暗号化"""
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt_data(json_str)
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """暗号化された JSON データを復号化"""
        json_str = self.decrypt_data(encrypted_data)
        return json.loads(json_str)

class AccessControl:
    """アクセス制御システム"""
    
    def __init__(self, db_path: str = "security.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.permissions: Dict[str, List[UserPermission]] = {}
        self.security_events: List[SecurityEvent] = []
        
        self._init_database()
        self._load_permissions()
        
        self.logger.info("アクセス制御システムを初期化しました")
    
    def _init_database(self):
        """セキュリティデータベースを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    resource_pattern TEXT NOT NULL,
                    access_types TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    expires_at TEXT,
                    granted_by TEXT,
                    granted_at TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_permissions_user 
                ON user_permissions(user_id)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON security_events(timestamp)
            ''')
            
            conn.commit()
    
    def _load_permissions(self):
        """権限情報をロード"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_id, resource_pattern, access_types, security_level,
                       expires_at, granted_by, granted_at
                FROM user_permissions
                WHERE expires_at IS NULL OR expires_at > ?
            ''', (datetime.now().isoformat(),))
            
            for row in cursor.fetchall():
                user_id, resource_pattern, access_types_str, security_level_str, expires_at, granted_by, granted_at = row
                
                access_types = [AccessType(t) for t in access_types_str.split(',')]
                security_level = SecurityLevel(security_level_str)
                expires_at_dt = datetime.fromisoformat(expires_at) if expires_at else None
                granted_at_dt = datetime.fromisoformat(granted_at)
                
                permission = UserPermission(
                    user_id=user_id,
                    resource_pattern=resource_pattern,
                    access_types=access_types,
                    security_level=security_level,
                    expires_at=expires_at_dt,
                    granted_by=granted_by,
                    granted_at=granted_at_dt
                )
                
                if user_id not in self.permissions:
                    self.permissions[user_id] = []
                self.permissions[user_id].append(permission)
    
    def grant_permission(self, user_id: str, resource_pattern: str, 
                        access_types: List[AccessType], 
                        security_level: SecurityLevel,
                        expires_at: Optional[datetime] = None,
                        granted_by: Optional[str] = None) -> bool:
        """権限を付与"""
        try:
            permission = UserPermission(
                user_id=user_id,
                resource_pattern=resource_pattern,
                access_types=access_types,
                security_level=security_level,
                expires_at=expires_at,
                granted_by=granted_by
            )
            
            # データベースに保存
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO user_permissions 
                    (user_id, resource_pattern, access_types, security_level, 
                     expires_at, granted_by, granted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    resource_pattern,
                    ','.join(t.value for t in access_types),
                    security_level.value,
                    expires_at.isoformat() if expires_at else None,
                    granted_by,
                    permission.granted_at.isoformat()
                ))
                conn.commit()
            
            # メモリに追加
            if user_id not in self.permissions:
                self.permissions[user_id] = []
            self.permissions[user_id].append(permission)
            
            self._log_security_event("permission_granted", user_id, resource_pattern, 
                                   "grant", True, details={
                                       "access_types": [t.value for t in access_types],
                                       "security_level": security_level.value,
                                       "granted_by": granted_by
                                   })
            
            return True
        except Exception as e:
            self.logger.error(f"権限付与エラー: {e}")
            return False
    
    def check_permission(self, user_id: str, resource: str, 
                        access_type: AccessType,
                        required_security_level: SecurityLevel = SecurityLevel.PUBLIC) -> bool:
        """権限をチェック"""
        try:
            user_permissions = self.permissions.get(user_id, [])
            
            for permission in user_permissions:
                # 有効期限チェック
                if permission.expires_at and permission.expires_at < datetime.now():
                    continue
                
                # リソースパターンマッチング（簡易実装）
                if self._match_resource_pattern(permission.resource_pattern, resource):
                    # アクセス種別チェック
                    if access_type in permission.access_types or AccessType.ADMIN in permission.access_types:
                        # セキュリティレベルチェック
                        if self._check_security_level(permission.security_level, required_security_level):
                            self._log_security_event("access_granted", user_id, resource, 
                                                   access_type.value, True)
                            return True
            
            self._log_security_event("access_denied", user_id, resource, 
                                   access_type.value, False, details={
                                       "reason": "insufficient_permissions"
                                   })
            return False
        except Exception as e:
            self.logger.error(f"権限チェックエラー: {e}")
            self._log_security_event("access_error", user_id, resource, 
                                   access_type.value, False, details={
                                       "error": str(e)
                                   })
            return False
    
    def _match_resource_pattern(self, pattern: str, resource: str) -> bool:
        """リソースパターンマッチング"""
        # 簡易実装：ワイルドカード対応
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return resource.startswith(pattern[:-1])
        return pattern == resource
    
    def _check_security_level(self, user_level: SecurityLevel, required_level: SecurityLevel) -> bool:
        """セキュリティレベルチェック"""
        level_hierarchy = {
            SecurityLevel.PUBLIC: 0,
            SecurityLevel.INTERNAL: 1,
            SecurityLevel.CONFIDENTIAL: 2,
            SecurityLevel.RESTRICTED: 3
        }
        
        return level_hierarchy[user_level] >= level_hierarchy[required_level]
    
    def _log_security_event(self, event_type: str, user_id: Optional[str], 
                           resource: str, action: str, success: bool,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None,
                           details: Optional[Dict[str, Any]] = None):
        """セキュリティイベントをログ"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
        
        self.security_events.append(event)
        
        # データベースに保存
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO security_events 
                    (timestamp, event_type, user_id, resource, action, success, 
                     ip_address, user_agent, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.user_id,
                    event.resource,
                    event.action,
                    event.success,
                    event.ip_address,
                    event.user_agent,
                    json.dumps(event.details, ensure_ascii=False)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"セキュリティイベント保存エラー: {e}")
        
        # アラートチェック
        self._check_security_alerts(event)
    
    def _check_security_alerts(self, event: SecurityEvent):
        """セキュリティアラートをチェック"""
        # 失敗したアクセス試行の監視
        if not event.success and event.event_type == "access_denied":
            recent_failures = [
                e for e in self.security_events[-10:]
                if (e.user_id == event.user_id and 
                    e.event_type == "access_denied" and 
                    not e.success and
                    e.timestamp > datetime.now() - timedelta(minutes=15))
            ]
            
            if len(recent_failures) >= 3:
                self.logger.warning(f"セキュリティアラート: ユーザー {event.user_id} の連続アクセス失敗")
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """セキュリティサマリーを取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.security_events if e.timestamp >= cutoff_time]
        
        total_events = len(recent_events)
        successful_events = len([e for e in recent_events if e.success])
        failed_events = total_events - successful_events
        
        # イベント種別別の統計
        event_types = {}
        for event in recent_events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        # ユーザー別の統計
        user_activity = {}
        for event in recent_events:
            if event.user_id:
                if event.user_id not in user_activity:
                    user_activity[event.user_id] = {"total": 0, "failed": 0}
                user_activity[event.user_id]["total"] += 1
                if not event.success:
                    user_activity[event.user_id]["failed"] += 1
        
        return {
            "period_hours": hours,
            "total_events": total_events,
            "successful_events": successful_events,
            "failed_events": failed_events,
            "success_rate": (successful_events / total_events * 100) if total_events > 0 else 0,
            "event_types": event_types,
            "user_activity": user_activity,
            "total_users": len(self.permissions),
            "recent_alerts": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "message": f"ユーザー {e.user_id} のアクセス失敗: {e.resource}",
                    "severity": "warning"
                }
                for e in recent_events[-5:]
                if not e.success and e.event_type == "access_denied"
            ]
        }

class SecureDataManager:
    """セキュアデータ管理システム"""
    
    def __init__(self, master_key: Optional[str] = None, db_path: str = "secure_data.db"):
        self.encryption = DataEncryption(master_key)
        self.access_control = AccessControl()
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        self._init_database()
    
    def _init_database(self):
        """セキュアデータベースを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS secure_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    encrypted_data TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_secure_data_key 
                ON secure_data(key)
            ''')
            
            conn.commit()
    
    def store_secure_data(self, key: str, data: Any, security_level: SecurityLevel,
                         user_id: str) -> bool:
        """セキュアにデータを保存"""
        try:
            # 権限チェック
            if not self.access_control.check_permission(user_id, key, AccessType.WRITE, security_level):
                return False
            
            # データを暗号化
            encrypted_data = self.encryption.encrypt_data(data)
            
            # チェックサムを生成
            checksum = hashlib.sha256(encrypted_data.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO secure_data 
                    (key, encrypted_data, security_level, created_by, updated_at, checksum)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    key,
                    encrypted_data,
                    security_level.value,
                    user_id,
                    datetime.now().isoformat(),
                    checksum
                ))
                conn.commit()
            
            self.logger.info(f"セキュアデータを保存しました: {key}")
            return True
        except Exception as e:
            self.logger.error(f"セキュアデータ保存エラー: {e}")
            return False
    
    def retrieve_secure_data(self, key: str, user_id: str) -> Optional[str]:
        """セキュアデータを取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT encrypted_data, security_level, checksum
                    FROM secure_data WHERE key = ?
                ''', (key,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                encrypted_data, security_level_str, stored_checksum = row
                security_level = SecurityLevel(security_level_str)
                
                # 権限チェック
                if not self.access_control.check_permission(user_id, key, AccessType.READ, security_level):
                    return None
                
                # チェックサム検証
                current_checksum = hashlib.sha256(encrypted_data.encode()).hexdigest()
                if current_checksum != stored_checksum:
                    self.logger.error(f"データ整合性エラー: {key}")
                    return None
                
                # 復号化
                decrypted_data = self.encryption.decrypt_data(encrypted_data)
                return decrypted_data
        except Exception as e:
            self.logger.error(f"セキュアデータ取得エラー: {e}")
            return None

# セキュリティデコレータ
def require_permission(resource: str, access_type: AccessType, 
                      security_level: SecurityLevel = SecurityLevel.PUBLIC):
    """権限チェックデコレータ"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # ユーザーIDを取得（実装依存）
            user_id = kwargs.get('user_id') or getattr(args[0], 'current_user_id', 'anonymous')
            
            # 権限チェック
            access_control = get_security_manager().access_control
            if not access_control.check_permission(user_id, resource, access_type, security_level):
                raise PermissionError(f"アクセス権限がありません: {resource}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# グローバルセキュリティマネージャー
_global_security_manager = None

def get_security_manager() -> SecureDataManager:
    """グローバルセキュリティマネージャーを取得"""
    global _global_security_manager
    if _global_security_manager is None:
        _global_security_manager = SecureDataManager()
    return _global_security_manager

if __name__ == "__main__":
    # テスト用のコード
    import tempfile
    import os
    
    # テンポラリディレクトリでテスト
    with tempfile.TemporaryDirectory() as temp_dir:
        security_db = os.path.join(temp_dir, "security_test.db")
        secure_db = os.path.join(temp_dir, "secure_test.db")
        
        # セキュリティシステムのテスト
        manager = SecureDataManager("test_master_key", secure_db)
        
        # テストユーザーに権限を付与
        manager.access_control.grant_permission(
            user_id="test_user",
            resource_pattern="test_*",
            access_types=[AccessType.READ, AccessType.WRITE],
            security_level=SecurityLevel.CONFIDENTIAL
        )
        
        # データの保存と取得をテスト
        test_data = {"sensitive_info": "機密データ", "case_id": "12345"}
        
        success = manager.store_secure_data(
            key="test_case_data",
            data=test_data,
            security_level=SecurityLevel.CONFIDENTIAL,
            user_id="test_user"
        )
        print(f"データ保存: {'成功' if success else '失敗'}")
        
        retrieved_data = manager.retrieve_secure_data(
            key="test_case_data",
            user_id="test_user"
        )
        print(f"データ取得: {retrieved_data}")
        
        # セキュリティサマリー
        summary = manager.access_control.get_security_summary()
        print(f"セキュリティサマリー: {json.dumps(summary, indent=2, ensure_ascii=False)}")
