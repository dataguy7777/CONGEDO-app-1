import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import plotly.graph_objects as go

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

# Helper function to render calendar
def render_calendar(leave_schedule, start_year):
    """
    Render a calendar visualization with leave days (blue), holidays (green), and working days (white).
    
    Args:
        leave_schedule (DataFrame): Optimized leave schedule.
        start_year (int): Starting year for the calendar.
    """
    st.write("### Leave Calendar with Holidays")

    # Create a list of all leave days
    leave_days = []
    for _, row in leave_schedule.iterrows():
        for day in range(row["Leave Duration"]):
            leave_days.append(row["Start Date"] + timedelta(days=day))
    
    leave_days = pd.Series(pd.to_datetime(leave_days))

    # Generate calendar visualization month by month
    for month in range(1, 13):
        days_in_month = pd.date_range(f"{start_year}-{month:02d}-01", periods=31, freq="D")
        month_days = [d for d in days_in_month if d.month == month]

        # Prepare data for visualization
        day_colors = []
        for day in month_days:
            if day in leave_days.values:
                day_colors.append("blue")  # Leave days
            elif day in ITALIAN_HOLIDAYS.values:
                day_colors.append("green")  # Public holidays
            else:
                day_colors.append("white")  # Working days

        # Create the calendar figure for the month
        fig = go.Figure(data=go.Table(
            header=dict(
                values=[f"<b>{calendar.month_name[month]} {start_year}</b>"],
                align='center',
                font=dict(size=16),
                fill_color="lightgray"
            ),
            cells=dict(
                values=[[f"{day.day} ({day.strftime('%a')})" for day in month_days]],
                align='center',
                font=dict(color=day_colors),
                fill_color=day_colors
            )
        ))

        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

# Streamlit app
def main():
    st.title("Parental Leave Maximizer with Calendar View")
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
        
        start_year = start_date.year
        render_calendar(leave_schedule, start_year)
        
        st.download_button(
            label="Download Leave Schedule",
            data=leave_schedule.to_csv(index=False),
            file_name="leave_schedule.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
