#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロフェッショナルUI設計計画

現在のTkinterベースのUIを大幅に改善し、実用的で美しいインターフェースを実現

改善戦略:
1. CustomTkinter導入による現代的デザイン
2. データ入力の効率化
3. リアルタイム計算・検証
4. 直感的なナビゲーション
5. 豊富な可視化機能
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
from datetime import datetime, date
from typing import Optional, Dict, Any, Callable
import threading
from decimal import Decimal

from models.case_data import CaseData
from calculation.compensation_engine import CompensationCalculationEngine
from database.db_manager import DatabaseManager

# CustomTkinterのテーマ設定
ctk.set_appearance_mode("light")  # "light" または "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class ModernCompensationCalculator:
    """次世代損害賠償計算システムUI"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.setup_window()
        self.init_components()
        self.create_modern_ui()
        
        # コンポーネント初期化
        self.calculation_engine = CompensationCalculationEngine()
        self.db_manager = DatabaseManager()
        self.current_case = CaseData()
        
        # リアルタイム計算フラグ
        self.auto_calculate = ctk.BooleanVar(value=True)
        self.calculation_timer = None
    
    def setup_window(self):
        """ウィンドウの基本設定"""
        self.root.title("弁護士基準損害賠償計算システム Pro")
        self.root.geometry("1400x900")
        
        # ウィンドウを中央に配置
        self.root.after(100, self.center_window)
        
        # アイコン設定（オプション）
        # self.root.iconbitmap("icon.ico")
    
    def center_window(self):
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def init_components(self):
        """UIコンポーネントの初期化"""
        # カラーテーマ
        self.colors = {
            'primary': '#2196F3',
            'primary_dark': '#1976D2',
            'secondary': '#4CAF50',
            'accent': '#FF9800',
            'error': '#F44336',
            'warning': '#FF5722',
            'success': '#4CAF50',
            'background': '#FAFAFA',
            'surface': '#FFFFFF',
            'text_primary': '#212121',
            'text_secondary': '#757575'
        }
        
        # フォント設定
        self.fonts = {
            'title': ctk.CTkFont(family="Meiryo UI", size=24, weight="bold"),
            'subtitle': ctk.CTkFont(family="Meiryo UI", size=18, weight="bold"),
            'body': ctk.CTkFont(family="Meiryo UI", size=14),
            'small': ctk.CTkFont(family="Meiryo UI", size=12),
            'large': ctk.CTkFont(family="Meiryo UI", size=16)
        }
    
    def create_modern_ui(self):
        """モダンUIの構築"""
        # メインコンテナ
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ヘッダー部分
        self.create_header()
        
        # メインコンテンツエリア
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # サイドバー（案件リスト・設定）
        self.create_sidebar()
        
        # メインパネル（タブエリア）
        self.create_main_panel()
        
        # ステータスバー
        self.create_status_bar()
    
    def create_header(self):
        """ヘッダーセクション"""
        header_frame = ctk.CTkFrame(self.main_container, height=80)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        # タイトル
        title_label = ctk.CTkLabel(
            header_frame,
            text="🏛️ 弁護士基準損害賠償計算システム Pro",
            font=self.fonts['title']
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        # ヘッダーボタン群
        header_buttons = ctk.CTkFrame(header_frame)
        header_buttons.pack(side="right", padx=20, pady=15)
        
        # 新規案件
        new_case_btn = ctk.CTkButton(
            header_buttons,
            text="📝 新規案件",
            command=self.new_case,
            width=100,
            font=self.fonts['body']
        )
        new_case_btn.pack(side="left", padx=5)
        
        # 保存
        save_btn = ctk.CTkButton(
            header_buttons,
            text="💾 保存",
            command=self.save_case,
            width=80,
            font=self.fonts['body']
        )
        save_btn.pack(side="left", padx=5)
        
        # 読み込み
        load_btn = ctk.CTkButton(
            header_buttons,
            text="📂 読み込み",
            command=self.load_case,
            width=100,
            font=self.fonts['body']
        )
        load_btn.pack(side="left", padx=5)
        
        # 設定
        settings_btn = ctk.CTkButton(
            header_buttons,
            text="⚙️ 設定",
            command=self.open_settings,
            width=80,
            font=self.fonts['body']
        )
        settings_btn.pack(side="left", padx=5)
    
    def create_sidebar(self):
        """サイドバー（案件リスト・クイック機能）"""
        # サイドバーは画面左側に配置
        self.sidebar = ctk.CTkFrame(self.content_frame, width=300)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        # サイドバータイトル
        sidebar_title = ctk.CTkLabel(
            self.sidebar,
            text="📋 案件管理",
            font=self.fonts['subtitle']
        )
        sidebar_title.pack(pady=15)
        
        # 検索フィールド
        search_frame = ctk.CTkFrame(self.sidebar)
        search_frame.pack(fill="x", padx=15, pady=10)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="案件番号・依頼者名で検索...",
            font=self.fonts['body']
        )
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        # 案件リスト
        self.case_list_frame = ctk.CTkScrollableFrame(self.sidebar, height=400)
        self.case_list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # クイック機能
        quick_frame = ctk.CTkFrame(self.sidebar)
        quick_frame.pack(fill="x", padx=15, pady=10)
        
        quick_title = ctk.CTkLabel(quick_frame, text="🚀 クイック機能", font=self.fonts['body'])
        quick_title.pack(pady=10)
        
        # リアルタイム計算トグル
        self.auto_calc_switch = ctk.CTkSwitch(
            quick_frame,
            text="リアルタイム計算",
            variable=self.auto_calculate,
            command=self.toggle_auto_calculate,
            font=self.fonts['small']
        )
        self.auto_calc_switch.pack(pady=5)
        
        # テンプレート機能
        template_btn = ctk.CTkButton(
            quick_frame,
            text="📋 テンプレート適用",
            command=self.apply_template,
            width=200,
            font=self.fonts['small']
        )
        template_btn.pack(pady=5)
        
        # 計算実行ボタン
        self.calculate_btn = ctk.CTkButton(
            quick_frame,
            text="🧮 計算実行",
            command=self.calculate_all,
            width=200,
            height=40,
            font=self.fonts['body'],
            fg_color=self.colors['secondary']
        )
        self.calculate_btn.pack(pady=10)
        
        # 案件リストを更新
        self.refresh_case_list()
    
    def create_main_panel(self):
        """メインパネル（入力・結果表示）"""
        self.main_panel = ctk.CTkFrame(self.content_frame)
        self.main_panel.pack(side="right", fill="both", expand=True)
        
        # タブビューの作成
        self.tabview = ctk.CTkTabview(self.main_panel)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 各タブの作成
        self.create_basic_info_tab()
        self.create_medical_tab()
        self.create_income_tab()
        self.create_results_tab()
        self.create_documents_tab()
    
    def create_basic_info_tab(self):
        """基本情報タブ（改良版）"""
        tab = self.tabview.add("📝 基本情報")
        
        # スクロール可能フレーム
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 案件情報セクション
        case_section = self.create_section(scroll_frame, "📋 案件情報")
        
        # 2列レイアウト
        left_col = ctk.CTkFrame(case_section)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_col = ctk.CTkFrame(case_section)
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # 左列
        self.case_number_entry = self.create_input_field(
            left_col, "案件番号 *", required=True,
            placeholder="例: 2024-001"
        )
        
        self.client_name_entry = self.create_input_field(
            left_col, "依頼者氏名 *", required=True,
            placeholder="姓名を入力"
        )
        
        self.accident_date_picker = self.create_date_picker(
            left_col, "事故発生日 *", required=True
        )
        
        # 右列
        self.victim_age_entry = self.create_input_field(
            right_col, "被害者年齢（事故時）", 
            placeholder="歳",
            input_type="number"
        )
        
        self.occupation_dropdown = self.create_dropdown(
            right_col, "職業",
            values=["給与所得者", "事業所得者", "家事従事者", "学生・生徒等", "無職・その他", "幼児・児童"]
        )
        
        self.symptom_fixed_date_picker = self.create_date_picker(
            right_col, "症状固定日"
        )
        
        # 過失・収入情報セクション
        fault_section = self.create_section(scroll_frame, "⚖️ 過失・収入情報")
        
        self.fault_percentage_entry = self.create_input_field(
            fault_section, "被害者過失割合",
            placeholder="%",
            input_type="number"
        )
        
        self.annual_income_entry = self.create_input_field(
            fault_section, "事故前年収（実収入）",
            placeholder="円",
            input_type="number"
        )
        
        self.gender_dropdown = self.create_dropdown(
            fault_section, "性別",
            values=["男性", "女性", "その他"]
        )
    
    def create_medical_tab(self):
        """医療情報タブ"""
        tab = self.tabview.add("🏥 医療情報")
        
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 入通院情報
        treatment_section = self.create_section(scroll_frame, "🏥 入通院情報")
        
        treatment_grid = ctk.CTkFrame(treatment_section)
        treatment_grid.pack(fill="x", pady=10)
        
        self.hospital_months_entry = self.create_input_field(
            treatment_grid, "入院期間", placeholder="ヶ月", input_type="number"
        )
        
        self.outpatient_months_entry = self.create_input_field(
            treatment_grid, "通院期間", placeholder="ヶ月", input_type="number"
        )
        
        self.actual_outpatient_days_entry = self.create_input_field(
            treatment_grid, "実通院日数", placeholder="日", input_type="number"
        )
        
        # むちうち症チェック
        self.whiplash_var = ctk.BooleanVar()
        whiplash_check = ctk.CTkCheckBox(
            treatment_section,
            text="むちうち症等（他覚症状なし）",
            variable=self.whiplash_var,
            font=self.fonts['body']
        )
        whiplash_check.pack(pady=10)
        
        # 後遺障害情報
        disability_section = self.create_section(scroll_frame, "♿ 後遺障害情報")
        
        self.disability_grade_dropdown = self.create_dropdown(
            disability_section, "後遺障害等級",
            values=["なし"] + [f"第{i}級" for i in range(1, 15)]
        )
        
        self.disability_details_text = ctk.CTkTextbox(
            disability_section,
            height=100,
            placeholder_text="後遺障害の詳細を入力..."
        )
        self.disability_details_text.pack(fill="x", pady=10)
        
        # 費用情報
        costs_section = self.create_section(scroll_frame, "💰 医療関係費")
        
        self.medical_expenses_entry = self.create_input_field(
            costs_section, "治療費", placeholder="円", input_type="number"
        )
        
        self.transportation_costs_entry = self.create_input_field(
            costs_section, "交通費", placeholder="円", input_type="number"
        )
        
        self.nursing_costs_entry = self.create_input_field(
            costs_section, "看護費", placeholder="円", input_type="number"
        )
    
    def create_income_tab(self):
        """収入・損害タブ"""
        tab = self.tabview.add("💰 収入・損害")
        
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 休業損害
        lost_income_section = self.create_section(scroll_frame, "📉 休業損害")
        
        self.lost_work_days_entry = self.create_input_field(
            lost_income_section, "休業日数", placeholder="日", input_type="number"
        )
        
        self.daily_income_entry = self.create_input_field(
            lost_income_section, "日額基礎収入", placeholder="円", input_type="number"
        )
        
        # 逸失利益
        future_loss_section = self.create_section(scroll_frame, "📊 後遺障害逸失利益")
        
        self.loss_period_entry = self.create_input_field(
            future_loss_section, "労働能力喪失期間", placeholder="年", input_type="number"
        )
        
        # 自動計算ボタン
        auto_calc_btn = ctk.CTkButton(
            future_loss_section,
            text="67歳まで自動計算",
            command=self.auto_calculate_loss_period,
            font=self.fonts['small']
        )
        auto_calc_btn.pack(pady=10)
        
        self.retirement_age_entry = self.create_input_field(
            future_loss_section, "就労可能年齢", placeholder="歳", input_type="number"
        )
        
        self.basic_annual_income_entry = self.create_input_field(
            future_loss_section, "基礎年収", placeholder="円", input_type="number"
        )
    
    def create_results_tab(self):
        """計算結果タブ"""
        tab = self.tabview.add("📊 計算結果")
        
        # 結果表示エリア
        self.results_frame = ctk.CTkScrollableFrame(tab)
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # エクスポートボタン
        export_frame = ctk.CTkFrame(tab, height=60)
        export_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        export_frame.pack_propagate(False)
        
        # PDF出力
        pdf_btn = ctk.CTkButton(
            export_frame,
            text="📄 PDF出力",
            command=self.export_pdf,
            width=120,
            font=self.fonts['body']
        )
        pdf_btn.pack(side="left", padx=10, pady=15)
        
        # Excel出力
        excel_btn = ctk.CTkButton(
            export_frame,
            text="📊 Excel出力",
            command=self.export_excel,
            width=120,
            font=self.fonts['body']
        )
        excel_btn.pack(side="left", padx=10, pady=15)
        
        # 印刷
        print_btn = ctk.CTkButton(
            export_frame,
            text="🖨️ 印刷",
            command=self.print_results,
            width=120,
            font=self.fonts['body']
        )
        print_btn.pack(side="left", padx=10, pady=15)
    
    def create_documents_tab(self):
        """書類管理タブ"""
        tab = self.tabview.add("📎 書類管理")
        
        # ファイル管理エリア
        files_frame = ctk.CTkScrollableFrame(tab)
        files_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ファイル操作ボタン
        file_ops_frame = ctk.CTkFrame(tab, height=60)
        file_ops_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        file_ops_frame.pack_propagate(False)
        
        upload_btn = ctk.CTkButton(
            file_ops_frame,
            text="📎 ファイル追加",
            command=self.upload_file,
            width=120,
            font=self.fonts['body']
        )
        upload_btn.pack(side="left", padx=10, pady=15)
    
    def create_status_bar(self):
        """ステータスバー"""
        self.status_bar = ctk.CTkFrame(self.main_container, height=30)
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.status_bar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="準備完了",
            font=self.fonts['small']
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # 最終更新時刻
        self.last_saved_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=self.fonts['small']
        )
        self.last_saved_label.pack(side="right", padx=10, pady=5)
    
    # ヘルパーメソッド
    def create_section(self, parent, title: str) -> ctk.CTkFrame:
        """セクションフレームを作成"""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=15)
        
        title_label = ctk.CTkLabel(section, text=title, font=self.fonts['subtitle'])
        title_label.pack(anchor="w", padx=15, pady=10)
        
        return section
    
    def create_input_field(self, parent, label: str, required: bool = False, 
                          placeholder: str = "", input_type: str = "text") -> ctk.CTkEntry:
        """入力フィールドを作成"""
        field_frame = ctk.CTkFrame(parent)
        field_frame.pack(fill="x", padx=15, pady=5)
        
        label_text = f"{label} {'*' if required else ''}"
        field_label = ctk.CTkLabel(field_frame, text=label_text, font=self.fonts['body'])
        field_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        entry = ctk.CTkEntry(
            field_frame,
            placeholder_text=placeholder,
            font=self.fonts['body']
        )
        entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # リアルタイム計算のトリガー
        if self.auto_calculate.get():
            entry.bind("<KeyRelease>", self.schedule_calculation)
        
        return entry
    
    def create_dropdown(self, parent, label: str, values: list) -> ctk.CTkComboBox:
        """ドロップダウンを作成"""
        field_frame = ctk.CTkFrame(parent)
        field_frame.pack(fill="x", padx=15, pady=5)
        
        field_label = ctk.CTkLabel(field_frame, text=label, font=self.fonts['body'])
        field_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        dropdown = ctk.CTkComboBox(
            field_frame,
            values=values,
            font=self.fonts['body']
        )
        dropdown.pack(fill="x", padx=10, pady=(0, 10))
        
        return dropdown
    
    def create_date_picker(self, parent, label: str, required: bool = False) -> Dict[str, ctk.CTkComboBox]:
        """日付選択を作成"""
        field_frame = ctk.CTkFrame(parent)
        field_frame.pack(fill="x", padx=15, pady=5)
        
        label_text = f"{label} {'*' if required else ''}"
        field_label = ctk.CTkLabel(field_frame, text=label_text, font=self.fonts['body'])
        field_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        date_frame = ctk.CTkFrame(field_frame)
        date_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # 年月日のドロップダウン
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 50, current_year + 5)]
        months = [f"{m:02}" for m in range(1, 13)]
        days = [f"{d:02}" for d in range(1, 32)]
        
        year_combo = ctk.CTkComboBox(date_frame, values=years, width=80)
        year_combo.pack(side="left", padx=(0, 5))
        
        month_combo = ctk.CTkComboBox(date_frame, values=months, width=60)
        month_combo.pack(side="left", padx=5)
        
        day_combo = ctk.CTkComboBox(date_frame, values=days, width=60)
        day_combo.pack(side="left", padx=5)
        
        return {"year": year_combo, "month": month_combo, "day": day_combo}
    
    # イベントハンドラー
    def schedule_calculation(self, event=None):
        """リアルタイム計算のスケジューリング"""
        if self.calculation_timer:
            self.root.after_cancel(self.calculation_timer)
        
        # 500ms後に計算実行（ユーザーの入力を待つ）
        self.calculation_timer = self.root.after(500, self.calculate_all)
    
    def toggle_auto_calculate(self):
        """リアルタイム計算のオン/オフ"""
        if self.auto_calculate.get():
            self.status_label.configure(text="リアルタイム計算: ON")
        else:
            self.status_label.configure(text="リアルタイム計算: OFF")
    
    # 案件管理メソッド
    def new_case(self):
        """新規案件作成"""
        self.current_case = CaseData()
        self.clear_all_inputs()
        self.status_label.configure(text="新規案件を作成しました")
    
    def save_case(self):
        """案件保存"""
        if self.validate_required_fields():
            self.update_case_data_from_ui()
            if self.db_manager.save_case(self.current_case):
                self.status_label.configure(text="案件を保存しました")
                self.refresh_case_list()
            else:
                messagebox.showerror("エラー", "案件の保存に失敗しました")
    
    def load_case(self):
        """案件読み込み"""
        # 案件選択ダイアログ（簡易版）
        case_number = ctk.CTkInputDialog(text="読み込む案件番号を入力してください:", title="案件読み込み").get_input()
        if case_number:
            case_data = self.db_manager.load_case(case_number)
            if case_data:
                self.current_case = case_data
                self.load_case_data_to_ui()
                self.status_label.configure(text=f"案件 {case_number} を読み込みました")
            else:
                messagebox.showerror("エラー", "指定された案件が見つかりません")
    
    def refresh_case_list(self):
        """案件リストの更新"""
        # 既存のウィジェットをクリア
        for widget in self.case_list_frame.winfo_children():
            widget.destroy()
        
        # 最新の案件リストを取得
        cases = self.db_manager.search_cases(limit=20)
        
        for case in cases:
            case_item = ctk.CTkFrame(self.case_list_frame)
            case_item.pack(fill="x", pady=2)
            
            case_label = ctk.CTkLabel(
                case_item,
                text=f"{case['case_number']}\n{case['client_name']}",
                font=self.fonts['small']
            )
            case_label.pack(side="left", padx=10, pady=5)
            
            load_btn = ctk.CTkButton(
                case_item,
                text="読込",
                width=50,
                command=lambda cn=case['case_number']: self.load_case_by_number(cn)
            )
            load_btn.pack(side="right", padx=10, pady=5)
    
    def load_case_by_number(self, case_number: str):
        """案件番号で案件を読み込み"""
        case_data = self.db_manager.load_case(case_number)
        if case_data:
            self.current_case = case_data
            self.load_case_data_to_ui()
            self.status_label.configure(text=f"案件 {case_number} を読み込みました")
    
    # データ操作メソッド
    def update_case_data_from_ui(self):
        """UIから案件データを更新"""
        # 基本情報
        self.current_case.case_number = self.case_number_entry.get()
        self.current_case.person_info.name = self.client_name_entry.get()
        self.current_case.person_info.age = int(self.victim_age_entry.get() or "0")
        # その他のフィールドも同様に更新...
    
    def load_case_data_to_ui(self):
        """案件データをUIに読み込み"""
        # 基本情報
        self.case_number_entry.delete(0, "end")
        self.case_number_entry.insert(0, self.current_case.case_number)
        
        self.client_name_entry.delete(0, "end")
        self.client_name_entry.insert(0, self.current_case.person_info.name)
        # その他のフィールドも同様に設定...
    
    def clear_all_inputs(self):
        """すべての入力をクリア"""
        # 全入力フィールドをクリア
        pass
    
    def validate_required_fields(self) -> bool:
        """必須フィールドの検証"""
        if not self.case_number_entry.get().strip():
            messagebox.showerror("入力エラー", "案件番号は必須です")
            return False
        
        if not self.client_name_entry.get().strip():
            messagebox.showerror("入力エラー", "依頼者氏名は必須です")
            return False
        
        return True
    
    # 計算・出力メソッド
    def calculate_all(self):
        """全項目計算"""
        try:
            self.update_case_data_from_ui()
            results = self.calculation_engine.calculate_all(self.current_case)
            self.display_results(results)
            self.status_label.configure(text="計算完了")
        except Exception as e:
            messagebox.showerror("計算エラー", f"計算中にエラーが発生しました: {str(e)}")
    
    def display_results(self, results: Dict[str, Any]):
        """計算結果の表示"""
        # 結果表示エリアをクリア
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # 各結果項目を表示
        for key, result in results.items():
            result_frame = ctk.CTkFrame(self.results_frame)
            result_frame.pack(fill="x", pady=10)
            
            title_label = ctk.CTkLabel(
                result_frame,
                text=result.item_name,
                font=self.fonts['subtitle']
            )
            title_label.pack(anchor="w", padx=15, pady=(10, 5))
            
            amount_label = ctk.CTkLabel(
                result_frame,
                text=f"¥{result.amount:,}",
                font=self.fonts['large']
            )
            amount_label.pack(anchor="w", padx=15, pady=5)
            
            details_text = ctk.CTkTextbox(result_frame, height=100)
            details_text.pack(fill="x", padx=15, pady=(5, 15))
            details_text.insert("1.0", result.calculation_details)
            details_text.configure(state="disabled")
    
    # その他のメソッド
    def on_search_change(self, event=None):
        """検索フィールドの変更時"""
        # 検索機能の実装
        pass
    
    def apply_template(self):
        """テンプレート適用"""
        # テンプレート機能の実装
        pass
    
    def auto_calculate_loss_period(self):
        """労働能力喪失期間の自動計算"""
        # 自動計算機能の実装
        pass
    
    def export_pdf(self):
        """PDF出力"""
        # PDF出力機能の実装
        pass
    
    def export_excel(self):
        """Excel出力"""
        # Excel出力機能の実装
        pass
    
    def print_results(self):
        """印刷"""
        # 印刷機能の実装
        pass
    
    def upload_file(self):
        """ファイルアップロード"""
        # ファイル管理機能の実装
        pass
    
    def open_settings(self):
        """設定画面を開く"""
        # 設定画面の実装
        pass
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

# 使用例
if __name__ == "__main__":
    app = ModernCompensationCalculator()
    app.run()
