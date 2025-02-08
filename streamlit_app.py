import streamlit as st
import pandas as pd
import altair as alt

st.title("Interactive Gantt Chart Timeline from CSV (Altair)")

st.markdown(
    """
Upload a CSV file with these columns:  
`Serial, Number, Time, From, Faction, To, Team, Method, On, Subject, Message, Reply, timestamp, Expected Action, Expected Action Title, Expected Action ImageURL, ImageURL`.

**Timeline Construction:**
- **Overall Timeline:**  
  Each unique **Serial** is represented by one bar.  
  The start time is the first inject’s **Time** for that serial.  
  The end time is the first **Time** of the next serial (or the last time for the final serial).

- **Detailed (Inject-level) Timeline:**  
  When you select a serial, its timeline “unfurls” to show each individual inject (row) as a separate bar.  
  For each inject, the start time is its **Time** value and the end time is the next inject’s **Time** (or the overall serial end for the final inject).  
  The **Subject** text is overlaid at the center of each bar.

Use the dropdown below to switch between the overall view and a detailed view.
"""
)

# File uploader widget
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV data
        df = pd.read_csv(uploaded_file)

        # Verify required columns exist.
        required_columns = ["Serial", "Time", "Subject"]
        for col in required_columns:
            if col not in df.columns:
                st.error(f"Missing required column: {col}")
                st.stop()

        # Convert the 'Time' column to datetime and sort the data.
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        if df["Time"].isnull().all():
            st.error("No valid dates found in the 'Time' column.")
            st.stop()
        df = df.sort_values("Time").reset_index(drop=True)

        # Build overall (serial-level) timeline data.
        serials = df["Serial"].unique()
        serial_timeline = []
        for i, serial in enumerate(serials):
            group = df[df["Serial"] == serial]
            start_time = group["Time"].iloc[0]
            if i < len(serials) - 1:
                # End time is the first Time of the next serial.
                next_serial = serials[i + 1]
                next_group = df[df["Serial"] == next_serial]
                end_time = next_group["Time"].iloc[0]
            else:
                # For the final serial, use the last time of the group.
                end_time = group["Time"].iloc[-1]
            serial_timeline.append({
                "Serial": serial,
                "Start": start_time,
                "End": end_time
            })
        serial_timeline_df = pd.DataFrame(serial_timeline)

        # Let the user choose between the overall timeline and a detailed view.
        options = ["Overall Timeline"] + list(serials)
        selected_serial = st.selectbox(
            "Select a Serial to view its detailed (inject-level) timeline:",
            options=options
        )

        if selected_serial == "Overall Timeline":
            st.subheader("Overall Timeline (Serial-level)")
            # In the overall view, we display one bar per serial.
            chart = alt.Chart(serial_timeline_df).mark_bar().encode(
                x=alt.X("Start:T", title="Time"),
                x2="End:T",
                y=alt.Y("Serial:N", title="Serial"),
                tooltip=["Serial", "Start", "End"]
            ).properties(width=700, height=300)
            
            # Overlay the Serial text at the start of each bar with a slight offset, in black.
            text = alt.Chart(serial_timeline_df).mark_text(
                align="left",
                baseline="middle",
                color="black",
                dx=3  # slight right offset
            ).encode(
                x=alt.X("Start:T"),
                y=alt.Y("Serial:N"),
                text=alt.Text("Serial:N")
            )
            
            st.altair_chart(chart + text, use_container_width=True)

        else:
            st.subheader(f"Detailed Timeline for Serial: **{selected_serial}**")
            # Get all injects (rows) for the selected serial.
            group = df[df["Serial"] == selected_serial].reset_index(drop=True)

            # Find the overall end for this serial using the serial_timeline info.
            overall_end = serial_timeline_df[serial_timeline_df["Serial"] == selected_serial]["End"].iloc[0]

            # Build inject-level timeline data.
            inject_timeline = []
            for i in range(len(group)):
                start_time = group["Time"].iloc[i]
                if i < len(group) - 1:
                    end_time = group["Time"].iloc[i + 1]
                else:
                    end_time = overall_end
                inject_timeline.append({
                    "Inject": f"Inject {i+1}",
                    "Start": start_time,
                    "End": end_time,
                    "Subject": group["Subject"].iloc[i]
                })
            inject_timeline_df = pd.DataFrame(inject_timeline)
            # Compute the midpoint of each bar for placing the text.
            inject_timeline_df["midpoint"] = inject_timeline_df.apply(
                lambda row: row["Start"] + (row["End"] - row["Start"]) / 2, axis=1
            )

            # Build the bar chart for the detailed view.
            bar_chart = alt.Chart(inject_timeline_df).mark_bar(color="orange").encode(
                x=alt.X("Start:T", title="Time"),
                x2="End:T",
                y=alt.Y("Inject:N", title="Inject"),
                tooltip=["Inject", "Start", "End", "Subject"]
            ).properties(width=700, height=100 + 30 * len(inject_timeline_df))

            # Overlay the subject text on each bar.
            text_chart = alt.Chart(inject_timeline_df).mark_text(
                align="center",
                baseline="middle",
                color="white",
                dx=0  # no horizontal offset
            ).encode(
                x=alt.X("midpoint:T"),
                y=alt.Y("Inject:N"),
                text=alt.Text("Subject:N")
            )

            st.altair_chart(bar_chart + text_chart, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
