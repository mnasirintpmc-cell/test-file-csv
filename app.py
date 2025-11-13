import streamlit as st
import pandas as pd

# Configure the page
st.set_page_config(
    page_title="Main Seal Test Viewer",
    page_icon="⚙️",
    layout="wide"
)

def main():
    st.title("⚙️ Main Seal Test Sequence Viewer")
    st.markdown("### Making technical data readable for technicians")
    
    try:
        # Read the CSV file
        df = pd.read_csv('MainSealSet2.csv', delimiter=';')
        
        # Create readable column names
        column_mapping = {
            'TST_SpeedDem': 'Speed (RPM)',
            'TST_CellPresDemand': 'Cell Pressure (bar)',
            'TST_InterPresDemand': 'Interface Pressure (bar)',
            'TST_InterBPDemand_DE': 'BP Drive End (bar)',
            'TST_InterBPDemand_NDE': 'BP Non-Drive End (bar)',
            'TST_GasInjectionDemand': 'Gas Injection (bar)',
            'TST_StepDuration': 'Duration (s)',
            'TST_APFlag': 'Auto Proceed',
            'TST_TempDemand': 'Temperature (°C)',
            'TST_GasType': 'Gas Type',
            'TST_TestMode': 'Test Mode',
            'TST_MeasurementReq': 'Measurement',
            'TST_TorqueCheck': 'Torque Check'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert values to readable format
        df['Auto Proceed'] = df['Auto Proceed'].map({0: 'No', 1: 'Yes'})
        df['Measurement'] = df['Measurement'].map({0: 'No', 1: 'Yes'})
        df['Torque Check'] = df['Torque Check'].map({0: 'No'})
        df['Test Mode'] = df['Test Mode'].map({1: 'Mode 1', 2: 'Mode 2'})
        
        # Add step numbers
        df.insert(0, 'Step', range(1, len(df) + 1))
        
        st.success(f"✅ Successfully loaded {len(df)} test steps!")
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Steps", len(df))
        with col2:
            st.metric("Temperature Range", f"{df['Temperature (°C)'].min()}°C - {df['Temperature (°C)'].max()}°C")
        with col3:
            st.metric("Test Modes", len(df['Test Mode'].unique()))
        with col4:
            st.metric("Total Duration", f"{df['Duration (s)'].sum()}s")
        
        # Filters
        st.sidebar.title("🔧 Filters")
        
        temperatures = st.sidebar.multiselect(
            "Filter by Temperature:",
            options=sorted(df['Temperature (°C)'].unique()),
            default=sorted(df['Temperature (°C)'].unique())
        )
        
        test_modes = st.sidebar.multiselect(
            "Filter by Test Mode:",
            options=df['Test Mode'].unique().tolist(),
            default=df['Test Mode'].unique().tolist()
        )
        
        # Apply filters
        filtered_df = df[
            (df['Temperature (°C)'].isin(temperatures)) &
            (df['Test Mode'].isin(test_modes))
        ]
        
        # Display data
        st.subheader("📋 Test Sequence Data")
        st.dataframe(filtered_df, use_container_width=True, height=500)
        
        # Download button
        st.subheader("📥 Export Data")
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download filtered data as CSV",
            data=csv,
            file_name="filtered_test_sequence.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info("""
        **Troubleshooting tips:**
        - Make sure 'MainSealSet2.csv' is in your GitHub repository
        - Check that the file uses semicolon (;) as delimiter
        - Verify the file is not empty
        """)

if __name__ == "__main__":
    main()
