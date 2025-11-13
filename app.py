import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="Main Seal Test Manager",
    page_icon="⚙️",
    layout="wide"
)

def create_technician_template():
    """Create an Excel template that's easy for technicians to edit"""
    
    # Define the template structure with descriptions
    template_data = {
        'Step': ['Enter step number (1,2,3...)'],
        'Speed_RPM': ['Rotational speed in RPM (0 for stationary)'],
        'Cell_Pressure_bar': ['Main cell pressure in bar'],
        'Interface_Pressure_bar': ['Interface pressure in bar'],
        'BP_Drive_End_bar': ['Back pressure - drive end in bar'],
        'BP_Non_Drive_End_bar': ['Back pressure - non-drive end in bar'],
        'Gas_Injection_bar': ['Gas injection pressure in bar'],
        'Duration_s': ['Step duration in seconds'],
        'Auto_Proceed': ['Auto proceed? (Yes/No)'],
        'Temperature_C': ['Temperature in Celsius'],
        'Gas_Type': ['Gas type (Air/N2/He...)'],
        'Test_Mode': ['Test mode (Mode 1/Mode 2)'],
        'Measurement': ['Take measurement? (Yes/No)'],
        'Torque_Check': ['Torque check? (Yes/No)'],
        'Notes': ['Optional notes for technician']
    }
    
    # Create template DataFrame
    template_df = pd.DataFrame(template_data)
    
    # Add example rows
    example_rows = [
        [1, 0, 0.21, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Initial low pressure'],
        [2, 0, 0.4, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Pressure increase'],
        [3, 0, 1.0, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Medium pressure'],
        [4, 3600, 10, 0, 1, 1, 0, 10, 'Yes', 155, 'Air', 'Mode 1', 'Yes', 'No', 'High speed test'],
        [5, 0, 0, 0, 0, 0, 0, 1, 'No', 155, 'Air', 'Mode 1', 'No', 'No', 'Cool down']
    ]
    
    example_df = pd.DataFrame(example_rows, columns=template_df.columns)
    
    return template_df, example_df

def excel_to_machine_csv(excel_file):
    """Convert technician Excel to machine-readable CSV"""
    
    # Read Excel file
    df = pd.read_excel(excel_file)
    
    # Remove template row if present
    if 'Enter step number' in str(df.iloc[0]['Step']):
        df = df.iloc[1:].reset_index(drop=True)
    
    # Convert back to machine format
    machine_mapping = {
        'Speed_RPM': 'TST_SpeedDem',
        'Cell_Pressure_bar': 'TST_CellPresDemand',
        'Interface_Pressure_bar': 'TST_InterPresDemand',
        'BP_Drive_End_bar': 'TST_InterBPDemand_DE',
        'BP_Non_Drive_End_bar': 'TST_InterBPDemand_NDE',
        'Gas_Injection_bar': 'TST_GasInjectionDemand',
        'Duration_s': 'TST_StepDuration',
        'Auto_Proceed': 'TST_APFlag',
        'Temperature_C': 'TST_TempDemand',
        'Gas_Type': 'TST_GasType',
        'Test_Mode': 'TST_TestMode',
        'Measurement': 'TST_MeasurementReq',
        'Torque_Check': 'TST_TorqueCheck'
    }
    
    # Rename columns
    df = df.rename(columns=machine_mapping)
    
    # Convert readable values back to machine codes
    df['TST_APFlag'] = df['TST_APFlag'].map({'Yes': 1, 'No': 0})
    df['TST_MeasurementReq'] = df['TST_MeasurementReq'].map({'Yes': 1, 'No': 0})
    df['TST_TorqueCheck'] = df['TST_TorqueCheck'].map({'Yes': 1, 'No': 0})
    df['TST_TestMode'] = df['TST_TestMode'].map({'Mode 1': 1, 'Mode 2': 2})
    
    # Remove Step and Notes columns for machine CSV
    machine_df = df.drop(['Step', 'Notes'], axis=1, errors='ignore')
    
    return machine_df

def machine_csv_to_excel(csv_file):
    """Convert machine CSV to technician Excel format"""
    
    # Read machine CSV
    df = pd.read_csv(csv_file, delimiter=';')
    
    # Convert to technician format
    technician_mapping = {
        'TST_SpeedDem': 'Speed_RPM',
        'TST_CellPresDemand': 'Cell_Pressure_bar',
        'TST_InterPresDemand': 'Interface_Pressure_bar',
        'TST_InterBPDemand_DE': 'BP_Drive_End_bar',
        'TST_InterBPDemand_NDE': 'BP_Non_Drive_End_bar',
        'TST_GasInjectionDemand': 'Gas_Injection_bar',
        'TST_StepDuration': 'Duration_s',
        'TST_APFlag': 'Auto_Proceed',
        'TST_TempDemand': 'Temperature_C',
        'TST_GasType': 'Gas_Type',
        'TST_TestMode': 'Test_Mode',
        'TST_MeasurementReq': 'Measurement',
        'TST_TorqueCheck': 'Torque_Check'
    }
    
    # Rename columns
    df = df.rename(columns=technician_mapping)
    
    # Convert machine codes to readable values
    df['Auto_Proceed'] = df['Auto_Proceed'].map({0: 'No', 1: 'Yes'})
    df['Measurement'] = df['Measurement'].map({0: 'No', 1: 'Yes'})
    df['Torque_Check'] = df['Torque_Check'].map({0: 'No'})
    df['Test_Mode'] = df['Test_Mode'].map({1: 'Mode 1', 2: 'Mode 2'})
    
    # Add Step numbers and Notes column
    df.insert(0, 'Step', range(1, len(df) + 1))
    df['Notes'] = ''  # Empty notes column for technicians
    
    return df

def main():
    st.title("⚙️ Main Seal Test Sequence Manager")
    st.markdown("### Bridge between Technicians and Machine Control System")
    
    # Sidebar
    st.sidebar.title("🔧 Operations")
    operation = st.sidebar.radio(
        "Choose Operation:",
        ["📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
    )
    
    if operation == "📥 Download Template":
        st.header("Download Technician Template")
        
        template_df, example_df = create_technician_template()
        
        st.info("""
        **Instructions:**
        1. Download the template below
        2. Edit in Excel (add your test steps)
        3. Save your completed test sequence
        4. Upload back here to generate machine CSV
        """)
        
        # Create downloadable template
        with pd.ExcelWriter('technician_template.xlsx', engine='openpyxl') as writer:
            # Template sheet with instructions
            template_df.to_excel(writer, sheet_name='TEMPLATE_INSTRUCTIONS', index=False)
            # Example sheet
            example_df.to_excel(writer, sheet_name='EXAMPLE_TEST', index=False)
        
        with open('technician_template.xlsx', 'rb') as f:
            st.download_button(
                label="📥 Download Technician Template (.xlsx)",
                data=f,
                file_name=f"test_sequence_template_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.subheader("Template Preview")
        st.dataframe(template_df, use_container_width=True)
        
        st.subheader("Example Test Sequence")
        st.dataframe(example_df, use_container_width=True)
    
    elif operation == "🔄 Excel to Machine CSV":
        st.header("Convert Excel to Machine CSV")
        
        uploaded_file = st.file_uploader("Upload your completed Excel template", type=['xlsx'])
        
        if uploaded_file:
            try:
                # Convert to machine format
                machine_df = excel_to_machine_csv(uploaded_file)
                
                st.success(f"✅ Successfully converted {len(machine_df)} test steps!")
                
                # Preview
                st.subheader("Machine CSV Preview")
                st.dataframe(machine_df, use_container_width=True)
                
                # Download machine CSV
                csv_data = machine_df.to_csv(index=False, sep=';')
                st.download_button(
                    label="📥 Download Machine CSV",
                    data=csv_data,
                    file_name=f"machine_sequence_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"❌ Error converting file: {str(e)}")
    
    elif operation == "📤 Machine CSV to Excel":
        st.header("Convert Machine CSV to Excel")
        
        uploaded_file = st.file_uploader("Upload machine CSV file", type=['csv'])
        
        if uploaded_file:
            try:
                # Convert to technician format
                technician_df = machine_csv_to_excel(uploaded_file)
                
                st.success(f"✅ Successfully converted {len(technician_df)} test steps!")
                
                # Preview
                st.subheader("Technician Excel Preview")
                st.dataframe(technician_df, use_container_width=True)
                
                # Download technician Excel
                with pd.ExcelWriter('technician_version.xlsx', engine='openpyxl') as writer:
                    technician_df.to_excel(writer, sheet_name='TEST_SEQUENCE', index=False)
                
                with open('technician_version.xlsx', 'rb') as f:
                    st.download_button(
                        label="📥 Download Technician Excel",
                        data=f,
                        file_name=f"technician_sequence_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
            except Exception as e:
                st.error(f"❌ Error converting file: {str(e)}")
    
    elif operation == "👀 View Current Test":
        st.header("Current Test Sequence")
        
        # Try to load the existing CSV
        try:
            df = pd.read_csv('MainSealSet2.csv', delimiter=';')
            technician_df = machine_csv_to_excel('MainSealSet2.csv')
            
            st.success(f"✅ Loaded existing test sequence with {len(df)} steps")
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Steps", len(df))
            with col2:
                st.metric("Temperature Range", f"{df['TST_TempDemand'].min()}°C - {df['TST_TempDemand'].max()}°C")
            with col3:
                st.metric("Max Speed", f"{df['TST_SpeedDem'].max()} RPM")
            with col4:
                st.metric("Total Duration", f"{df['TST_StepDuration'].sum()}s")
            
            # Display in technician-friendly format
            st.subheader("Current Test Sequence (Technician View)")
            st.dataframe(technician_df, use_container_width=True, height=500)
            
        except Exception as e:
            st.error(f"❌ Could not load current test sequence: {str(e)}")
            st.info("Upload a file using the conversion tools above to get started.")

if __name__ == "__main__":
    main()
