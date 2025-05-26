#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案件データモデル定義
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, List, Any
import json
from decimal import Decimal # Ensure Decimal is imported

@dataclass
class PersonInfo:
    """個人情報データクラス"""
    name: str = ""
    age: int = 0
    gender: str = ""
    occupation: str = ""
    annual_income: Decimal = field(default_factory=lambda: Decimal('0'))
    fault_percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'occupation': self.occupation,
            'annual_income': str(self.annual_income),
            'fault_percentage': self.fault_percentage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonInfo':
        return cls(
            name=data.get('name', ''),
            age=data.get('age', 0),
            gender=data.get('gender', ''),
            occupation=data.get('occupation', ''),
            annual_income=Decimal(data.get('annual_income', '0')),
            fault_percentage=data.get('fault_percentage', 0.0)
        )

@dataclass
class AccidentInfo:
    """事故情報データクラス"""
    accident_date: Optional[date] = None
    symptom_fixed_date: Optional[date] = None
    location: str = ""
    weather: str = ""
    road_condition: str = ""
    accident_type: str = ""
    police_report_number: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'accident_date': self.accident_date.isoformat() if self.accident_date else None,
            'symptom_fixed_date': self.symptom_fixed_date.isoformat() if self.symptom_fixed_date else None,
            'location': self.location,
            'weather': self.weather,
            'road_condition': self.road_condition,
            'accident_type': self.accident_type,
            'police_report_number': self.police_report_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccidentInfo':
        return cls(
            accident_date=datetime.fromisoformat(data['accident_date']).date() if data.get('accident_date') else None,
            symptom_fixed_date=datetime.fromisoformat(data['symptom_fixed_date']).date() if data.get('symptom_fixed_date') else None,
            location=data.get('location', ''),
            weather=data.get('weather', ''),
            road_condition=data.get('road_condition', ''),
            accident_type=data.get('accident_type', ''),
            police_report_number=data.get('police_report_number', '')
        )

@dataclass
class MedicalInfo:
    """医療情報データクラス"""
    hospital_months: int = 0
    outpatient_months: int = 0
    actual_outpatient_days: int = 0
    is_whiplash: bool = False
    disability_grade: int = 0
    disability_details: str = ""
    medical_expenses: Decimal = field(default_factory=lambda: Decimal('0'))
    transportation_costs: Decimal = field(default_factory=lambda: Decimal('0'))
    nursing_costs: Decimal = field(default_factory=lambda: Decimal('0'))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hospital_months': self.hospital_months,
            'outpatient_months': self.outpatient_months,
            'actual_outpatient_days': self.actual_outpatient_days,
            'is_whiplash': self.is_whiplash,
            'disability_grade': self.disability_grade,
            'disability_details': self.disability_details,
            'medical_expenses': str(self.medical_expenses),
            'transportation_costs': str(self.transportation_costs),
            'nursing_costs': str(self.nursing_costs)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MedicalInfo':
        return cls(
            hospital_months=data.get('hospital_months', 0),
            outpatient_months=data.get('outpatient_months', 0),
            actual_outpatient_days=data.get('actual_outpatient_days', 0),
            is_whiplash=data.get('is_whiplash', False),
            disability_grade=data.get('disability_grade', 0),
            disability_details=data.get('disability_details', ''),
            medical_expenses=Decimal(data.get('medical_expenses', '0')),
            transportation_costs=Decimal(data.get('transportation_costs', '0')),
            nursing_costs=Decimal(data.get('nursing_costs', '0'))
        )

@dataclass
class IncomeInfo:
    """収入情報データクラス"""
    lost_work_days: int = 0
    daily_income: Decimal = field(default_factory=lambda: Decimal('0'))
    loss_period_years: int = 0
    retirement_age: int = 67
    basic_annual_income: Decimal = field(default_factory=lambda: Decimal('0'))
    bonus_ratio: float = 0.0  # ボーナス比率
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lost_work_days': self.lost_work_days,
            'daily_income': str(self.daily_income),
            'loss_period_years': self.loss_period_years,
            'retirement_age': self.retirement_age,
            'basic_annual_income': str(self.basic_annual_income),
            'bonus_ratio': self.bonus_ratio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IncomeInfo':
        return cls(
            lost_work_days=data.get('lost_work_days', 0),
            daily_income=Decimal(data.get('daily_income', '0')),
            loss_period_years=data.get('loss_period_years', 0),
            retirement_age=data.get('retirement_age', 67),
            basic_annual_income=Decimal(data.get('basic_annual_income', '0')),
            bonus_ratio=data.get('bonus_ratio', 0.0)
        )

@dataclass
class InterestCalculationInput:
    """Inputs for legal interest calculation"""
    principal_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    interest_start_date: Optional[date] = None
    interest_end_date: Optional[date] = None
    description: str = "法定利息"  # Default description for the interest item

    def to_dict(self) -> Dict[str, Any]:
        return {
            'principal_amount': str(self.principal_amount),
            'interest_start_date': self.interest_start_date.isoformat() if self.interest_start_date else None,
            'interest_end_date': self.interest_end_date.isoformat() if self.interest_end_date else None,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterestCalculationInput':
        # Ensure correct parsing for dates that might be None
        start_date_str = data.get('interest_start_date')
        end_date_str = data.get('interest_end_date')
        
        return cls(
            principal_amount=Decimal(data.get('principal_amount', '0')),
            interest_start_date=date.fromisoformat(start_date_str) if start_date_str else None,
            interest_end_date=date.fromisoformat(end_date_str) if end_date_str else None,
            description=data.get('description', "法定利息")
        )

@dataclass
class CaseData:
    """包括的な案件データ"""
    case_number: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    status: str = "作成中"  # 作成中, 計算完了, 最終確定, アーカイブ
    person_info: PersonInfo = field(default_factory=PersonInfo)
    accident_info: AccidentInfo = field(default_factory=AccidentInfo)
    medical_info: MedicalInfo = field(default_factory=MedicalInfo)
    income_info: IncomeInfo = field(default_factory=IncomeInfo) # Keep existing field order for clarity
    interest_input: Optional[InterestCalculationInput] = field(default=None) # Add new field here
    notes: str = ""
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    calculation_results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'case_number': self.case_number,
            'created_date': self.created_date.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'status': self.status,
            'person_info': self.person_info.to_dict(),
            'accident_info': self.accident_info.to_dict(),
            'medical_info': self.medical_info.to_dict(),
            'income_info': self.income_info.to_dict(),
            'interest_input': self.interest_input.to_dict() if self.interest_input else None, # Add to_dict logic
            'notes': self.notes,
            'custom_fields': self.custom_fields,
            'calculation_results': self.calculation_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CaseData':
        # Ensure interest_input is correctly parsed if present
        interest_input_data = data.get('interest_input')
        interest_input_obj = InterestCalculationInput.from_dict(interest_input_data) if interest_input_data else None
        
        return cls(
            case_number=data.get('case_number', ''),
            created_date=datetime.fromisoformat(data.get('created_date', datetime.now().isoformat())),
            last_modified=datetime.fromisoformat(data.get('last_modified', datetime.now().isoformat())),
            status=data.get('status', '作成中'),
            person_info=PersonInfo.from_dict(data.get('person_info', {})),
            accident_info=AccidentInfo.from_dict(data.get('accident_info', {})),
            medical_info=MedicalInfo.from_dict(data.get('medical_info', {})),
            income_info=IncomeInfo.from_dict(data.get('income_info', {})),
            interest_input=interest_input_obj, # Add from_dict logic
            notes=data.get('notes', ''),
            custom_fields=data.get('custom_fields', {}),
            calculation_results=data.get('calculation_results', {})
        )
    
    def save_to_json(self, filepath: str) -> None:
        """JSONファイルに保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2, default=str)
    
    @classmethod
    def load_from_json(cls, filepath: str) -> 'CaseData':
        """JSONファイルから読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
