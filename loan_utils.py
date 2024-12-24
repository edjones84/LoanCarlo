# loan_utils.py

import numpy as np


def simulate_student_loan(initial_balance, interest_rate, repayment_threshold, repayment_rate, loan_term_years, salary,
                          annual_growth_mean, annual_growth_std, iterations):
    """
    Simulate student loan repayment over multiple iterations, including salary growth variability.
    Interest is only paid if salary exceeds the repayment threshold.

    Parameters:
        initial_balance (float): Initial student loan balance.
        interest_rate (float): Annual interest rate (e.g., 0.05 for 5%).
        repayment_threshold (float): Salary threshold for repayments.
        repayment_rate (float): Repayment rate as a decimal (e.g., 0.09 for 9%).
        loan_term_years (int): Loan term in years.
        salary (float): Salary of the person each year (could vary with growth).
        annual_growth_mean (float): The average annual salary growth.
        annual_growth_std (float): The standard deviation of the annual salary growth.
        iterations (int): The number of Monte Carlo simulations.

    Returns:
        avg_interest_paid (float): The average interest paid across all simulations.
    """
    total_interest_paid = 0

    for _ in range(iterations):
        balance = initial_balance
        interest_paid = 0
        current_salary = salary

        for year in range(1, loan_term_years + 1):
            if balance <= 0:  # Stop if loan is paid off early
                break

            # Apply interest for the current year
            if current_salary > repayment_threshold:
                annual_interest = balance * interest_rate
                interest_paid += annual_interest  # Add the interest to the total interest paid

                # Calculate repayment based on salary
                repayment = (current_salary - repayment_threshold) * repayment_rate

                # Repayment is first used to pay off interest, then the remaining amount reduces the principal
                if repayment > annual_interest:
                    principal_repayment = repayment - annual_interest  # Remaining after interest
                    balance -= principal_repayment  # Reduce the principal by the remaining amount
                else:
                    # If repayment is less than interest, the loan balance just grows
                    balance += annual_interest - repayment
            else:
                # If salary is below the threshold, no repayment occurs, no interest is paid
                balance += balance * interest_rate

            # Update salary for the next year using a normal distribution for growth
            current_salary *= (1 + np.random.normal(annual_growth_mean, annual_growth_std))

        # If the loan is wiped out after 30 years (as per your specification), we reset the balance
        if loan_term_years >= 30 and balance > 0:
            balance = 0  # Loan is wiped at 30 years

        # Add the interest paid for this iteration to the total
        total_interest_paid += interest_paid

    # Calculate the average interest paid
    avg_interest_paid = total_interest_paid / iterations
    return avg_interest_paid


def simulate_mortgage(lump_sum, mortgage_balance, interest_rate, years):
    """
    Simulate the mortgage balance and interest paid over time with a lump sum applied initially.

    Parameters:
        lump_sum (float): Amount applied to reduce the mortgage balance.
        mortgage_balance (float): Initial mortgage balance before applying the lump sum.
        interest_rate (float): Annual interest rate (e.g., 0.05 for 5%).
        years (int): Total mortgage term in years.

    Returns:
        total_interest_paid (float): Total interest paid over the mortgage term.
    """
    # Apply the lump sum to reduce the mortgage balance
    remaining_balance = max(mortgage_balance - lump_sum, 0)

    # Calculate the monthly interest rate and total number of payments
    monthly_interest_rate = interest_rate / 12
    total_months = years * 12

    # Calculate monthly repayment using the amortization formula
    monthly_repayment = remaining_balance * (monthly_interest_rate * (1 + monthly_interest_rate) ** total_months) / \
                        ((1 + monthly_interest_rate) ** total_months - 1)


    total_interest_paid = 0

    for month in range(total_months):
        # Calculate monthly interest
        monthly_interest = remaining_balance * monthly_interest_rate
        total_interest_paid += monthly_interest

        # Apply the repayment to the balance
        principal_repayment = max(monthly_repayment - monthly_interest, 0)
        remaining_balance -= principal_repayment

        # Stop simulation if balance is fully repaid
        if remaining_balance <= 0:
            break

    return total_interest_paid


def simulate_index_fund(lump_sum, annual_return_mean, annual_return_std, years, iterations):
    total_future_value = 0

    for _ in range(iterations):
        current_value = lump_sum
        for year in range(years):
            # Simulate the return for the year
            annual_return = np.random.normal(annual_return_mean, annual_return_std)
            current_value *= (1 + annual_return)
        total_future_value += current_value

    avg_future_value = total_future_value / iterations
    avg_gains = avg_future_value - lump_sum  # Subtract the initial lump sum to calculate gains
    return avg_gains