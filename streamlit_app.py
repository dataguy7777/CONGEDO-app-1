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
    schedule = []

    parental_leave_counter = 1
    ferie_counter = 1
    weekend_counter = 1

    while days_limit > 0:
        # Determine if this week includes a weekend
        week_start = current_date
        week_end = week_start + timedelta(days=6)

        # Use ferie on Monday and Friday to skip weekend
        if week_start.weekday() <= 4 and week_end.weekday() >= 5:
            if ferie_limit >= 2:
                schedule.append((week_start, "Leave Day", ferie_counter))
                ferie_counter += 1
                schedule.append((week_start + timedelta(days=4), "Leave Day", ferie_counter))
                ferie_counter += 1
                ferie_limit -= 2
            else:
                for i in range(7):
                    if week_start.weekday() < 5:  # Weekday: Parental Leave Day
                        schedule.append((week_start, "Parental Leave Day", parental_leave_counter))
                        parental_leave_counter += 1
                        days_limit -= 1
                    else:  # Weekend
                        schedule.append((week_start, "Weekend", weekend_counter))
                        weekend_counter += 1
                    week_start += timedelta(days=1)
            current_date += timedelta(days=7)
        else:  # Week without a weekend
            for i in range(5):
                schedule.append((current_date, "Parental Leave Day", parental_leave_counter))
                parental_leave_counter += 1
                days_limit -= 1
                current_date += timedelta(days=1)

    # Create a DataFrame for the schedule
    schedule_df = pd.DataFrame(schedule, columns=["Date", "Day Type", "Sequence"])
    return schedule_df

# Helper function: Render calendar
def render_calendar_with_calplot(schedule):
    """
    Render a calendar visualization using calplot with detailed leave days, ferie, weekends, and holidays.

    Args:
        schedule (DataFrame): Optimized leave schedule.
    """
    st.write("### Leave Calendar Heatmap")

    # Map day types to numeric values
    schedule["Value"] = schedule["Day Type"].map(
        {"Parental Leave Day": 1, "Leave Day": 2, "Holiday": 3, "Weekend": 4, "Working Day": 0}
    )

    # Generate a Series for calplot
    values = pd.Series(schedule["Value"].values, index=pd.to_datetime(schedule["Date"]))

    # Define custom colormap
    cmap = ListedColormap(["white", "blue", "orange", "lightgreen", "green"])

    # Plot with calplot
    fig, axs = calplot.calplot(
        values,
        cmap="RdBu",
        suptitle="Leave Calendar Heatmap",
        suptitle_kws={"x": 0.5, "y": 1.0},
        figsize=(16, 8),
        textformat="{:.0f}",
        textfiller="-",
        textcolor="black",
    )

    st.pyplot(fig)

    # Display schedule DataFrame
    st.write("### Detailed Leave Schedule")
    st.dataframe(schedule)

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
        schedule = optimize_leave(start_date, ferie_limit)
        st.subheader("Leave Schedule Generated Successfully!")
        
        render_calendar_with_calplot(schedule)
        st.download_button(
            label="Download Leave Schedule",
            data=schedule.to_csv(index=False),
            file_name="leave_schedule.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
