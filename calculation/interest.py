# calculation/interest.py
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

# Define the cut-off date for the new interest rate law
NEW_LAW_START_DATE = date(2020, 4, 1)

# Pre-revision fixed legal interest rate (annual)
OLD_CIVIL_LEGAL_INTEREST_RATE = Decimal('0.05')  # 5%
# Commercial rate could also be considered if relevant, e.g., Decimal('0.06')

# Post-revision initial legal interest rate (annual)
# This rate is variable and reviewed every 3 years. Initial rate is 3%.
NEW_LEGAL_INTEREST_RATE_INITIAL = Decimal('0.03') # 3%

class LegalInterestError(ValueError):
    """Custom exception for interest calculation errors."""
    pass

def get_applicable_annual_interest_rate(accrual_start_date: date) -> Decimal:
    """
    Determines the applicable annual legal interest rate based on the accrual start date.
    For simplicity, this currently only distinguishes between pre and post new law.
    It does not yet implement the 3-year floating rate review mechanism for dates far into the future
    post-NEW_LAW_START_DATE, as that would require historical/future rate data.
    """
    if not isinstance(accrual_start_date, date):
        raise LegalInterestError("accrual_start_date must be a valid date object.")

    if accrual_start_date < NEW_LAW_START_DATE:
        # Potentially, distinguish between civil and commercial if needed by the application
        return OLD_CIVIL_LEGAL_INTEREST_RATE
    else:
        # For now, assume the initial 3% for any date on or after new law.
        # A more complex implementation would check the specific 3-year period.
        return NEW_LEGAL_INTEREST_RATE_INITIAL

def calculate_simple_interest(
    principal: Decimal,
    annual_rate: Decimal,
    start_date: date,
    end_date: date
) -> tuple[Decimal, str]:
    """
    Calculates simple interest for a given period.
    Includes a detailed breakdown of the calculation.

    Args:
        principal: The principal amount.
        annual_rate: The annual interest rate (e.g., Decimal('0.05') for 5%).
        start_date: The start date of the interest period (inclusive).
        end_date: The end date of the interest period (inclusive).

    Returns:
        A tuple containing:
            - calculated_interest: The total interest amount.
            - details: A string explaining the calculation.
    Raises:
        LegalInterestError: If inputs are invalid (e.g., end_date is before start_date).
    """
    if not isinstance(principal, Decimal):
        try:
            principal = Decimal(str(principal))
        except Exception:
            raise LegalInterestError("Principal must be a valid number or Decimal.")
    if not isinstance(annual_rate, Decimal):
        try:
            annual_rate = Decimal(str(annual_rate))
        except Exception:
            raise LegalInterestError("Annual rate must be a valid number or Decimal.")
    if not (isinstance(start_date, date) and isinstance(end_date, date)):
        raise LegalInterestError("Start and end dates must be valid date objects.")

    if principal <= Decimal('0'):
        return Decimal('0'), "Principal is zero or negative, no interest calculated."
    if annual_rate <= Decimal('0'):
        return Decimal('0'), "Annual rate is zero or negative, no interest calculated."
    if end_date < start_date:
        raise LegalInterestError("End date cannot be before start date.")

    # Calculate the number of days
    # Note: Practices for day count can vary (e.g., actual/365, actual/360, or specific day-counting conventions).
    # Here, we use a simple actual number of days.
    # For legal interest in Japan, leap years are typically included in day count (うるう年を含む).
    # Daily interest is usually calculated by dividing the annual amount by 365 (not pro-rata for leap years specifically in the divisor).
    
    total_days = (end_date - start_date).days + 1 # Inclusive of end date

    # Interest per day: principal * annual_rate / days_in_year
    # The division by 365 is standard, even in leap years for daily rate calculation.
    # However, for total interest, using total_days is more accurate than daily interest * total_days if intermediate rounding happens.
    # Total Interest = Principal * Annual Rate * (Total Days / 365)
    
    # Using Decimal for precision
    days_in_standard_year = Decimal('365')
    
    calculated_interest = (principal * annual_rate * Decimal(total_days)) / days_in_standard_year
    
    # Round to the nearest whole number (typical for yen amounts in final calculations)
    # The rounding rule (e.g., half up, floor) might depend on specific legal or accounting practices.
    # Using ROUND_HALF_UP as a common standard.
    calculated_interest = calculated_interest.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    details = (
        f"Principal: {principal:,.2f}円\n"
        f"Annual Interest Rate: {annual_rate*100:.2f}%\n"
        f"Interest Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
        f"Total Days: {total_days}日\n"
        f"Calculation: {principal:,.2f}円 × {annual_rate:.4f} (年利) × ({total_days}日 / 365日) = {calculated_interest:,.0f}円"
    )
    
    return calculated_interest, details

# Example Usage (for testing purposes, will be removed or moved to tests)
if __name__ == '__main__':
    try:
        print("--- Old Law Example (5%) ---")
        rate_old = get_applicable_annual_interest_rate(date(2020, 3, 31))
        print(f"Applicable rate for 2020-03-31: {rate_old*100}%")
        interest_old, details_old = calculate_simple_interest(Decimal('1000000'), rate_old, date(2019, 4, 1), date(2020, 3, 31))
        print(f"Interest: {interest_old:,.0f}円")
        print("Details:\n" + details_old.replace('\n', '\n'))

        print("\n--- New Law Example (3%) ---")
        rate_new = get_applicable_annual_interest_rate(date(2020, 4, 1))
        print(f"Applicable rate for 2020-04-01: {rate_new*100}%")
        interest_new, details_new = calculate_simple_interest(Decimal('1000000'), rate_new, date(2020, 4, 1), date(2021, 3, 31))
        print(f"Interest: {interest_new:,.0f}円")
        print("Details:\n" + details_new.replace('\n', '\n'))

        print("\n--- Edge Case: Zero Principal ---")
        interest_zero_p, details_zero_p = calculate_simple_interest(Decimal('0'), rate_new, date(2020, 4, 1), date(2021, 3, 31))
        print(f"Interest: {interest_zero_p:,.0f}円")
        print("Details:\n" + details_zero_p.replace('\n', '\n'))
        
        print("\n--- Edge Case: Date Error ---")
        # calculate_simple_interest(Decimal('1000000'), rate_new, date(2022, 4, 1), date(2021, 3, 31)) # Should raise error

    except LegalInterestError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
