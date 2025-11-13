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
    """Create an Excel template with dropdowns using pandas styling"""
    
    # Create template with sample data
    template_data = {
        'Step': [1, 2, 3, 4, 5],
        'Speed_RPM': [0, 0, 0, 3600, 0],
        'Cell_Pressure_bar': [0.21, 0.4, 1.0, 10.0, 0],
        'Interface_Pressure_bar': [0, 0, 0, 0, 0],
        'BP_Drive_End_bar': [0, 0, 0, 1.0, 0],
        'BP_Non_Drive_End_bar': [0, 0, 0, 1.0, 0],
        'Gas_Injection_bar': [0, 0, 0, 0, 0],
        'Duration_s': [2, 2, 2, 10, 1],
        'Auto_Proceed': ['No', 'No', 'No', 'Yes', 'No'],
        'Temperature_C': [30, 30, 30, 155, 155],
        'Gas_Type': ['Air', 'Air', 'Air', 'Air', 'Air'],
        'Test_Mode': ['Mode 1', 'Mode 1', 'Mode 1', 'Mode 1', 'Mode 1'],
        'Measurement': ['Yes', 'Yes', 'Yes', 'Yes', 'No'],
        'Torque_Check': ['No', 'No', 'No', 'No', 'No'],
        'Notes': [
            'Initial low pressure test',
            'Pressure increase', 
            'Medium pressure check',
            'High speed operation',
            'System cool down'
        ]
    }
    
    df = pd.DataFrame(template_data)
    
    return df

def create_instructions_sheet():
    """Create instructions as a separate DataFrame"""
    instructions = {
        'Instruction': [
            'MAIN SEAL TEST SEQUENCE TEMPLATE - INSTRUCTIONS',
            '',
            'HOW TO USE THIS TEMPLATE:',
            '1. Fill in the TEST_SEQUENCE sheet with your test parameters',
            '2. Use the dropdown menus for standardized inputs',
            '3. Required fields: Step, Speed, Cell Pressure, Duration, Temperature',
            '4. Save your completed file and upload back to the web app',
            '5. Download the generated CSV for your control system',
            '',
            'FIELD DESCRIPTIONS:',
            'Step: Sequential test step number (1, 2, 3...)',
            'Speed_RPM: Rotational speed (0 = stationary, 3600 = max speed)',
            'Cell_Pressure_bar: Main chamber pressure (0.1 - 100 bar)',
            'Interface_Pressure_bar: Interface pressure (0-40 bar)',
            'BP_Drive_End_bar: Back pressure drive end (0-7 bar)',
            'BP_Non_Drive_End_bar: Back pressure non-drive end (0-7 bar)',
            'Gas_Injection_bar: Gas injection pressure (0-5 bar)',
            'Duration_s: Step duration in seconds (1-300)',
            'Auto_Proceed: Automatic step progression (Yes/No)',
            'Temperature_C: Test temperature (30-155°C)',
            'Gas_Type: Test gas type (Air/N2/He)',
            'Test_Mode: Operating mode (Mode 1/Mode 2)',
            'Measurement: Take measurements (Yes/No)',
            'Torque_Check: Perform torque check (Yes/No)',
            'Notes: Additional comments or observations'
        ]
    }
    
    return pd.DataFrame(instructions)

def excel_to_machine_csv(excel_file):
    """Convert technician Excel to machine-readable CSV"""
    
    # Read Excel file
    df = pd.read_excel(excel_file)
    
    # Remove empty rows
    df = df.dropna(subset=['Step']).reset_index(drop=True)
    
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
    st.markdown("### Professional Template System for Technicians")
    
    # Sidebar
    st.sidebar.title("🔧 Operations")
    operation = st.sidebar.radio(
        "Choose Operation:",
        ["📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
    )
    
    if operation == "📥 Download Template":
        st.header("Download Professional Excel Template")
        
        st.info("""
        **🎯 Features of this template:**
        - 📋 **Pre-formatted columns** with clear headers
        - 📝 **Sample data** for guidance
        - 🔄 **Easy conversion** to machine format
        - 💡 **Built-in validation** through standardized formats
        """)
        
        # Create templates
        template_df = create_technician_template()
        instructions_df = create_instructions_sheet()
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter('technician_template.xlsx', engine='openpyxl') as writer:
            instructions_df.to_excel(writer, sheet_name='INSTRUCTIONS', index=False)
            template_df.to_excel(writer, sheet_name='TEST_SEQUENCE', index=False)
        
        with open('technician_template.xlsx', 'rb') as f:
            st.download_button(
                label="📥 Download Professional Template (.xlsx)",
                data=f,
                file_name=f"main_seal_template_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.subheader("📋 Template Preview")
        st.dataframe(template_df, use_container_width=True)
        
        st.subheader("📝 How to Use Dropdowns in Excel")
        st.markdown("""
        **To add dropdown menus in Excel after downloading:**
        1. Select the cells you want to have dropdowns
        2. Go to **Data** → **Data Validation**
        3. Choose **List** from Allow dropdown
        4. Enter the options separated by commas:
           - **Auto_Proceed**: `Yes,No`
           - **Gas_Type**: `Air,N2,He`
           - **Test_Mode**: `Mode 1,Mode 2`
           - **Measurement**: `Yes,No`
           - **Torque_Check**: `Yes,No`
        """)
    
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
                
                # Show conversion summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Steps", len(machine_df))
                with col2:
                    st.metric("Auto Proceed Steps", 
                             len(machine_df[machine_df['TST_APFlag'] == 1]))
                with col3:
                    st.metric("Total Duration", f"{machine_df['TST_StepDuration'].sum()}s")
                
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
                st.info("Make sure you're using the provided template format.")
    
    elif operation == "📤 Machine CSV to Excel":
        st.header("Convert Machine CSV to Excel")
        
        uploaded_file = st.file_uploader("Upload machine CSV file", type=['csv'])
        
        if uploaded_file:
            try:
                # Convert to technician format
                technician_df = machine_csv_to_excel(uploaded_file)
                
                st.success(f"✅ Successfully converted {len(technician_df)} test steps!")
                
                # Preview
                st.subheader("Converted Data Preview")
                st.dataframe(technician_df, use_container_width=True)
                
                # Create Excel for download
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
                st.metric("Auto Proceed Steps", len(df[df['TST_APFlag'] == 1]))
            
            # Display in technician-friendly format
            st.subheader("Current Test Sequence")
            st.dataframe(technician_df, use_container_width=True, height=500)
            
        except Exception as e:
            st.error(f"❌ Could not load current test sequence: {str(e)}")
            st.info("Upload a file using the conversion tools above to get started.")

if __name__ == "__main__":
    main()
