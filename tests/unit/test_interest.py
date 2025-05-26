# tests/unit/test_interest.py
import unittest
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

# Assuming interest.py is in calculation directory and tests/unit is at the same level as calculation
# Adjust path if necessary, e.g., by adding to sys.path or using relative imports if structured as a package
import sys
import os
# Add the parent directory of 'calculation' to sys.path to allow direct import
# This assumes the script is run from a context where 'calculation' is a subdirectory
# or 'tests' and 'calculation' are sibling directories.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from calculation.interest import (
    get_applicable_annual_interest_rate,
    calculate_simple_interest,
    LegalInterestError,
    NEW_LAW_START_DATE,
    OLD_CIVIL_LEGAL_INTEREST_RATE,
    NEW_LEGAL_INTEREST_RATE_INITIAL
)

class TestInterestCalculation(unittest.TestCase):

    def test_get_applicable_annual_interest_rate(self):
        # Test date before new law
        self.assertEqual(get_applicable_annual_interest_rate(date(2020, 3, 31)), OLD_CIVIL_LEGAL_INTEREST_RATE)
        self.assertEqual(get_applicable_annual_interest_rate(date(2019, 1, 1)), OLD_CIVIL_LEGAL_INTEREST_RATE)

        # Test date on new law start
        self.assertEqual(get_applicable_annual_interest_rate(date(2020, 4, 1)), NEW_LEGAL_INTEREST_RATE_INITIAL)

        # Test date after new law
        self.assertEqual(get_applicable_annual_interest_rate(date(2021, 1, 1)), NEW_LEGAL_INTEREST_RATE_INITIAL)
        self.assertEqual(get_applicable_annual_interest_rate(date(2023, 12, 31)), NEW_LEGAL_INTEREST_RATE_INITIAL)
        
        # Test with non-date input
        with self.assertRaisesRegex(LegalInterestError, "accrual_start_date must be a valid date object."):
            get_applicable_annual_interest_rate("not-a-date")

    def test_calculate_simple_interest_old_rate_one_year(self):
        principal = Decimal('1000000')
        rate = OLD_CIVIL_LEGAL_INTEREST_RATE # 5%
        start = date(2019, 4, 1)
        end = date(2020, 3, 31) # Exactly one year (366 days due to 2020 leap year)
        
        # Expected: 1,000,000 * 0.05 * (366/365) = 50136.986... rounded to 50137
        # Note: The calculation (P * R * Days) / 365 means leap year days are fully counted.
        expected_interest = (principal * rate * Decimal(366)) / Decimal(365)
        expected_interest = expected_interest.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        self.assertEqual(expected_interest, Decimal('50137'))

        interest, details = calculate_simple_interest(principal, rate, start, end)
        self.assertEqual(interest, expected_interest)
        self.assertIn(f"Principal: {principal:,.2f}円", details)
        self.assertIn(f"Annual Interest Rate: {rate*100:.2f}%", details)
        self.assertIn(f"Total Days: 366日", details) # 2020 is a leap year
        self.assertIn(f"= {expected_interest:,.0f}円", details)

    def test_calculate_simple_interest_new_rate_one_year(self):
        principal = Decimal('1000000')
        rate = NEW_LEGAL_INTEREST_RATE_INITIAL # 3%
        start = date(2020, 4, 1)
        end = date(2021, 3, 31) # Exactly one year (365 days)
        
        # Expected: 1,000,000 * 0.03 * (365/365) = 30000
        expected_interest = (principal * rate * Decimal(365)) / Decimal(365)
        expected_interest = expected_interest.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        self.assertEqual(expected_interest, Decimal('30000'))
        
        interest, details = calculate_simple_interest(principal, rate, start, end)
        self.assertEqual(interest, expected_interest)
        self.assertIn(f"Principal: {principal:,.2f}円", details)
        self.assertIn(f"Annual Interest Rate: {rate*100:.2f}%", details)
        self.assertIn(f"Total Days: 365日", details)
        self.assertIn(f"= {expected_interest:,.0f}円", details)

    def test_calculate_simple_interest_new_rate_part_year(self):
        principal = Decimal('500000')
        rate = NEW_LEGAL_INTEREST_RATE_INITIAL # 3%
        start = date(2021, 1, 1)
        end = date(2021, 6, 30) # 181 days
        # Days: Jan(31) + Feb(28) + Mar(31) + Apr(30) + May(31) + Jun(30) = 181 days
        total_days = (end - start).days + 1
        self.assertEqual(total_days, 181)

        expected_interest = (principal * rate * Decimal(total_days)) / Decimal(365)
        expected_interest = expected_interest.quantize(Decimal('1'), rounding=ROUND_HALF_UP) # 7438.35... -> 7438
        self.assertEqual(expected_interest, Decimal('7438'))

        interest, _ = calculate_simple_interest(principal, rate, start, end)
        self.assertEqual(interest, expected_interest)

    def test_calculate_simple_interest_multi_year_跨る(self):
        principal = Decimal('100000')
        rate = OLD_CIVIL_LEGAL_INTEREST_RATE # 5%
        start = date(2018, 1, 1)
        end = date(2020, 12, 31) # 3 years exactly (2018, 2019, 2020-leap)
        # Days: 365 (2018) + 365 (2019) + 366 (2020) = 1096 days
        total_days = (end - start).days + 1
        self.assertEqual(total_days, 1096)

        expected_interest = (principal * rate * Decimal(total_days)) / Decimal(365)
        expected_interest = expected_interest.quantize(Decimal('1'), rounding=ROUND_HALF_UP) # 15013.69... -> 15014
        self.assertEqual(expected_interest, Decimal('15014'))
        
        interest, _ = calculate_simple_interest(principal, rate, start, end)
        self.assertEqual(interest, expected_interest)

    def test_calculate_simple_interest_zero_principal(self):
        interest, details = calculate_simple_interest(Decimal('0'), NEW_LEGAL_INTEREST_RATE_INITIAL, date(2020, 1, 1), date(2020, 12, 31))
        self.assertEqual(interest, Decimal('0'))
        self.assertEqual(details, "Principal is zero or negative, no interest calculated.")

    def test_calculate_simple_interest_zero_rate(self):
        interest, details = calculate_simple_interest(Decimal('1000000'), Decimal('0'), date(2020, 1, 1), date(2020, 12, 31))
        self.assertEqual(interest, Decimal('0'))
        self.assertEqual(details, "Annual rate is zero or negative, no interest calculated.")

    def test_calculate_simple_interest_zero_days(self):
        # Start date equals end date, so 1 day of interest
        principal = Decimal('1000000')
        rate = NEW_LEGAL_INTEREST_RATE_INITIAL
        start = date(2020, 1, 1)
        end = date(2020, 1, 1) 
        total_days = 1

        expected_interest = (principal * rate * Decimal(total_days)) / Decimal(365)
        expected_interest = expected_interest.quantize(Decimal('1'), rounding=ROUND_HALF_UP) # 30000 / 365 = 82.19 -> 82
        self.assertEqual(expected_interest, Decimal('82'))

        interest, _ = calculate_simple_interest(principal, rate, start, end)
        self.assertEqual(interest, expected_interest)

    def test_calculate_simple_interest_end_date_before_start_date(self):
        with self.assertRaisesRegex(LegalInterestError, "End date cannot be before start date."):
            calculate_simple_interest(Decimal('10000'), Decimal('0.05'), date(2020, 1, 2), date(2020, 1, 1))

    def test_calculate_simple_interest_invalid_principal_type(self):
        with self.assertRaisesRegex(LegalInterestError, "Principal must be a valid number or Decimal."):
            calculate_simple_interest("invalid", Decimal('0.05'), date(2020, 1, 1), date(2020, 1, 2))
        with self.assertRaisesRegex(LegalInterestError, "Principal must be a valid number or Decimal."):
            calculate_simple_interest(None, Decimal('0.05'), date(2020, 1, 1), date(2020, 1, 2))

    def test_calculate_simple_interest_invalid_rate_type(self):
        with self.assertRaisesRegex(LegalInterestError, "Annual rate must be a valid number or Decimal."):
            calculate_simple_interest(Decimal('1000'), "invalid", date(2020, 1, 1), date(2020, 1, 2))
        with self.assertRaisesRegex(LegalInterestError, "Annual rate must be a valid number or Decimal."):
            calculate_simple_interest(Decimal('1000'), None, date(2020, 1, 1), date(2020, 1, 2))

    def test_calculate_simple_interest_invalid_date_types(self):
        with self.assertRaisesRegex(LegalInterestError, "Start and end dates must be valid date objects."):
            calculate_simple_interest(Decimal('1000'), Decimal('0.05'), "2020-01-01", date(2020, 1, 2))
        with self.assertRaisesRegex(LegalInterestError, "Start and end dates must be valid date objects."):
            calculate_simple_interest(Decimal('1000'), Decimal('0.05'), date(2020, 1, 1), "2020-01-02")

    def test_rounding_half_up(self):
        principal = Decimal('10000')
        rate = Decimal('0.03') # 3%
        # Test case 1: 10000 * 0.03 * (1/365) = 0.8219... -> rounds to 1
        interest_1, _ = calculate_simple_interest(principal, rate, date(2021,1,1), date(2021,1,1)) # 1 day
        self.assertEqual(interest_1, Decimal('1')) # (10000 * 0.03 * 1)/365 = 0.8219 -> 1

        # Test case 2: 10000 * 0.03 * (2/365) = 1.6438... -> rounds to 2
        interest_2, _ = calculate_simple_interest(principal, rate, date(2021,1,1), date(2021,1,2)) # 2 days
        self.assertEqual(interest_2, Decimal('2')) # (10000 * 0.03 * 2)/365 = 1.6438 -> 2
        
        # Test case where fraction is exactly .5
        # P * R * D / 365 = X.5. Need to find P, R, D such that this happens.
        # E.g. P=18250, R=0.01, D=1.  (18250 * 0.01 * 1) / 365 = 182.5 / 365 = 0.5
        principal_half = Decimal('182.50') # Using a principal that results in .5
        rate_half = Decimal('0.01')
        days_half = 1
        # (182.50 * 0.01 * 1) / 365 = 0.005. This is too small.
        # Let's try P=18250, R=0.01, D=1. Interest = 0.5
        # (18250 * 0.01 * 1) / 365 = 0.5
        interest_half, _ = calculate_simple_interest(Decimal('18250'), Decimal('0.01'), date(2021,1,1), date(2021,1,1))
        self.assertEqual(interest_half, Decimal('1')) # Should round up from 0.5

        # Test case for value just below .5 to round down
        # (18249 * 0.01 * 1) / 365 = 0.4999... -> 0
        interest_just_below_half, _ = calculate_simple_interest(Decimal('18249'), Decimal('0.01'), date(2021,1,1), date(2021,1,1))
        self.assertEqual(interest_just_below_half, Decimal('0'))


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
