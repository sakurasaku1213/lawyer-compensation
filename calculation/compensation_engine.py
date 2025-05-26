#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
損害賠償計算エンジン
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from typing import Dict, Optional, Any

from models.case_data import (
    CaseData, PersonInfo, AccidentInfo, MedicalInfo, IncomeInfo, 
    InterestCalculationInput # Added InterestCalculationInput
)
from utils.error_handling import ErrorSeverity, CalculationError, ErrorHandler # Assuming ErrorHandler exists
from utils.logging_config import setup_logging # Assuming setup_logging exists

# Import interest calculation functions
from .interest import (
    get_applicable_annual_interest_rate,
    calculate_simple_interest,
    LegalInterestError
)

# Default values and constants
DEFAULT_RETIREMENT_AGE = 67
HOSPITALIZATION_CONSOLATION_BASE = { #入院慰謝料基準（赤い本基準）
    1: Decimal('190000'), 2: Decimal('360000'), 3: Decimal('530000'),
    4: Decimal('700000'), 5: Decimal('850000'), 6: Decimal('980000') 
} # Extend this as needed or use a more complex calculation

DISABILITY_CONSOLATION_BASE = { #後遺障害慰謝料（赤い本別表I）
    1: Decimal('28000000'), 2: Decimal('23700000'), 3: Decimal('19900000'),
    # ... (Fill in all grades)
    14: Decimal('1100000')
} # Extend this as needed

DISABILITY_LABOR_CAPACITY_LOSS_RATE = { #労働能力喪失率（後遺障害等級別）
    1: 1.0, 2: 1.0, 3: 1.0, 4: 0.92, 5: 0.79, 6: 0.67, 7: 0.56,
    8: 0.45, 9: 0.35, 10: 0.27, 11: 0.20, 12: 0.14, 13: 0.09, 14: 0.05
} # Extend this as needed

#ライプニッツ係数 (簡易版 - 年数に対応する係数を定義)
#実際の計算ではより精密なテーブルまたは計算式を使用
HOFFMANN_COEFFICIENTS_PRE_2020 = { # 2020年3月31日まで
    1: Decimal('0.9524'), 5: Decimal('4.3295'), 10: Decimal('7.7217'), 
    15: Decimal('10.3797'), 20: Decimal('12.4622'), 25: Decimal('14.0939'),
    # ... (add more as needed)
}
LEIBNIZ_COEFFICIENTS_POST_2020 = { # 2020年4月1日以降（法定利率3%の場合の例）
    1: Decimal('0.9709'), 5: Decimal('4.5797'), 10: Decimal('8.5302'),
    15: Decimal('11.9379'), 20: Decimal('14.8775'), 25: Decimal('17.4131'),
    # ... (add more as needed)
}

@dataclass
class CalculationResult:
    item_name: str
    amount: Decimal
    calculation_details: str
    legal_basis: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_name": self.item_name,
            "amount": str(self.amount), # Convert Decimal to string for serialization
            "calculation_details": self.calculation_details,
            "legal_basis": self.legal_basis,
            "notes": self.notes,
        }

class CompensationEngine:
    """
    損害賠償額を計算するクラス
    """
    def __init__(self, error_handler: Optional[ErrorHandler] = None, logger: Optional[logging.Logger] = None):
        self.standards = {} # Calculation standards (e.g., Red Book, Blue Book)
        self._error_handler = error_handler if error_handler else ErrorHandler()
        self.logger = logger if logger else setup_logging() # Use setup_logging or a default logger
        self.init_standards()

    def init_standards(self, standard_type: str = "RedBook"):
        """計算基準の初期化（例：赤い本）"""
        if standard_type == "RedBook":
            self.standards['hospitalization_consolation'] = HOSPITALIZATION_CONSOLATION_BASE
            self.standards['disability_consolation'] = DISABILITY_CONSOLATION_BASE
            self.standards['labor_capacity_loss_rate'] = DISABILITY_LABOR_CAPACITY_LOSS_RATE
            # Add other standards as needed
        else:
            # Potentially load other standards or raise error
            self.logger.warning(f"Standard type '{standard_type}' not fully implemented. Using defaults.")
            # Fallback to some default if necessary
            self.standards['hospitalization_consolation'] = HOSPITALIZATION_CONSOLATION_BASE
            self.standards['disability_consolation'] = DISABILITY_CONSOLATION_BASE
            self.standards['labor_capacity_loss_rate'] = DISABILITY_LABOR_CAPACITY_LOSS_RATE

    def _get_leibniz_or_hoffmann_coefficient(self, period_years: int, calculation_date: date) -> Decimal:
        """
        ライプニッツ係数またはホフマン係数を取得
        2020年4月1日を境に法定利率と使用する係数が変わる
        """
        if period_years <= 0: return Decimal('0')

        # 簡易的な実装：期間に最も近い定義済み係数を使用
        # より正確な実装では、期間ごとに精密な値を計算または参照する
        if calculation_date < date(2020, 4, 1): # ホフマン係数（旧法定利率5%）
            coeffs = HOFFMANN_COEFFICIENTS_PRE_2020
            rate_type = "ホフマン係数"
        else: # ライプニッツ係数（新法定利率3%）
            coeffs = LEIBNIZ_COEFFICIENTS_POST_2020
            rate_type = "ライプニッツ係数"
        
        # Find closest available year in coeffs if exact match not found
        closest_year = min(coeffs.keys(), key=lambda y: abs(y - period_years))
        coefficient = coeffs[closest_year]
        
        self.logger.info(f"{period_years}年間の{rate_type}（{calculation_date}時点基準）: {coefficient} (参照年: {closest_year})")
        return coefficient

    def calculate_hospitalization_compensation(self, medical_info: MedicalInfo) -> CalculationResult:
        """入院慰謝料の計算"""
        months = medical_info.hospital_months
        if months <= 0:
            return CalculationResult("入院慰謝料", Decimal('0'), "入院期間なし")

        base_amounts = self.standards.get('hospitalization_consolation', HOSPITALIZATION_CONSOLATION_BASE)
        
        # Simple lookup: use the exact month if available, otherwise use the largest available for smaller months
        # or implement interpolation/extrapolation for more complex scenarios.
        # This example uses the value for the given month, or the max defined if month is larger.
        # A more robust version would define amounts for many more months or use a formula.
        if months in base_amounts:
            amount = base_amounts[months]
        elif months > max(base_amounts.keys()):
             # For months longer than defined, could extrapolate or use a per-diem based on the last increment.
             # Simple approach: use the max defined amount.
            amount = base_amounts[max(base_amounts.keys())] 
            details_note = f"入院期間{months}ヶ月は定義最大値({max(base_amounts.keys())}ヶ月)を適用。"
        else: # months < min(base_amounts.keys()) but > 0
            amount = base_amounts[min(base_amounts.keys())] # Use smallest defined for very short periods
            details_note = f"入院期間{months}ヶ月は定義最小値({min(base_amounts.keys())}ヶ月)を適用。"

        calc_details = f"入院期間: {months}ヶ月\n基準額: {amount:,.0f}円"
        if 'details_note' in locals(): calc_details += f"\n{details_note}"
        
        return CalculationResult(
            item_name="入院慰謝料",
            amount=amount,
            calculation_details=calc_details,
            legal_basis="赤い本 別表II等に基づく"
        )

    def calculate_disability_compensation(self, medical_info: MedicalInfo) -> CalculationResult:
        """後遺障害慰謝料の計算"""
        grade = medical_info.disability_grade
        if not grade or grade < 1 or grade > 14:
            return CalculationResult("後遺障害慰謝料", Decimal('0'), "後遺障害等級なし、または不適切な等級")

        base_amounts = self.standards.get('disability_consolation', DISABILITY_CONSOLATION_BASE)
        amount = base_amounts.get(grade, Decimal('0'))
        
        return CalculationResult(
            item_name=f"後遺障害慰謝料 ({grade}級)",
            amount=amount,
            calculation_details=f"後遺障害等級: {grade}級\n基準額: {amount:,.0f}円",
            legal_basis="赤い本 別表I等に基づく"
        )

    def calculate_lost_income(self, income_info: IncomeInfo) -> CalculationResult:
        """休業損害の計算"""
        if income_info.lost_work_days <= 0 or income_info.daily_income <= Decimal('0'):
            return CalculationResult("休業損害", Decimal('0'), "休業日数または日額収入なし")

        amount = income_info.daily_income * income_info.lost_work_days
        amount = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        
        return CalculationResult(
            item_name="休業損害",
            amount=amount,
            calculation_details=f"日額収入: {income_info.daily_income:,.0f}円\n休業日数: {income_info.lost_work_days}日\n計算: {income_info.daily_income:,.0f}円 × {income_info.lost_work_days}日 = {amount:,.0f}円",
            legal_basis="民法第709条、実務上の算定基準"
        )

    def calculate_future_income_loss(self, person_info: PersonInfo, medical_info: MedicalInfo, income_info: IncomeInfo) -> CalculationResult:
        """逸失利益の計算"""
        grade = medical_info.disability_grade
        if not grade or grade < 1 or grade > 14:
            return CalculationResult("逸失利益", Decimal('0'), "後遺障害等級なし、または不適切な等級")

        loss_rates = self.standards.get('labor_capacity_loss_rate', DISABILITY_LABOR_CAPACITY_LOSS_RATE)
        loss_rate = Decimal(str(loss_rates.get(grade, 0.0))) # Convert float to Decimal via str

        if loss_rate <= Decimal('0'):
            return CalculationResult("逸失利益", Decimal('0'), f"{grade}級では労働能力喪失なし")

        annual_income = income_info.basic_annual_income
        if annual_income <= Decimal('0'):
            # Fallback to person_info.annual_income if basic_annual_income is not set in income_info
            annual_income = person_info.annual_income 
            if annual_income <= Decimal('0'):
                 return CalculationResult("逸失利益", Decimal('0'), "基礎収入の情報なし")

        # 労働能力喪失期間の計算 (症状固定から定年まで。より複雑なケースでは就労可能年数表等も参照)
        # ここでは簡易的に定年から現在の年齢を引く
        # 症状固定日が必要。事故日を仮に使用。実際には症状固定日を使うべき
        # For simplicity, assuming calculation_date is today or a fixed date for coefficient lookup.
        # In a real app, this should be the date the calculation is legally relevant (e.g., court submission date).
        calculation_relevant_date = date.today() # Or CaseData.accident_info.symptom_fixed_date if available

        # Use loss_period_years from IncomeInfo if provided and valid, otherwise calculate
        if income_info.loss_period_years > 0:
            loss_period_years = income_info.loss_period_years
        else:
            age_at_fixation = person_info.age # This should be age at symptom_fixed_date
            retirement_age = income_info.retirement_age if income_info.retirement_age > age_at_fixation else DEFAULT_RETIREMENT_AGE
            loss_period_years = max(0, retirement_age - age_at_fixation)

        if loss_period_years <= 0:
            return CalculationResult("逸失利益", Decimal('0'), "労働能力喪失期間なし")

        coefficient = self._get_leibniz_or_hoffmann_coefficient(loss_period_years, calculation_relevant_date)
        
        # 計算式: 基礎収入 × 労働能力喪失率 × ライプニッツ係数（またはホフマン係数）
        lost_profit = annual_income * loss_rate * coefficient
        lost_profit = lost_profit.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        details = (
            f"基礎年収: {annual_income:,.0f}円\n"
            f"後遺障害等級: {grade}級\n"
            f"労働能力喪失率: {loss_rate*100:.0f}%\n"
            f"労働能力喪失期間: {loss_period_years}年 (係数適用日: {calculation_relevant_date.isoformat()})\n"
            f"適用係数 ({'ライプニッツ' if calculation_relevant_date >= date(2020,4,1) else 'ホフマン'}): {coefficient}\n"
            f"計算: {annual_income:,.0f}円 × {loss_rate:.2f} × {coefficient} = {lost_profit:,.0f}円"
        )
        
        return CalculationResult(
            item_name="逸失利益",
            amount=lost_profit,
            calculation_details=details,
            legal_basis="民法第709条、第416条、実務上の算定基準"
        )

    def calculate_medical_expenses(self, medical_info: MedicalInfo) -> CalculationResult:
        """治療費・医療関連費用の計算"""
        # This is typically actual expenses, so it's more about summing them up.
        # Here, we assume medical_expenses field in MedicalInfo is the total.
        if medical_info.medical_expenses < Decimal('0'): # Allow 0, but not negative
            raise CalculationError("医療費に負の値が設定されています。", "医療費は0以上である必要があります。")

        amount = medical_info.medical_expenses.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return CalculationResult(
            item_name="治療関係費",
            amount=amount,
            calculation_details=f"請求治療費合計: {amount:,.0f}円",
            notes="領収書等に基づき計上された実費"
        )
    
    def calculate_legal_interest(self, interest_input: Optional[InterestCalculationInput]) -> CalculationResult:
        """Calculates legal interest based on provided inputs."""
        if not interest_input:
            return CalculationResult(
                item_name="法定利息", # Default name if no description
                amount=Decimal('0'),
                calculation_details="法定利息の計算に必要な入力が提供されていません。",
                notes="入力データなし"
            )

        item_name = interest_input.description or "法定利息"

        if not all([interest_input.principal_amount, interest_input.interest_start_date, interest_input.interest_end_date]):
            return CalculationResult(
                item_name=item_name,
                amount=Decimal('0'),
                calculation_details="法定利息の計算に必要な主たる金額、開始日、または終了日が不足しています。",
                notes="入力不備"
            )
        
        if interest_input.principal_amount <= Decimal('0'):
             return CalculationResult(
                item_name=item_name,
                amount=Decimal('0'),
                calculation_details="主たる金額が0以下です。",
                notes="主たる金額なし"
            )

        try:
            # Ensure interest_start_date is a date object for get_applicable_annual_interest_rate
            if not isinstance(interest_input.interest_start_date, date):
                 # This case should ideally be caught by Pydantic/dataclass validation earlier
                 raise LegalInterestError("利息開始日が有効な日付オブジェクトではありません。")

            applicable_rate = get_applicable_annual_interest_rate(interest_input.interest_start_date)
            
            interest_amount, details_str = calculate_simple_interest(
                principal=interest_input.principal_amount,
                annual_rate=applicable_rate,
                start_date=interest_input.interest_start_date,
                end_date=interest_input.interest_end_date
            )
            
            # Replace literal \n with actual newlines for the final CalculationResult detail string
            formatted_details = details_str.replace('\\n', '\n')

            return CalculationResult(
                item_name=item_name,
                amount=interest_amount,
                calculation_details=formatted_details,
                legal_basis="民法第404条等に基づく" # General legal basis
            )

        except LegalInterestError as e:
            self.logger.error(f"Legal interest calculation error for '{item_name}': {str(e)}")
            return CalculationResult(
                item_name=item_name,
                amount=Decimal('0'),
                calculation_details=f"法定利息の計算エラー: {str(e)}",
                notes="計算エラー"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during legal interest calculation for '{item_name}': {str(e)}", exc_info=True)
            return CalculationResult(
                item_name=item_name,
                amount=Decimal('0'),
                calculation_details=f"予期せぬエラーにより法定利息を計算できませんでした: {str(e)}",
                notes="計算エラー"
            )

    def _estimate_lawyer_fee(self, amount_before_fee: Decimal) -> Decimal:
        """弁護士費用の概算 (例: 請求額の10% + 18万円)"""
        # This is a very common but simplified model. Actual fees vary.
        if amount_before_fee <= Decimal('0'):
            return Decimal('0')
        
        fee = amount_before_fee * Decimal('0.1') + Decimal('180000')
        return fee.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    def calculate_all(self, case_data: CaseData) -> Dict[str, CalculationResult]:
        """全損害項目の計算"""
        results = {}
        try:
            self.logger.info(f"計算開始: 案件番号 {case_data.case_number if case_data.case_number else 'N/A'}")

            results['hospitalization'] = self.calculate_hospitalization_compensation(case_data.medical_info)
            results['disability'] = self.calculate_disability_compensation(case_data.medical_info)
            results['lost_income'] = self.calculate_lost_income(case_data.income_info)
            results['future_income_loss'] = self.calculate_future_income_loss(
                case_data.person_info, case_data.medical_info, case_data.income_info
            )
            results['medical_expenses'] = self.calculate_medical_expenses(case_data.medical_info)
            
            # Add legal interest calculation
            results['legal_interest'] = self.calculate_legal_interest(case_data.interest_input) # New line

            # 合計額の計算
            total_before_deduction = Decimal('0')
            for key, result_obj in results.items():
                if result_obj and isinstance(result_obj, CalculationResult) and isinstance(result_obj.amount, Decimal):
                    total_before_deduction += result_obj.amount
            
            self.logger.info(f"過失相殺前の合計損害額: {total_before_deduction:,.0f}円")

            fault_percentage = case_data.person_info.fault_percentage
            if not isinstance(fault_percentage, (int, float, Decimal)):
                 self.logger.error(f"過失割合の型が無効: {type(fault_percentage)}")
                 raise TypeError(f"過失割合は数値である必要がありますが、{type(fault_percentage)} を受け取りました。")
            
            fault_ratio = Decimal(str(fault_percentage)) / Decimal('100')
            total_after_fault = total_before_deduction * (Decimal('1') - fault_ratio)
            total_after_fault = total_after_fault.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            self.logger.info(f"過失相殺後の合計損害額 ({fault_percentage}%): {total_after_fault:,.0f}円")
            
            lawyer_fee = self._estimate_lawyer_fee(total_after_fault)
            self.logger.info(f"概算弁護士費用: {lawyer_fee:,.0f}円")
            
            final_amount = total_after_fault + lawyer_fee
            self.logger.info(f"最終支払見込額: {final_amount:,.0f}円")
            
            results['summary'] = CalculationResult(
                item_name="総合計",
                amount=final_amount,
                calculation_details=(
                    f"損害合計（過失相殺前）: {total_before_deduction:,.0f}円\n"
                    f"被害者過失割合: {case_data.person_info.fault_percentage}%\n"
                    f"損害合計（過失相殺後）: {total_after_fault:,.0f}円\n"
                    f"弁護士費用（概算）: {lawyer_fee:,.0f}円\n"
                    f"最終支払見込額: {final_amount:,.0f}円"
                ),
                legal_basis="民法第709条、第722条等",
                notes="弁護士費用は一般的な概算です。実際の費用は個別の契約により異なります。"
            )
            self.logger.info(f"計算完了: 案件番号 {case_data.case_number if case_data.case_number else 'N/A'}")
            return results

        except CalculationError as e: 
            self.logger.error(f"計算処理中にエラー: {e.message} (User message: {e.user_message})", exc_info=True)
            # Ensure summary is populated even if other calculations failed partially
            error_summary_msg = f"計算エラー: {e.user_message} (詳細はログを確認してください)"
            if 'summary' not in results or not results['summary']: # If summary hasn't been made at all
                 results['summary'] = CalculationResult("総合計", Decimal('0'), error_summary_msg, notes="一部または全体の計算に失敗しました")
            else: # If summary exists but an error occurred elsewhere (e.g. during fault calc)
                 results['summary'].notes = (results['summary'].notes + f"; {error_summary_msg}") if results['summary'].notes else error_summary_msg
                 results['summary'].amount = Decimal('0') # Indicate failure by zeroing amount
                 results['summary'].calculation_details = error_summary_msg
            return results

        except Exception as e:
            # This is a fallback for truly unexpected errors.
            self.logger.critical(f"全体の損害額計算中に予期せぬ重大なエラー: {str(e)}", exc_info=True)
            
            # Use the error handler if available
            context = {"case_data_summary": str(case_data)[:200], "original_error": str(e)}
            if self._error_handler:
                 self._error_handler.handle_exception(e, severity=ErrorSeverity.CRITICAL, context=context)
            
            user_msg = "損害賠償額全体の計算中に予期せぬ重大なエラーが発生しました。管理者に連絡してください。"
            return {
                'summary': CalculationResult(
                    item_name="総合計", 
                    amount=Decimal('0'), 
                    calculation_details=user_msg,
                    notes="計算全体に致命的なエラーが発生しました。"
                )
            }

# Example Usage (for testing or demonstration)
if __name__ == '__main__':
    # Setup basic logging for demonstration
    logger = setup_logging(level=logging.DEBUG)
    error_handler = ErrorHandler(logger)
    engine = CompensationEngine(error_handler=error_handler, logger=logger)

    # Create sample CaseData
    sample_case = CaseData(
        case_number="EX001",
        person_info=PersonInfo(name="テスト被害者", age=30, fault_percentage=10.0),
        accident_info=AccidentInfo(accident_date=date(2022, 1, 15), symptom_fixed_date=date(2022, 7, 15)),
        medical_info=MedicalInfo(
            hospital_months=1, 
            outpatient_months=6, 
            actual_outpatient_days=50,
            disability_grade=14,
            medical_expenses=Decimal('500000')
        ),
        income_info=IncomeInfo(
            basic_annual_income=Decimal('4000000'),
            lost_work_days=30,
            daily_income=Decimal('10000') # 4000000 / 365 roughly, or actual daily rate
        ),
        interest_input=InterestCalculationInput( # Sample interest input
            principal_amount=Decimal('1000000'), # e.g. a portion of damages subject to interest
            interest_start_date=date(2022, 1, 15), # Typically accident date
            interest_end_date=date.today(), # Typically date of judgment or payment
            description="治療費等に対する遅延損害金"
        )
    )
    
    logger.info(f"--- Calculating for Case: {sample_case.case_number} ---")
    all_results = engine.calculate_all(sample_case)

    logger.info("\n--- 計算結果 ---")
    for item_name, result in all_results.items():
        logger.info(f"\n【{result.item_name}】")
        logger.info(f"  金額: {result.amount:,.0f}円")
        logger.info(f"  計算根拠:\n{result.calculation_details.replace(chr(10), chr(10) + '    ')}") # Indent details
        if result.legal_basis:
            logger.info(f"  法的根拠: {result.legal_basis}")
        if result.notes:
            logger.info(f"  備考: {result.notes}")

    logger.info(f"\n--- Example of accessing a specific result ---")
    if 'legal_interest' in all_results:
        li_result = all_results['legal_interest']
        logger.info(f"Calculated Legal Interest: {li_result.amount:,.0f}円 for '{li_result.item_name}'")

    logger.info("\n--- Example with missing interest input ---")
    sample_case_no_interest = CaseData(
        case_number="EX002",
        person_info=PersonInfo(name="テスト被害者2", age=40, fault_percentage=0),
        medical_info=MedicalInfo(medical_expenses=Decimal('10000')),
        interest_input=None # No interest input
    )
    results_no_interest = engine.calculate_all(sample_case_no_interest)
    logger.info(f"Legal interest for EX002: {results_no_interest.get('legal_interest', {}).get('amount', 'N/A')}")
    logger.info(f"Summary for EX002: {results_no_interest.get('summary', {}).get('amount', 'N/A')}")


    logger.info("\n--- Example with interest input but missing dates/principal ---")
    sample_case_incomplete_interest = CaseData(
        case_number="EX003",
         person_info=PersonInfo(name="テスト被害者3", age=40, fault_percentage=0),
        medical_info=MedicalInfo(medical_expenses=Decimal('10000')),
        interest_input=InterestCalculationInput(principal_amount=Decimal('50000')) # Missing dates
    )
    results_incomplete_interest = engine.calculate_all(sample_case_incomplete_interest)
    li_result_incomplete = results_incomplete_interest.get('legal_interest')
    if li_result_incomplete:
        logger.info(f"Legal interest for EX003: {li_result_incomplete.amount} (Notes: {li_result_incomplete.notes})")
        logger.info(f"Details: {li_result_incomplete.calculation_details}")
    logger.info(f"Summary for EX003: {results_incomplete_interest.get('summary', {}).get('amount', 'N/A')}")

    logger.info("\n--- Example with interest on pre-2020 accident date ---")
    sample_case_old_law = CaseData(
        case_number="EX004",
        person_info=PersonInfo(name="テスト被害者旧法", age=50, fault_percentage=0),
        medical_info=MedicalInfo(medical_expenses=Decimal('200000')),
        interest_input=InterestCalculationInput(
            principal_amount=Decimal('200000'),
            interest_start_date=date(2019, 1, 1), # Pre new law
            interest_end_date=date(2020, 3, 31),   # Still pre new law adjustment
            description="旧法定利率対象の損害金"
        )
    )
    results_old_law = engine.calculate_all(sample_case_old_law)
    li_result_old_law = results_old_law.get('legal_interest')
    if li_result_old_law:
        logger.info(f"Legal interest for EX004: {li_result_old_law.amount:,.0f}円 (Notes: {li_result_old_law.notes})")
        logger.info(f"Details:\n{li_result_old_law.calculation_details}")

    logger.info(f"Summary for EX004: {results_old_law.get('summary', {}).get('amount', 'N/A')}")
    logger.info("--- Compensation Engine Example Run Finished ---")
