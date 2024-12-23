import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import random  # Import random for sampling

# Streamlit app configuration
st.set_page_config(
    page_title="Student Loan Repayment Simulator",
    layout="wide"
)

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
    "Starting Salaries (£):", options=[20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 110000, 120000],
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
        life_event_type = np.random.choice(["pregnancy", "layoff", "sick_leave", "job_change"], p=[0.3, 0.3, 0.2, 0.2])

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
            # Calculate annual interest accrued
            interest_accrued = balance * interest_rate
            total_interest += interest_accrued

            # Update loan balance with interest
            balance += interest_accrued

            # Apply life events and repayments
            salary, balance, event_message = apply_life_events(year, salary, balance, simulate_pregnancy,
                                                               simulate_layoff, simulate_sick_leave,
                                                               simulate_job_change, paycut_percentage)

            # Record event messages
            if event_message:
                if year not in event_messages:
                    event_messages[year] = []
                event_messages[year].append((sim_num + 1, event_message))

            # Calculate repayment
            if salary > repayment_threshold:
                repayment = (salary - repayment_threshold) * repayment_rate
            else:
                repayment = 0

            # Deduct repayment from balance
            balance -= repayment

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
