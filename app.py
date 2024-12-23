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

for idx, initial_salary in enumerate(starting_salaries):
    trajectories = []
    labels = []
    final_balances = []

    for sim_num in range(iterations):
        balance = initial_loan_balance
        salary = initial_salary
        annual_growth_rate = np.random.normal(annual_growth_mean, annual_growth_std)
        trajectory = []

        for year in range(1, loan_term_years + 1):
            # Apply interest to the loan
            balance *= (1 + interest_rate)

            # Apply life events based on user selection
            salary, balance, event_message = apply_life_events(year, salary, balance, simulate_pregnancy,
                                                               simulate_layoff, simulate_sick_leave,
                                                               simulate_job_change, paycut_percentage)

            # If an event occurred, record the event message along with simulation number
            if event_message:
                if year not in event_messages:
                    event_messages[year] = []
                event_messages[year].append((sim_num + 1, event_message))  # Store simulation number along with event

            # Calculate annual repayment
            if salary > repayment_threshold:
                repayment = (salary - repayment_threshold) * repayment_rate
            else:
                repayment = 0

            # Deduct repayment from balance
            balance -= repayment
            trajectory.append(balance if balance > 0 else 0)

            # Check if loan is paid off
            if balance <= 0:
                break

            # Update salary for the next year
            salary *= (1 + annual_growth_rate)

        trajectories.append(trajectory)
        labels.append(f"Sim {sim_num + 1}: Growth Rate {annual_growth_rate:.2%}")
        final_balances.append((sim_num, trajectory[-1] if len(trajectory) == loan_term_years else 0))

    # Sort final balances to pick top, bottom, and middle trajectories
    final_balances.sort(key=lambda x: x[1])
    top_indices = [idx for idx, _ in final_balances[:3]]  # Lowest balances (fastest repayment)
    middle_indices = [final_balances[len(final_balances) // 2][0]]  # Median balance
    bottom_indices = [idx for idx, _ in final_balances[-3:]]  # Highest balances (slowest repayment)
    annotate_indices = top_indices + middle_indices + bottom_indices

    # Plotting repayment trajectories for each starting salary
    ax = axes[idx]
    for i, trajectory in enumerate(trajectories):
        if i in annotate_indices:
            ax.plot(trajectory, alpha=0.8, linewidth=1.5, label=labels[i])
        else:
            ax.plot(trajectory, alpha=0.3, linewidth=0.8, color='gray')

    ax.set_title(f"Starting Salary: £{initial_salary}")
    ax.set_xlabel("Years")
    ax.set_ylabel("Loan Balance (£)")
    ax.grid(True)
    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small', ncol=1)

plt.tight_layout()
st.pyplot(fig)

# Display random sampled life events with simulation number
st.subheader("Random Sample of Life Events")
event_messages_flat = [(sim_num, msg) for msgs in event_messages.values() for sim_num, msg in msgs]
random_sample = random.sample(event_messages_flat, min(len(event_messages_flat), 5))  # Show up to 5 random events

for sim_num, event in random_sample:
    st.write(f"- Simulation {sim_num}: {event}")
