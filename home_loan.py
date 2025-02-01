import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math

# Set page title and icon
st.set_page_config(page_title="Indian Home Loan Calculator", page_icon="🏠")

# Title
st.title("🏠 Indian Home Loan Calculator")

# Function to validate all inputs
def validate_inputs(home_value, deposit, interest_rate, loan_term, processing_fees, prepayment):
    errors = []
    
    if home_value <= 0:
        errors.append("Home value must be greater than 0")
    
    if deposit < 0:
        errors.append("Deposit cannot be negative")
    
    if deposit > home_value:
        errors.append("Deposit cannot exceed home value")
    
    if interest_rate <= 0:
        errors.append("Interest rate must be greater than 0")
    
    if loan_term <= 0:
        errors.append("Loan term must be at least 1 year")
    
    if processing_fees < 0:
        errors.append("Processing fees cannot be negative")
    
    if prepayment < 0:
        errors.append("Prepayment cannot be negative")
    
    return errors

# Sidebar for additional options
st.sidebar.header("Additional Options")
show_tax_benefits = st.sidebar.checkbox("Show Tax Benefits", value=True)
compare_renting = st.sidebar.checkbox("Compare with Renting", value=True)

# Input Data
st.write("### Input Data")
col1, col2 = st.columns(2)

try:
    home_value = col1.number_input("Home Value (₹)", min_value=0, value=10_000_000)
    deposit = col1.number_input("Deposit (₹)", min_value=0, value=4_000_000)
    interest_rate = col2.number_input("Interest Rate (in %)", min_value=0.0, value=8.75)
    loan_term = col2.number_input("Loan Term (in years)", min_value=1, value=20)
    processing_fees = col1.number_input("Processing Fees (₹)", min_value=0, value=10_000)
    prepayment = col2.number_input("Prepayment (₹ per year)", min_value=0, value=0)

    # Validate inputs
    validation_errors = validate_inputs(
        home_value, deposit, interest_rate, loan_term, processing_fees, prepayment
    )
    
    if validation_errors:
        for error in validation_errors:
            st.error(error)
        st.stop()

    # Calculate loan details
    loan_amount = home_value - deposit
    if loan_amount <= 0:
        st.error("Loan amount must be greater than 0. Reduce your deposit amount.")
        st.stop()

    monthly_interest_rate = (interest_rate / 100) / 12
    number_of_payments = loan_term * 12
    
    # Handle zero interest rate edge case
    if monthly_interest_rate == 0:
        monthly_payment = loan_amount / number_of_payments
    else:
        try:
            monthly_payment = (
                loan_amount
                * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments)
                / ((1 + monthly_interest_rate) ** number_of_payments - 1)
            )
        except OverflowError:
            st.error("Interest rate calculation resulted in overflow. Please try different values.")
            st.stop()

    if not math.isfinite(monthly_payment):
        st.error("Invalid monthly payment calculation. Please check your input values.")
        st.stop()

    # Adjust for prepayments
    prepayment_amount = 0
    if prepayment > 0:
        prepayment_frequency = st.sidebar.radio("Prepayment Frequency", ["Yearly", "Monthly"])
        if prepayment_frequency == "Yearly":
            prepayment_amount = prepayment / 12
        else:
            prepayment_amount = prepayment

    # Display repayments
    total_payments = monthly_payment * number_of_payments
    total_interest = total_payments - loan_amount

    st.write("### Repayments")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Monthly Repayments", value=f"₹{monthly_payment:,.2f}")
    col2.metric(label="Total Repayments", value=f"₹{total_payments:,.0f}")
    col3.metric(label="Total Interest", value=f"₹{total_interest:,.0f}")

    # Amortization Schedule
    st.write("### Amortization Schedule")
    schedule = []
    remaining_balance = loan_amount

    for i in range(1, number_of_payments + 1):
        try:
            interest_payment = remaining_balance * monthly_interest_rate
            principal_payment = monthly_payment - interest_payment
            
            # Apply prepayment
            if prepayment > 0 and i % 12 == 0:  # Yearly prepayment
                principal_payment += prepayment
            
            # Handle remaining balance going negative
            if principal_payment > remaining_balance:
                principal_payment = remaining_balance
                monthly_payment = principal_payment + interest_payment
            
            remaining_balance -= principal_payment
            year = math.ceil(i / 12)
            
            schedule.append([
                i,
                monthly_payment,
                principal_payment,
                interest_payment,
                max(remaining_balance, 0),  # Prevent negative balance
                year,
            ])
            
            if remaining_balance <= 0:
                break

        except Exception as e:
            st.error(f"Error calculating amortization schedule: {str(e)}")
            st.stop()

    df = pd.DataFrame(
        schedule,
        columns=["Month", "Payment", "Principal", "Interest", "Remaining Balance", "Year"],
    )

    # Tax Benefits Calculation (Fixed)
    if show_tax_benefits:
        st.write("### Tax Benefits")
        st.write("""
        - **Section 24**: Deduction of up to ₹2,00,000 per year on interest paid
        - **Section 80C**: Deduction of up to ₹1,50,000 per year on principal repayment
        """)
        
        # Calculate yearly tax benefits
        yearly_tax = df.groupby('Year').agg({'Principal': 'sum', 'Interest': 'sum'}).reset_index()
        yearly_tax['Interest Deduction'] = yearly_tax['Interest'].apply(lambda x: min(x, 200000))
        yearly_tax['Principal Deduction'] = yearly_tax['Principal'].apply(lambda x: min(x, 150000))
        total_tax_savings = (yearly_tax['Interest Deduction'] + yearly_tax['Principal Deduction']).sum()
        
        st.metric(label="Estimated Total Tax Savings", value=f"₹{total_tax_savings:,.0f}")

    # Compare with Renting (Fixed)
    if compare_renting:
        st.write("### Buying vs Renting")
        try:
            rent = st.sidebar.number_input("Monthly Rent (₹)", min_value=0, value=20000)
            rent_increase = st.sidebar.number_input("Yearly Rent Increase (%)", min_value=0.0, value=5.0)
            
            if rent_increase < 0:
                st.error("Rent increase percentage cannot be negative")
                st.stop()
            
            total_rent = 0
            current_rent = rent
            for year in range(1, loan_term + 1):
                total_rent += current_rent * 12
                current_rent *= (1 + rent_increase / 100)
            
            st.metric(label="Total Rent Paid", value=f"₹{total_rent:,.0f}")
            savings = total_rent - total_payments  # Corrected calculation
            st.metric(label="Savings by Buying", value=f"₹{savings:,.0f}")

        except Exception as e:
            st.error(f"Error in rent comparison calculation: {str(e)}")

except ZeroDivisionError:
    st.error("Division by zero error occurred. Please check your input values.")
except OverflowError:
    st.error("Numerical overflow occurred. Please try smaller values.")
except Exception as e:
    st.error(f"An unexpected error occurred: {str(e)}")