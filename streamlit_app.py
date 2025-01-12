import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calplot
import matplotlib.pyplot as plt

# List of public holidays in Italy
ITALIAN_HOLIDAYS = [
    "2025-01-01",  # New Year's Day
    "2025-01-06",  # Epiphany
    "2025-04-25",  # Liberation Day
    "2025-05-01",  # Labor Day
    "2025-06-02",  # Republic Day
    "2025-08-15",  # Assumption of Mary
    "2025-11-01",  # All Saints' Day
    "2025-12-08",  # Immaculate Conception
    "2025-12-25",  # Christmas Day
    "2025-12-26",  # St. Stephen's Day
]
ITALIAN_HOLIDAYS = pd.to_datetime(ITALIAN_HOLIDAYS)

# Helper function to optimize leave
def optimize_leave(start_date: datetime, leave_format: str):
    """
    Optimize parental leave distribution based on the selected format.
    
    Args:
        start_date (datetime): Start date for leave.
        leave_format (str): Leave format - "Days", "Months", or "Hours".
    
    Returns:
        DataFrame: Leave schedule.
        int: Maximum elapsed days.
    """
    days_limit = 180
    current_date = pd.to_datetime(start_date)
    leave_schedule = []
    
    while days_limit > 0:
        if leave_format == "Days":
            leave_duration = min(5, days_limit)  # Take blocks of 5 days
            days_limit -= leave_duration
        elif leave_format == "Months":
            leave_duration = min(30, days_limit)  # Approximate month as 30 days
            days_limit -= leave_duration
        elif leave_format == "Hours":
            leave_duration = min(120, days_limit * 24)  # Convert hours to days
            days_limit -= leave_duration / 24

        leave_schedule.append((current_date, leave_duration))
        current_date += timedelta(days=leave_duration)

    df_schedule = pd.DataFrame(leave_schedule, columns=["Start Date", "Leave Duration"])
    max_elapsed_days = (df_schedule["Start Date"].iloc[-1] - pd.to_datetime(start_date)).days

    return df_schedule, max_elapsed_days

def render_calendar_with_calplot(leave_schedule):
    """
    Render a calendar visualization using calplot with leave days and holidays.

    Args:
        leave_schedule (DataFrame): Optimized leave schedule.
    """
    st.write("### Leave Calendar Heatmap")

    # Create a list of all leave days
    leave_days = []
    for _, row in leave_schedule.iterrows():
        for day in range(row["Leave Duration"]):
            leave_days.append(row["Start Date"] + timedelta(days=day))
    
    leave_days = pd.Series(pd.to_datetime(leave_days), name="Leave Days")

    # Combine leave days and public holidays into a DataFrame
    all_days_index = pd.Index(leave_days).union(pd.Index(ITALIAN_HOLIDAYS))  # Merge leave and holidays
    all_days = pd.DataFrame(index=all_days_index)
    all_days["Type"] = "Working Day"
    all_days.loc[all_days.index.isin(leave_days), "Type"] = "Leave Day"
    all_days.loc[all_days.index.isin(ITALIAN_HOLIDAYS), "Type"] = "Holiday"
    all_days["Value"] = all_days["Type"].map({"Leave Day": 1, "Holiday": 2, "Working Day": 0})
    
    # Prepare values for calplot
    calplot_values = all_days["Value"]
    calplot_values.index = pd.to_datetime(all_days.index)

    # Plot with calplot
    fig, ax = calplot.calplot(
        calplot_values,
        cmap=["white", "blue", "green"],
        suptitle="Leave Calendar Heatmap",
        suptitle_kws={"x": 0.5, "y": 1.0},
        figsize=(16, 8),
    )
    st.pyplot(fig)

# Streamlit app
def main():
    st.title("Parental Leave Maximizer with Heatmap")
    st.markdown(
        """
        Use this app to plan and maximize your parental leave usage while adhering to the 180-day limit.
        """
    )
    
    # Inputs
    start_date = st.date_input("Select your starting date for parental leave:", value=datetime.today())
    leave_format = st.selectbox("Choose leave format:", ["Days", "Months", "Hours"])
    submit = st.button("Calculate Optimal Leave")
    
    if submit:
        leave_schedule, max_elapsed_days = optimize_leave(start_date, leave_format)
        st.subheader(f"Maximized Leave Elapsed: {max_elapsed_days} days")
        
        render_calendar_with_calplot(leave_schedule)
        
        st.download_button(
            label="Download Leave Schedule",
            data=leave_schedule.to_csv(index=False),
            file_name="leave_schedule.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
