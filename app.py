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

def create_professional_template():
    """Create a professionally formatted Excel template with borders and dropdowns"""
    
    # Create sample data
    sample_data = [
        [1, 0, 0.21, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Initial low pressure test'],
        [2, 0, 0.4, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Pressure increase'],
        [3, 0, 1.0, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Medium pressure check'],
        [4, 3600, 10.0, 0, 1.0, 1.0, 0, 10, 'Yes', 155, 'Air', 'Mode 1', 'Yes', 'No', 'High speed operation'],
        [5, 0, 0, 0, 0, 0, 0, 1, 'No', 155, 'Air', 'Mode 1', 'No', 'No', 'System cool down']
    ]
    
    headers = [
        'Step', 'Speed_RPM', 'Cell_Pressure_bar', 'Interface_Pressure_bar',
        'BP_Drive_End_bar', 'BP_Non_Drive_End_bar', 'Gas_Injection_bar',
        'Duration_s', 'Auto_Proceed', 'Temperature_C', 'Gas_Type', 
        'Test_Mode', 'Measurement', 'Torque_Check', 'Notes'
    ]
    
    # Create Excel file with xlsxwriter
    output = io.BytesIO()
    workbook = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Create DataFrame and write to Excel
    df = pd.DataFrame(sample_data, columns=headers)
    df.to_excel(workbook, sheet_name='TEST_SEQUENCE', index=False)
    
    # Get workbook and worksheet objects
    worksheet = workbook.sheets['TEST_SEQUENCE']
    
    # Get xlsxwriter workbook and worksheet objects
    xlsx_workbook = workbook.book
    xlsx_worksheet = workbook.sheets['TEST_SEQUENCE']
    
    # Define formats
    header_format = xlsx_workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#366092',
        'font_color': 'white',
        'border': 1,
        'align': 'center'
    })
    
    cell_format = xlsx_workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    number_format = xlsx_workbook.add_format({
        'border': 1,
        'align': 'center',
        'num_format': '0.00'
    })
    
    notes_format = xlsx_workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter'
    })
    
    # Apply header formatting
    for col_num, value in enumerate(headers):
        xlsx_worksheet.write(0, col_num, value, header_format)
    
    # Apply cell formatting to data
    for row_num in range(1, len(sample_data) + 1):
        for col_num in range(len(headers)):
            if headers[col_num] == 'Notes':
                xlsx_worksheet.write(row_num, col_num, sample_data[row_num-1][col_num], notes_format)
            elif headers[col_num] in ['Step', 'Duration_s', 'Temperature_C']:
                xlsx_worksheet.write(row_num, col_num, sample_data[row_num-1][col_num], cell_format)
            elif headers[col_num] in ['Speed_RPM', 'Cell_Pressure_bar', 'Interface_Pressure_bar', 
                                    'BP_Drive_End_bar', 'BP_Non_Drive_End_bar', 'Gas_Injection_bar']:
                xlsx_worksheet.write(row_num, col_num, sample_data[row_num-1][col_num], number_format)
            else:
                xlsx_worksheet.write(row_num, col_num, sample_data[row_num-1][col_num], cell_format)
    
    # Set column widths
    column_widths = [8, 12, 18, 20, 18, 22, 18, 12, 12, 15, 12, 12, 12, 12, 30]
    for col_num, width in enumerate(column_widths):
        xlsx_worksheet.set_column(col_num, col_num, width)
    
    # Add data validation for dropdowns
    # Auto_Proceed dropdown (Column I)
    xlsx_worksheet.data_validation('I2:I100', {
        'validate': 'list',
        'source': ['Yes', 'No'],
        'error_title': 'Invalid Input',
        'error_message': 'Please select either Yes or No'
    })
    
    # Gas_Type dropdown (Column K)
    xlsx_worksheet.data_validation('K2:K100', {
        'validate': 'list',
        'source': ['Air', 'N2', 'He'],
        'error_title': 'Invalid Input',
        'error_message': 'Please select Air, N2, or He'
    })
    
    # Test_Mode dropdown (Column L)
    xlsx_worksheet.data_validation('L2:L100', {
        'validate': 'list',
        'source': ['Mode 1', 'Mode 2'],
        'error_title': 'Invalid Input',
        'error_message': 'Please select Mode 1 or Mode 2'
    })
    
    # Measurement dropdown (Column M)
    xlsx_worksheet.data_validation('M2:M100', {
        'validate': 'list',
        'source': ['Yes', 'No'],
        'error_title': 'Invalid Input',
        'error_message': 'Please select either Yes or No'
    })
    
    # Torque_Check dropdown (Column N)
    xlsx_worksheet.data_validation('N2:N100', {
        'validate': 'list',
        'source': ['Yes', 'No'],
        'error_title': 'Invalid Input',
        'error_message': 'Please select either Yes or No'
    })
    
    # Create INSTRUCTIONS sheet
    instructions_worksheet = xlsx_workbook.add_worksheet('INSTRUCTIONS')
    
    instructions = [
        "MAIN SEAL TEST SEQUENCE TEMPLATE - INSTRUCTIONS",
        "",
        "HOW TO USE THIS TEMPLATE:",
        "1. Fill in the TEST_SEQUENCE sheet with your test parameters",
        "2. Use dropdown menus for fields with limited options (Auto Proceed, Gas Type, etc.)",
        "3. Required fields: Step, Speed, Cell Pressure, Duration, Temperature",
        "4. Save your completed file and upload back to the web app",
        "5. Download the generated CSV for your control system",
        "",
        "FIELD DESCRIPTIONS:",
        "Step: Sequential test step number (1, 2, 3...)",
        "Speed_RPM: Rotational speed (0 = stationary, 3600 = max speed)",
        "Cell_Pressure_bar: Main chamber pressure (0.1 - 100 bar)",
        "Interface_Pressure_bar: Interface pressure (0-40 bar)",
        "BP_Drive_End_bar: Back pressure drive end (0-7 bar)",
        "BP_Non_Drive_End_bar: Back pressure non-drive end (0-7 bar)",
        "Gas_Injection_bar: Gas injection pressure (0-5 bar)",
        "Duration_s: Step duration in seconds (1-300)",
        "Auto_Proceed: Automatic step progression (Yes/No)",
        "Temperature_C: Test temperature (30-155°C)",
        "Gas_Type: Test gas type (Air/N2/He)",
        "Test_Mode: Operating mode (Mode 1/Mode 2)",
        "Measurement: Take measurements (Yes/No)",
        "Torque_Check: Perform torque check (Yes/No)",
        "Notes: Additional comments or observations"
    ]
    
    # Write instructions with formatting
    title_format = xlsx_workbook.add_format({
        'bold': True,
        'font_size': 14,
        'font_color': '#366092',
        'valign': 'top'
    })
    
    header_format_instructions = xlsx_workbook.add_format({
        'bold': True,
        'font_color': '#366092',
        'valign': 'top'
    })
    
    for row_num, instruction in enumerate(instructions):
        if row_num == 0:
            instructions_worksheet.write(row_num, 0, instruction, title_format)
        elif "HOW TO USE" in instruction or "FIELD DESCRIPTIONS" in instruction:
            instructions_worksheet.write(row_num, 0, instruction, header_format_instructions)
        else:
            instructions_worksheet.write(row_num, 0, instruction)
    
    instructions_worksheet.set_column('A:A', 60)
    
    workbook.close()
    output.seek(0)
    
    return output

def excel_to_machine_csv(excel_file):
    """Convert technician Excel to machine-readable CSV"""
    
    # Read Excel file
    df = pd.read_excel(excel_file, sheet_name='TEST_SEQUENCE')
    
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
    """Convert machine CSV to formatted technician Excel"""
    
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
    st.markdown("### Professional Excel Template with Borders & Dropdowns")
    
    # Sidebar
    st.sidebar.title("🔧 Operations")
    operation = st.sidebar.radio(
        "Choose Operation:",
        ["📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
    )
    
    if operation == "📥 Download Template":
        st.header("Download Professional Excel Template")
        
        st.success("""
        **🎯 This template includes:**
        - 🎨 **Professional borders** and cell formatting
        - 📋 **Real dropdown menus** (no manual setup needed)
        - 🔵 **Colored headers** with white text
        - 📐 **Centered alignment** for numbers
        - 📝 **Instructions sheet** with guidance
        - 💡 **Data validation** to prevent errors
        """)
        
        # Create and download template
        excel_output = create_professional_template()
        
        st.download_button(
            label="📥 Download Professional Template (.xlsx)",
            data=excel_output.getvalue(),
            file_name=f"main_seal_template_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("📋 Template Features Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎨 Formatting Features:**
            - Blue headers with white text
            - Black borders around all cells
            - Centered text alignment
            - Number formatting for values
            - Optimized column widths
            """)
        
        with col2:
            st.markdown("""
            **📋 Dropdown Menus:**
            - Auto Proceed: Yes/No
            - Gas Type: Air/N2/He  
            - Test Mode: Mode 1/Mode 2
            - Measurement: Yes/No
            - Torque Check: Yes/No
            
            *Dropdowns work automatically in Excel!*
            """)
        
        st.markdown("""
        **📁 Template Structure:**
        - **INSTRUCTIONS sheet**: Detailed guide and field descriptions
        - **TEST_SEQUENCE sheet**: Formatted data entry with sample data
        - **Professional design**: Ready for technician use
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
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    technician_df.to_excel(writer, sheet_name='TEST_SEQUENCE', index=False)
                    
                    # Get workbook and add formatting
                    workbook = writer.book
                    worksheet = writer.sheets['TEST_SEQUENCE']
                    
                    # Add header formatting
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#366092',
                        'font_color': 'white',
                        'border': 1,
                        'align': 'center'
                    })
                    
                    cell_format = workbook.add_format({
                        'border': 1,
                        'align': 'center'
                    })
                    
                    # Apply formatting
                    for col_num, value in enumerate(technician_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Set column widths
                    column_widths = [8, 12, 18, 20, 18, 22, 18, 12, 12, 15, 12, 12, 12, 12, 30]
                    for col_num, width in enumerate(column_widths):
                        worksheet.set_column(col_num, col_num, width)
                
                output.seek(0)
                
                st.download_button(
                    label="📥 Download Formatted Excel",
                    data=output.getvalue(),
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
