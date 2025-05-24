#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel・帳票出力エンジン
プロフェッショナルな書類作成機能
"""

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
from openpyxl.drawing.image import Image
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

from models.case_data import CaseData
from calculation.compensation_engine import CalculationResult

class ExcelReportGenerator:
    """Excel帳票生成クラス"""
    
    def __init__(self):
        self.setup_styles()
    
    def setup_styles(self):
        """Excelスタイルの設定"""
        # フォント
        self.fonts = {
            'title': Font(name='Meiryo UI', size=16, bold=True),
            'subtitle': Font(name='Meiryo UI', size=14, bold=True),
            'header': Font(name='Meiryo UI', size=12, bold=True),
            'body': Font(name='Meiryo UI', size=11),
            'small': Font(name='Meiryo UI', size=10),
            'number': Font(name='Meiryo UI', size=11, bold=True)
        }
        
        # 罫線
        self.borders = {
            'thin_all': Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            ),
            'thick_bottom': Border(bottom=Side(style='thick')),
            'medium_all': Border(
                left=Side(style='medium'), right=Side(style='medium'),
                top=Side(style='medium'), bottom=Side(style='medium')
            )
        }
        
        # 塗りつぶし
        self.fills = {
            'header': PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid'),
            'subheader': PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid'),
            'total': PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid'),
            'amount': PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
        }
        
        # 配置
        self.alignments = {
            'center': Alignment(horizontal='center', vertical='center'),
            'left': Alignment(horizontal='left', vertical='center'),
            'right': Alignment(horizontal='right', vertical='center'),
            'center_wrap': Alignment(horizontal='center', vertical='center', wrap_text=True)
        }
    
    def create_compensation_report(self, case_data: CaseData, results: Dict[str, CalculationResult], 
                                 output_path: str) -> bool:
        """損害賠償計算書の作成"""
        try:
            wb = openpyxl.Workbook()
            
            # 計算書シート
            self._create_calculation_sheet(wb, case_data, results)
            
            # 詳細シート
            self._create_detail_sheet(wb, case_data, results)
            
            # グラフシート
            self._create_chart_sheet(wb, results)
            
            # 付属資料シート
            self._create_reference_sheet(wb)
            
            # 不要なデフォルトシートを削除
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])
            
            wb.save(output_path)
            return True
            
        except Exception as e:
            print(f"Excel出力エラー: {e}")
            return False
    
    def _create_calculation_sheet(self, wb: openpyxl.Workbook, case_data: CaseData, 
                                results: Dict[str, CalculationResult]):
        """計算書シートの作成"""
        ws = wb.active
        ws.title = "損害賠償計算書"
        
        # ヘッダー部分
        self._create_header(ws, case_data)
        
        # 案件情報
        self._create_case_info(ws, case_data, start_row=8)
        
        # 計算結果
        self._create_calculation_results(ws, results, start_row=18)
        
        # フッター
        self._create_footer(ws, start_row=35)
        
        # 列幅調整
        self._adjust_column_widths(ws)
    
    def _create_header(self, ws, case_data: CaseData):
        """ヘッダー部分の作成"""
        # タイトル
        ws['A1'] = "損害賠償計算書"
        ws['A1'].font = self.fonts['title']
        ws['A1'].alignment = self.alignments['center']
        ws.merge_cells('A1:H1')
        
        # 作成日
        ws['G2'] = "作成日:"
        ws['H2'] = datetime.now().strftime("%Y年%m月%d日")
        ws['G2'].font = self.fonts['body']
        ws['H2'].font = self.fonts['body']
        ws['G2'].alignment = self.alignments['right']
        ws['H2'].alignment = self.alignments['right']
        
        # 案件番号
        ws['A3'] = f"案件番号: {case_data.case_number}"
        ws['A3'].font = self.fonts['subtitle']
        ws.merge_cells('A3:D3')
        
        # 依頼者名
        ws['E3'] = f"依頼者: {case_data.person_info.name} 様"
        ws['E3'].font = self.fonts['subtitle']
        ws.merge_cells('E3:H3')
        
        # 罫線
        for row in range(1, 4):
            for col in range(1, 9):
                cell = ws.cell(row=row, column=col)
                cell.border = self.borders['thin_all']
    
    def _create_case_info(self, ws, case_data: CaseData, start_row: int):
        """案件情報部分の作成"""
        row = start_row
        
        # セクションタイトル
        ws[f'A{row}'] = "【案件概要】"
        ws[f'A{row}'].font = self.fonts['header']
        ws[f'A{row}'].fill = self.fills['subheader']
        ws.merge_cells(f'A{row}:H{row}')
        row += 1
        
        # 情報テーブル
        info_data = [
            ("事故発生日", case_data.accident_info.accident_date.strftime("%Y年%m月%d日") if case_data.accident_info.accident_date else "未入力"),
            ("症状固定日", case_data.accident_info.symptom_fixed_date.strftime("%Y年%m月%d日") if case_data.accident_info.symptom_fixed_date else "未入力"),
            ("被害者年齢", f"{case_data.person_info.age}歳"),
            ("職業", case_data.person_info.occupation),
            ("性別", case_data.person_info.gender),
            ("過失割合", f"{case_data.person_info.fault_percentage}%"),
            ("年収", f"{case_data.person_info.annual_income:,}円"),
            ("後遺障害等級", f"第{case_data.medical_info.disability_grade}級" if case_data.medical_info.disability_grade > 0 else "なし")
        ]
        
        for i, (label, value) in enumerate(info_data):
            col_offset = (i % 2) * 4  # 2列レイアウト
            if i % 2 == 0:
                row += 1
            
            ws.cell(row=row, column=1 + col_offset, value=label)
            ws.cell(row=row, column=2 + col_offset, value=value)
            
            # スタイル適用
            ws.cell(row=row, column=1 + col_offset).font = self.fonts['body']
            ws.cell(row=row, column=2 + col_offset).font = self.fonts['body']
            ws.cell(row=row, column=1 + col_offset).fill = self.fills['subheader']
            
            # 罫線
            for col in range(1 + col_offset, 3 + col_offset):
                ws.cell(row=row, column=col).border = self.borders['thin_all']
    
    def _create_calculation_results(self, ws, results: Dict[str, CalculationResult], start_row: int):
        """計算結果部分の作成"""
        row = start_row
        
        # セクションタイトル
        ws[f'A{row}'] = "【損害賠償額計算結果】"
        ws[f'A{row}'].font = self.fonts['header']
        ws[f'A{row}'].fill = self.fills['subheader']
        ws.merge_cells(f'A{row}:H{row}')
        row += 1
        
        # テーブルヘッダー
        headers = ["損害項目", "金額", "計算根拠", "法的根拠"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.fonts['header']
            cell.fill = self.fills['header']
            cell.font = Font(name='Meiryo UI', size=12, bold=True, color='FFFFFF')
            cell.alignment = self.alignments['center']
            cell.border = self.borders['thin_all']
        
        # 列幅設定
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 25
        
        row += 1
        
        # 各損害項目
        total_amount = Decimal('0')
        for key, result in results.items():
            if key == 'summary':  # 合計は最後に表示
                continue
                
            ws.cell(row=row, column=1, value=result.item_name)
            ws.cell(row=row, column=2, value=f"¥{result.amount:,}")
            ws.cell(row=row, column=3, value=result.calculation_details)
            ws.cell(row=row, column=4, value=result.legal_basis)
            
            # スタイル適用
            ws.cell(row=row, column=1).font = self.fonts['body']
            ws.cell(row=row, column=2).font = self.fonts['number']
            ws.cell(row=row, column=2).alignment = self.alignments['right']
            ws.cell(row=row, column=3).font = self.fonts['small']
            ws.cell(row=row, column=3).alignment = self.alignments['left']
            ws.cell(row=row, column=4).font = self.fonts['small']
            
            # 金額セルの背景色
            if result.amount > 0:
                ws.cell(row=row, column=2).fill = self.fills['amount']
            
            # 罫線
            for col in range(1, 5):
                ws.cell(row=row, column=col).border = self.borders['thin_all']
            
            total_amount += result.amount
            row += 1
        
        # 合計行
        if 'summary' in results:
            summary = results['summary']
            ws.cell(row=row, column=1, value="【総合計】")
            ws.cell(row=row, column=2, value=f"¥{summary.amount:,}")
            
            # 合計行のスタイル
            ws.cell(row=row, column=1).font = self.fonts['header']
            ws.cell(row=row, column=2).font = Font(name='Meiryo UI', size=14, bold=True)
            ws.cell(row=row, column=2).alignment = self.alignments['right']
            
            for col in range(1, 3):
                ws.cell(row=row, column=col).fill = self.fills['total']
                ws.cell(row=row, column=col).border = self.borders['medium_all']
    
    def _create_detail_sheet(self, wb: openpyxl.Workbook, case_data: CaseData, 
                           results: Dict[str, CalculationResult]):
        """詳細シートの作成"""
        ws = wb.create_sheet("計算詳細")
        
        row = 1
        
        # 各項目の詳細計算
        for key, result in results.items():
            if key == 'summary':
                continue
            
            # 項目タイトル
            ws.cell(row=row, column=1, value=f"【{result.item_name}】")
            ws.cell(row=row, column=1).font = self.fonts['subtitle']
            ws.merge_cells(f'A{row}:E{row}')
            row += 1
            
            # 計算詳細
            details_lines = result.calculation_details.split('\n')
            for line in details_lines:
                if line.strip():
                    ws.cell(row=row, column=1, value=line)
                    ws.cell(row=row, column=1).font = self.fonts['body']
                    row += 1
            
            # 法的根拠
            if result.legal_basis:
                ws.cell(row=row, column=1, value=f"法的根拠: {result.legal_basis}")
                ws.cell(row=row, column=1).font = self.fonts['small']
                row += 1
            
            # 注意事項
            if result.notes:
                ws.cell(row=row, column=1, value=f"注意: {result.notes}")
                ws.cell(row=row, column=1).font = self.fonts['small']
                row += 1
            
            row += 2  # 項目間のスペース
    
    def _create_chart_sheet(self, wb: openpyxl.Workbook, results: Dict[str, CalculationResult]):
        """グラフシートの作成"""
        ws = wb.create_sheet("グラフ")
        
        # データ準備
        row = 2
        ws.cell(row=1, column=1, value="損害項目")
        ws.cell(row=1, column=2, value="金額")
        
        chart_data = []
        for key, result in results.items():
            if key == 'summary' or result.amount == 0:
                continue
            
            ws.cell(row=row, column=1, value=result.item_name)
            ws.cell(row=row, column=2, value=float(result.amount))
            chart_data.append((result.item_name, float(result.amount)))
            row += 1
        
        # 棒グラフ作成
        if chart_data:
            chart = BarChart()
            chart.title = "損害項目別金額"
            chart.x_axis.title = "損害項目"
            chart.y_axis.title = "金額（円）"
            
            data = Reference(ws, min_col=2, min_row=1, max_row=row-1)
            categories = Reference(ws, min_col=1, min_row=2, max_row=row-1)
            
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(categories)
            
            ws.add_chart(chart, "D2")
    
    def _create_reference_sheet(self, wb: openpyxl.Workbook):
        """付属資料シートの作成"""
        ws = wb.create_sheet("付属資料")
        
        # 弁護士基準の説明
        explanations = [
            "【弁護士基準（裁判基準）について】",
            "",
            "弁護士基準とは、過去の裁判例に基づいて定められた損害賠償の算定基準です。",
            "一般的に自賠責基準や任意保険基準よりも高額になる傾向があります。",
            "",
            "【計算に使用した基準】",
            "・入通院慰謝料: 赤い本2023年版 別表I/II",
            "・後遺障害慰謝料: 赤い本2023年版",
            "・ライプニッツ係数: 法定利率3%（令和2年4月1日以降）",
            "",
            "【注意事項】",
            "・本計算書は弁護士基準に基づく概算額です",
            "・実際の示談交渉や裁判では個別事情により変動する可能性があります",
            "・最新の法改正や判例により基準が変更される場合があります"
        ]
        
        for i, text in enumerate(explanations, 1):
            ws.cell(row=i, column=1, value=text)
            if text.startswith("【") and text.endswith("】"):
                ws.cell(row=i, column=1).font = self.fonts['header']
            else:
                ws.cell(row=i, column=1).font = self.fonts['body']
    
    def _create_footer(self, ws, start_row: int):
        """フッター部分の作成"""
        footer_text = f"※ 本計算書は {datetime.now().strftime('%Y年%m月%d日')} 時点の弁護士基準に基づいて作成されました"
        ws[f'A{start_row}'] = footer_text
        ws[f'A{start_row}'].font = self.fonts['small']
        ws.merge_cells(f'A{start_row}:H{start_row}')
    
    def _adjust_column_widths(self, ws):
        """列幅の自動調整"""
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)  # 最大50文字
            ws.column_dimensions[column_letter].width = adjusted_width

class TemplateManager:
    """Excelテンプレート管理クラス"""
    
    def __init__(self):
        self.template_dir = Path("templates")
        self.template_dir.mkdir(exist_ok=True)
    
    def create_standard_templates(self):
        """標準テンプレートの作成"""
        # 交通事故テンプレート
        self._create_traffic_accident_template()
        
        # 労災事故テンプレート
        self._create_work_accident_template()
        
        # 医療過誤テンプレート
        self._create_medical_malpractice_template()
    
    def _create_traffic_accident_template(self):
        """交通事故用テンプレート"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "交通事故損害賠償計算書"
        
        # テンプレート固有の項目を設定
        # 実装詳細は省略...
        
        template_path = self.template_dir / "traffic_accident_template.xlsx"
        wb.save(template_path)
    
    def _create_work_accident_template(self):
        """労災事故用テンプレート"""
        # 実装詳細...
        pass
    
    def _create_medical_malpractice_template(self):
        """医療過誤用テンプレート"""
        # 実装詳細...
        pass
    
    def apply_template(self, template_name: str, case_data: CaseData) -> openpyxl.Workbook:
        """テンプレートの適用"""
        template_path = self.template_dir / f"{template_name}.xlsx"
        
        if template_path.exists():
            wb = openpyxl.load_workbook(template_path)
            # テンプレートにデータを埋め込む
            return wb
        else:
            raise FileNotFoundError(f"テンプレート {template_name} が見つかりません")

# 使用例
if __name__ == "__main__":
    # サンプル使用
    generator = ExcelReportGenerator()
    
    # テンプレートマネージャー
    template_mgr = TemplateManager()
    template_mgr.create_standard_templates()
