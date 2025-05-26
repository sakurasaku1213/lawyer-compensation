#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDFレポート生成モジュール
"""

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import traceback
import os

# 日本語フォント対応のため追加
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models.case_data import CaseData
from calculation.compensation_engine import CalculationResult 
from utils.error_handler import get_error_handler, CompensationSystemError, ErrorCategory, ErrorSeverity, FileIOError, ConfigurationError
from config.app_config import AppConfig
import logging

class PdfReportGenerator:
    """PDFレポート生成クラス"""

    def __init__(self, config: AppConfig, case_data: CaseData, calculation_results: dict[str, CalculationResult]):
        self.config = config
        self.report_config = config.report
        self.case_data = case_data
        self.calculation_results = calculation_results
        self.styles = getSampleStyleSheet()
        self.error_handler = get_error_handler()
        self.logger = logging.getLogger(__name__)
        self._register_fonts()
        self.custom_styles()

    def _register_fonts(self):
        """設定に基づいてフォントを登録する"""
        font_name_gothic = self.report_config.font_name_gothic
        font_path_gothic = self.report_config.font_path_gothic

        if not font_name_gothic or not font_path_gothic:
            self.error_handler.handle_exception(
                ConfigurationError(
                    "PDF生成に必要なゴシックフォント名またはパスが設定されていません。",
                    user_message="PDF設定でゴシックフォント名またはパスが指定されていません。設定を確認してください。",
                    severity=ErrorSeverity.HIGH,
                    context={"font_name": font_name_gothic, "font_path": font_path_gothic}
                )
            )
            self.logger.error("ゴシックフォントの設定が不完全なため、PDF生成に問題が発生する可能性があります。")
            return

        try:
            if os.path.exists(font_path_gothic):
                pdfmetrics.registerFont(TTFont(font_name_gothic, font_path_gothic))
                self.logger.info(f"フォント '{font_name_gothic}' を '{font_path_gothic}' から登録しました。")
            else:
                self.error_handler.handle_exception(
                    FileIOError(
                        f"指定されたフォントファイルが見つかりません: {font_path_gothic}",
                        user_message=f"PDF生成に必要なフォントファイル '{font_path_gothic}' が見つかりません。設定を確認してください。",
                        severity=ErrorSeverity.HIGH,
                        context={"font_name": font_name_gothic, "font_path": font_path_gothic}
                    )
                )
                self.logger.error(f"フォントファイル '{font_path_gothic}' が見つかりません。")
        except Exception as e:
            self.error_handler.handle_exception(
                FileIOError(
                    f"日本語フォント '{font_name_gothic}' の読み込みに失敗しました。'{font_path_gothic}' を確認してください。エラー: {e}",
                    user_message=f"PDF生成に必要な日本語フォント '{font_name_gothic}' が見つからないか、読み込めませんでした。PDF内の日本語が正しく表示されない可能性があります。フォントパス '{font_path_gothic}' を確認してください。",
                    severity=ErrorSeverity.MEDIUM,
                    context={"font_name": font_name_gothic, "font_path": font_path_gothic, "exception": str(e)}
                )
            )
            self.logger.warning(f"日本語フォント '{font_name_gothic}' の読み込みに失敗。PDFの日本語表示に問題が出る可能性があります。")


    def custom_styles(self):
        """カスタムスタイルの定義"""
        font_name_gothic = self.report_config.font_name_gothic
        base_font = font_name_gothic if pdfmetrics.getFont(font_name_gothic, None) else 'Helvetica'
        
        if base_font == 'Helvetica' and font_name_gothic:
            self.logger.warning(f"指定されたフォント '{font_name_gothic}' が利用できないため、Helveticaにフォールバックします。")

        self.styles.add(ParagraphStyle(name='MainTitle', fontSize=18, alignment=TA_CENTER, spaceAfter=10*mm, fontName=base_font, leading=22))
        self.styles.add(ParagraphStyle(name='SubTitle', fontSize=14, alignment=TA_LEFT, spaceAfter=5*mm, spaceBefore=5*mm, fontName=base_font, leading=18))
        self.styles.add(ParagraphStyle(name='Normal', fontSize=10, alignment=TA_LEFT, fontName=base_font, leading=14))
        self.styles.add(ParagraphStyle(name='NormalRight', fontSize=10, alignment=TA_RIGHT, fontName=base_font, leading=14))
        self.styles.add(ParagraphStyle(name='NormalJustify', fontSize=10, alignment=TA_JUSTIFY, leading=14, fontName=base_font))
        self.styles.add(ParagraphStyle(name='TableHeader', fontSize=10, alignment=TA_CENTER, fontName=base_font, textColor=colors.whitesmoke, leading=12))
        self.styles.add(ParagraphStyle(name='TableCell', fontSize=9, alignment=TA_LEFT, fontName=base_font, leading=11))
        self.styles.add(ParagraphStyle(name='TableCellRight', fontSize=9, alignment=TA_RIGHT, fontName=base_font, leading=11))
        self.styles.add(ParagraphStyle(name='Footer', fontSize=8, alignment=TA_CENTER, fontName=base_font, leading=10))
        self.styles.add(ParagraphStyle(name='SmallText', fontSize=8, alignment=TA_LEFT, fontName=base_font, leading=10))

    def _create_detail_table(self, details_str: str) -> Table:
        """
        Creates a ReportLab Table from a multi-line string where each line
        is expected to be a key-value pair separated by a colon.
        """
        data = []
        lines = details_str.strip().split('\n') 
        cell_style = self.styles['TableCell'] 
        
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = Paragraph(parts[0].strip() + ":", cell_style)
                value_str = parts[1].strip()
                if '×' in value_str and '=' in value_str :
                     value_paragraph = Paragraph(value_str, self.styles['TableCellRight'])
                else:
                     value_paragraph = Paragraph(value_str, cell_style)
                data.append([key, value_paragraph])
            elif line.strip():
                data.append([Paragraph(line.strip(), cell_style), ''])

        if not data:
            return Paragraph("詳細なし", cell_style)

        detail_table_col_widths = [30*mm, None]
        detail_table = Table(data, colWidths=detail_table_col_widths)
        detail_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5*mm),
        ]))
        return detail_table

    def generate_report(self, output_filename: str):
        output_dir = self.report_config.default_output_directory
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.logger.info(f"出力ディレクトリ '{output_dir}' を作成しました。")
            except OSError as e:
                self.error_handler.handle_exception(
                    FileIOError(
                        f"出力ディレクトリ '{output_dir}' の作成に失敗しました: {e}",
                        user_message=f"レポートの出力先ディレクトリ '{output_dir}' を作成できませんでした。",
                        severity=ErrorSeverity.HIGH, context={"path": output_dir, "exception": str(e)}
                    )
                )
                return

        filepath = os.path.join(output_dir, output_filename)
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                topMargin=20*mm, bottomMargin=20*mm,
                                leftMargin=20*mm, rightMargin=20*mm,
                                author=self.report_config.default_author,
                                title=f"損害賠償額計算書 - {self.case_data.case_number or 'N/A'}"
                                )
        story = []

        try:
            if self.report_config.company_logo_path and os.path.exists(self.report_config.company_logo_path):
                try:
                    logo = Image(self.report_config.company_logo_path)
                    logo.drawHeight = 15*mm 
                    logo.drawWidth = (logo.drawHeight / logo.imageHeight) * logo.imageWidth
                    logo.hAlign = 'RIGHT'
                    story.append(logo)
                    story.append(Spacer(1, 5*mm))
                except Exception as e:
                    self.error_handler.handle_exception(
                        FileIOError(
                            f"会社ロゴファイル '{self.report_config.company_logo_path}' の読み込み失敗: {e}",
                            user_message="会社ロゴの表示に失敗しました。",
                            severity=ErrorSeverity.WARNING,
                            context={"logo_path": self.report_config.company_logo_path, "exception": str(e)}
                        )
                    )
                    self.logger.warning(f"会社ロゴの読み込み失敗: {self.report_config.company_logo_path}, エラー: {e}")
            elif self.report_config.company_logo_path:
                 self.logger.warning(f"会社ロゴファイルが見つかりません: {self.report_config.company_logo_path}")

            story.append(Paragraph("損害賠償額計算書", self.styles['MainTitle']))
            story.append(Spacer(1, 5*mm))
            
            header_data = [
                [Paragraph("案件番号:", self.styles['Normal']), Paragraph(str(self.case_data.case_number or '未設定'), self.styles['Normal'])],
                [Paragraph("依頼者名:", self.styles['Normal']), Paragraph(str(self.case_data.person_info.name or '未設定'), self.styles['Normal'])],
                [Paragraph("作成日:", self.styles['Normal']), Paragraph(datetime.now().strftime("%Y年%m月%d日"), self.styles['Normal'])],
                [Paragraph("作成者:", self.styles['Normal']), Paragraph(self.report_config.default_author or '未設定', self.styles['Normal'])],
            ]
            header_table = Table(header_data, colWidths=[40*mm, None])
            header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm)]))
            story.append(header_table)
            story.append(Spacer(1, 10*mm))

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
            basic_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 2*mm), ('RIGHTPADDING', (0,0), (-1,-1), 2*mm)]))
            story.append(basic_table)
            story.append(Spacer(1, 7*mm))

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
            medical_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 2*mm), ('RIGHTPADDING', (0,0), (-1,-1), 2*mm), ('SPAN', (1,6), (-1,6))]))
            story.append(medical_table)
            story.append(Spacer(1, 7*mm))

            story.append(Paragraph("3. 収入・損害情報", self.styles['SubTitle']))
            inc_info = self.case_data.income_info
            income_info_data = [
                [Paragraph("休業日数:", self.styles['TableCell']), Paragraph(f"{inc_info.lost_work_days} 日" if inc_info.lost_work_days is not None else '-', self.styles['TableCell'])],
                [Paragraph("日額基礎収入:", self.styles['TableCell']), Paragraph(f"{inc_info.daily_income:,.0f} 円" if inc_info.daily_income is not None else '-', self.styles['TableCellRight'])],
                [Paragraph("基礎年収（逸失利益用）:", self.styles['TableCell']), Paragraph(f"{inc_info.base_annual_income:,.0f} 円" if inc_info.base_annual_income is not None else '-', self.styles['TableCellRight'])],
                [Paragraph("労働能力喪失期間:", self.styles['TableCell']), Paragraph(f"{inc_info.loss_period_years} 年" if inc_info.loss_period_years is not None else '-', self.styles['TableCell'])],
                [Paragraph("就労可能年数上限:", self.styles['TableCell']), Paragraph(f"{self.case_data.person_info.retirement_age} 歳" if self.case_data.person_info.retirement_age is not None else '-', self.styles['TableCell'])], # Corrected to use retirement_age from PersonInfo
            ]
            income_table = Table(income_info_data, colWidths=[50*mm, None])
            income_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 2*mm), ('RIGHTPADDING', (0,0), (-1,-1), 2*mm)]))
            story.append(income_table)
            story.append(Spacer(1, 10*mm))
            
            story.append(PageBreak())

            story.append(Paragraph("4. 損害賠償額計算結果", self.styles['SubTitle']))
            results_header_items = [
                Paragraph("<b>費目</b>", self.styles['TableHeader']),
                Paragraph("<b>金額（円）</b>", self.styles['TableHeader']),
            ]
            if self.report_config.include_detailed_calculation_in_pdf:
                results_header_items.append(Paragraph("<b>計算根拠・備考</b>", self.styles['TableHeader']))
            results_data = [results_header_items]
            
            display_order = [
                'hospitalization', 'disability', 'lost_income', 
                'future_income_loss', 'medical_expenses', 'legal_interest',
            ]
            calculated_keys = [k for k in self.calculation_results.keys() if k != 'summary']
            sorted_keys = sorted(
                calculated_keys,
                key=lambda k: (display_order.index(k) if k in display_order else float('inf'), k)
            )

            grand_total_before_fault_offset = Decimal('0')

            for key in sorted_keys:
                result = self.calculation_results.get(key)
                if not isinstance(result, CalculationResult):
                    continue

                if isinstance(result.amount, Decimal):
                     grand_total_before_fault_offset += result.amount

                if result.amount != Decimal('0') or (key == 'legal_interest' and result.calculation_details):
                    row_content = [
                        Paragraph(result.item_name, self.styles['TableCell']),
                        Paragraph(f"{result.amount:,.0f}", self.styles['TableCellRight']),
                    ]
                    if self.report_config.include_detailed_calculation_in_pdf:
                        details_content = ""
                        if result.calculation_details:
                            if key == 'legal_interest' or "利息" in result.item_name: 
                                try:
                                    details_content = self._create_detail_table(result.calculation_details)
                                except Exception as e:
                                    self.logger.error(f"Failed to create detail table for {result.item_name}: {e}")
                                    details_content = Paragraph(result.calculation_details, self.styles['SmallText'])
                            else:
                                temp_details = result.calculation_details or "-"
                                if len(temp_details) > 100:
                                    temp_details = temp_details[:100] + "..."
                                details_content = Paragraph(temp_details, self.styles['TableCell'])
                        else:
                            details_content = Paragraph("-", self.styles['TableCell'])
                        row_content.append(details_content)
                    results_data.append(row_content)
            
            total_row_before_offset = [
                Paragraph("<b>合計（過失相殺前）</b>", self.styles['TableCell']),
                Paragraph(f"<b>{grand_total_before_fault_offset:,.0f}</b>", self.styles['TableCellRight']),
            ]
            if self.report_config.include_detailed_calculation_in_pdf:
                total_row_before_offset.append(Paragraph("", self.styles['TableCell']))
            results_data.append(total_row_before_offset)
            
            fault_percentage = self.case_data.person_info.fault_percentage or 0
            fault_offset_amount = (grand_total_before_fault_offset * Decimal(str(fault_percentage)) / Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            offset_row = [
                Paragraph(f"過失相殺（{fault_percentage}%）", self.styles['TableCell']),
                Paragraph(f"<u>-{fault_offset_amount:,.0f}</u>", self.styles['TableCellRight']),
            ]
            if self.report_config.include_detailed_calculation_in_pdf:
                offset_row.append(Paragraph(f"{grand_total_before_fault_offset:,.0f}円 × {fault_percentage}%", self.styles['TableCell']))
            results_data.append(offset_row)

            final_total_amount = grand_total_before_fault_offset - fault_offset_amount
            final_total_row = [
                Paragraph("<b>最終合計金額</b>", self.styles['TableCell']),
                Paragraph(f"<b>{final_total_amount:,.0f}</b>", self.styles['TableCellRight']),
            ]
            if self.report_config.include_detailed_calculation_in_pdf:
                final_total_row.append(Paragraph("", self.styles['TableCell']))
            results_data.append(final_total_row)

            col_widths = [60*mm, 40*mm]
            if self.report_config.include_detailed_calculation_in_pdf:
                col_widths.append(None)

            results_table = Table(results_data, colWidths=col_widths)
            table_style_commands = [
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4682B4")), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'), 
                ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
                ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
                ('LINEBELOW', (0,-2), (-1,-2), 1, colors.black), 
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black, None, None, 2, 0), 
                ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.black, None, None, 0, 0), 
            ]
            results_table.setStyle(TableStyle(table_style_commands))
            story.append(results_table)
            story.append(Spacer(1, 10*mm))

            story.append(Paragraph("---", self.styles['Normal']))
            story.append(Spacer(1, 2*mm))
            disclaimer = "この計算書は、提供された情報に基づいて作成された概算であり、法的な助言や最終的な賠償金額を保証するものではありません。具体的な事案については、弁護士にご相談ください。"
            story.append(Paragraph(disclaimer, self.styles['SmallText']))

            doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            self.logger.info(f"PDFレポート '{filepath}' が正常に生成されました。")

        except CompensationSystemError as e:
            self.error_handler.handle_exception(e)
            self.logger.error(f"PDFレポート生成中にエラー（CompensationSystemError）: {e.log_message}")
        except Exception as e:
            tb_str = traceback.format_exc()
            self.error_handler.handle_exception(
                CompensationSystemError(
                    f"PDFレポート生成中に予期せぬエラー: {e}",
                    user_message="PDFレポート作成中に予期しない問題が発生しました。",
                    category=ErrorCategory.REPORT_GENERATION,
                    severity=ErrorSeverity.CRITICAL,
                    context={"filepath": filepath, "exception_type": type(e).__name__, "traceback": tb_str}
                )
            )
            self.logger.error(f"PDFレポート '{filepath}' 生成中に予期せぬエラー: {e}\n{tb_str}")

    def _add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(self.styles['Footer'].fontName, self.styles['Footer'].fontSize)
        page_num_text = f"Page {doc.page}"
        canvas.drawCentredString(A4[0]/2, 10*mm, page_num_text)
        canvas.restoreState()

if __name__ == '__main__':
    from config.app_config import load_config
    from decimal import Decimal

    try:
        # NOTE: Adjust this path to your actual config file location for testing
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'app_config.json')
        if not os.path.exists(config_path):
             # Fallback for execution from a different CWD, e.g. project root
             config_path = os.path.join('config', 'app_config.json') 
        if not os.path.exists(config_path):
            print(f"テスト用の設定ファイルが見つかりません: {config_path}")
            # Create a dummy config for basic testing if none found
            class DummyReportConfig:
                font_name_gothic = "Helvetica" # Fallback font
                font_path_gothic = "" 
                default_output_directory = "output_reports_test"
                company_logo_path = ""
                default_author = "Test Author"
                include_detailed_calculation_in_pdf = True
            class DummyAppConfig:
                report = DummyReportConfig()
            app_config = DummyAppConfig()
            if not os.path.exists(app_config.report.default_output_directory):
                os.makedirs(app_config.report.default_output_directory)
            print("警告: 設定ファイルが見つからないため、基本的なフォールバック設定でテストを実行します。")
        else:
            app_config = load_config(config_path)
            
        case_data = CaseData(
            case_number="TEST-PDF-001",
            person_info=CaseData().person_info.from_dict({'name':"テスト次郎", 'age':40, 'gender':"男性", 'occupation':"エンジニア", 'annual_income':"6000000", 'fault_percentage':20.0, 'retirement_age':67}),
            accident_info=CaseData().accident_info.from_dict({'accident_date':"2023-03-10", 'symptom_fixed_date':"2023-09-10"}),
            medical_info=CaseData().medical_info.from_dict({'hospital_months':2, 'outpatient_months':7, 'actual_outpatient_days':60, 'is_whiplash':True, 'disability_grade':12, 'disability_details':"腰椎捻挫による持続的な腰痛と可動域制限"}),
            income_info=CaseData().income_info.from_dict({'lost_work_days':45, 'daily_income':"20000", 'base_annual_income':"5800000", 'loss_period_years':10})
        )
        
        calculation_results = {
            'medical_expenses': CalculationResult(item_name="治療関係費", amount=Decimal("800000"), calculation_details="領収書に基づく実費合計"),
            'hospitalization': CalculationResult(item_name="入院慰謝料", amount=Decimal("360000"), calculation_details="赤い本基準: 2ヶ月"),
            'lost_income': CalculationResult(item_name="休業損害", amount=Decimal("900000"), calculation_details="20,000円/日 × 45日"),
            'disability': CalculationResult(item_name="後遺障害慰謝料", amount=Decimal("2900000"), calculation_details="12級基準（むちうち以外）"),
            'future_income_loss': CalculationResult(item_name="逸失利益", amount=Decimal("5000000"), calculation_details="基礎年収580万 × 14% × 10年対応ライプニッツ係数X.XXX"),
            'legal_interest': CalculationResult(
                item_name="治療費等に対する遅延損害金", 
                amount=Decimal("75000"), 
                calculation_details=(
                    "Principal: 800,000円\n"
                    "Annual Interest Rate: 3.00%\n"
                    "Interest Period: 2023-03-10 to 2024-03-10\n"
                    "Total Days: 366日\n"
                    "Calculation: 800,000円 × 0.0300 (年利) × (366日 / 365日) = 75,000円" # Example, actual calc may vary
                )
            ),
            'summary': CalculationResult(item_name="総合計", amount=Decimal("0"), calculation_details="") # Summary will be recalculated
        }
        # Simulate what CompensationEngine's calculate_all would produce for summary
        summary_result = CalculationResult(item_name="総合計", amount=Decimal('0'), calculation_details="")
        current_total = sum(res.amount for key, res in calculation_results.items() if key != 'summary' and isinstance(res.amount, Decimal))
        fault_perc = case_data.person_info.fault_percentage or 0
        total_after_fault = current_total * (Decimal(1) - Decimal(str(fault_perc))/Decimal(100))
        # Simplified lawyer fee for test
        lawyer_fee_test = total_after_fault * Decimal('0.1')
        summary_result.amount = (total_after_fault + lawyer_fee_test).quantize(Decimal('1'), ROUND_HALF_UP)
        summary_result.calculation_details = f"損害合計（過失相殺前）: {current_total:,.0f}円\n被害者過失割合: {fault_perc}%\n損害合計（過失相殺後）: {total_after_fault:,.0f}円\n弁護士費用（概算）: {lawyer_fee_test:,.0f}円\n最終支払見込額: {summary_result.amount:,.0f}円"
        calculation_results['summary'] = summary_result


        generator = PdfReportGenerator(app_config, case_data, calculation_results)
        output_pdf_filename = f"test_report_{case_data.case_number}.pdf"
        generator.generate_report(output_pdf_filename)
        print(f"テストレポート '{os.path.join(app_config.report.default_output_directory, output_pdf_filename)}' が生成されました。")

    except ConfigurationError as ce:
        print(f"設定エラー: {ce.user_message} (詳細はログを確認)")
    except FileNotFoundError as fnfe:
        print(f"ファイルが見つかりません: {fnfe}")
    except Exception as ex:
        print(f"テスト中に予期せぬエラーが発生しました: {ex}")
        traceback.print_exc()
