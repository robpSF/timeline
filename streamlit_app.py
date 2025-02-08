import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events

st.title("Interactive Gantt Chart Timeline from CSV")

st.markdown("""
Upload a CSV file with the following columns:  
`Serial, Number, Time, From, Faction, To, Team, Method, On, Subject, Message, Reply, timestamp, Expected Action, Expected Action Title, Expected Action ImageURL, ImageURL`.

- **Timeline Creation:**  
  For each serial (group of one or more rows sharing the same **Serial** value):
  - The first **Time** is used as the start time.
  - The first **Time** of the next serial is used as the end time.
  - For the final serial, the last available **Time** is used as the end.
  
- **Interactivity:**  
  Click on a Gantt bar (representing a serial) to reveal the detailed injects (the CSV rows with that Serial).
""")

# File uploader widget
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV data
        df = pd.read_csv(uploaded_file)
        
        # Check for required columns
        required_columns = ["Serial", "Time"]
        for col in required_columns:
            if col not in df.columns:
                st.error(f"Missing required column: {col}")
                st.stop()
        
        # Convert the 'Time' column to datetime and sort the data
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        if df["Time"].isnull().all():
            st.error("No valid dates found in the 'Time' column.")
            st.stop()
        df = df.sort_values("Time").reset_index(drop=True)
        
        st.subheader("Uploaded Data (First 5 Rows)")
        st.dataframe(df.head())
        
        # Build timeline data for each serial
        serials = df["Serial"].unique()
        timeline_data = []
        
        for i, serial in enumerate(serials):
            group_df = df[df["Serial"] == serial]
            start_time = group_df["Time"].iloc[0]
            if i < len(serials) - 1:
                # Use the first time of the next serial as the end time
                next_serial = serials[i + 1]
                next_group_df = df[df["Serial"] == next_serial]
                end_time = next_group_df["Time"].iloc[0]
            else:
                # For the final serial, use the last time of the group as the end
                end_time = group_df["Time"].iloc[-1]
            
            timeline_data.append({
                "Serial": serial,
                "Start": start_time,
                "End": end_time
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        st.subheader("Timeline Data")
        st.dataframe(timeline_df)
        
        # Create the Gantt chart timeline using Plotly Express
        fig = px.timeline(
            timeline_df,
            x_start="Start",
            x_end="End",
            y="Serial",
            title="Gantt Chart Timeline"
        )
        # Reverse the y-axis so the earliest serial is at the top
        fig.update_yaxes(autorange="reversed")
        
        st.subheader("Interactive Gantt Chart")
        st.markdown("Click on a bar to view the injects (detailed rows) for that serial.")
        
        # Capture click events on the Plotly chart
        clicked_points = plotly_events(fig, click_event=True)
        
        if clicked_points:
            clicked_serial = clicked_points[0]['y']
            st.markdown(f"### Details for Serial: **{clicked_serial}**")
            injects = df[df["Serial"] == clicked_serial]
            st.dataframe(injects)
        else:
            st.info("Click on a bar to see detailed injects.")
            
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
