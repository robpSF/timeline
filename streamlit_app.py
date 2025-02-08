import streamlit as st
import pandas as pd
import altair as alt

st.title("Interactive Gantt Chart Timeline from CSV (Altair)")

st.markdown(
    """
Upload a CSV file with these columns:  
`Serial, Number, Time, From, Faction, To, Team, Method, On, Subject, Message, Reply, timestamp, Expected Action, Expected Action Title, Expected Action ImageURL, ImageURL`.

**Timeline Construction:**

- **Overall Timeline (Serial-level):**  
  Each unique **Serial** is represented by one bar.  
  • The start time is the first inject’s **Time** for that serial.  
  • The end time is the first **Time** of the next serial (or the last time for the final serial).  
  • The bar is labeled (on the bar, aligned left in black) with the **Serial**.

- **Detailed Timeline (Inject-level):**  
  When you select a serial, its timeline “unfurls” to show each individual inject (row) as a separate bar.  
  • For each inject, the start time is its **Time** value and the end time is the next inject’s **Time** (or the overall serial end for the final inject).  
  • The overlaid text on each bar (aligned left in black with a slight offset) is determined as follows:  
  – If **Subject** is nonempty and not `"null"`, then use **Subject**.  
  – Otherwise, use the first **30** characters of **Message** (with `"..."` appended if **Message** is longer than 30 characters).  
  • The tooltip displays the first **120** characters of **Message**.  
  • If **ImageURL** is provided (nonempty), an image (50×50 pixels) appears on hover to the right of the bar.  
  • **New:** Instead of showing generic “Inject 1”, “Inject 2”, etc. on the y‑axis, a toggle switch lets you choose whether to show either the **From** field (“Persona”) or the **Method** field (“Channel”).

Use the dropdown below to switch between the overall view and a detailed view.
"""
)

# File uploader widget.
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV data.
        df = pd.read_csv(uploaded_file)

        # Verify required columns exist.
        required_columns = ["Serial", "Time", "Subject", "Message", "ImageURL", "From", "Method"]
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

        ##############################
        # Overall (Serial-level) Timeline
        ##############################
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

        ##############################
        # Select Overall or Detailed View
        ##############################
        options = ["Overall Timeline"] + list(serials)
        selected_serial = st.selectbox(
            "Select a Serial to view its detailed (inject-level) timeline:",
            options=options
        )

        if selected_serial == "Overall Timeline":
            st.subheader("Overall Timeline (Serial-level)")
            # Overall timeline: one bar per serial with the Serial label.
            overall_chart = alt.Chart(serial_timeline_df).mark_bar().encode(
                x=alt.X("Start:T", title="Time"),
                x2="End:T",
                y=alt.Y("Serial:N", title="Serial"),
                tooltip=["Serial", "Start", "End"]
            ).properties(width=700, height=300)
            
            # Overlay the Serial text at the start of each bar (left aligned, black).
            overall_text = alt.Chart(serial_timeline_df).mark_text(
                align="left",
                baseline="middle",
                color="black",
                dx=3  # slight offset from the start of the bar
            ).encode(
                x=alt.X("Start:T"),
                y=alt.Y("Serial:N"),
                text=alt.Text("Serial:N")
            )
            
            st.altair_chart(overall_chart + overall_text, use_container_width=True)

        else:
            st.subheader(f"Detailed Timeline for Serial: **{selected_serial}**")
            # Let the user choose whether to label the detailed timeline by Persona or Channel.
            label_option = st.radio("Select detailed timeline label", ["Persona", "Channel"])
            # 'Persona' will display the 'From' column; 'Channel' will display the 'Method' column.

            # Get all injects (rows) for the selected serial.
            group = df[df["Serial"] == selected_serial].reset_index(drop=True)
            # Determine overall end for this serial using the overall timeline info.
            overall_end = serial_timeline_df[serial_timeline_df["Serial"] == selected_serial]["End"].iloc[0]

            ##############################
            # Build inject-level timeline data.
            ##############################
            inject_timeline = []
            for i in range(len(group)):
                start_time = group["Time"].iloc[i]
                if i < len(group) - 1:
                    end_time = group["Time"].iloc[i + 1]
                else:
                    end_time = overall_end

                # Determine display text.
                subject_val = group["Subject"].iloc[i]
                message_val = group["Message"].iloc[i] if pd.notnull(group["Message"].iloc[i]) else ""
                if (pd.isna(subject_val) or str(subject_val).strip() == "" or 
                    str(subject_val).strip().lower() == "null"):
                    # Use first 30 characters of Message.
                    if isinstance(message_val, str) and len(message_val) > 30:
                        display_text = message_val[:30] + "..."
                    else:
                        display_text = message_val
                else:
                    display_text = subject_val

                # Build message snippet for tooltip (first 120 characters of Message).
                if isinstance(message_val, str) and len(message_val) > 120:
                    message_snippet = message_val[:120] + "..."
                else:
                    message_snippet = message_val

                # Also capture ImageURL.
                image_url = group["ImageURL"].iloc[i] if pd.notnull(group["ImageURL"].iloc[i]) else ""

                # Determine the axis label based on the toggle switch.
                if label_option == "Persona":
                    axis_label = group["From"].iloc[i]
                else:
                    axis_label = group["Method"].iloc[i]

                inject_timeline.append({
                    "AxisLabel": axis_label,
                    "Start": start_time,
                    "End": end_time,
                    "DisplayText": display_text,
                    "MessageSnippet": message_snippet,
                    "ImageURL": image_url
                })

            inject_timeline_df = pd.DataFrame(inject_timeline)

            ##############################
            # Build Detailed Timeline Chart with Hover
            ##############################
            # Define a hover selection on the AxisLabel field.
            hover = alt.selection_single(fields=["AxisLabel"], on="mouseover", nearest=True, empty="none")

            # Base bar chart.
            bar_chart = alt.Chart(inject_timeline_df).mark_bar(color="orange").encode(
                x=alt.X("Start:T", title="Time"),
                x2="End:T",
                y=alt.Y("AxisLabel:N", title=label_option),
                tooltip=[
                    alt.Tooltip("AxisLabel:N", title=label_option),
                    alt.Tooltip("Start:T", title="Start"),
                    alt.Tooltip("End:T", title="End"),
                    alt.Tooltip("MessageSnippet:N", title="Message")
                ]
            ).properties(width=700, height=100 + 30 * len(inject_timeline_df)).add_selection(hover)

            # Overlay the display text at the start of each bar (left aligned, black).
            text_chart = alt.Chart(inject_timeline_df).mark_text(
                align="left",
                baseline="middle",
                color="black",
                dx=3
            ).encode(
                x=alt.X("Start:T"),
                y=alt.Y("AxisLabel:N"),
                text=alt.Text("DisplayText:N")
            )

            # Create an image layer that appears on hover if ImageURL is not empty.
            image_layer = alt.Chart(inject_timeline_df).mark_image(width=50, height=50).encode(
                # Position the image to the right of the bar (using the End time).
                x=alt.X("End:T", title="Time"),
                y=alt.Y("AxisLabel:N", title=label_option),
                url=alt.Url("ImageURL:N"),
                opacity=alt.condition(hover, alt.value(1), alt.value(0))
            ).transform_filter("datum.ImageURL != ''")

            # Layer the bar chart, text, and image.
            detailed_chart = bar_chart + text_chart + image_layer

            st.altair_chart(detailed_chart, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
