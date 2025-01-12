import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from matplotlib.colors import ListedColormap
import calplot
import matplotlib.pyplot as plt

# List of public holidays in Italy
ITALIAN_HOLIDAYS = pd.to_datetime([
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
])

# Helper function: Optimize leave
def optimize_leave(start_date: datetime, ferie_limit: int):
    """
    Optimize leave by strategically using 'ferie' (vacation days) on Mondays and Fridays to avoid counting weekends.

    Args:
        start_date (datetime): Start date for leave.
        ferie_limit (int): Maximum number of "ferie" (vacation days) available.

    Returns:
        DataFrame: Leave schedule.
    """
    days_limit = 180
    current_date = pd.to_datetime(start_date)
    leave_schedule = []

    while days_limit > 0:
        # Check if the week includes a weekend
        week_start = current_date
        week_end = week_start + timedelta(days=6)

        if week_start.weekday() <= 4 and week_end.weekday() >= 5:  # Contains a weekend
            if ferie_limit >= 2:  # Use ferie on Monday and Friday
                ferie_limit -= 2
                leave_schedule.append((current_date, "Ferie"))  # Monday
                leave_schedule.append((current_date + timedelta(days=4), "Ferie"))  # Friday
            else:
                leave_schedule.append((current_date, "Leave"))  # Count full week
                days_limit -= 7
            current_date += timedelta(days=7)
        else:  # No weekend in the period
            leave_schedule.append((current_date, "Leave"))
            days_limit -= 5
            current_date += timedelta(days=7)

    leave_schedule_df = pd.DataFrame(leave_schedule, columns=["Start Date", "Type"])
    return leave_schedule_df

# Helper function: Render calendar
def render_calendar_with_calplot(leave_schedule):
    """
    Render a calendar visualization using calplot with numbered leave days, ferie, weekends, and holidays.

    Args:
        leave_schedule (DataFrame): Optimized leave schedule.
    """
    st.write("### Leave Calendar Heatmap with 'Ferie' and Leave Days")

    # Collect leave and ferie days
    leave_days = []
    ferie_days = []
    leave_day_numbers = {}
    leave_counter = 1

    for _, row in leave_schedule.iterrows():
        if row["Type"] == "Ferie":
            ferie_days.append(row["Start Date"])
        elif row["Type"] == "Leave":
            current_date = row["Start Date"]
            for i in range(7):  # Count full week
                leave_days.append(current_date)
                leave_day_numbers[current_date] = leave_counter
                leave_counter += 1
                current_date += timedelta(days=1)

    leave_days = pd.Series(pd.to_datetime(leave_days), name="Leave Days")
    ferie_days = pd.Series(pd.to_datetime(ferie_days), name="Ferie Days")

    # Combine leave days, ferie days, public holidays, and weekends
    all_days_index = pd.date_range(start=leave_days.min(), end=leave_days.max(), freq="D")
    all_days = pd.DataFrame(index=all_days_index)
    all_days["Type"] = "Working Day"
    all_days.loc[all_days.index.isin(leave_days), "Type"] = "Leave Day"
    all_days.loc[all_days.index.isin(ferie_days), "Type"] = "Ferie"
    all_days.loc[all_days.index.isin(ITALIAN_HOLIDAYS), "Type"] = "Holiday"
    all_days["Is Weekend"] = all_days.index.weekday >= 5
    all_days.loc[all_days["Is Weekend"], "Type"] = "Weekend"

    # Map types to numerical values for visualization
    all_days["Value"] = all_days["Type"].map(
        {"Leave Day": 1, "Ferie": 2, "Holiday": 3, "Weekend": 4, "Working Day": 0}
    )

    # Prepare text annotations for leave days
    text_annotations = all_days.index.map(
        lambda x: str(leave_day_numbers[x]) if x in leave_day_numbers else "-"
    )

    # Plot with calplot
    fig, axs = calplot.calplot(
        all_days["Value"],
        cmap="RdBu",
        suptitle="Leave Calendar Heatmap",
        suptitle_kws={"x": 0.5, "y": 1.0},
        figsize=(16, 8),
        textformat="{:.0f}",
        textfiller="-",
        textcolor="black",
    )

    st.pyplot(fig)

    # Show DataFrame
    st.write("### Leave Schedule Details")
    all_days.reset_index(inplace=True)
    all_days.rename(columns={"index": "Date", "Type": "Day Type"}, inplace=True)
    st.dataframe(all_days)

# Streamlit app
def main():
    st.title("Parental Leave Maximizer with 'Ferie' Optimization")
    st.markdown(
        """
        Plan your leave schedule to optimize the use of 'permesso' and 'ferie'.
        """
    )
    
    # Inputs
    start_date = st.date_input("Select your starting date for leave:", value=datetime.today())
    ferie_limit = st.number_input("Enter maximum number of 'ferie' days available:", min_value=0, value=10, step=1)
    submit = st.button("Calculate Optimal Leave")
    
    if submit:
        leave_schedule = optimize_leave(start_date, ferie_limit)
        st.subheader("Leave Schedule Generated Successfully!")
        
        render_calendar_with_calplot(leave_schedule)
        st.download_button(
            label="Download Leave Schedule",
            data=leave_schedule.to_csv(index=False),
            file_name="leave_schedule.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
