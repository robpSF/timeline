import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events

st.title("Interactive Gantt Chart Timeline from CSV")
st.markdown(
    """
Upload a CSV file with these columns:  
`Serial, Number, Time, From, Faction, To, Team, Method, On, Subject, Message, Reply, timestamp, Expected Action, Expected Action Title, Expected Action ImageURL, ImageURL`.

**How it works:**

- **Main Timeline:** Each unique **Serial** is represented by one bar.  
  • The start time is the first inject’s **Time**.  
  • The end time is the first **Time** of the next serial (or the last time for the final serial).

- **Interactive Expansion:**  
  Click on a serial’s bar to toggle expansion. An expanded bar “unfurls” into separate sub‑bars representing each inject (row) in that serial. Click again to collapse.
"""
)

# Initialize session state for expanded serial.
if "expanded_serial" not in st.session_state:
    st.session_state.expanded_serial = None

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV data
        df = pd.read_csv(uploaded_file)

        # Check for required columns.
        required_columns = ["Serial", "Time"]
        for col in required_columns:
            if col not in df.columns:
                st.error(f"Missing required column: {col}")
                st.stop()

        # Convert 'Time' column to datetime and sort the data.
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        if df["Time"].isnull().all():
            st.error("No valid dates were found in the 'Time' column.")
            st.stop()
        df = df.sort_values("Time").reset_index(drop=True)

        # Compute overall timeline start/end for each serial.
        serials = list(df["Serial"].unique())
        serial_timeline = {}  # serial -> dict with keys "start" and "end"
        for i, serial in enumerate(serials):
            group = df[df["Serial"] == serial]
            start = group["Time"].iloc[0]
            if i < len(serials) - 1:
                # End time is the first Time of the next serial.
                next_serial = serials[i + 1]
                next_group = df[df["Serial"] == next_serial]
                end = next_group["Time"].iloc[0]
            else:
                end = group["Time"].iloc[-1]
            serial_timeline[serial] = {"start": start, "end": end}

        # Build chart data.
        # For each serial, if it is expanded then break it into its individual injects,
        # otherwise, add one bar for the entire serial.
        chart_data = []
        expanded_serial = st.session_state.expanded_serial
        for serial in serials:
            if expanded_serial == serial:
                group = df[df["Serial"] == serial].reset_index(drop=True)
                overall_end = serial_timeline[serial]["end"]
                # For each inject in the serial.
                for i in range(len(group)):
                    inject_start = group["Time"].iloc[i]
                    if i < len(group) - 1:
                        inject_end = group["Time"].iloc[i + 1]
                    else:
                        inject_end = overall_end
                    label = f"{serial} (Inject {i + 1})"
                    chart_data.append({
                        "Label": label,
                        "Start": inject_start,
                        "End": inject_end,
                        "Serial": serial,
                        "Type": "inject"
                    })
            else:
                overall_start = serial_timeline[serial]["start"]
                overall_end = serial_timeline[serial]["end"]
                chart_data.append({
                    "Label": serial,
                    "Start": overall_start,
                    "End": overall_end,
                    "Serial": serial,
                    "Type": "serial"
                })

        chart_df = pd.DataFrame(chart_data)

        # Create the timeline chart using Plotly Express.
        # We pass custom_data so that when a bar is clicked, we know which serial it represents.
        fig = px.timeline(
            chart_df,
            x_start="Start",
            x_end="End",
            y="Label",
            color="Type",
            title="Gantt Chart Timeline (Click on a bar to expand/collapse)",
            custom_data=["Serial", "Type"]
        )
        # Reverse the y-axis so the earliest entry is at the top.
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(clickmode="event+select")

        st.subheader("Interactive Timeline Chart")
        st.markdown("Click on a serial bar to expand (or collapse) its injects.")

        # Capture click events on the chart.
        click_data = plotly_events(fig, click_event=True, override_height=600)
        if click_data:
            clicked_serial = click_data[0]["customdata"][0]
            # Toggle expansion: collapse if already expanded; otherwise, expand.
            if st.session_state.expanded_serial == clicked_serial:
                st.session_state.expanded_serial = None
            else:
                st.session_state.expanded_serial = clicked_serial
            # Rerun to update the chart.
            st.experimental_rerun()

        # Display the timeline chart.
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
