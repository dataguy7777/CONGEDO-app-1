import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import plotly.graph_objects as go

# Streamlit app configuration
st.set_page_config(page_title="Parental Leave Maximizer", layout="wide")

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

def render_calendar(leave_schedule):
    """
    Render a visual calendar with leave days highlighted.
    
    Args:
        leave_schedule (DataFrame): Optimized leave schedule.
    """
    st.write("### Leave Calendar")

    # Create a list of all leave days
    leave_days = []
    for _, row in leave_schedule.iterrows():
        for day in range(row["Leave Duration"]):
            leave_days.append(row["Start Date"] + timedelta(days=day))
    
    # Convert leave_days to a pandas Series for compatibility
    leave_days = pd.Series(pd.to_datetime(leave_days))

    # Generate calendar visualization for the year
    calendar_fig = go.Figure()

    for month in range(1, 13):
        # Filter leave days for the specific month
        month_leave_days = leave_days[leave_days.dt.month == month]
        
        # Create all days for the month
        days_in_month = pd.date_range(f"{leave_days.min().year}-{month:02d}-01", periods=31, freq="D")
        month_days = [d for d in days_in_month if d.month == month]

        # Highlight leave days
        highlights = [1 if d in month_leave_days.values else 0 for d in month_days]

        calendar_fig.add_trace(
            go.Heatmap(
                z=highlights,
                x=[d.strftime("%a") for d in month_days],
                y=[f"{d.day}" for d in month_days],
                hoverinfo="text",
                text=[f"{d:%Y-%m-%d}" for d in month_days],
                colorscale=["#fff", "#007ACC"],
                showscale=False,
            )
        )

    calendar_fig.update_layout(
        title="Leave Calendar Visualization",
        xaxis_title="Day of the Week",
        yaxis_title="Day of the Month",
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(calendar_fig, use_container_width=True)

# Streamlit app
def main():
    st.title("Parental Leave Maximizer")
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
        
        render_calendar(leave_schedule)
        
        st.download_button(
            label="Download Leave Schedule",
            data=leave_schedule.to_csv(index=False),
            file_name="leave_schedule.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
