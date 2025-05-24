#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLiteデータベース管理システム (Simplified for basic CaseData)
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from contextlib import contextmanager

# Assuming models.case_data.CaseData is the simple version:
# from dataclasses import dataclass, field
# from datetime import datetime
# @dataclass
# class CaseData:
#     case_id: str
#     client_name: str
#     accident_date: str
#     created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
from models.case_data import CaseData


class DatabaseManager:
    """SQLiteデータベース管理クラス (Simplified)"""
    
    def __init__(self, db_path: str = "compensation_cases.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        # Ensure logger is configured if you want to see output
        # logging.basicConfig(level=logging.INFO) 
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row 
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"データベース接続エラー: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_database(self) -> None:
        """データベースとテーブルの初期化 (Simplified)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Simplified 'cases' table
                # Using 'case_id' as the column name to match CaseData.case_id for simplicity here.
                # The original db_manager used 'case_number' for the column.
                # For this PoC, aligning with CaseData's field name directly in DB.
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cases (
                        case_id TEXT PRIMARY KEY,
                        client_name TEXT NOT NULL,
                        accident_date TEXT,
                        created_at TEXT NOT NULL
                    )
                ''')
                
                # Removed other tables (calculation_history, backup_records, settings) for simplification
                
                # Simplified Index
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_case_id ON cases(case_id)')
                
                conn.commit()
                self.logger.info(f"簡易データベースを初期化しました: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"簡易データベース初期化エラー: {e}")
            raise
    
    def save_case(self, case_data: CaseData) -> bool:
        """案件データを保存（新規作成・更新両対応 - Simplified）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if case_id exists to decide on INSERT or UPDATE
                cursor.execute('SELECT case_id FROM cases WHERE case_id = ?', (case_data.case_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    # Note: created_at should generally not be updated once set.
                    # Here, we are just re-saving all fields from CaseData.
                    cursor.execute('''
                        UPDATE cases SET
                            client_name = ?,
                            accident_date = ?,
                            created_at = ? 
                        WHERE case_id = ?
                    ''', (
                        case_data.client_name,
                        case_data.accident_date,
                        case_data.created_at, # Persist created_at from object
                        case_data.case_id
                    ))
                    self.logger.info(f"案件データを更新しました: {case_data.case_id}")
                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO cases (
                            case_id, client_name, accident_date, created_at
                        ) VALUES (?, ?, ?, ?)
                    ''', (
                        case_data.case_id,
                        case_data.client_name,
                        case_data.accident_date,
                        case_data.created_at
                    ))
                    self.logger.info(f"新規案件データを作成しました: {case_data.case_id}")
                
                conn.commit()
                return True
                
        except sqlite3.IntegrityError as e: # Handles PRIMARY KEY constraint failure
            self.logger.error(f"案件保存エラー (整合性): {case_data.case_id} - {e}")
            return False
        except Exception as e:
            self.logger.error(f"案件保存エラー: {case_data.case_id} - {e}")
            return False
            
    def load_case(self, case_id_to_load: str) -> Optional[CaseData]:
        """案件IDで案件データを読み込み (Simplified)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Fetching based on case_id (which is PRIMARY KEY)
                cursor.execute('SELECT * FROM cases WHERE case_id = ?', (case_id_to_load,))
                row = cursor.fetchone()
                
                if row:
                    # Reconstruct the simple CaseData object
                    return CaseData(
                        case_id=row['case_id'],
                        client_name=row['client_name'],
                        accident_date=row['accident_date'],
                        created_at=row['created_at']
                    )
        except Exception as e:
            self.logger.error(f"案件読み込みエラー: {case_id_to_load} - {e}")
        
        return None

    def search_cases(self, client_name_pattern: str = None, limit: int = 100) -> List[CaseData]:
        """案件検索 (Simplified - e.g., by client name)"""
        cases_list = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM cases'
                params = []
                if client_name_pattern:
                    query += ' WHERE client_name LIKE ?'
                    params.append(f'%{client_name_pattern}%')
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                for row in rows:
                    cases_list.append(CaseData(
                        case_id=row['case_id'],
                        client_name=row['client_name'],
                        accident_date=row['accident_date'],
                        created_at=row['created_at']
                    ))
        except Exception as e:
            self.logger.error(f"案件検索エラー: {e}")
        return cases_list

    def delete_case(self, case_id_to_delete: str) -> bool:
        """案件を削除 (Simplified)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cases WHERE case_id = ?', (case_id_to_delete,))
                conn.commit()
                if cursor.rowcount > 0:
                    self.logger.info(f"案件を削除しました: {case_id_to_delete}")
                    return True
                else:
                    self.logger.warning(f"削除対象の案件が見つかりません: {case_id_to_delete}")
                    return False
        except Exception as e:
            self.logger.error(f"案件削除エラー: {case_id_to_delete} - {e}")
            return False

    # Methods like create_backup and get_statistics would need significant simplification
    # or removal if they depend on the old complex schema. For now, they are omitted.
    # If kept, they should be reviewed for compatibility with the simplified 'cases' table.

# Example Usage (for direct testing of this simplified db_manager)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("Running simplified db_manager.py example usage...")
    
    # Use a test-specific database to avoid interfering with the main one
    test_db_manager = DatabaseManager(db_path="test_compensation_cases.db")

    # Ensure the table exists (init_database is called by constructor)
    # test_db_manager.init_database() # Already called in __init__

    # Create some CaseData objects
    case1 = CaseData(case_id="TEST001", client_name="Test User One", accident_date="2024-01-01")
    case2 = CaseData(case_id="TEST002", client_name="Test User Two", accident_date="2024-02-15", created_at="2024-02-15 10:00:00")

    # Save them
    print(f"Saving case {case1.case_id}: {'Success' if test_db_manager.save_case(case1) else 'Failed'}")
    print(f"Saving case {case2.case_id}: {'Success' if test_db_manager.save_case(case2) else 'Failed'}")

    # Try saving a duplicate - should update (or use specific logic for duplicates if preferred)
    case1_updated = CaseData(case_id="TEST001", client_name="Test User One (Updated)", accident_date="2024-01-02")
    print(f"Updating case {case1_updated.case_id}: {'Success' if test_db_manager.save_case(case1_updated) else 'Failed'}")

    # Load a specific case
    loaded_case = test_db_manager.load_case("TEST001")
    if loaded_case:
        print(f"Loaded case TEST001: {loaded_case}")
        assert loaded_case.client_name == "Test User One (Updated)"
    else:
        print("Case TEST001 not found.")

    # Load all cases
    all_cases = test_db_manager.search_cases()
    if all_cases:
        print(f"\nFound {len(all_cases)} cases:")
        for c in all_cases:
            print(c)
    else:
        print("No cases found.")

    # Delete a case
    print(f"Deleting case TEST002: {'Success' if test_db_manager.delete_case('TEST002') else 'Failed'}")
    deleted_case = test_db_manager.load_case("TEST002")
    assert deleted_case is None, "Case TEST002 should have been deleted"
    print("Case TEST002 successfully deleted and verified.")


    print("\nExample usage finished.")
    # Clean up the test database
    try:
        os.remove("test_compensation_cases.db")
        print("Test database 'test_compensation_cases.db' removed.")
    except OSError as e:
        print(f"Error removing test database: {e}")
```
