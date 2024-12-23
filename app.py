import random
import numpy as np
from matplotlib import pyplot as plt
import streamlit as st
import pandas as pd

import streamlit as st
from loan_utils import simulate_student_loan, simulate_mortgage

# Add page navigation
page = st.sidebar.selectbox("Choose a Page", ["Student Loan Simulation","Lump-Sum Analysis", "Parameter Analysis"])

if page == "Student Loan Simulation":
    # Existing student loan simulation code
    st.title("Student Loan Repayment Simulator")
    # Sidebar controls
    st.sidebar.header("Simulation Parameters")
    initial_loan_balance = st.sidebar.number_input("Initial Loan Balance (£):", min_value=0, value=60000)
    repayment_threshold = st.sidebar.number_input("Repayment Threshold (£):", min_value=0, value=24990)
    repayment_rate = st.sidebar.slider("Repayment Rate (%):", min_value=0.0, max_value=20.0, value=9.0) / 100
    interest_rate = st.sidebar.slider("Interest Rate (%):", min_value=0.0, max_value=10.0, value=4.3) / 100
    loan_term_years = st.sidebar.number_input("Loan Term (Years):", min_value=1, value=25)
    iterations = st.sidebar.number_input("Number of Simulations:", min_value=10, max_value=1000, value=100)
    starting_salaries = st.sidebar.multiselect(
        "Starting Salaries (£):",
        options=[20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 110000, 120000],
        default=[30000, 60000, 90000, 120000]
    )
    annual_growth_mean = st.sidebar.slider("Average Annual Salary Growth (%):", min_value=-10.0, max_value=10.0,
                                           value=3.0) / 100
    annual_growth_std = st.sidebar.slider("Annual Growth Std Dev (%):", min_value=0.0, max_value=20.0, value=5.0) / 100

    # Sidebar controls for life events
    st.sidebar.header("Life Events")
    simulate_pregnancy = st.sidebar.checkbox("Simulate Pregnancy (9 months no income)", value=True)
    simulate_layoff = st.sidebar.checkbox("Simulate Layoff (6 months reduced income)", value=True)
    simulate_sick_leave = st.sidebar.checkbox("Simulate Sick Leave (3 months reduced income)", value=True)
    simulate_job_change = st.sidebar.checkbox("Simulate Job Change (X%)", value=True)
    paycut_percentage = st.sidebar.slider("Paycut Percentage (%)", min_value=0, max_value=50, value=20)
    payrise_percentage = st.sidebar.slider("Payrise Percentage (%)", min_value=0, max_value=50, value=20)


    # Function to simulate life events
    def apply_life_events(year, salary, loan_balance, simulate_pregnancy, simulate_layoff, simulate_sick_leave,
                          simulate_job_change, paycut_percentage):
        # Randomly decide if a life event happens this year
        life_event_prob = 0.1  # 10% chance of a life event per year
        event = np.random.random()
        event_message = None

        if event < life_event_prob:  # If life event occurs
            life_event_type = np.random.choice(["pregnancy", "layoff", "sick_leave", "job_change"],
                                               p=[0.3, 0.3, 0.2, 0.2])

            if life_event_type == "pregnancy" and simulate_pregnancy:
                # Assume pregnancy lasts for 9 months (about 0.75 years) with no salary
                salary = 0  # No salary during pregnancy
                loan_balance += loan_balance * interest_rate * 0.75  # Accrued interest during absence
                event_message = f"Pregnancy event - no salary for 9 months."

            elif life_event_type == "layoff" and simulate_layoff:
                # Assume being laid off for 6 months
                salary = salary * 0.5  # Reduced salary (50% of original)
                loan_balance += loan_balance * interest_rate * 0.5  # Interest accrues during this time
                event_message = f"Layoff event - reduced salary for 6 months."

            elif life_event_type == "sick_leave" and simulate_sick_leave:
                # Sick leave, no income for 3 months
                salary = salary * 0.8  # Reduced salary (80% of original)
                loan_balance += loan_balance * interest_rate * 0.25  # Partial interest accrual during this time
                event_message = f"Sick leave event - reduced salary for 3 months."


            elif life_event_type == "job_change" and simulate_job_change:

                # Apply either a paycut or payrise

                job_event = np.random.choice(["paycut", "payrise"], p=[0.5, 0.5])  # 50% chance for paycut or payrise

                if job_event == "paycut":

                    salary = salary * (1 - paycut_percentage / 100)  # Apply paycut

                    event_message = f"Job change - {paycut_percentage}% paycut."

                else:

                    salary = salary * (1 + payrise_percentage / 100)  # Apply payrise

                    event_message = f"Job change - {payrise_percentage}% payrise."

        return salary, loan_balance, event_message


    # Monte Carlo Simulation
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
    axes = axes.flatten()

    # Dictionary to store event messages with simulation number
    event_messages = {}

    # Loop over each starting salary
    for idx, initial_salary in enumerate(starting_salaries):
        trajectories = []
        labels = []
        final_balances = []
        interest_costs = []  # To store total interest for this starting salary

        for sim_num in range(iterations):
            balance = initial_loan_balance
            salary = initial_salary
            annual_growth_rate = np.random.normal(annual_growth_mean, annual_growth_std)
            trajectory = []
            total_interest = 0  # Track total interest for this simulation

            for year in range(1, loan_term_years + 1):
                if balance <= 0:  # Stop if loan is paid off early
                    break

                # Apply interest for the current year if salary exceeds the repayment threshold
                if salary > repayment_threshold:
                    annual_interest = balance * interest_rate
                    total_interest += annual_interest  # Add the interest to the total interest paid

                    # Calculate repayment based on salary
                    repayment = (salary - repayment_threshold) * repayment_rate

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

                # Apply life events and repayments
                salary, balance, event_message = apply_life_events(year, salary, balance, simulate_pregnancy,
                                                                   simulate_layoff, simulate_sick_leave,
                                                                   simulate_job_change, paycut_percentage)

                # Record event messages
                if event_message:
                    if year not in event_messages:
                        event_messages[year] = []
                    event_messages[year].append((sim_num + 1, event_message))

                # Track trajectory
                trajectory.append(balance if balance > 0 else 0)

                # Break if loan is fully repaid
                if balance <= 0:
                    break

                # Update salary for the next year
                salary *= (1 + annual_growth_rate)

            # Store results for this simulation
            trajectories.append(trajectory)
            labels.append(f"Sim {sim_num + 1}: Growth Rate {annual_growth_rate:.2%}")
            final_balances.append((sim_num, trajectory[-1] if len(trajectory) == loan_term_years else 0))
            interest_costs.append(total_interest)  # Store total interest for this simulation

        # Calculate average interest for this salary
        avg_interest = np.mean(interest_costs)

        # Sort final balances to pick top, bottom, and middle trajectories
        final_balances.sort(key=lambda x: x[1])
        top_indices = [idx for idx, _ in final_balances[:3]]  # Lowest balances (fastest repayment)
        middle_indices = [final_balances[len(final_balances) // 2][0]]  # Median balance
        bottom_indices = [idx for idx, _ in final_balances[-3:]]  # Highest balances (slowest repayment)
        annotate_indices = top_indices + middle_indices + bottom_indices

        # Plot repayment trajectories
        ax = axes[idx]
        for i, trajectory in enumerate(trajectories):
            if i in annotate_indices:
                ax.plot(trajectory, alpha=0.8, linewidth=1.5, label=labels[i])
            else:
                ax.plot(trajectory, alpha=0.3, linewidth=0.8, color='gray')

        # Add the average interest paid to the subplot title
        ax.set_title(f"Starting Salary: £{initial_salary}\nAvg Interest Paid: £{avg_interest:,.2f}")
        ax.set_xlabel("Years")
        ax.set_ylabel("Loan Balance (£)")
        ax.grid(True)
        ax.axhline(0, color='black', linestyle='--', linewidth=1)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small', ncol=1)

    plt.tight_layout()
    st.pyplot(fig)

    # Assumptions Summary
    st.subheader("Assumptions Summary")
    st.markdown("""
    ### Loan and Repayment Assumptions
    - Initial loan balance, repayment threshold, repayment rate, interest rate, and loan term are user-defined inputs.
    - Interest is compounded annually on the remaining balance.

    ### Salary Growth
    - Starting salaries are selected from user inputs, and annual salary growth is modeled using a normal distribution with user-defined mean and standard deviation.
    - The annual growth standard deviation refers to the variability or dispersion of the annual salary growth rate. It is a measure of how much the salary growth rate can fluctuate from year to year. In other words, it indicates how much the actual growth rate can differ from the expected average growth rate.

    Here’s a breakdown of how it works:
    
    Annual Growth Mean: This is the average (or expected) percentage by which your salary grows each year. For example, if the annual growth mean is 0.03, it means the average annual growth rate of the salary is 3%.
    
    Annual Growth Standard Deviation: This measures the degree of variation or uncertainty around the annual growth mean. For example, if the standard deviation is 0.02 (or 2%), it means that in most cases, the actual salary growth rate for a given year will fall within 2% of the mean (either above or below the mean), but in some cases, it could be higher or lower than that.
    
    For example:
    
    Mean = 3% and Standard Deviation = 2% means that each year, the salary growth could vary between -1% (3% - 2%) and 5% (3% + 2%) in most cases, based on a normal distribution

    ### Life Events
    - Life events are randomly simulated with a 10% chance per year:
        - **Pregnancy**: 9 months of no income, during which interest accrues on the loan balance.
        - **Layoff**: 6 months with 50% reduced income and accrued interest.
        - **Sick Leave**: 3 months with 20% reduced income and accrued interest.
        - **Job Change**: Either a user-defined pay cut or pay rise, occurring with equal probability.
    - The occurrence of life events is governed by user preferences for each event type.

    ### Repayment Calculations
    - Repayments are calculated annually if the salary exceeds the repayment threshold.
    - Repayment equals the amount over the threshold multiplied by the repayment rate.

    ### Monte Carlo Simulation
    - Each simulation runs for up to the specified loan term or until the loan is paid off.
    - Results include trajectories for loan repayment across multiple simulations for selected starting salaries.
    """)

    # Display random sampled life events with simulation number
    st.subheader("Random Sample of Life Events")
    event_messages_flat = [(sim_num, msg) for msgs in event_messages.values() for sim_num, msg in msgs]
    random_sample = random.sample(event_messages_flat, min(len(event_messages_flat), 5))  # Show up to 5 random events

    for sim_num, event in random_sample:
        st.write(f"- Simulation {sim_num}: {event}")
# Add this to app.py
elif page == "Parameter Analysis":
    st.title("Monte Carlo Parameter Analysis")

    # Parameter ranges, including lump sums

    # Parameter ranges
    param_ranges = {
        'starting_salary': np.linspace(30000, 120000, 10),
        'student_loan_rate': np.linspace(0.02, 0.08, 10),
        'mortgage_rate': np.linspace(0.02, 0.08, 10),
    }

    # Allow the user to input the lump sum value
    lump_sum_input = st.number_input("Enter the lump sum amount for mortgage", min_value=0, max_value=100000, step=5000, value=50000)
    mortgage_loan_term = st.slider("Enter the mortgage loan term", min_value=0, max_value=40, value=25)
    sl_loan_term = st.slider("Enter the student loan term", min_value=0, max_value=40, value=25)
    sl_loan_rate = st.slider("Enter the student loan repayment rate %", min_value=0, max_value=20, value=9)
    initial_sl_balance = st.slider("Initial student loan balance", min_value=0, max_value=100000, value=60000)
    repayment_threshold = st.slider("Student loan repayment_threshold", min_value=0, max_value=100000, value=24990)
    annual_growth_mean = 0.03
    annual_growth_std = 0.05
    iterations = 100
    mortgage_balance = st.slider("Initial Mortgage Balance", min_value=0, max_value=2000000, value=450000)


    # Run simulations
    results = []
    global im
    for salary in param_ranges['starting_salary']:
        for sl_rate in param_ranges['student_loan_rate']:
            for m_rate in param_ranges['mortgage_rate']:
                lump_sum = lump_sum_input
                # Student loan simulation
                sl_interest = simulate_student_loan(
                    initial_balance=initial_sl_balance,
                    interest_rate=sl_rate,
                    repayment_threshold=repayment_threshold,
                    repayment_rate=sl_loan_rate/100,
                    loan_term_years=sl_loan_term,
                    salary=salary,
                    annual_growth_mean=annual_growth_mean,
                    annual_growth_std=annual_growth_std,
                    iterations=iterations
                )

                # Mortgage simulation with different lump sums
                m_interest = simulate_mortgage(
                    lump_sum=lump_sum,
                    mortgage_balance=mortgage_balance,
                    interest_rate=m_rate,
                    years=mortgage_loan_term
                )

                results.append({
                    'salary': salary,
                    'student_loan_rate': sl_rate * 100,
                    'mortgage_rate': m_rate * 100,
                    'lump_sum': lump_sum,  # Track lump sum
                    'student_loan_interest': sl_interest,
                    'mortgage_interest': m_interest,
                    'difference': sl_interest - m_interest,
                    'better_choice': 'Student Loan' if sl_interest > m_interest else 'Mortgage'
                })

    df = pd.DataFrame(results)

    # Create heatmap for each salary level
    fig, axes = plt.subplots(2, 2, figsize=(15, 15))
    axes = axes.flatten()

    salary_samples = np.quantile(param_ranges['starting_salary'], [0.2, 0.4, 0.6, 0.8])

    # Find global min and max for consistent color scaling
    vmin = df['difference'].min()
    vmax = df['difference'].max()

    for idx, salary in enumerate(salary_samples):
        salary_data = df[np.isclose(df['salary'], salary, atol=5000)]

        # Use pivot_table with aggregation to handle duplicates
        pivot = salary_data.pivot_table(
            index='student_loan_rate',
            columns='mortgage_rate',
            values='difference',
            aggfunc='mean'  # Aggregating by mean to handle duplicates
        )

        im = axes[idx].imshow(pivot, cmap='RdYlBu', aspect='auto', vmin=vmin, vmax=vmax)
        axes[idx].set_title(f'Salary: £{salary:,.0f}, Lump Sum: £{salary_data["lump_sum"].iloc[0]:,.0f}')
        axes[idx].set_xlabel('Mortgage Rate (%)')
        axes[idx].set_ylabel('Student Loan Rate (%)')

        # Add decision boundary line
        zero_level = axes[idx].contour(pivot.values, levels=[0], colors='black', linestyles='dashed')

        # Adjust annotation positions
        ax = axes[idx]
        ax.annotate(f"Salary Growth Avg: {annual_growth_mean*100:,.1f}%", xy=(0.02, 0.95), xycoords='axes fraction', ha='left', va='top',
                    fontsize=10, color='black')
        ax.annotate(f"Iterations: {iterations}", xy=(0.02, 0.85), xycoords='axes fraction', ha='left',
                    va='top', fontsize=10, color='black')

    plt.tight_layout()
    st.pyplot(fig)

    st.write("Blue regions indicate paying off student loan is better")
    st.write("Red regions indicate paying off mortgage is better")
    st.write("Dotted line indicates decision boundary line")
    # Show key patterns
    st.subheader("Key Findings")
    high_diff = df.nlargest(1, 'difference')
    low_diff = df.nsmallest(1, 'difference')

    st.write(f"Most favorable for student loan: Salary £{high_diff['salary'].iloc[0]:,.0f}, "
             f"SL Rate {high_diff['student_loan_rate'].iloc[0]:.1f}%, "
             f"Mortgage Rate {high_diff['mortgage_rate'].iloc[0]:.1f}%, "
             f"Lump Sum £{high_diff['lump_sum'].iloc[0]:,.0f}")

    st.write(f"Most favorable for mortgage: Salary £{low_diff['salary'].iloc[0]:,.0f}, "
             f"SL Rate {low_diff['student_loan_rate'].iloc[0]:.1f}%, "
             f"Mortgage Rate {low_diff['mortgage_rate'].iloc[0]:.1f}%, "
             f"Lump Sum £{low_diff['lump_sum'].iloc[0]:,.0f}")

else:
    st.title("Lump-Sum Analysis")
    st.write("Determine whether a lump sum is best used to pay off a mortgage or a student loan.")

    # User inputs
    lump_sum = st.number_input("Lump Sum Available (£):", min_value=0, value=50000)
    mortgage_balance = st.number_input("Mortgage Balance (£):", min_value=0, value=200000)
    mortgage_interest_rate = st.slider("Mortgage Interest Rate (%):", min_value=1.0, max_value=10.0, value=3.0) / 100
    mortgage_term_years = st.number_input("Mortgage Term (Years):", min_value=1, value=25)

    # Student loan parameters (user can reuse the settings from the simulation)
    st.subheader("Student Loan Parameters")
    initial_loan_balance = st.number_input("Student Loan Balance (£):", min_value=0, value=60000)
    starting_salary = st.number_input("Starting Salary (£):", min_value=0, value=30000)
    repayment_threshold = st.number_input("Repayment Threshold (£):", min_value=0, value=24990)
    repayment_rate = st.slider("Repayment Rate (%):", min_value=0.0, max_value=20.0, value=9.0) / 100
    loan_interest_rate = st.slider("Student Loan Interest Rate (%):", min_value=0.0, max_value=10.0, value=4.3) / 100
    loan_term_years = st.number_input("Loan Term (Years):", min_value=1, value=25)
    annual_growth_mean = st.slider("Annual Salary Growth Mean (%):", min_value=-10.0, max_value=10.0, value=3.0) / 100
    annual_growth_std = st.slider("Annual Growth Std Dev (%):", min_value=0.0, max_value=20.0, value=5.0) / 100
    iterations = st.number_input("Number of Simulations:", min_value=10, max_value=1000, value=100)

    # Simulate interest paid on the student loan
    avg_student_loan_interest = simulate_student_loan(initial_loan_balance, loan_interest_rate, repayment_threshold,
                                                      repayment_rate, loan_term_years, starting_salary,
                                                      annual_growth_mean, annual_growth_std, iterations)

    # Simulate interest savings on the mortgage
    mortgage_interest_savings = simulate_mortgage(
        lump_sum, mortgage_balance, mortgage_interest_rate, mortgage_term_years
    )

    # Display results
    st.subheader("Results")
    st.write(f"**Average Interest Paid on Student Loan:** £{avg_student_loan_interest:,.2f}")
    st.write(f"**Interest Saved on Mortgage with Lump Sum:** £{mortgage_interest_savings:,.2f}")

    if mortgage_interest_savings > avg_student_loan_interest:
        st.success("Using the lump sum to pay off the mortgage is more beneficial.")
    else:
        st.success("Using the lump sum to pay off the student loan is more beneficial.")
