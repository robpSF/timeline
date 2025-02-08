import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Gantt Chart Timeline from CSV")

st.markdown("""
Upload a CSV file with the following columns:  
`Serial, Number, Time, From, Faction, To, Team, Method, On, Subject, Message, Reply, timestamp, Expected Action, Expected Action Title, Expected Action ImageURL, ImageURL`.

The app will use the **Serial** column as the label. For each serial group (one or more rows with the same Serial), the first **Time** value is used as the start of that serial, and the first **Time** of the next serial is used as its end. For the final serial, the last available **Time** is used as the end.
""")

# File uploader widget
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV data
        df = pd.read_csv(uploaded_file)
        
        # Ensure the required columns exist
        required_columns = ["Serial", "Time"]
        for col in required_columns:
            if col not in df.columns:
                st.error(f"Missing required column: {col}")
                st.stop()
        
        # Convert the 'Time' column to datetime
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        if df["Time"].isnull().all():
            st.error("No valid dates found in 'Time' column.")
            st.stop()
        
        # Sort the dataframe by time (if not already sorted)
        df = df.sort_values("Time").reset_index(drop=True)
        
        st.subheader("Uploaded Data")
        st.dataframe(df.head())

        # Get the unique serials in the order they appear
        serials = df["Serial"].unique()
        timeline_data = []

        # Loop through each serial group to compute start and end times
        for i, serial in enumerate(serials):
            group_df = df[df["Serial"] == serial]
            start_time = group_df["Time"].iloc[0]
            if i < len(serials) - 1:
                # For non-last serials, use the first time of the next serial as the end time.
                next_serial = serials[i + 1]
                next_group_df = df[df["Serial"] == next_serial]
                end_time = next_group_df["Time"].iloc[0]
            else:
                # For the final serial, use the last time in the group.
                end_time = group_df["Time"].iloc[-1]
            
            timeline_data.append({
                "Serial": serial,
                "Start": start_time,
                "End": end_time
            })

        timeline_df = pd.DataFrame(timeline_data)
        
        st.subheader("Timeline Data")
        st.dataframe(timeline_df)

        # Create the Gantt chart using Plotly Express timeline
        fig = px.timeline(
            timeline_df,
            x_start="Start",
            x_end="End",
            y="Serial",
            title="Gantt Chart Timeline"
        )
        # Optionally, reverse the y-axis so the first serial appears at the top
        fig.update_yaxes(autorange="reversed")
        
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
