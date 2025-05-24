#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLiteデータベース管理システム
案件データの永続化、検索、バックアップを担当
"""

import sqlite3
import json
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import shutil
from contextlib import contextmanager

from models.case_data import CaseData

class DatabaseManager:
    """SQLiteデータベース管理クラス"""
    
    def __init__(self, db_path: str = "compensation_cases.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self) -> None:
        """データベースとテーブルの初期化"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 案件テーブル
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        case_number TEXT UNIQUE NOT NULL,
                        created_date TEXT NOT NULL,
                        last_modified TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT '作成中',
                        person_info TEXT NOT NULL,
                        accident_info TEXT NOT NULL,
                        medical_info TEXT NOT NULL,
                        income_info TEXT NOT NULL,
                        notes TEXT,
                        custom_fields TEXT,
                        calculation_results TEXT,
                        is_archived BOOLEAN DEFAULT 0
                    )
                ''')
                
                # 計算履歴テーブル
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calculation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        case_id INTEGER NOT NULL,
                        calculation_date TEXT NOT NULL,
                        calculation_type TEXT NOT NULL,
                        input_parameters TEXT NOT NULL,
                        results TEXT NOT NULL,
                        FOREIGN KEY (case_id) REFERENCES cases (id)
                    )
                ''')
                
                # バックアップ記録テーブル
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS backup_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backup_date TEXT NOT NULL,
                        backup_file_path TEXT NOT NULL,
                        backup_type TEXT NOT NULL,
                        file_size INTEGER,
                        notes TEXT
                    )
                ''')
                
                # 設定テーブル
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        last_updated TEXT NOT NULL
                    )
                ''')
                
                # インデックス作成
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_case_number ON cases(case_number)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON cases(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_date ON cases(created_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_calculation_case_id ON calculation_history(case_id)')
                
                conn.commit()
                self.logger.info(f"データベースを初期化しました: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"データベース初期化エラー: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"データベース接続エラー: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_case(self, case_data: CaseData) -> bool:
        """案件データを保存（新規作成・更新両対応）"""
        try:
            case_data.last_modified = datetime.now()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 既存データの確認
                cursor.execute('SELECT id FROM cases WHERE case_number = ?', (case_data.case_number,))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新
                    cursor.execute('''
                        UPDATE cases SET
                            last_modified = ?,
                            status = ?,
                            person_info = ?,
                            accident_info = ?,
                            medical_info = ?,
                            income_info = ?,
                            notes = ?,
                            custom_fields = ?,
                            calculation_results = ?
                        WHERE case_number = ?
                    ''', (
                        case_data.last_modified.isoformat(),
                        case_data.status,
                        json.dumps(case_data.person_info.to_dict(), ensure_ascii=False),
                        json.dumps(case_data.accident_info.to_dict(), ensure_ascii=False),
                        json.dumps(case_data.medical_info.to_dict(), ensure_ascii=False),
                        json.dumps(case_data.income_info.to_dict(), ensure_ascii=False),
                        case_data.notes,
                        json.dumps(case_data.custom_fields, ensure_ascii=False),
                        json.dumps(case_data.calculation_results, ensure_ascii=False),
                        case_data.case_number
                    ))
                    self.logger.info(f"案件データを更新しました: {case_data.case_number}")
                else:
                    # 新規作成
                    cursor.execute('''
                        INSERT INTO cases (
                            case_number, created_date, last_modified, status,
                            person_info, accident_info, medical_info, income_info,
                            notes, custom_fields, calculation_results
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        case_data.case_number,
                        case_data.created_date.isoformat(),
                        case_data.last_modified.isoformat(),
                        case_data.status,
                        json.dumps(case_data.person_info.to_dict(), ensure_ascii=False),
                        json.dumps(case_data.accident_info.to_dict(), ensure_ascii=False),
                        json.dumps(case_data.medical_info.to_dict(), ensure_ascii=False),
                        json.dumps(case_data.income_info.to_dict(), ensure_ascii=False),
                        case_data.notes,
                        json.dumps(case_data.custom_fields, ensure_ascii=False),
                        json.dumps(case_data.calculation_results, ensure_ascii=False)
                    ))
                    self.logger.info(f"新規案件データを作成しました: {case_data.case_number}")
                
                conn.commit()
                return True
                
        except sqlite3.IntegrityError as e:
            self.logger.error(f"案件番号重複エラー: {case_data.case_number} - {e}")
            return False
        except Exception as e:
            self.logger.error(f"案件保存エラー: {e}")
            return False
    
    def load_case(self, case_number: str) -> Optional[CaseData]:
        """案件番号で案件データを読み込み"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM cases WHERE case_number = ? AND is_archived = 0', (case_number,))
                row = cursor.fetchone()
                
                if row:
                    case_data = CaseData()
                    case_data.case_number = row['case_number']
                    case_data.created_date = datetime.fromisoformat(row['created_date'])
                    case_data.last_modified = datetime.fromisoformat(row['last_modified'])
                    case_data.status = row['status']
                    case_data.person_info = case_data.person_info.from_dict(json.loads(row['person_info']))
                    case_data.accident_info = case_data.accident_info.from_dict(json.loads(row['accident_info']))
                    case_data.medical_info = case_data.medical_info.from_dict(json.loads(row['medical_info']))
                    case_data.income_info = case_data.income_info.from_dict(json.loads(row['income_info']))
                    case_data.notes = row['notes'] or ""
                    case_data.custom_fields = json.loads(row['custom_fields']) if row['custom_fields'] else {}
                    case_data.calculation_results = json.loads(row['calculation_results']) if row['calculation_results'] else {}
                    
                    return case_data
                    
        except Exception as e:
            self.logger.error(f"案件読み込みエラー: {case_number} - {e}")
        
        return None
    
    def search_cases(self, 
                    case_number_pattern: str = None,
                    client_name_pattern: str = None,
                    status: str = None,
                    date_from: date = None,
                    date_to: date = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """案件検索"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT case_number, created_date, last_modified, status,
                           json_extract(person_info, '$.name') as client_name,
                           json_extract(accident_info, '$.accident_date') as accident_date
                    FROM cases 
                    WHERE is_archived = 0
                '''
                params = []
                
                if case_number_pattern:
                    query += ' AND case_number LIKE ?'
                    params.append(f'%{case_number_pattern}%')
                
                if client_name_pattern:
                    query += ' AND json_extract(person_info, "$.name") LIKE ?'
                    params.append(f'%{client_name_pattern}%')
                
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                
                if date_from:
                    query += ' AND created_date >= ?'
                    params.append(date_from.isoformat())
                
                if date_to:
                    query += ' AND created_date <= ?'
                    params.append(date_to.isoformat())
                
                query += ' ORDER BY last_modified DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"案件検索エラー: {e}")
            return []
    
    def delete_case(self, case_number: str) -> bool:
        """案件を論理削除（アーカイブ）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE cases SET is_archived = 1 WHERE case_number = ?', (case_number,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"案件をアーカイブしました: {case_number}")
                    return True
                else:
                    self.logger.warning(f"アーカイブ対象の案件が見つかりません: {case_number}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"案件削除エラー: {case_number} - {e}")
            return False
    
    def create_backup(self, backup_dir: str = "backups") -> bool:
        """データベースのバックアップ作成"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"compensation_db_backup_{timestamp}.db"
            
            shutil.copy2(self.db_path, backup_file)
            
            # バックアップ記録を保存
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO backup_records (backup_date, backup_file_path, backup_type, file_size)
                    VALUES (?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    str(backup_file),
                    "自動バックアップ",
                    backup_file.stat().st_size
                ))
                conn.commit()
            
            self.logger.info(f"バックアップを作成しました: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"バックアップ作成エラー: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """データベース統計情報を取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 総案件数
                cursor.execute('SELECT COUNT(*) FROM cases WHERE is_archived = 0')
                stats['total_cases'] = cursor.fetchone()[0]
                
                # ステータス別件数
                cursor.execute('SELECT status, COUNT(*) FROM cases WHERE is_archived = 0 GROUP BY status')
                stats['status_counts'] = dict(cursor.fetchall())
                
                # 月別作成件数（直近12ヶ月）
                cursor.execute('''
                    SELECT strftime('%Y-%m', created_date) as month, COUNT(*) 
                    FROM cases 
                    WHERE is_archived = 0 AND created_date >= date('now', '-12 months')
                    GROUP BY month 
                    ORDER BY month
                ''')
                stats['monthly_cases'] = dict(cursor.fetchall())
                
                return stats
                
        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {}
