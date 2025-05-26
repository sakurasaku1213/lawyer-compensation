#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDFレポート生成モジュール
"""

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from decimal import Decimal
from datetime import datetime

# 日本語フォント対応のため追加
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models.case_data import CaseData
from calculation.compensation_engine import CalculationResult # CalculationResultをインポート

# 日本語フォントの登録 (フォントファイルへのパスは環境に合わせて変更してください)
# 例: IPAexゴシック
FONT_NAME_GOTHIC = "IPAexGothic"
# FONT_FILE_PATH_GOTHIC = "C:\\Windows\\Fonts\\ipaexg.ttf" # Windowsの場合の例
FONT_FILE_PATH_GOTHIC = "e:\\fonts\\ipaexg.ttf" # 仮のパス。ユーザーに置き換えを促す。

try:
    pdfmetrics.registerFont(TTFont(FONT_NAME_GOTHIC, FONT_FILE_PATH_GOTHIC))
except Exception as e:
    print(f"警告: 日本語フォント '{FONT_NAME_GOTHIC}' の読み込みに失敗しました。'{FONT_FILE_PATH_GOTHIC}' を確認してください。エラー: {e}")
    print("PDF内の日本語が正しく表示されない可能性があります。")
    # フォールバックとして標準フォントを使用するなどの処理も検討できますが、
    # ここでは警告のみとし、スタイル定義では登録したフォント名を引き続き使用します。
    # reportlabがフォントを見つけられない場合、標準フォントにフォールバックすることがあります。

class PdfReportGenerator:
    """PDFレポート生成クラス"""

    def __init__(self, case_data: CaseData, calculation_results: dict[str, CalculationResult]):
        self.case_data = case_data
        self.calculation_results = calculation_results
        self.styles = getSampleStyleSheet()
        self.custom_styles()

    def custom_styles(self):
        """カスタムスタイルの定義"""
        # 日本語フォントが登録されていればそれを使用し、されていなければHelveticaを試みる
        base_font = FONT_NAME_GOTHIC if pdfmetrics.getFont(FONT_NAME_GOTHIC) else 'Helvetica'
        bold_font = base_font + "-Bold" # reportlabは -Bold を自動的に探さないため、別途登録が必要な場合がある
                                      # IPAexGothicのようなフォントは通常Bold体を含んでいるか、
                                      # reportlabが擬似ボールドを適用する。
                                      # より確実に太字を表示するには、太字用のフォントファイルも登録する。
                                      # ここでは簡略化のため、ベースフォント名に-Boldを付加する。
                                      # 実際にIPAexGothicを使用する場合、太字スタイルはフォント自体が持つ。

        # 太字フォントも登録 (例: IPAexゴシックのBold体がない場合、通常のフォントで代用)
        # 通常、TTFontで登録したフォント名に '-Bold' をつけると reportlab が太字を探しますが、
        # IPAフォントの場合、標準で太字が含まれているため、fontName='IPAexGothic', bold=True のようにするか、
        # ParagraphStyle の中で <para bold="true"> のようにマークアップします。
        # ここでは、ParagraphStyleのfontNameにベースフォントを指定し、必要に応じてスタイル内で太字を指定します。

        self.styles.add(ParagraphStyle(name='MainTitle', fontSize=18, alignment=TA_CENTER, spaceAfter=10*mm, fontName=base_font, leading=22)) # bold=True は Paragraph内で <b/> を使う方が一般的
        self.styles.add(ParagraphStyle(name='SubTitle', fontSize=14, alignment=TA_LEFT, spaceAfter=5*mm, spaceBefore=5*mm, fontName=base_font, leading=18)) # bold=True
        self.styles.add(ParagraphStyle(name='Normal', fontSize=10, alignment=TA_LEFT, fontName=base_font, leading=14)) # 元のNormalスタイルがなかったので追加
        self.styles.add(ParagraphStyle(name='NormalRight', fontSize=10, alignment=TA_RIGHT, fontName=base_font, leading=14))
        self.styles.add(ParagraphStyle(name='NormalJustify', fontSize=10, alignment=TA_JUSTIFY, leading=14, fontName=base_font))
        self.styles.add(ParagraphStyle(name='TableHeader', fontSize=10, alignment=TA_CENTER, fontName=base_font, textColor=colors.whitesmoke, leading=12)) # bold=True
        self.styles.add(ParagraphStyle(name='TableCell', fontSize=9, alignment=TA_LEFT, fontName=base_font, leading=11))
        self.styles.add(ParagraphStyle(name='TableCellRight', fontSize=9, alignment=TA_RIGHT, fontName=base_font, leading=11))
        self.styles.add(ParagraphStyle(name='Footer', fontSize=8, alignment=TA_CENTER, fontName=base_font, leading=10))
        self.styles.add(ParagraphStyle(name='SmallText', fontSize=8, alignment=TA_LEFT, fontName=base_font, leading=10))

    def generate_report(self, filepath: str):
        """PDFレポートを生成"""
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                topMargin=20*mm, bottomMargin=20*mm,
                                leftMargin=20*mm, rightMargin=20*mm)
        
        story = []

        # 1. ヘッダー情報
        story.append(Paragraph("損害賠償額計算書", self.styles['MainTitle']))
        story.append(Spacer(1, 5*mm))
        
        header_data = [
            [Paragraph("案件番号:", self.styles['Normal']), Paragraph(str(self.case_data.case_number or '未設定'), self.styles['Normal'])],
            [Paragraph("依頼者名:", self.styles['Normal']), Paragraph(str(self.case_data.person_info.name or '未設定'), self.styles['Normal'])],
            [Paragraph("作成日:", self.styles['Normal']), Paragraph(datetime.now().strftime("%Y年%m月%d日"), self.styles['Normal'])],
        ]
        header_table = Table(header_data, colWidths=[40*mm, None])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10*mm))

        # 2. 基本情報
        story.append(Paragraph("1. 基本情報", self.styles['SubTitle']))
        basic_info_data = [
            [Paragraph("事故発生日:", self.styles['TableCell']), Paragraph(str(self.case_data.accident_info.accident_date or '-'), self.styles['TableCell'])],
            [Paragraph(f"被害者年齢（事故時）:", self.styles['TableCell']), Paragraph(f"{self.case_data.person_info.age} 歳" if self.case_data.person_info.age is not None else '-', self.styles['TableCell'])],
            [Paragraph("性別:", self.styles['TableCell']), Paragraph(str(self.case_data.person_info.gender or '-'), self.styles['TableCell'])],
            [Paragraph("職業:", self.styles['TableCell']), Paragraph(str(self.case_data.person_info.occupation or '-'), self.styles['TableCell'])],
            [Paragraph("事故前年収:", self.styles['TableCell']), Paragraph(f"{self.case_data.person_info.annual_income:,.0f} 円" if self.case_data.person_info.annual_income is not None else '-', self.styles['TableCellRight'])],
            [Paragraph("被害者過失割合:", self.styles['TableCell']), Paragraph(f"{self.case_data.person_info.fault_percentage or 0} %", self.styles['TableCellRight'])],
        ]
        basic_table = Table(basic_info_data, colWidths=[50*mm, None])
        basic_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
            ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
        ]))
        story.append(basic_table)
        story.append(Spacer(1, 7*mm))

        # 3. 医療情報
        story.append(Paragraph("2. 医療情報", self.styles['SubTitle']))
        med_info = self.case_data.medical_info
        medical_info_data = [
            [Paragraph("症状固定日:", self.styles['TableCell']), Paragraph(str(self.case_data.accident_info.symptom_fixed_date or '-'), self.styles['TableCell'])],
            [Paragraph("入院期間:", self.styles['TableCell']), Paragraph(f"{med_info.hospital_months} ヶ月" if med_info.hospital_months is not None else '-', self.styles['TableCell'])],
            [Paragraph("通院期間:", self.styles['TableCell']), Paragraph(f"{med_info.outpatient_months} ヶ月" if med_info.outpatient_months is not None else '-', self.styles['TableCell'])],
            [Paragraph("実通院日数:", self.styles['TableCell']), Paragraph(f"{med_info.actual_outpatient_days} 日" if med_info.actual_outpatient_days is not None else '-', self.styles['TableCell'])],
            [Paragraph("むちうち等:", self.styles['TableCell']), Paragraph("該当" if med_info.is_whiplash else "非該当", self.styles['TableCell'])],
            [Paragraph("後遺障害等級:", self.styles['TableCell']), Paragraph(f"第 {med_info.disability_grade} 級" if med_info.disability_grade and med_info.disability_grade > 0 else "なし", self.styles['TableCell'])],
            [Paragraph("後遺障害詳細:", self.styles['TableCell']), Paragraph(med_info.disability_details or '-', self.styles['TableCell'])],
        ]
        medical_table = Table(medical_info_data, colWidths=[50*mm, None])
        medical_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
            ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
            ('SPAN', (1,6), (-1,6)) # 後遺障害詳細のセルを結合
        ]))
        story.append(medical_table)
        story.append(Spacer(1, 7*mm))

        # 4. 収入・損害情報 (逸失利益関連)
        story.append(Paragraph("3. 収入・損害情報", self.styles['SubTitle']))
        inc_info = self.case_data.income_info
        income_info_data = [
            [Paragraph("休業日数:", self.styles['TableCell']), Paragraph(f"{inc_info.lost_work_days} 日" if inc_info.lost_work_days is not None else '-', self.styles['TableCell'])],
            [Paragraph("日額基礎収入:", self.styles['TableCell']), Paragraph(f"{inc_info.daily_income:,.0f} 円" if inc_info.daily_income is not None else '-', self.styles['TableCellRight'])],
            [Paragraph("基礎年収（逸失利益用）:", self.styles['TableCell']), Paragraph(f"{inc_info.base_annual_income:,.0f} 円" if inc_info.base_annual_income is not None else '-', self.styles['TableCellRight'])],
            [Paragraph("労働能力喪失期間:", self.styles['TableCell']), Paragraph(f"{inc_info.loss_period_years} 年" if inc_info.loss_period_years is not None else '-', self.styles['TableCell'])],
            [Paragraph("就労可能年数上限:", self.styles['TableCell']), Paragraph(f"{self.case_data.person_info.retirement_age} 歳" if self.case_data.person_info.retirement_age is not None else '-', self.styles['TableCell'])],
        ]
        income_table = Table(income_info_data, colWidths=[50*mm, None])
        income_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
            ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
        ]))
        story.append(income_table)
        story.append(Spacer(1, 10*mm))
        
        story.append(PageBreak()) # 計算結果は新しいページから

        # 5. 計算結果
        story.append(Paragraph("4. 損害賠償額計算結果", self.styles['SubTitle']))
        
        results_data = [
            # ヘッダー
            [Paragraph("<b>費目</b>", self.styles['TableHeader']), # 太字に変更
             Paragraph("<b>金額（円）</b>", self.styles['TableHeader']), # 太字に変更
             Paragraph("<b>計算根拠・備考</b>", self.styles['TableHeader'])] # 太字に変更
        ]
        
        # 個別項目
        ordered_items = [
            'hospitalization', 'disability', 'lost_income', 
            'future_income_loss', 'medical_expenses'
        ]

        for key in ordered_items:
            result = self.calculation_results.get(key)
            if result:
                amount_str = f"{result.amount:,.0f}"
                # 計算根拠を整形
                details_text = result.calculation_details.replace("\\n", "<br/>")
                if result.legal_basis:
                    details_text += f"<br/><b>法的根拠:</b> {result.legal_basis}"
                if result.notes:
                    details_text += f"<br/><b>備考:</b> {result.notes}"
                details_paragraph = Paragraph(details_text, self.styles['SmallText'])
                
                results_data.append([
                    Paragraph(result.item_name, self.styles['TableCell']),
                    Paragraph(amount_str, self.styles['TableCellRight']),
                    details_paragraph
                ])
        
        # 合計などサマリー情報
        summary_result = self.calculation_results.get('summary')
        if summary_result:
            story.append(Spacer(1, 5*mm))
            summary_title = Paragraph("<b>計算概要</b>", self.styles['SubTitle'])
            story.append(summary_title)
            
            summary_details_cleaned = summary_result.calculation_details.replace("\\n", "<br/>")
            # summary_paragraph = Paragraph(summary_details_cleaned, self.styles['NormalJustify'])
            # NormalJustifyだと日本語の禁則処理がうまくいかない場合があるので、Normal（左揃え）に変更
            summary_paragraph = Paragraph(summary_details_cleaned, self.styles['Normal'])
            story.append(summary_paragraph)
            story.append(Spacer(1, 5*mm))
            
            final_amount_text = f"<b><u>最終支払見込額: {summary_result.amount:,.0f} 円</u></b>"
            story.append(Paragraph(final_amount_text, self.styles['SubTitle']))


        results_table = Table(results_data, colWidths=[40*mm, 40*mm, None])
        results_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4682B4")), # ヘッダー背景色
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
            ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
            ('TOPPADDING', (0,0), (-1,-1), 2*mm),
        ]))
        story.append(results_table)
        story.append(Spacer(1, 10*mm))

        # フッター (各ページに表示させる場合は onFirstPage, onLaterPages を使う)
        # ここでは最終ページにのみ簡易的に追加
        # story.append(Paragraph(f"© {datetime.now().year} 法律事務所名など", self.styles['Footer']))

        try:
            doc.build(story)
            return True
        except Exception as e:
            print(f"PDF生成エラー: {e}")
            # self.logger.error(f"PDF生成エラー: {e}", exc_info=True) # クラス内にロガーがあれば
            return False

if __name__ == '__main__':
    # ダミーデータでテスト
    from models.case_data import PersonInfo, AccidentInfo, MedicalInfo, IncomeInfo
    
    sample_case = CaseData(
        case_number="2024-PDF-001",
        person_info=PersonInfo(name="山田 太郎", age=35, gender="男性", occupation="会社員", annual_income=Decimal("5000000"), fault_percentage=10.0, retirement_age=67), # retirement_age追加
        accident_info=AccidentInfo(accident_date="2023-01-15", symptom_fixed_date="2023-07-15"),
        medical_info=MedicalInfo(hospital_months=1, outpatient_months=6, actual_outpatient_days=60, is_whiplash=False, disability_grade=14, disability_details="頚椎捻挫後の神経症状", medical_expenses=Decimal("500000"), transportation_costs=Decimal("50000")), # disability_details追加
        income_info=IncomeInfo(lost_work_days=30, daily_income=Decimal("15000"), loss_period_years=5, base_annual_income=Decimal("5000000"))
    )
    
    sample_results = {
        'hospitalization': CalculationResult(item_name="入通院慰謝料", amount=Decimal("1200000"), calculation_details="入院1ヶ月、通院6ヶ月\\n別表I適用", legal_basis="赤い本", notes="骨折なし"),
        'disability': CalculationResult(item_name="後遺障害慰謝料", amount=Decimal("1100000"), calculation_details="14級9号相当", legal_basis="赤い本", notes="弁護士基準"),
        'lost_income': CalculationResult(item_name="休業損害", amount=Decimal("450000"), calculation_details="基礎収入日額 15,000円 × 休業日数 30日", legal_basis="民法709条", notes=""),
        'future_income_loss': CalculationResult(item_name="後遺障害逸失利益", amount=Decimal("2300000"), calculation_details="基礎年収 5,000,000円 × 労働能力喪失率 5% × 労働能力喪失期間 5年に対するライプニッツ係数 4.5797", legal_basis="民法709条", notes="中間利息控除"),
        'medical_expenses': CalculationResult(item_name="治療関係費", amount=Decimal("550000"), calculation_details="治療費 500,000円 + 付添看護費 0円 + 将来雑費 0円 + 通院交通費 50,000円", legal_basis="", notes="実費"),
        'summary': CalculationResult(item_name="総合計", amount=Decimal("5085000"), calculation_details="損害合計（過失相殺前）: 5,600,000円\\n被害者過失割合: 10.0% (減額 560,000円)\\n損害合計（過失相殺後）: 5,040,000円\\n弁護士費用（請求額の10%として）: 504,000円\\n既払金（自賠責保険金等）: 0円\\n最終支払見込額: 5,085,000円", legal_basis="", notes="弁護士費用特約の有無により変動可能性あり") # summaryのdetailsをより詳細に
    }

    generator = PdfReportGenerator(sample_case, sample_results)
    output_pdf_path = "e:\\sample_report_jp.pdf"
    if generator.generate_report(output_pdf_path):
        print(f"テストPDFが {output_pdf_path} に生成されました。")
        print(f"注意: 日本語フォントが正しく表示されるには、'{FONT_FILE_PATH_GOTHIC}' に有効な日本語フォントファイルが必要です。")
    else:
        print("テストPDFの生成に失敗しました。")

