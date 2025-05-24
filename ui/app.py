#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律事務所向け 弁護士基準損害賠償計算アプリケーション (改良版v2)
事務員の方でも使いやすい、シンプルで正確な計算ツール
UI/UX改善、過失相殺、弁護士費用概算、入力補助機能などを追加
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkFont
import datetime
from datetime import date, datetime # Ensure datetime is imported directly for strptime if used
import json # 将来的なデータ保存機能の拡張用
import os   # 現状未使用だが、将来的なファイル操作の可能性を考慮し残置

from reportlab.pdfgen import canvas as reportlab_canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import mm # PDF出力時の単位指定用

# Attempt to import CaseData, assuming models package is in PYTHONPATH or relative path works
try:
    from models.case_data import CaseData
except ImportError:
    # This is a fallback for scenarios where the module structure isn't perfectly recognized
    # by the execution environment. Ideally, the project structure and PYTHONPATH should handle this.
    print("Warning: Could not import CaseData from models.case_data. Using a dummy if needed.")
    # Define a dummy CaseData if the import fails, to allow basic UI loading
    from dataclasses import dataclass, field
    @dataclass
    class CaseData:
        case_id: str
        client_name: str
        accident_date: str
        created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class CompensationCalculator:
    # --- 定数定義 ---
    APP_TITLE = "弁護士基準 損害賠償計算システム Ver.2.0"
    FONT_FAMILY_DEFAULT = 'メイリオ' # Meiryo UIも候補
    FONT_SIZE_DEFAULT = 10
    FONT_SIZE_LARGE = 14
    FONT_SIZE_XLARGE = 18
    FONT_SIZE_BUTTON = 12
    FONT_SIZE_TEXT_AREA = 11

    COLOR_PRIMARY = '#3498db'    # 青系
    COLOR_SECONDARY = '#2ecc71'  # 緑系
    COLOR_DANGER = '#e74c3c'     # 赤系
    COLOR_WARNING = '#f39c12'   # オレンジ系
    COLOR_INFO = '#95a5a6'      # グレー系
    COLOR_BACKGROUND = '#ecf0f1' # 明るいグレー
    COLOR_TEXT_DARK = '#2c3e50'  # 濃い青グレー
    COLOR_TEXT_LIGHT = 'white'
    COLOR_DISABLED_BG = '#bdc3c7'

    YEAR_MAX_LEIBNIZ = 67 # ライプニッツ係数表の最大年数（例）
    DEFAULT_RETIREMENT_AGE = 67 # 標準的な就労可能年齢の上限

    LAWYER_FEE_TIERS_SAMPLE = [
        (3000000, 0.08, 0, 0.16, 0),
        (30000000, 0.05, 90000, 0.10, 180000),
        (300000000, 0.03, 690000, 0.06, 1380000),
        (float('inf'), 0.02, 3690000, 0.04, 7380000)
    ]

    def __init__(self, root, db_manager):
        self.root = root
        self.db_manager = db_manager
        self.root.title(self.APP_TITLE)
        self.root.geometry("1100x780")
        self.root.configure(bg=self.COLOR_BACKGROUND)
        self.root.option_add("*Font", (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT))

        self.initialize_styles()
        self.initialize_standards()
        self.create_main_ui()
        self.set_initial_focus()

    def initialize_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.COLOR_BACKGROUND, borderwidth=1)
        style.configure("TNotebook.Tab", background="#d0d0d0", foreground=self.COLOR_TEXT_DARK, padding=[12, 6], font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT + 1, 'bold'))
        style.map("TNotebook.Tab", background=[("selected", self.COLOR_PRIMARY)], foreground=[("selected", self.COLOR_TEXT_LIGHT)], expand=[("selected", [1, 1, 1, 0])])
        style.configure("TFrame", background=self.COLOR_BACKGROUND)
        style.configure("Content.TFrame", background='white', relief="solid", borderwidth=1)
        style.configure("TLabel", background=self.COLOR_BACKGROUND, foreground=self.COLOR_TEXT_DARK, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT))
        style.configure("Header.TLabel", font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_LARGE, 'bold'), foreground=self.COLOR_PRIMARY)
        style.configure("SubHeader.TLabel", font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT + 1, 'bold'), foreground=self.COLOR_TEXT_DARK)
        style.configure("Placeholder.TLabel", foreground='grey')
        style.configure("TEntry", font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT), padding=6, relief="solid", borderwidth=1)
        style.map("TEntry", bordercolor=[('focus', self.COLOR_PRIMARY)])
        style.configure("TButton", font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_BUTTON), padding=(10,6), borderwidth=1)
        style.map("TButton", background=[('active', self.COLOR_PRIMARY), ('!disabled', '#f0f0f0')], foreground=[('active', self.COLOR_TEXT_LIGHT), ('!disabled', self.COLOR_TEXT_DARK)], relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        style.configure("Primary.TButton", background=self.COLOR_PRIMARY, foreground=self.COLOR_TEXT_LIGHT)
        style.map("Primary.TButton", background=[('active', self.COLOR_SECONDARY)])
        style.configure("Success.TButton", background=self.COLOR_SECONDARY, foreground=self.COLOR_TEXT_LIGHT)
        style.map("Success.TButton", background=[('active', '#27ae60')])
        style.configure("Danger.TButton", background=self.COLOR_DANGER, foreground=self.COLOR_TEXT_LIGHT)
        style.map("Danger.TButton", background=[('active', '#c0392b')])
        style.configure("Info.TButton", background=self.COLOR_INFO, foreground=self.COLOR_TEXT_LIGHT)
        style.map("Info.TButton", background=[('active', '#7f8c8d')])
        style.configure("TCombobox", font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT), padding=6, relief="solid", borderwidth=1)
        self.root.option_add('*TCombobox*Listbox.font', (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT))
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.COLOR_PRIMARY)
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.COLOR_TEXT_LIGHT)
        style.configure("TLabelframe", background=self.COLOR_BACKGROUND, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_LARGE -1 , 'bold'), relief="groove", borderwidth=2, padding=15)
        style.configure("TLabelframe.Label", background=self.COLOR_BACKGROUND, foreground=self.COLOR_TEXT_DARK, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_LARGE - 2, 'bold'))
        style.configure("TCheckbutton", background=self.COLOR_BACKGROUND, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT))
        style.map("TCheckbutton", indicatorcolor=[('selected', self.COLOR_PRIMARY)])

    def initialize_standards(self):
        self.hospitalization_compensation_table_1 = {0: {0:0, 1:28, 2:52, 3:73, 4:90, 5:105, 6:116, 7:124, 8:132, 9:139, 10:145, 11:150, 12:154, 13:158, 14:162, 15:166}, 1: {0:53, 1:77, 2:98, 3:115, 4:130, 5:141, 6:150, 7:158, 8:164, 9:169, 10:174, 11:177, 12:181, 13:185, 14:189, 15:193}, 2: {0:101, 1:122, 2:140, 3:154, 4:167, 5:176, 6:183, 7:188, 8:193, 9:196, 10:199, 11:201, 12:204, 13:207, 14:210, 15:213}, 3: {0:145, 1:162, 2:177, 3:188, 4:197, 5:204, 6:209, 7:213, 8:216, 9:218, 10:221, 11:223, 12:225, 13:228, 14:231, 15:233}, 4: {0:165, 1:184, 2:198, 3:208, 4:216, 5:223, 6:228, 7:232, 8:235, 9:237, 10:239, 11:241, 12:243, 13:245, 14:247, 15:249}, 5: {0:183, 1:202, 2:215, 3:225, 4:233, 5:239, 6:244, 7:248, 8:250, 9:252, 10:254, 11:256, 12:258, 13:260, 14:262, 15:264}, 6: {0:199, 1:218, 2:230, 3:239, 4:246, 5:252, 6:257, 7:260, 8:262, 9:264, 10:266, 11:268, 12:270, 13:272, 14:274, 15:276}}
        self.hospitalization_compensation_table_2 = {k: {vk: round(vv * 0.67) for vk, vv in v.items()} for k, v in self.hospitalization_compensation_table_1.items()}
        self.disability_compensation_std = {1: 2800, 2: 2370, 3: 1990, 4: 1670, 5: 1400, 6: 1180, 7: 1000, 8: 830, 9: 690, 10: 550, 11: 420, 12: 290, 13: 180, 14: 110}
        self.disability_loss_rate_std = {1: 100, 2: 100, 3: 100, 4: 92, 5: 79, 6: 67, 7: 56, 8: 45, 9: 35, 10: 27, 11: 20, 12: 14, 13: 9, 14: 5}
        self.leibniz_coefficient_std = {i: round((1 - (1.03 ** -i)) / 0.03, 3) for i in range(1, self.YEAR_MAX_LEIBNIZ + 1)}
        leibniz_manual_override = {1: 0.971, 2: 1.913, 3: 2.829, 4: 3.717, 5: 4.580, 10: 8.530, 15: 11.938, 20: 14.877, 25: 17.413, 30: 19.600, 35: 21.487, 40: 23.115, 45: 24.519, 50: 25.730}
        self.leibniz_coefficient_std.update(leibniz_manual_override)

    def create_main_ui(self):
        title_frame = tk.Frame(self.root, bg=self.COLOR_TEXT_DARK, height=60); title_frame.pack(fill='x', pady=(0,5)); title_frame.pack_propagate(False)
        tk.Label(title_frame, text=self.APP_TITLE, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_XLARGE, 'bold'), fg=self.COLOR_TEXT_LIGHT, bg=self.COLOR_TEXT_DARK).pack(expand=True)
        self.notebook = ttk.Notebook(self.root, style="TNotebook"); self.notebook.pack(fill='both', expand=True, padx=15, pady=10)
        self.create_basic_info_tab(); self.create_hospitalization_tab(); self.create_disability_tab(); self.create_lost_income_tab(); self.create_result_tab()
        button_frame = ttk.Frame(self.root, style="TFrame", padding=(0,10,0,10)); button_frame.pack(fill='x', padx=15, pady=(5,15))
        ttk.Button(button_frame, text="計算実行", command=self.calculate_all, style="Primary.TButton", width=18).pack(side='left', padx=10)
        ttk.Button(button_frame, text="結果を保存 (.txt)", command=self.save_result, style="Success.TButton", width=18).pack(side='left', padx=10)
        ttk.Button(button_frame, text="PDF出力", command=self.export_pdf, style="Danger.TButton", width=18).pack(side='left', padx=10)
        ttk.Button(button_frame, text="データクリア", command=self.clear_data, style="Info.TButton", width=18).pack(side='right', padx=10)

    def _create_scrollable_frame_for_tab(self, parent_tab):
        outer_content_frame = ttk.Frame(parent_tab, style="Content.TFrame", padding=10); outer_content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        canvas = tk.Canvas(outer_content_frame, bg='white', highlightthickness=0); scrollbar = ttk.Scrollbar(outer_content_frame, orient="vertical", command=canvas.yview)
        scrollable_content_frame = ttk.Frame(canvas, style="TFrame", padding=(10,5)); scrollable_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_content_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        return scrollable_content_frame

    def _create_date_entry(self, parent, label_text, row, col_offset=0):
        ttk.Label(parent, text=label_text).grid(row=row, column=col_offset, sticky='w', padx=5, pady=6); date_frame = ttk.Frame(parent, style="TFrame"); date_frame.grid(row=row, column=col_offset + 1, sticky='w', padx=5, pady=2)
        current_year = datetime.today().year; years = [str(y) for y in range(current_year - 100, current_year + 5)]; months = [f"{m:02}" for m in range(1, 13)]; days = [f"{d:02}" for d in range(1, 32)]
        year_cb = ttk.Combobox(date_frame, values=years, width=6, state="readonly"); year_cb.pack(side='left', padx=(0,2)); ttk.Label(date_frame, text="年", background='white').pack(side='left', padx=(0,5))
        month_cb = ttk.Combobox(date_frame, values=months, width=4, state="readonly"); month_cb.pack(side='left', padx=(0,2)); ttk.Label(date_frame, text="月", background='white').pack(side='left', padx=(0,5))
        day_cb = ttk.Combobox(date_frame, values=days, width=4, state="readonly"); day_cb.pack(side='left', padx=(0,2)); ttk.Label(date_frame, text="日", background='white').pack(side='left')
        return year_cb, month_cb, day_cb

    def _get_date_from_entries(self, y_cb, m_cb, d_cb):
        y, m, d = y_cb.get(), m_cb.get(), d_cb.get()
        if y and m and d:
            try: return date(int(y), int(m), int(d)).strftime("%Y-%m-%d")
            except ValueError: return None
        return None

    def _set_date_entries(self, y_cb, m_cb, d_cb, date_str=None):
        if date_str:
            try: dt_obj = datetime.strptime(date_str, "%Y-%m-%d").date(); y_cb.set(str(dt_obj.year)); m_cb.set(f"{dt_obj.month:02}"); d_cb.set(f"{dt_obj.day:02}"); return
            except (ValueError, TypeError): pass
        y_cb.set(''); m_cb.set(''); d_cb.set('')

    def create_basic_info_tab(self):
        tab_frame = ttk.Frame(self.notebook, style="TFrame", padding=5); self.notebook.add(tab_frame, text=" 📝 基本情報 ")
        content_frame = self._create_scrollable_frame_for_tab(tab_frame)
        ttk.Label(content_frame, text="案件基本情報", style="Header.TLabel").grid(row=0, column=0, columnspan=4, pady=(0,20), sticky='w')
        ttk.Label(content_frame, text="案件番号:").grid(row=1, column=0, sticky='w', padx=5, pady=6); self.case_number = ttk.Entry(content_frame, width=28); self.case_number.grid(row=1, column=1, padx=5, pady=6)
        col_offset = 2; ttk.Label(content_frame, text="依頼者氏名:").grid(row=1, column=col_offset, sticky='w', padx=15, pady=6); self.client_name = ttk.Entry(content_frame, width=28); self.client_name.grid(row=1, column=col_offset + 1, padx=5, pady=6)
        self.accident_date_year, self.accident_date_month, self.accident_date_day = self._create_date_entry(content_frame, "事故発生日:", 2, 0)
        self.symptom_fixed_date_year, self.symptom_fixed_date_month, self.symptom_fixed_date_day = self._create_date_entry(content_frame, "症状固定日:", 2, col_offset)
        ttk.Label(content_frame, text="被害者年齢(事故時):").grid(row=3, column=0, sticky='w', padx=5, pady=6); self.victim_age = ttk.Entry(content_frame, width=10); self.victim_age.grid(row=3, column=1, sticky='w', padx=5, pady=6); self.victim_age.insert(0, "0"); ttk.Label(content_frame, text="歳", background='white').grid(row=3, column=1, sticky='e', padx=(0,100))
        ttk.Label(content_frame, text="性別:").grid(row=3, column=col_offset, sticky='w', padx=15, pady=6); self.victim_gender = ttk.Combobox(content_frame, values=["男性", "女性", "その他/不明"], width=15, state="readonly"); self.victim_gender.grid(row=3, column=col_offset + 1, sticky='w', padx=5, pady=6)
        ttk.Label(content_frame, text="職業:").grid(row=4, column=0, sticky='w', padx=5, pady=6); self.occupation = ttk.Combobox(content_frame, values=["給与所得者", "事業所得者", "家事従事者", "学生・生徒等", "無職・その他", "幼児・児童"], width=26, state="readonly"); self.occupation.grid(row=4, column=1, padx=5, pady=6)
        ttk.Label(content_frame, text="事故前年収(実収入):").grid(row=4, column=col_offset, sticky='w', padx=15, pady=6); self.annual_income = ttk.Entry(content_frame, width=18); self.annual_income.grid(row=4, column=col_offset + 1, sticky='w', padx=5, pady=6); self.annual_income.insert(0, "0"); ttk.Label(content_frame, text="円", background='white').grid(row=4, column=col_offset+1, sticky='e', padx=(0,60))
        ttk.Label(content_frame, text="被害者の過失割合:").grid(row=5, column=0, sticky='w', padx=5, pady=6); self.victim_fault_percentage = ttk.Entry(content_frame, width=10); self.victim_fault_percentage.grid(row=5, column=1, sticky='w', padx=5, pady=6); self.victim_fault_percentage.insert(0, "0"); ttk.Label(content_frame, text="%", background='white').grid(row=5, column=1, sticky='e', padx=(0,100))
        
        db_test_lf_row = 6; db_test_frame = ttk.LabelFrame(content_frame, text="データベース連携テスト", padding=(10, 5)); db_test_frame.grid(row=db_test_lf_row, column=0, columnspan=4, sticky="ew", pady=(20,10), padx=5)
        current_db_test_row = 0
        ttk.Label(db_test_frame, text="テスト用 案件ID:").grid(row=current_db_test_row, column=0, sticky="w", padx=5, pady=3); self.test_case_id_entry = ttk.Entry(db_test_frame, width=40); self.test_case_id_entry.grid(row=current_db_test_row, column=1, sticky="ew", padx=5, pady=3); current_db_test_row += 1
        ttk.Label(db_test_frame, text="テスト用 依頼者名:").grid(row=current_db_test_row, column=0, sticky="w", padx=5, pady=3); self.test_client_name_entry = ttk.Entry(db_test_frame, width=40); self.test_client_name_entry.grid(row=current_db_test_row, column=1, sticky="ew", padx=5, pady=3); current_db_test_row += 1
        ttk.Label(db_test_frame, text="テスト用 事故発生日 (YYYY-MM-DD):").grid(row=current_db_test_row, column=0, sticky="w", padx=5, pady=3); self.test_accident_date_entry = ttk.Entry(db_test_frame, width=40); self.test_accident_date_entry.grid(row=current_db_test_row, column=1, sticky="ew", padx=5, pady=3); current_db_test_row += 1
        db_button_frame = ttk.Frame(db_test_frame); db_button_frame.grid(row=current_db_test_row, column=0, columnspan=2, pady=(10,5), sticky="w")
        self.test_save_button = ttk.Button(db_button_frame, text="保存テスト", command=self._test_save_case_data); self.test_save_button.pack(side="left", padx=5)
        self.test_load_button = ttk.Button(db_button_frame, text="読み込みテスト", command=self._test_load_case_data); self.test_load_button.pack(side="left", padx=5); current_db_test_row += 1 # Command added
        self.test_result_label = ttk.Label(db_test_frame, text="結果表示エリア"); self.test_result_label.grid(row=current_db_test_row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        db_test_frame.columnconfigure(1, weight=1)

    def _test_save_case_data(self):
        case_id = self.test_case_id_entry.get()
        client_name = self.test_client_name_entry.get()
        accident_date = self.test_accident_date_entry.get()

        if not case_id:
            self.test_result_label.config(text="エラー: 案件IDは必須です。", foreground="red")
            messagebox.showerror("保存エラー", "案件IDを入力してください。")
            return

        if accident_date: # Only validate if not empty
            try: 
                datetime.strptime(accident_date, "%Y-%m-%d")
            except ValueError:
                self.test_result_label.config(text="エラー: 事故発生日の形式が無効です (YYYY-MM-DD)。", foreground="red")
                messagebox.showerror("保存エラー", "事故発生日は YYYY-MM-DD 形式で入力してください。")
                return
        else: # If accident_date is empty, treat as acceptable (e.g., set to None or empty string for DB)
            accident_date = "" # Or None, depending on DB schema and CaseData handling

        new_case = CaseData(
            case_id=case_id,
            client_name=client_name,
            accident_date=accident_date
        )

        try:
            success = self.db_manager.save_case(new_case) 
            if success:
                self.test_result_label.config(text=f"案件 {case_id} を保存しました。", foreground="green")
                messagebox.showinfo("保存成功", f"案件 {case_id} をデータベースに保存しました。")
            else:
                self.test_result_label.config(text=f"エラー: 案件 {case_id} の保存に失敗しました。", foreground="red")
                messagebox.showerror("保存失敗", f"案件 {case_id} の保存に失敗しました。重複IDの可能性があります。")
        except AttributeError as ae: 
             self.test_result_label.config(text=f"属性エラー: {str(ae)}. CaseData構造とDBスキーマの不一致の可能性。", foreground="red")
             messagebox.showerror("保存属性エラー", f"保存中に属性エラーが発生しました: {str(ae)}\nCaseDataの構造とDBの期待するスキーマが一致していない可能性があります。")
        except Exception as e: 
            self.test_result_label.config(text=f"エラー: 保存中に例外発生 - {type(e).__name__}: {str(e)}", foreground="red")
            messagebox.showerror("保存例外", f"保存中に予期せぬエラーが発生しました: {type(e).__name__}: {str(e)}")

    def _test_load_case_data(self):
        case_id = self.test_case_id_entry.get()

        if not case_id:
            self.test_result_label.config(text="エラー: 案件IDを入力してください。", foreground="red")
            messagebox.showerror("読み込みエラー", "読み込む案件IDを入力してください。")
            return

        try:
            case_data = self.db_manager.load_case(case_id)

            if case_data:
                self.test_result_label.config(
                    text=f"読込: ID={case_data.case_id},依頼者={case_data.client_name},事故日={case_data.accident_date},作成日={case_data.created_at}",
                    foreground="blue"
                )
                # Populate the fields:
                self.test_client_name_entry.delete(0, tk.END)
                self.test_client_name_entry.insert(0, case_data.client_name)
                self.test_accident_date_entry.delete(0, tk.END)
                self.test_accident_date_entry.insert(0, case_data.accident_date)
                # self.test_case_id_entry can remain as is, or be cleared if desired
                messagebox.showinfo("読み込み成功", f"案件 {case_id} の情報を読み込みました。")
            else:
                self.test_result_label.config(text=f"エラー: 案件ID {case_id} が見つかりません。", foreground="orange")
                # Clear other fields if not found
                self.test_client_name_entry.delete(0, tk.END)
                self.test_accident_date_entry.delete(0, tk.END)
                messagebox.showwarning("読み込み失敗", f"案件ID {case_id} はデータベース内に見つかりませんでした。")
        except Exception as e:
            self.test_result_label.config(text=f"エラー: 読み込み中に例外発生 - {type(e).__name__}: {str(e)}", foreground="red")
            messagebox.showerror("読み込み例外", f"読み込み中に予期せぬエラーが発生しました: {type(e).__name__}: {str(e)}")


    def create_hospitalization_tab(self):
        tab_frame = ttk.Frame(self.notebook, style="TFrame", padding=5); self.notebook.add(tab_frame, text=" 🏥 入通院慰謝料 ")
        content_frame = self._create_scrollable_frame_for_tab(tab_frame)
        ttk.Label(content_frame, text="入通院慰謝料 計算", style="Header.TLabel").pack(pady=(0,20), anchor='w')
        input_area = ttk.Frame(content_frame, style="TFrame"); input_area.pack(fill='x', pady=10); field_frame = ttk.Frame(input_area, style="TFrame"); field_frame.pack()
        ttk.Label(field_frame, text="入院期間:").grid(row=0, column=0, sticky='e', padx=5, pady=8); self.hospital_months = ttk.Entry(field_frame, width=8, justify='right'); self.hospital_months.grid(row=0, column=1, padx=5, pady=8); self.hospital_months.insert(0, "0"); ttk.Label(field_frame, text="ヶ月", background='white').grid(row=0, column=2, sticky='w', padx=5)
        ttk.Label(field_frame, text="通院期間:").grid(row=1, column=0, sticky='e', padx=5, pady=8); self.outpatient_months = ttk.Entry(field_frame, width=8, justify='right'); self.outpatient_months.grid(row=1, column=1, padx=5, pady=8); self.outpatient_months.insert(0, "0"); ttk.Label(field_frame, text="ヶ月", background='white').grid(row=1, column=2, sticky='w', padx=5)
        ttk.Label(field_frame, text="実通院日数(参考):").grid(row=2, column=0, sticky='e', padx=5, pady=8); self.actual_outpatient_days = ttk.Entry(field_frame, width=8, justify='right'); self.actual_outpatient_days.grid(row=2, column=1, padx=5, pady=8); self.actual_outpatient_days.insert(0, "0"); ttk.Label(field_frame, text="日", background='white').grid(row=2, column=2, sticky='w', padx=5)
        self.whiplash_var = tk.BooleanVar(); ttk.Checkbutton(field_frame, text="むちうち症等（他覚所見なし）で、別表IIを適用する", variable=self.whiplash_var, style="TCheckbutton").grid(row=3, column=0, columnspan=3, sticky='w', pady=15, padx=5)
        result_display_frame = ttk.LabelFrame(content_frame, text="このタブの計算結果", style="TLabelframe"); result_display_frame.pack(fill='both', expand=True, padx=0, pady=15)
        self.hospital_result_text = tk.Text(result_display_frame, height=10, width=70, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_TEXT_AREA -1), relief="flat", bd=0, wrap=tk.WORD, background='#fdfdfd'); self.hospital_result_text.pack(fill='both', expand=True, padx=5, pady=5); self.hospital_result_text.insert(tk.END, "計算実行ボタンを押すと、ここに結果が表示されます。"); self.hospital_result_text.configure(state='disabled')

    def create_disability_tab(self):
        tab_frame = ttk.Frame(self.notebook, style="TFrame", padding=5); self.notebook.add(tab_frame, text=" ♿ 後遺障害 ")
        content_frame = self._create_scrollable_frame_for_tab(tab_frame)
        ttk.Label(content_frame, text="後遺障害関連 計算", style="Header.TLabel").pack(pady=(0,20), anchor='w')
        input_area = ttk.Frame(content_frame, style="TFrame"); input_area.pack(fill='x', pady=10); field_frame = ttk.Frame(input_area, style="TFrame"); field_frame.pack()
        ttk.Label(field_frame, text="後遺障害等級:").grid(row=0, column=0, sticky='e', padx=5, pady=8); self.disability_grade = ttk.Combobox(field_frame, values=["なし"] + [f"第{i}級" for i in range(1, 15)], width=15, state="readonly"); self.disability_grade.grid(row=0, column=1, padx=5, pady=8); self.disability_grade.set("なし")
        result_display_frame = ttk.LabelFrame(content_frame, text="このタブの計算結果", style="TLabelframe"); result_display_frame.pack(fill='both', expand=True, padx=0, pady=15)
        self.disability_result_text = tk.Text(result_display_frame, height=12, width=70, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_TEXT_AREA -1), relief="flat", bd=0, wrap=tk.WORD, background='#fdfdfd'); self.disability_result_text.pack(fill='both', expand=True, padx=5, pady=5); self.disability_result_text.insert(tk.END, "計算実行ボタンを押すと、ここに結果が表示されます。"); self.disability_result_text.configure(state='disabled')

    def create_lost_income_tab(self):
        tab_frame = ttk.Frame(self.notebook, style="TFrame", padding=5); self.notebook.add(tab_frame, text=" 📉 休業損害・逸失利益 ")
        content_frame = self._create_scrollable_frame_for_tab(tab_frame)
        lost_income_lf = ttk.LabelFrame(content_frame, text="休業損害", style="TLabelframe"); lost_income_lf.pack(fill='x', padx=0, pady=(0,15))
        ttk.Label(lost_income_lf, text="休業日数:").grid(row=0, column=0, sticky='e', padx=5, pady=8); self.lost_work_days = ttk.Entry(lost_income_lf, width=10, justify='right'); self.lost_work_days.grid(row=0, column=1, padx=5, pady=8); self.lost_work_days.insert(0, "0"); ttk.Label(lost_income_lf, text="日").grid(row=0, column=2, sticky='w', padx=5)
        ttk.Label(lost_income_lf, text="日額基礎収入:").grid(row=1, column=0, sticky='e', padx=5, pady=8); self.daily_income = ttk.Entry(lost_income_lf, width=15, justify='right'); self.daily_income.grid(row=1, column=1, padx=5, pady=8); self.daily_income.insert(0, "0"); ttk.Label(lost_income_lf, text="円").grid(row=1, column=2, sticky='w', padx=5); ttk.Label(lost_income_lf, text="(事故前3ヶ月間の実収入 ÷ 90日など)", style="Placeholder.TLabel").grid(row=1, column=3, sticky='w', padx=5)
        future_income_lf = ttk.LabelFrame(content_frame, text="後遺障害逸失利益", style="TLabelframe"); future_income_lf.pack(fill='x', padx=0, pady=10)
        ttk.Label(future_income_lf, text="労働能力喪失期間:").grid(row=0, column=0, sticky='e', padx=5, pady=8); self.loss_period = ttk.Entry(future_income_lf, width=10, justify='right'); self.loss_period.grid(row=0, column=1, padx=5, pady=8); self.loss_period.insert(0, "0"); ttk.Label(future_income_lf, text="年").grid(row=0, column=2, sticky='w', padx=5)
        calc_loss_period_button = ttk.Button(future_income_lf, text=f"{self.DEFAULT_RETIREMENT_AGE}歳までを自動計算", command=self.auto_calculate_loss_period, style="Info.TButton", width=20); calc_loss_period_button.grid(row=0, column=3, padx=10, pady=5, sticky='w'); ttk.Label(future_income_lf, text=f"(症状固定時年齢を基本情報タブに入力)", style="Placeholder.TLabel").grid(row=0, column=4, sticky='w', padx=5)
        result_display_frame = ttk.LabelFrame(content_frame, text="このタブの計算結果", style="TLabelframe"); result_display_frame.pack(fill='both', expand=True, padx=0, pady=15)
        self.income_result_text = tk.Text(result_display_frame, height=15, width=70, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_TEXT_AREA -1), relief="flat", bd=0, wrap=tk.WORD, background='#fdfdfd'); self.income_result_text.pack(fill='both', expand=True, padx=5, pady=5); self.income_result_text.insert(tk.END, "計算実行ボタンを押すと、ここに結果が表示されます。"); self.income_result_text.configure(state='disabled')

    def auto_calculate_loss_period(self):
        try:
            age_at_symptom_fix_str = self.victim_age.get() 
            if not age_at_symptom_fix_str: messagebox.showwarning("入力不足", "基本情報タブの「被害者年齢」を入力してください。"); self.notebook.select(0); self.victim_age.focus(); return
            age_at_symptom_fix = int(age_at_symptom_fix_str)
            if not (0 <= age_at_symptom_fix <= 120): messagebox.showwarning("入力エラー", "被害者年齢が不正です。"); return
            remaining_work_years = self.DEFAULT_RETIREMENT_AGE - age_at_symptom_fix
            if remaining_work_years < 0: remaining_work_years = 0
            self.loss_period.delete(0, tk.END); self.loss_period.insert(0, str(remaining_work_years))
            messagebox.showinfo("自動計算完了", f"労働能力喪失期間を {remaining_work_years} 年としてセットしました。\n（{self.DEFAULT_RETIREMENT_AGE}歳 - {age_at_symptom_fix}歳）\n※これは目安です。個別の事案に応じて調整してください。")
        except ValueError: messagebox.showerror("入力エラー", "基本情報タブの「被害者年齢」を正しい数値で入力してください。"); self.notebook.select(0); self.victim_age.focus()
        except Exception as e: messagebox.showerror("エラー", f"自動計算中にエラーが発生しました: {str(e)}")

    def create_result_tab(self):
        tab_frame = ttk.Frame(self.notebook, style="TFrame", padding=5); self.notebook.add(tab_frame, text=" 📊 総合結果 ")
        content_frame = self._create_scrollable_frame_for_tab(tab_frame)
        ttk.Label(content_frame, text="損害賠償額 総合計算結果", style="Header.TLabel").pack(pady=(0,15), anchor='w')
        text_widget_frame = ttk.Frame(content_frame, style="TFrame"); text_widget_frame.pack(fill="both", expand=True, padx=0, pady=5)
        self.total_result_text = tk.Text(text_widget_frame, height=28, width=90, font=(self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_TEXT_AREA), relief="solid", bd=1, wrap=tk.WORD, background="#ffffff", foreground=self.COLOR_TEXT_DARK, padx=10, pady=10)
        scrollbar_total_result = ttk.Scrollbar(text_widget_frame, orient="vertical", command=self.total_result_text.yview); self.total_result_text.configure(yscrollcommand=scrollbar_total_result.set)
        self.total_result_text.pack(side="left", fill="both", expand=True); scrollbar_total_result.pack(side="right", fill="y")
        self.total_result_text.insert(tk.END, "計算実行ボタンを押すと、ここに総合結果が表示されます。"); self.total_result_text.configure(state='disabled')

    def set_initial_focus(self): self.case_number.focus_set()
    def _get_int_value_from_entry(self, entry_widget, default=0):
        try: val_str = entry_widget.get().strip(); return default if not val_str else int(val_str)
        except ValueError: return default

    def _validate_date_inputs(self):
        acc_y, acc_m, acc_d = self.accident_date_year.get(), self.accident_date_month.get(), self.accident_date_day.get()
        if not (acc_y and acc_m and acc_d): messagebox.showwarning("入力エラー", "基本情報タブの「事故発生日」をすべて選択してください。"); self.notebook.select(0); self.accident_date_year.focus(); return False
        try: date(int(acc_y), int(acc_m), int(acc_d))
        except ValueError: messagebox.showwarning("入力エラー", "基本情報タブの「事故発生日」が不正な日付です。"); self.notebook.select(0); self.accident_date_year.focus(); return False
        sym_y, sym_m, sym_d = self.symptom_fixed_date_year.get(), self.symptom_fixed_date_month.get(), self.symptom_fixed_date_day.get()
        if sym_y or sym_m or sym_d:
            if not (sym_y and sym_m and sym_d): messagebox.showwarning("入力エラー", "基本情報タブの「症状固定日」は年月日をすべて選択するか、すべて空にしてください。"); self.notebook.select(0); self.symptom_fixed_date_year.focus(); return False
            try: date(int(sym_y), int(sym_m), int(sym_d))
            except ValueError: messagebox.showwarning("入力エラー", "基本情報タブの「症状固定日」が不正な日付です。"); self.notebook.select(0); self.symptom_fixed_date_year.focus(); return False
        return True

    def validate_all_inputs(self):
        if not self.case_number.get().strip(): messagebox.showwarning("入力エラー", "基本情報タブの「案件番号」を入力してください。"); self.notebook.select(0); self.case_number.focus(); return False
        if not self.client_name.get().strip(): messagebox.showwarning("入力エラー", "基本情報タブの「依頼者氏名」を入力してください。"); self.notebook.select(0); self.client_name.focus(); return False
        if not self._validate_date_inputs(): return False
        age_str = self.victim_age.get().strip();
        if not age_str or not age_str.isdigit() or not (0 <= int(age_str) <= 120): messagebox.showwarning("入力エラー", "基本情報タブの「被害者年齢」は0～120の数値を入力してください。"); self.notebook.select(0); self.victim_age.focus(); return False
        income_str = self.annual_income.get().strip()
        if not income_str or not income_str.isdigit() or int(income_str) < 0: messagebox.showwarning("入力エラー", "基本情報タブの「事故前年収」は0以上の数値を入力してください。"); self.notebook.select(0); self.annual_income.focus(); return False
        fault_str = self.victim_fault_percentage.get().strip()
        if not fault_str or not fault_str.isdigit() or not (0 <= int(fault_str) <= 100): messagebox.showwarning("入力エラー", "基本情報タブの「被害者の過失割合」は0～100の数値を入力してください。"); self.notebook.select(0); self.victim_fault_percentage.focus(); return False
        h_months_str = self.hospital_months.get().strip()
        if not h_months_str or not h_months_str.isdigit() or int(h_months_str) < 0: messagebox.showwarning("入力エラー", "入通院慰謝料タブの「入院期間」は0以上の数値を入力してください。"); self.notebook.select(1); self.hospital_months.focus(); return False
        o_months_str = self.outpatient_months.get().strip()
        if not o_months_str or not o_months_str.isdigit() or int(o_months_str) < 0: messagebox.showwarning("入力エラー", "入通院慰謝料タブの「通院期間」は0以上の数値を入力してください。"); self.notebook.select(1); self.outpatient_months.focus(); return False
        a_days_str = self.actual_outpatient_days.get().strip()
        if not a_days_str or not a_days_str.isdigit() or int(a_days_str) < 0: messagebox.showwarning("入力エラー", "入通院慰謝料タブの「実通院日数」は0以上の数値を入力してください。"); self.notebook.select(1); self.actual_outpatient_days.focus(); return False
        lost_days_str = self.lost_work_days.get().strip()
        if not lost_days_str or not lost_days_str.isdigit() or int(lost_days_str) < 0: messagebox.showwarning("入力エラー", "休業損害タブの「休業日数」は0以上の数値を入力してください。"); self.notebook.select(3); self.lost_work_days.focus(); return False
        daily_inc_str = self.daily_income.get().strip()
        if not daily_inc_str or not daily_inc_str.isdigit() or int(daily_inc_str) < 0: messagebox.showwarning("入力エラー", "休業損害タブの「日額基礎収入」は0以上の数値を入力してください。"); self.notebook.select(3); self.daily_income.focus(); return False
        loss_period_str = self.loss_period.get().strip()
        if not loss_period_str or not loss_period_str.isdigit() or int(loss_period_str) < 0: messagebox.showwarning("入力エラー", "逸失利益タブの「労働能力喪失期間」は0以上の数値を入力してください。"); self.notebook.select(3); self.loss_period.focus(); return False
        return True

    def calculate_all(self):
        if not self.validate_all_inputs(): return
        try:
            hospital_comp_data = self.calculate_hospitalization_compensation(); disability_comp_data = self.calculate_disability_compensation()
            lost_income_data = self.calculate_lost_income(); future_loss_data = self.calculate_future_income_loss(disability_comp_data['loss_rate_percent'])
            self.display_individual_tab_results(hospital_comp_data, disability_comp_data, lost_income_data, future_loss_data)
            self.display_total_result_summary(hospital_comp_data, disability_comp_data, lost_income_data, future_loss_data)
            self.notebook.select(4); messagebox.showinfo("計算完了", "計算が完了しました。各タブおよび総合結果タブをご確認ください。")
        except Exception as e: messagebox.showerror("計算エラー", f"計算中に予期せぬエラーが発生しました:\n{type(e).__name__}: {str(e)}")

    def calculate_hospitalization_compensation(self):
        h_months, o_months, actual_o_days = self._get_int_value_from_entry(self.hospital_months), self._get_int_value_from_entry(self.outpatient_months), self._get_int_value_from_entry(self.actual_outpatient_days)
        table_to_use, table_name_display = (self.hospitalization_compensation_table_2, "別表II (むちうち等他覚所見なし)") if self.whiplash_var.get() else (self.hospitalization_compensation_table_1, "別表I (通常)")
        clamped_h_months = min(h_months, max(table_to_use.keys())); max_o_months_for_clamped_h = max(table_to_use[clamped_h_months].keys()) if clamped_h_months in table_to_use else 0; clamped_o_months = min(o_months, max_o_months_for_clamped_h)
        base_amount_万, basis_text = 0, f"入院{h_months}ヶ月、通院{o_months}ヶ月"
        if clamped_h_months in table_to_use and clamped_o_months in table_to_use[clamped_h_months]: base_amount_万 = table_to_use[clamped_h_months][clamped_o_months];
        if (h_months > max(table_to_use.keys()) or o_months > max_o_months_for_clamped_h) and base_amount_万 > 0 : basis_text += f" (表上限: 入院{clamped_h_months}ヶ月, 通院{clamped_o_months}ヶ月で計算)"
        elif h_months == 0 and o_months == 0: basis_text = "入院・通院なし"
        elif base_amount_万 == 0 : # Covers cases where combination is not in table or values are zero
            if h_months == 0 and o_months > 0 and 0 in table_to_use and clamped_o_months in table_to_use[0]: base_amount_万 = table_to_use[0][clamped_o_months]
            elif h_months > 0 and o_months == 0 and clamped_h_months in table_to_use and 0 in table_to_use[clamped_h_months]: base_amount_万 = table_to_use[clamped_h_months][0]
            else: basis_text += " (表に該当なしまたは0円)"
        return {'amount_yen': base_amount_万 * 10000, 'basis_text': basis_text, 'table_name_display': table_name_display, 'h_months': h_months, 'o_months': o_months, 'actual_o_days': actual_o_days}

    def calculate_disability_compensation(self):
        grade_selection = self.disability_grade.get();
        if grade_selection == "なし" or not grade_selection: return {'amount_yen': 0, 'grade_text_display': 'なし', 'loss_rate_percent': 0, 'grade_num': 0}
        try: grade_num = int(grade_selection.replace("第", "").replace("級", ""))
        except ValueError: return {'amount_yen': 0, 'grade_text_display': '無効な等級', 'loss_rate_percent': 0, 'grade_num': 0}
        amount_万, loss_rate = self.disability_compensation_std.get(grade_num, 0), self.disability_loss_rate_std.get(grade_num, 0)
        return {'amount_yen': amount_万 * 10000, 'grade_text_display': f"第{grade_num}級", 'loss_rate_percent': loss_rate, 'grade_num': grade_num}

    def calculate_lost_income(self): days, daily_income_val = self._get_int_value_from_entry(self.lost_work_days), self._get_int_value_from_entry(self.daily_income); return {'amount_yen': days * daily_income_val, 'days': days, 'daily_income_val': daily_income_val}
    def calculate_future_income_loss(self, loss_rate_percent):
        annual_income_val, loss_period_years = self._get_int_value_from_entry(self.annual_income), self._get_int_value_from_entry(self.loss_period)
        if loss_rate_percent == 0 or annual_income_val == 0 or loss_period_years == 0: return {'amount_yen': 0, 'annual_income_val': annual_income_val, 'loss_rate_percent': loss_rate_percent, 'loss_period_years': loss_period_years, 'leibniz_coeff': 0, 'calculation_formula': "N/A"}
        loss_rate_decimal, leibniz_coeff = loss_rate_percent / 100.0, self.get_leibniz_coefficient_val(loss_period_years)
        amount = annual_income_val * loss_rate_decimal * leibniz_coeff; formula = f"{annual_income_val:,}円 × {loss_rate_percent}% × {leibniz_coeff} (L係数 {loss_period_years}年)"
        return {'amount_yen': int(round(amount)), 'annual_income_val': annual_income_val, 'loss_rate_percent': loss_rate_percent, 'loss_period_years': loss_period_years, 'leibniz_coeff': leibniz_coeff, 'calculation_formula': formula}

    def get_leibniz_coefficient_val(self, years):
        if years <= 0: return 0.0
        if years > self.YEAR_MAX_LEIBNIZ: return self.leibniz_coefficient_std.get(self.YEAR_MAX_LEIBNIZ, 0.0)
        return self.leibniz_coefficient_std.get(years, 0.0)

    def calculate_lawyer_fees(self, economic_benefit):
        if economic_benefit <= 0: return 0, "経済的利益なし"
        total_fee, calc_basis = 0, ""
        for limit, rate_init, fixed_init, rate_reward, fixed_reward in self.LAWYER_FEE_TIERS_SAMPLE:
            if economic_benefit <= limit :
                initial_fee, reward_fee = economic_benefit * rate_init + fixed_init, economic_benefit * rate_reward + fixed_reward
                total_fee = initial_fee + reward_fee; calc_basis = f"着手金目安:({economic_benefit:,.0f}×{rate_init*100:.1f}% + {fixed_init:,.0f}円) + 報酬金目安:({economic_benefit:,.0f}×{rate_reward*100:.1f}% + {fixed_reward:,.0f}円)"; break
        return int(round(total_fee)), calc_basis

    def display_individual_tab_results(self, hospital_data, disability_data, lost_income_data, future_loss_data):
        self.hospital_result_text.configure(state='normal'); self.hospital_result_text.delete(1.0, tk.END); self.hospital_result_text.insert(tk.END, f"【入通院慰謝料 計算結果】\n\n  適用基準: {hospital_data['table_name_display']}\n  入力期間: 入院{hospital_data['h_months']}ヶ月, 通院{hospital_data['o_months']}ヶ月\n  (実通院日数: {hospital_data['actual_o_days']}日)\n  計算根拠詳細: {hospital_data['basis_text']}\n\n  慰謝料額 (概算): {hospital_data['amount_yen']:,} 円\n"); self.hospital_result_text.configure(state='disabled')
        self.disability_result_text.configure(state='normal'); self.disability_result_text.delete(1.0, tk.END); self.disability_result_text.insert(tk.END, f"【後遺障害関連 計算結果】\n\n  後遺障害等級: {disability_data['grade_text_display']}\n");
        if disability_data['grade_num'] > 0: self.disability_result_text.insert(tk.END, f"  労働能力喪失率: {disability_data['loss_rate_percent']}%\n  後遺障害慰謝料 (弁護士基準目安): {disability_data['amount_yen']:,} 円\n\n※ これは弁護士基準（赤い本等）に基づく一般的な目安です。\n")
        else: self.disability_result_text.insert(tk.END, "  後遺障害なし、または等級が無効のため、関連損害は算定されません。\n")
        self.disability_result_text.configure(state='disabled')
        self.income_result_text.configure(state='normal'); self.income_result_text.delete(1.0, tk.END); self.income_result_text.insert(tk.END, f"【休業損害 計算結果】\n  休業日数: {lost_income_data['days']}日\n  日額基礎収入: {lost_income_data['daily_income_val']:,}円\n  休業損害額 (概算): {lost_income_data['amount_yen']:,}円\n\n"); self.income_result_text.insert(tk.END, f"【後遺障害逸失利益 計算結果】\n")
        if disability_data['grade_num'] == 0 or disability_data['loss_rate_percent'] == 0: self.income_result_text.insert(tk.END, "  後遺障害なし、または労働能力喪失がないため、逸失利益は発生しません。\n")
        elif future_loss_data['amount_yen'] > 0 : self.income_result_text.insert(tk.END, f"  基礎年収: {future_loss_data['annual_income_val']:,}円\n  労働能力喪失率: {future_loss_data['loss_rate_percent']}%\n  労働能力喪失期間: {future_loss_data['loss_period_years']}年\n  ライプニッツ係数: {future_loss_data['leibniz_coeff']}\n  計算式: {future_loss_data['calculation_formula']}\n  逸失利益額 (概算): {future_loss_data['amount_yen']:,}円\n")
        else: self.income_result_text.insert(tk.END, f"  基礎年収、労働能力喪失期間のいずれかが0のため、逸失利益は0円です。\n  (基礎年収: {future_loss_data['annual_income_val']:,}円, 喪失率: {future_loss_data['loss_rate_percent']}%, 喪失期間: {future_loss_data['loss_period_years']}年)\n")
        self.income_result_text.configure(state='disabled')

    def display_total_result_summary(self, hospital_data, disability_data, lost_income_data, future_loss_data):
        self.total_result_text.configure(state='normal'); self.total_result_text.delete(1.0, tk.END)
        tags = {"header": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_LARGE, "bold"), "subheader": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT + 2, "bold"), "item_name": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT + 1), "item_value": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT + 1, "bold"), "item_detail": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT), "total_section": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT + 2, "bold"), "final_amount": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_LARGE, "bold"), "disclaimer": (self.FONT_FAMILY_DEFAULT, self.FONT_SIZE_DEFAULT -1)}
        colors = {"header": self.COLOR_PRIMARY, "subheader": self.COLOR_TEXT_DARK, "item_value": self.COLOR_TEXT_DARK, "total_section": self.COLOR_PRIMARY, "final_amount": self.COLOR_DANGER, "item_detail": "grey", "disclaimer": "grey"}
        margins = {"subheader": (10,10), "item_name": (20,20), "item_value": (20,20), "item_detail": (30,30), "total_section": (10,10), "final_amount": (10,10), "disclaimer": (10,10)}; spacing = {"header": 10, "subheader": 5, "total_section": 8, "final_amount": 10, "separator_major": 10, "separator_minor": 5, "disclaimer": 10}
        for tag, font_val in tags.items(): self.total_result_text.tag_configure(tag, font=font_val, foreground=colors.get(tag, self.COLOR_TEXT_DARK), lmargin1=margins.get(tag, (0,0))[0], lmargin2=margins.get(tag, (0,0))[1], spacing3=spacing.get(tag,0))
        self.total_result_text.tag_configure("separator_major", font=(self.FONT_FAMILY_DEFAULT,1), overstrike=True, spacing1=spacing["separator_major"], spacing3=spacing["separator_major"]); self.total_result_text.tag_configure("separator_minor", font=(self.FONT_FAMILY_DEFAULT,1), overstrike=True, spacing1=spacing["separator_minor"], spacing3=spacing["separator_minor"], foreground="lightgrey")
        def add_line(text, style_tag): self.total_result_text.insert(tk.END, text + "\n", style_tag)
        def add_separator(major=True): self.total_result_text.insert(tk.END, " " * 80 + "\n", "separator_major" if major else "separator_minor")
        add_line("損害賠償額計算書（弁護士基準・概算）", "header"); add_separator()
        add_line("【案件情報】", "subheader"); add_line(f"  案件番号: {self.case_number.get()}", "item_name"); add_line(f"  依頼者氏名: {self.client_name.get()}", "item_name"); acc_date_str = self._get_date_from_entries(self.accident_date_year, self.accident_date_month, self.accident_date_day) or "未入力"; add_line(f"  事故発生日: {acc_date_str}", "item_name"); sym_date_str = self._get_date_from_entries(self.symptom_fixed_date_year, self.symptom_fixed_date_month, self.symptom_fixed_date_day) or "未入力/算定不能"; add_line(f"  症状固定日: {sym_date_str}", "item_name"); add_line(f"  被害者年齢(事故時): {self.victim_age.get()}歳", "item_name"); add_line(f"  性別: {self.victim_gender.get() or '未選択'}", "item_name"); add_line(f"  職業: {self.occupation.get() or '未選択'}", "item_name"); annual_income_val_str = f"{self._get_int_value_from_entry(self.annual_income):,}" if self.annual_income.get().isdigit() else (self.annual_income.get() or "未入力"); add_line(f"  事故前年収: {annual_income_val_str}円", "item_name"); add_line(f"  計算実行日: {date.today().strftime('%Y-%m-%d')}", "item_name"); add_separator()
        add_line("【損害項目別 金額】", "subheader"); total_positive_damage = 0
        add_line(f"1. 入通院慰謝料: {hospital_data['amount_yen']:,} 円", "item_value"); add_line(f"   (基準: {hospital_data['table_name_display']}, {hospital_data['basis_text']})", "item_detail"); total_positive_damage += hospital_data['amount_yen']
        add_line(f"2. 後遺障害慰謝料: {disability_data['amount_yen']:,} 円", "item_value"); add_line(f"   (等級: {disability_data['grade_text_display']}, 喪失率: {disability_data['loss_rate_percent']}%)", "item_detail"); total_positive_damage += disability_data['amount_yen']
        add_line(f"3. 休業損害: {lost_income_data['amount_yen']:,} 円", "item_value"); add_line(f"   (休業{lost_income_data['days']}日 × 日額{lost_income_data['daily_income_val']:,}円)", "item_detail"); total_positive_damage += lost_income_data['amount_yen']
        add_line(f"4. 後遺障害逸失利益: {future_loss_data['amount_yen']:,} 円", "item_value")
        if future_loss_data['amount_yen'] > 0: add_line(f"   ({future_loss_data['calculation_formula']})", "item_detail")
        elif disability_data['grade_num'] > 0 and disability_data['loss_rate_percent'] > 0: add_line(f"   (基礎年収または喪失期間が0のため算定不能)", "item_detail")
        else: add_line(f"   (後遺障害なし、または労働能力喪失なし)", "item_detail")
        total_positive_damage += future_loss_data['amount_yen']; add_separator(major=False); add_line(f"  上記損害合計 (A): {total_positive_damage:,} 円", "total_section"); add_separator()
        add_line("【過失相殺】", "subheader"); victim_fault_percent = self._get_int_value_from_entry(self.victim_fault_percentage); fault_deduction = int(round(total_positive_damage * (victim_fault_percent / 100.0))); amount_after_fault = total_positive_damage - fault_deduction
        add_line(f"  被害者の過失割合: {victim_fault_percent}%", "item_name"); add_line(f"  過失相殺による減額 (B) = (A) × {victim_fault_percent}%: ▲ {fault_deduction:,} 円", "item_name"); add_line(f"  過失相殺後の損害額 (C) = (A) - (B): {amount_after_fault:,} 円", "total_section"); add_separator()
        add_line("【弁護士費用（着手金・報酬金合計の概算）】", "subheader"); lawyer_fee, lawyer_fee_basis = self.calculate_lawyer_fees(amount_after_fault); add_line(f"  弁護士費用概算 (D): {lawyer_fee:,} 円", "item_value"); add_line(f"   (計算根拠目安: {lawyer_fee_basis})", "item_detail"); add_line(f"   (注: これは旧報酬規定等を参考にした機械的な概算です。事案により変動します。消費税別途の場合あり)", "item_detail"); add_separator()
        add_line("【総合計（弁護士基準による損害賠償請求額の目安）】", "total_section"); add_line(f"  {amount_after_fault:,} 円", "final_amount"); add_line(f"  (上記は、過失相殺を考慮した損害額の合計です)", "item_detail"); add_separator()
        add_line("【注意事項】", "subheader"); disclaimer_text = ("・本計算書は、入力情報に基づき弁護士基準（赤い本等）を参考に機械的に算定した概算です。\n・実際の賠償額は、事故態様、過失割合の具体的認定、個別事情（既往症、素因減額等）、治療の相当性、証拠、交渉経緯等により大きく変動します。\n・ライプニッツ係数は令和2年4月1日以降の事故（法定利率3%）を前提としています。\n・弁護士費用は、事務所の報酬基準や事案の難易度により異なります。上記はあくまで簡易な目安です。\n・本計算結果は法的な助言や最終的な賠償額を保証するものではありません。正確な評価のためには必ず弁護士にご相談ください."); add_line(disclaimer_text, "disclaimer"); self.total_result_text.configure(state='disabled')

    def save_result(self):
        result_content = self.total_result_text.get(1.0, tk.END).strip()
        if not result_content or "計算実行ボタンを押すと" in result_content: messagebox.showwarning("保存不可", "保存する計算結果がありません。先に「計算実行」をしてください。"); return
        case_num_str = self.case_number.get().strip() or "NoCase"; default_filename = f"損害賠償計算結果_{case_num_str}_{date.today().strftime('%Y%m%d')}.txt"
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")], title="計算結果を名前を付けて保存", initialfile=default_filename)
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f: f.write(f"{self.APP_TITLE}\n作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'-'*70}\n{result_content}")
                messagebox.showinfo("保存完了", f"計算結果を保存しました:\n{filepath}")
            except Exception as e: messagebox.showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{str(e)}")

    def export_pdf(self):
        result_content_raw = self.total_result_text.get(1.0, tk.END).strip()
        if not result_content_raw or "計算実行ボタンを押すと" in result_content_raw: messagebox.showwarning("PDF出力不可", "PDF出力する計算結果がありません。先に「計算実行」をしてください。"); return
        case_num_str = self.case_number.get().strip() or "NoCase"; default_filename = f"損害賠償計算書_{case_num_str}_{date.today().strftime('%Y%m%d')}.pdf"
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDFファイル", "*.pdf"), ("すべてのファイル", "*.*")], title="計算結果をPDFで保存", initialfile=default_filename)
        if not filepath: return
        try:
            pdf_canvas = reportlab_canvas.Canvas(filepath, pagesize=A4); registered_font_name = None; jp_font_candidates = ['HeiseiKakuGo-W5', 'IPAexGothic', 'MS-Mincho', 'YuMincho', 'Osaka']
            for font_name in jp_font_candidates:
                try: pdfmetrics.registerFont(UnicodeCIDFont(font_name)); registered_font_name = font_name; break
                except Exception: continue
            if not registered_font_name: messagebox.showwarning("フォント警告", "適切な日本語フォントが見つかりませんでした。\nPDFが正しく表示されない可能性があります。\nIPAフォント等のインストールをお試しください。"); registered_font_name = 'Helvetica'
            page_width, page_height = A4; margin_top, margin_bottom, margin_left = 20*mm, 20*mm, 15*mm; line_height_normal, line_height_small = 5*mm, 4*mm; current_y = page_height - margin_top
            def draw_line_on_pdf(text, font_name, font_size, line_h, x_offset=0):
                nonlocal current_y
                if current_y < margin_bottom + line_h: pdf_canvas.showPage(); current_y = page_height - margin_top
                pdf_canvas.setFont(font_name, font_size); pdf_canvas.drawString(margin_left + x_offset, current_y, text); current_y -= line_h
            draw_line_on_pdf(self.APP_TITLE, registered_font_name, 16, 8*mm); draw_line_on_pdf(f"作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}", registered_font_name, 9, 5*mm); current_y -= 5*mm
            lines = result_content_raw.split('\n')
            for line_text in lines:
                font_size_pdf, current_line_height, x_offset_pdf = 10, line_height_normal, 0
                if line_text.startswith("【") and line_text.endswith("】"): font_size_pdf, current_line_height = 12, 6*mm
                elif line_text.strip().startswith("・") or "   (" in line_text: font_size_pdf, current_line_height = 9, line_height_small;
                if not line_text.strip().startswith("・") and ("   (" in line_text): x_offset_pdf = 5*mm
                elif "円" in line_text and (line_text.strip().endswith("円") or " 円" in line_text.strip()): font_size_pdf = 11
                if any(kw in line_text for kw in ["合計:", "総合計", "最終支払見込額"]): font_size_pdf = 12 if "総合計" in line_text else 11
                draw_line_on_pdf(line_text.strip(), registered_font_name, font_size_pdf, current_line_height, x_offset_pdf)
            pdf_canvas.save(); messagebox.showinfo("PDF出力完了", f"PDFを保存しました:\n{filepath}")
        except Exception as e: messagebox.showerror("PDF出力エラー", f"PDF出力中にエラーが発生しました:\n{type(e).__name__}: {str(e)}")

    def clear_data(self):
        if not messagebox.askyesno("データクリア確認", "入力されたすべてのデータと計算結果をクリアしますか？\nこの操作は元に戻せません。"): return
        entries_with_defaults = [(self.case_number, ""), (self.client_name, ""), (self.victim_age, "0"), (self.annual_income, "0"), (self.victim_fault_percentage, "0"), (self.hospital_months, "0"), (self.outpatient_months, "0"), (self.actual_outpatient_days, "0"), (self.lost_work_days, "0"), (self.daily_income, "0"), (self.loss_period, "0")]
        for entry, default_val in entries_with_defaults: entry.delete(0, tk.END); entry.insert(0, default_val)
        self._set_date_entries(self.accident_date_year, self.accident_date_month, self.accident_date_day); self._set_date_entries(self.symptom_fixed_date_year, self.symptom_fixed_date_month, self.symptom_fixed_date_day)
        self.victim_gender.set(''); self.occupation.set(''); self.disability_grade.set('なし'); self.whiplash_var.set(False)
        text_widgets_with_placeholders = [(self.hospital_result_text, "計算実行ボタンを押すと、ここに結果が表示されます。"),(self.disability_result_text, "計算実行ボタンを押すと、ここに結果が表示されます。"),(self.income_result_text, "計算実行ボタンを押すと、ここに結果が表示されます。"),(self.total_result_text, "計算実行ボタンを押すと、ここに総合結果が表示されます。")]
        for text_widget, placeholder in text_widgets_with_placeholders: text_widget.configure(state='normal'); text_widget.delete(1.0, tk.END); text_widget.insert(tk.END, placeholder); text_widget.configure(state='disabled')
        self.notebook.select(0); self.set_initial_focus(); messagebox.showinfo("クリア完了", "すべてのデータがクリアされました。")

def main():
    db_manager_for_standalone = None
    try:
        from database.db_manager import DatabaseManager
        # CaseData import for DatabaseManager might be needed if it type hints or uses it directly
        # from models.case_data import CaseData 
        db_manager_for_standalone = DatabaseManager()
    except ImportError as e:
        print(f"Could not import real DatabaseManager for standalone app.py run: {e}")
        class DummyDBManager:
            def __init__(self): print("Using DummyDBManager for ui/app.py standalone run")
        db_manager_for_standalone = DummyDBManager()
    root = tk.Tk()
    app = CompensationCalculator(root, db_manager_for_standalone)
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2
    root.geometry(f"+{int(x)}+{int(y-30)}")
    root.mainloop()

if __name__ == "__main__":
    main()
