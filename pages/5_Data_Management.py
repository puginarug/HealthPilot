"""Data Management page.

Upload and manage health data (activity, heart rate, sleep).
"""

from __future__ import annotations

import logging
from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Data Management", page_icon="📊", layout="wide")


def main() -> None:
    """Render the data management page."""
    st.header("📊 Data Management")
    st.caption("Upload and manage your health data")

    st.markdown(
        """
        Upload CSV files with your health data to enable AI-powered insights and analytics.
        The app supports three types of data: **Activity**, **Heart Rate**, and **Sleep**.
        """
    )

    # Create tabs for different data types
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚶 Activity Data",
        "❤️ Heart Rate Data",
        "😴 Sleep Data",
        "📥 Current Data"
    ])

    # ===== TAB 1: ACTIVITY DATA =====
    with tab1:
        st.subheader("🚶 Activity Data Upload")

        st.markdown(
            """
            Upload your daily activity data including steps, distance, calories, and active minutes.
            This data is used for activity analysis and recommendations.
            """
        )

        # Show expected format
        with st.expander("📋 Expected CSV Format", expanded=False):
            st.markdown(
                """
                **Required columns:**
                - `date` (YYYY-MM-DD format)
                - `steps` (integer)
                - `distance_km` (float)
                - `calories_burned` (integer)
                - `active_minutes` (integer)

                **Example:**
                ```
                date,steps,distance_km,calories_burned,active_minutes
                2024-01-01,8500,6.2,320,45
                2024-01-02,10200,7.5,380,58
                ```
                """
            )

        # Sample template download
        sample_activity = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "steps": [8500, 10200, 7800],
            "distance_km": [6.2, 7.5, 5.9],
            "calories_burned": [320, 380, 290],
            "active_minutes": [45, 58, 38],
        })

        st.download_button(
            "📥 Download Sample Template",
            data=sample_activity.to_csv(index=False),
            file_name="activity_data_template.csv",
            mime="text/csv",
            help="Download a sample CSV to see the expected format",
        )

        st.markdown("---")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload Activity Data CSV",
            type=["csv"],
            key="activity_upload",
            help="Upload your activity data CSV file",
        )

        if uploaded_file is not None:
            try:
                # Read CSV
                df = pd.read_csv(uploaded_file)

                # Validate columns
                required_cols = ["date", "steps", "distance_km", "calories_burned", "active_minutes"]
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    # Show preview
                    st.success(f"✅ Valid CSV! Found {len(df)} rows")
                    st.dataframe(df.head(10), use_container_width=True)

                    # Save button
                    if st.button("💾 Save Activity Data", type="primary"):
                        data_dir = Path("data")
                        data_dir.mkdir(exist_ok=True)

                        output_path = data_dir / "activity_data.csv"
                        df.to_csv(output_path, index=False)

                        st.success(f"✅ Activity data saved to {output_path}")
                        logger.info("Activity data uploaded: %d rows", len(df))

            except Exception as e:
                logger.error("Failed to process activity data: %s", e)
                st.error(f"❌ Error processing file: {e}")

    # ===== TAB 2: HEART RATE DATA =====
    with tab2:
        st.subheader("❤️ Heart Rate Data Upload")

        st.markdown(
            """
            Upload your heart rate measurements for heart rate zone analysis and fitness insights.
            """
        )

        # Show expected format
        with st.expander("📋 Expected CSV Format", expanded=False):
            st.markdown(
                """
                **Required columns:**
                - `timestamp` (YYYY-MM-DD HH:MM:SS format)
                - `heart_rate` (integer, beats per minute)

                **Example:**
                ```
                timestamp,heart_rate
                2024-01-01 08:30:00,72
                2024-01-01 09:45:00,95
                2024-01-01 10:30:00,68
                ```
                """
            )

        # Sample template download
        sample_hr = pd.DataFrame({
            "timestamp": [
                "2024-01-01 08:30:00",
                "2024-01-01 09:45:00",
                "2024-01-01 10:30:00",
            ],
            "heart_rate": [72, 95, 68],
        })

        st.download_button(
            "📥 Download Sample Template",
            data=sample_hr.to_csv(index=False),
            file_name="heart_rate_data_template.csv",
            mime="text/csv",
        )

        st.markdown("---")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload Heart Rate Data CSV",
            type=["csv"],
            key="hr_upload",
            help="Upload your heart rate data CSV file",
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)

                required_cols = ["timestamp", "heart_rate"]
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.success(f"✅ Valid CSV! Found {len(df)} rows")
                    st.dataframe(df.head(10), use_container_width=True)

                    if st.button("💾 Save Heart Rate Data", type="primary"):
                        data_dir = Path("data")
                        data_dir.mkdir(exist_ok=True)

                        output_path = data_dir / "heart_rate_data.csv"
                        df.to_csv(output_path, index=False)

                        st.success(f"✅ Heart rate data saved to {output_path}")
                        logger.info("Heart rate data uploaded: %d rows", len(df))

            except Exception as e:
                logger.error("Failed to process heart rate data: %s", e)
                st.error(f"❌ Error processing file: {e}")

    # ===== TAB 3: SLEEP DATA =====
    with tab3:
        st.subheader("😴 Sleep Data Upload")

        st.markdown(
            """
            Upload your sleep tracking data for sleep analysis and recommendations.
            """
        )

        # Show expected format
        with st.expander("📋 Expected CSV Format", expanded=False):
            st.markdown(
                """
                **Required columns:**
                - `date` (YYYY-MM-DD format)
                - `bedtime` (HH:MM:SS format)
                - `wake_time` (HH:MM:SS format)
                - `duration_hours` (float)
                - `quality` (1-5 scale, optional)

                **Example:**
                ```
                date,bedtime,wake_time,duration_hours,quality
                2024-01-01,23:00:00,07:00:00,8.0,4
                2024-01-02,23:30:00,06:45:00,7.25,3
                ```
                """
            )

        # Sample template download
        sample_sleep = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "bedtime": ["23:00:00", "23:30:00", "22:45:00"],
            "wake_time": ["07:00:00", "06:45:00", "07:15:00"],
            "duration_hours": [8.0, 7.25, 8.5],
            "quality": [4, 3, 5],
        })

        st.download_button(
            "📥 Download Sample Template",
            data=sample_sleep.to_csv(index=False),
            file_name="sleep_data_template.csv",
            mime="text/csv",
        )

        st.markdown("---")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload Sleep Data CSV",
            type=["csv"],
            key="sleep_upload",
            help="Upload your sleep data CSV file",
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)

                required_cols = ["date", "bedtime", "wake_time", "duration_hours"]
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.success(f"✅ Valid CSV! Found {len(df)} rows")
                    st.dataframe(df.head(10), use_container_width=True)

                    if st.button("💾 Save Sleep Data", type="primary"):
                        data_dir = Path("data")
                        data_dir.mkdir(exist_ok=True)

                        output_path = data_dir / "sleep_data.csv"
                        df.to_csv(output_path, index=False)

                        st.success(f"✅ Sleep data saved to {output_path}")
                        logger.info("Sleep data uploaded: %d rows", len(df))

            except Exception as e:
                logger.error("Failed to process sleep data: %s", e)
                st.error(f"❌ Error processing file: {e}")

    # ===== TAB 4: CURRENT DATA =====
    with tab4:
        st.subheader("📥 Current Data Files")

        st.markdown("View and manage your currently uploaded health data.")

        data_dir = Path("data")

        # Activity data
        activity_path = data_dir / "activity_data.csv"
        if activity_path.exists():
            st.markdown("### 🚶 Activity Data")
            try:
                df = pd.read_csv(activity_path)
                st.success(f"✅ {len(df)} rows | Last modified: {datetime.fromtimestamp(activity_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

                with st.expander("Preview Data", expanded=False):
                    st.dataframe(df.head(20), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Download",
                        data=df.to_csv(index=False),
                        file_name="activity_data.csv",
                        mime="text/csv",
                    )
                with col2:
                    if st.button("🗑️ Delete Activity Data"):
                        activity_path.unlink()
                        st.success("Deleted!")
                        st.rerun()
            except Exception as e:
                st.error(f"Error loading activity data: {e}")
        else:
            st.info("📭 No activity data uploaded yet")

        st.markdown("---")

        # Heart rate data
        hr_path = data_dir / "heart_rate_data.csv"
        if hr_path.exists():
            st.markdown("### ❤️ Heart Rate Data")
            try:
                df = pd.read_csv(hr_path)
                st.success(f"✅ {len(df)} rows | Last modified: {datetime.fromtimestamp(hr_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

                with st.expander("Preview Data", expanded=False):
                    st.dataframe(df.head(20), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Download",
                        data=df.to_csv(index=False),
                        file_name="heart_rate_data.csv",
                        mime="text/csv",
                    )
                with col2:
                    if st.button("🗑️ Delete Heart Rate Data"):
                        hr_path.unlink()
                        st.success("Deleted!")
                        st.rerun()
            except Exception as e:
                st.error(f"Error loading heart rate data: {e}")
        else:
            st.info("📭 No heart rate data uploaded yet")

        st.markdown("---")

        # Sleep data
        sleep_path = data_dir / "sleep_data.csv"
        if sleep_path.exists():
            st.markdown("### 😴 Sleep Data")
            try:
                df = pd.read_csv(sleep_path)
                st.success(f"✅ {len(df)} rows | Last modified: {datetime.fromtimestamp(sleep_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

                with st.expander("Preview Data", expanded=False):
                    st.dataframe(df.head(20), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Download",
                        data=df.to_csv(index=False),
                        file_name="sleep_data.csv",
                        mime="text/csv",
                    )
                with col2:
                    if st.button("🗑️ Delete Sleep Data"):
                        sleep_path.unlink()
                        st.success("Deleted!")
                        st.rerun()
            except Exception as e:
                st.error(f"Error loading sleep data: {e}")
        else:
            st.info("📭 No sleep data uploaded yet")


# Run main function
main()
