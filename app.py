import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np  # ADD THIS IMPORT

# Configure the page
st.set_page_config(
    page_title="Seal Test Manager",
    page_icon="⚙️",
    layout="wide"
)

def detect_file_type(df):
    """Detect whether it's a Main Seal or Separation Seal file"""
    columns = df.columns.tolist()
    
    if 'TST_CellPresDemand' in columns:
        return 'main_seal'
    elif 'TST_SepSealFlwSet1' in columns:
        return 'separation_seal'
    else:
        # Check for technician column names
        if 'Cell_Pressure_bar' in columns:
            return 'main_seal'
        elif 'Sep_Seal_Flow_Set1' in columns:
            return 'separation_seal'
        return 'unknown'

def get_column_mapping(file_type):
    """Get the appropriate column mapping based on file type"""
    
    if file_type == 'main_seal':
        return {
            'technician_to_machine': {
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
            },
            'machine_to_technician': {
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
            },
            'headers': [
                'Step', 'Speed_RPM', 'Cell_Pressure_bar', 'Interface_Pressure_bar',
                'BP_Drive_End_bar', 'BP_Non_Drive_End_bar', 'Gas_Injection_bar',
                'Duration_s', 'Auto_Proceed', 'Temperature_C', 'Gas_Type', 
                'Test_Mode', 'Measurement', 'Torque_Check', 'Notes'
            ],
            'sample_data': [
                [1, 0, 0.21, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Initial low pressure test'],
                [2, 0, 0.4, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Pressure increase'],
                [3, 0, 1.0, 0, 0, 0, 0, 2, 'No', 30, 'Air', 'Mode 1', 'Yes', 'No', 'Medium pressure check'],
                [4, 3600, 10.0, 0, 1.0, 1.0, 0, 10, 'Yes', 155, 'Air', 'Mode 1', 'Yes', 'No', 'High speed operation'],
                [5, 0, 0, 0, 0, 0, 0, 1, 'No', 155, 'Air', 'Mode 1', 'No', 'No', 'System cool down']
            ]
        }
    
    elif file_type == 'separation_seal':
        return {
            'technician_to_machine': {
                'Speed_RPM': 'TST_SpeedDem',
                'Sep_Seal_Flow_Set1': 'TST_SepSealFlwSet1',
                'Sep_Seal_Flow_Set2': 'TST_SepSealFlwSet2',
                'Sep_Seal_Pressure_Set1': 'TST_SepSealPSet1',
                'Sep_Seal_Pressure_Set2': 'TST_SepSealPSet2',
                'Sep_Seal_Control_Type': 'TST_SepSealControlTyp',
                'Duration_s': 'TST_StepDuration',
                'Auto_Proceed': 'TST_APFlag',
                'Temperature_C': 'TST_TempDemand',
                'Gas_Type': 'TST_GasType',
                'Measurement': 'TST_MeasurementReq',
                'Torque_Check': 'TST_TorqueCheck'
            },
            'machine_to_technician': {
                'TST_SpeedDem': 'Speed_RPM',
                'TST_SepSealFlwSet1': 'Sep_Seal_Flow_Set1',
                'TST_SepSealFlwSet2': 'Sep_Seal_Flow_Set2',
                'TST_SepSealPSet1': 'Sep_Seal_Pressure_Set1',
                'TST_SepSealPSet2': 'Sep_Seal_Pressure_Set2',
                'TST_SepSealControlTyp': 'Sep_Seal_Control_Type',
                'TST_StepDuration': 'Duration_s',
                'TST_APFlag': 'Auto_Proceed',
                'TST_TempDemand': 'Temperature_C',
                'TST_GasType': 'Gas_Type',
                'TST_MeasurementReq': 'Measurement',
                'TST_TorqueCheck': 'Torque_Check'
            },
            'headers': [
                'Step', 'Speed_RPM', 'Sep_Seal_Flow_Set1', 'Sep_Seal_Flow_Set2',
                'Sep_Seal_Pressure_Set1', 'Sep_Seal_Pressure_Set2', 'Sep_Seal_Control_Type',
                'Duration_s', 'Auto_Proceed', 'Temperature_C', 'Gas_Type', 
                'Measurement', 'Torque_Check', 'Notes'
            ],
            'sample_data': [
                [1, 0, 47.5, 0, 1.0, 0, 0, 2, 'No', 100, 'Air', 'Yes', 'No', 'Initial stationary test'],
                [2, 1275, 47.5, 0, 1.0, 0, 0, 5, 'Yes', 100, 'Air', 'Yes', 'No', 'Low speed operation'],
                [3, 2550, 47.5, 0, 1.0, 0, 0, 5, 'Yes', 100, 'Air', 'Yes', 'No', 'Medium speed'],
                [4, 5100, 47.5, 0, 1.0, 0, 0, 5, 'Yes', 100, 'Air', 'Yes', 'No', 'High speed'],
                [5, 16550, 47.5, 0, 1.0, 0, 0, 10, 'Yes', 100, 'Air', 'Yes', 'No', 'Max speed test']
            ]
        }
    
    else:
        return None

def create_professional_template(file_type='main_seal'):
    """Create a professionally formatted Excel template"""
    
    mapping = get_column_mapping(file_type)
    if not mapping:
        st.error("Unsupported file type")
        return None
    
    headers = mapping['headers']
    sample_data = mapping['sample_data']
    
    # Create Excel file with xlsxwriter
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as workbook:
        # Create DataFrame and write to Excel
        df = pd.DataFrame(sample_data, columns=headers)
        df.to_excel(workbook, sheet_name='TEST_SEQUENCE', index=False)
        
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
                elif any(num in headers[col_num] for num in ['Speed', 'Pressure', 'Flow']):
                    xlsx_worksheet.write(row_num, col_num, sample_data[row_num-1][col_num], number_format)
                else:
                    xlsx_worksheet.write(row_num, col_num, sample_data[row_num-1][col_num], cell_format)
        
        # Set column widths
        column_widths = [8, 12, 18, 18, 18, 18, 20, 12, 12, 15, 12, 12, 12, 30]
        for col_num, width in enumerate(column_widths[:len(headers)]):
            xlsx_worksheet.set_column(col_num, col_num, width)
        
        # Add data validation for dropdowns
        dropdown_columns = {
            'Auto_Proceed': ['Yes', 'No'],
            'Gas_Type': ['Air', 'N2', 'He'],
            'Measurement': ['Yes', 'No'],
            'Torque_Check': ['Yes', 'No']
        }
        
        if file_type == 'main_seal':
            dropdown_columns['Test_Mode'] = ['Mode 1', 'Mode 2']
        
        # Find column indices for dropdowns
        col_indices = {col: headers.index(col) for col in dropdown_columns.keys() if col in headers}
        
        for col_name, col_idx in col_indices.items():
            col_letter = chr(65 + col_idx)  # A, B, C, etc.
            xlsx_worksheet.data_validation(f'{col_letter}2:{col_letter}100', {
                'validate': 'list',
                'source': dropdown_columns[col_name],
                'error_title': 'Invalid Input',
                'error_message': f'Please select from: {", ".join(dropdown_columns[col_name])}'
            })
        
        # Create INSTRUCTIONS sheet
        instructions_worksheet = xlsx_workbook.add_worksheet('INSTRUCTIONS')
        
        seal_type = "Main Seal" if file_type == 'main_seal' else "Separation Seal"
        instructions = [
            f"{seal_type.upper()} TEST SEQUENCE TEMPLATE - INSTRUCTIONS",
            "",
            "HOW TO USE THIS TEMPLATE:",
            "1. Fill in the TEST_SEQUENCE sheet with your test parameters",
            "2. Use dropdown menus for fields with limited options",
            "3. Required fields: Step, Speed, Duration, Temperature",
            "4. Save your completed file and upload back to the web app",
            "5. Download the generated CSV for your control system",
            "",
            "FIELD DESCRIPTIONS:"
        ]
        
        # Add field descriptions based on file type
        field_descriptions = {
            'main_seal': [
                "Step: Sequential test step number (1, 2, 3...)",
                "Speed_RPM: Rotational speed (0-3600 RPM)",
                "Cell_Pressure_bar: Main chamber pressure (0.1-100 bar)",
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
            ],
            'separation_seal': [
                "Step: Sequential test step number (1, 2, 3...)",
                "Speed_RPM: Rotational speed (0-16550 RPM)",
                "Sep_Seal_Flow_Set1: Separation seal flow setting 1 (0-100)",
                "Sep_Seal_Flow_Set2: Separation seal flow setting 2 (0-100)",
                "Sep_Seal_Pressure_Set1: Separation seal pressure setting 1 (0-1 bar)",
                "Sep_Seal_Pressure_Set2: Separation seal pressure setting 2 (0-1 bar)",
                "Sep_Seal_Control_Type: Control type (0=Pressure, 1=Flow)",
                "Duration_s: Step duration in seconds (1-300)",
                "Auto_Proceed: Automatic step progression (Yes/No)",
                "Temperature_C: Test temperature (100°C)",
                "Gas_Type: Test gas type (Air/N2/He)",
                "Measurement: Take measurements (Yes/No)",
                "Torque_Check: Perform torque check (Yes/No)",
                "Notes: Additional comments or observations"
            ]
        }
        
        instructions.extend(field_descriptions[file_type])
        
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
    
    output.seek(0)
    return output

def create_professional_excel_from_data(technician_df, file_type):
    """Create a professionally formatted Excel file from existing test data"""
    
    mapping = get_column_mapping(file_type)
    if not mapping:
        return None
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as workbook:
        # Write main data sheet
        technician_df.to_excel(workbook, sheet_name='TEST_SEQUENCE', index=False)
        
        # Get xlsxwriter objects
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
        for col_num, value in enumerate(technician_df.columns.values):
            xlsx_worksheet.write(0, col_num, value, header_format)
        
        # Apply cell formatting to all data rows
        for row_num in range(1, len(technician_df) + 1):
            for col_num, col_name in enumerate(technician_df.columns):
                value = technician_df.iloc[row_num-1, col_num]
                
                if col_name == 'Notes':
                    xlsx_worksheet.write(row_num, col_num, value, notes_format)
                elif col_name in ['Step', 'Duration_s', 'Temperature_C']:
                    xlsx_worksheet.write(row_num, col_num, value, cell_format)
                elif any(num_term in col_name for num_term in ['Speed', 'Pressure', 'Flow']):
                    try:
                        float_value = float(value)
                        xlsx_worksheet.write(row_num, col_num, float_value, number_format)
                    except (ValueError, TypeError):
                        xlsx_worksheet.write(row_num, col_num, value, cell_format)
                else:
                    xlsx_worksheet.write(row_num, col_num, value, cell_format)
        
        # Set column widths
        column_widths = [8, 12, 18, 18, 18, 18, 20, 12, 12, 15, 12, 12, 12, 30]
        for col_num, width in enumerate(column_widths[:len(technician_df.columns)]):
            xlsx_worksheet.set_column(col_num, col_num, width)
        
        # Add data validation for dropdowns
        dropdown_columns = {
            'Auto_Proceed': ['Yes', 'No'],
            'Gas_Type': ['Air', 'N2', 'He'],
            'Measurement': ['Yes', 'No'],
            'Torque_Check': ['Yes', 'No']
        }
        
        if file_type == 'main_seal':
            dropdown_columns['Test_Mode'] = ['Mode 1', 'Mode 2']
        
        # Find column indices for dropdowns
        col_indices = {col: list(technician_df.columns).index(col) for col in dropdown_columns.keys() if col in technician_df.columns}
        
        for col_name, col_idx in col_indices.items():
            col_letter = chr(65 + col_idx)  # A, B, C, etc.
            xlsx_worksheet.data_validation(f'{col_letter}2:{col_letter}{len(technician_df)+1}', {
                'validate': 'list',
                'source': dropdown_columns[col_name],
                'error_title': 'Invalid Input',
                'error_message': f'Please select from: {", ".join(dropdown_columns[col_name])}'
            })
        
        # Create INSTRUCTIONS sheet
        instructions_worksheet = xlsx_workbook.add_worksheet('INSTRUCTIONS')
        
        seal_type = "Main Seal" if file_type == 'main_seal' else "Separation Seal"
        instructions = [
            f"{seal_type.upper()} TEST SEQUENCE - EXPORTED {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "HOW TO USE THIS FILE:",
            "1. This file contains your current test sequence in professional format",
            "2. All cells have proper borders and formatting",
            "3. Dropdown menus are included for standardized inputs",
            "4. You can edit this file and upload it back to the web app",
            "5. Use the conversion tool to generate machine CSV files",
            "",
            "FIELD DESCRIPTIONS:"
        ]
        
        # Add field descriptions based on file type
        field_descriptions = {
            'main_seal': [
                "Step: Sequential test step number (1, 2, 3...)",
                "Speed_RPM: Rotational speed (0-3600 RPM)",
                "Cell_Pressure_bar: Main chamber pressure (0.1-100 bar)",
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
            ],
            'separation_seal': [
                "Step: Sequential test step number (1, 2, 3...)",
                "Speed_RPM: Rotational speed (0-16550 RPM)",
                "Sep_Seal_Flow_Set1: Separation seal flow setting 1 (0-100)",
                "Sep_Seal_Flow_Set2: Separation seal flow setting 2 (0-100)",
                "Sep_Seal_Pressure_Set1: Separation seal pressure setting 1 (0-1 bar)",
                "Sep_Seal_Pressure_Set2: Separation seal pressure setting 2 (0-1 bar)",
                "Sep_Seal_Control_Type: Control type (0=Pressure, 1=Flow)",
                "Duration_s: Step duration in seconds (1-300)",
                "Auto_Proceed: Automatic step progression (Yes/No)",
                "Temperature_C: Test temperature (100°C)",
                "Gas_Type: Test gas type (Air/N2/He)",
                "Measurement: Take measurements (Yes/No)",
                "Torque_Check: Perform torque check (Yes/No)",
                "Notes: Additional comments or observations"
            ]
        }
        
        instructions.extend(field_descriptions[file_type])
        
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
    
    output.seek(0)
    return output

def excel_to_machine_csv(excel_file):
    """Convert technician Excel to machine-readable CSV"""
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, sheet_name='TEST_SEQUENCE')
        
        # Remove empty rows
        df = df.dropna(subset=['Step']).reset_index(drop=True)
        
        # Detect file type based on columns present
        file_type = detect_file_type(df)
        mapping = get_column_mapping(file_type)
        
        if not mapping:
            st.error("Unsupported file format. Please use the provided templates.")
            return None
        
        # DEBUG: Show what columns we have
        st.info(f"📊 Found columns: {list(df.columns)}")
        
        # Rename columns - only rename the ones that exist
        existing_columns = df.columns.tolist()
        rename_dict = {}
        
        for tech_col, machine_col in mapping['technician_to_machine'].items():
            if tech_col in existing_columns:
                rename_dict[tech_col] = machine_col
        
        df = df.rename(columns=rename_dict)
        
        # Convert readable values back to machine codes
        df = convert_to_machine_codes(df, file_type)
        
        # Remove Step and Notes columns for machine CSV (if they exist)
        columns_to_drop = ['Step', 'Notes']
        machine_df = df.drop([col for col in columns_to_drop if col in df.columns], axis=1)
        
        # DEBUG: Show final columns
        st.info(f"🔧 Final machine columns: {list(machine_df.columns)}")
        
        return machine_df, file_type
        
    except Exception as e:
        st.error(f"❌ Error reading Excel file: {str(e)}")
        return None

def convert_to_machine_codes(df, file_type):
    """Convert readable values to machine codes"""
    
    # Common conversions
    if 'TST_APFlag' in df.columns:
        df['TST_APFlag'] = df['TST_APFlag'].map({'Yes': 1, 'No': 0, 'YES': 1, 'NO': 0})
        # Fill any NaN values with 0
        df['TST_APFlag'] = df['TST_APFlag'].fillna(0)
    
    if 'TST_MeasurementReq' in df.columns:
        df['TST_MeasurementReq'] = df['TST_MeasurementReq'].map({'Yes': 1, 'No': 0, 'YES': 1, 'NO': 0})
        df['TST_MeasurementReq'] = df['TST_MeasurementReq'].fillna(0)
    
    if 'TST_TorqueCheck' in df.columns:
        df['TST_TorqueCheck'] = df['TST_TorqueCheck'].map({'Yes': 1, 'No': 0, 'YES': 1, 'NO': 0})
        df['TST_TorqueCheck'] = df['TST_TorqueCheck'].fillna(0)
    
    # Type-specific conversions
    if file_type == 'main_seal' and 'TST_TestMode' in df.columns:
        df['TST_TestMode'] = df['TST_TestMode'].map({'Mode 1': 1, 'Mode 2': 2, 'MODE 1': 1, 'MODE 2': 2})
        df['TST_TestMode'] = df['TST_TestMode'].fillna(1)
    
    return df

def machine_csv_to_excel(csv_file):
    """Convert machine CSV to formatted technician Excel"""
    
    # Read machine CSV
    df = pd.read_csv(csv_file, delimiter=';')
    
    # ⬇️⬇️ ADD THE FIX RIGHT HERE - Clean NaN/INF values ⬇️⬇️
    df = df.fillna(0)  # Replace NaN with 0
    df = df.replace([np.inf, -np.inf], 0)  # Replace INF with 0
    # ⬆️⬆️ ADD THE FIX RIGHT HERE ⬆️⬆️
    
    # Detect file type
    file_type = detect_file_type(df)
    mapping = get_column_mapping(file_type)
    
    if not mapping:
        st.error("Unsupported CSV format")
        return None
    
    # Convert to technician format
    machine_to_tech = mapping['machine_to_technician']
    df = df.rename(columns=machine_to_tech)
    
    # Convert machine codes to readable values
    df = convert_to_readable_values(df, file_type)
    
    # Add Step numbers and Notes column
    df.insert(0, 'Step', range(1, len(df) + 1))
    df['Notes'] = ''
    
    return df, file_type

def convert_to_readable_values(df, file_type):
    """Convert machine codes to readable values"""
    
    # Common conversions
    if 'Auto_Proceed' in df.columns:
        df['Auto_Proceed'] = df['Auto_Proceed'].map({0: 'No', 1: 'Yes'})
    if 'Measurement' in df.columns:
        df['Measurement'] = df['Measurement'].map({0: 'No', 1: 'Yes'})
    if 'Torque_Check' in df.columns:
        df['Torque_Check'] = df['Torque_Check'].map({0: 'No'})
    
    # Type-specific conversions
    if file_type == 'main_seal' and 'Test_Mode' in df.columns:
        df['Test_Mode'] = df['Test_Mode'].map({1: 'Mode 1', 2: 'Mode 2'})
    
    return df

def main():
    st.title("⚙️ Universal Seal Test Manager")
    st.markdown("### Supports Main Seal & Separation Seal Tests")
    
    # Sidebar
    st.sidebar.title("🔧 Operations")
    operation = st.sidebar.radio(
        "Choose Operation:",
        ["📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
    )
    
    # Template type selection
    template_type = st.sidebar.selectbox(
        "Select Seal Type:",
        ["Main Seal", "Separation Seal"]
    )
    
    file_type_map = {"Main Seal": "main_seal", "Separation Seal": "separation_seal"}
    selected_file_type = file_type_map[template_type]
    
    if operation == "📥 Download Template":
        st.header(f"Download {template_type} Template")
        
        st.success(f"""
        **🎯 This {template_type} template includes:**
        - 🎨 **Professional borders** and cell formatting
        - 📋 **Real dropdown menus** (no manual setup needed)
        - 🔵 **Colored headers** with white text
        - 📐 **Centered alignment** for numbers
        - 📝 **Instructions sheet** with guidance
        - 💡 **Data validation** to prevent errors
        """)
        
        # Create and download template
        excel_output = create_professional_template(selected_file_type)
        
        if excel_output:
            st.download_button(
                label=f"📥 Download {template_type} Template (.xlsx)",
                data=excel_output.getvalue(),
                file_name=f"{template_type.lower().replace(' ', '_')}_template_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Show template preview
        mapping = get_column_mapping(selected_file_type)
        if mapping:
            st.subheader("📋 Template Preview")
            preview_df = pd.DataFrame(mapping['sample_data'], columns=mapping['headers'])
            st.dataframe(preview_df, use_container_width=True)
    
    elif operation == "🔄 Excel to Machine CSV":
        st.header("Convert Excel to Machine CSV")
        
        uploaded_file = st.file_uploader("Upload your completed Excel template", type=['xlsx'])
        
        if uploaded_file:
            try:
                # Convert to machine format
                result = excel_to_machine_csv(uploaded_file)
                if result:
                    machine_df, detected_type = result
                    
                    seal_type = "Main Seal" if detected_type == 'main_seal' else "Separation Seal"
                    st.success(f"✅ Successfully converted {len(machine_df)} {seal_type} test steps!")
                    
                    # Preview
                    st.subheader("Machine CSV Preview")
                    st.dataframe(machine_df, use_container_width=True)
                    
                    # Show conversion summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Steps", len(machine_df))
                    with col2:
                        if 'TST_APFlag' in machine_df.columns:
                            auto_steps = len(machine_df[machine_df['TST_APFlag'] == 1])
                            st.metric("Auto Proceed Steps", auto_steps)
                    with col3:
                        if 'TST_StepDuration' in machine_df.columns:
                            total_duration = machine_df['TST_StepDuration'].sum()
                            st.metric("Total Duration", f"{total_duration}s")
                    
                    # Download machine CSV
                    csv_data = machine_df.to_csv(index=False, sep=';')
                    st.download_button(
                        label="📥 Download Machine CSV",
                        data=csv_data,
                        file_name=f"{detected_type}_sequence_{datetime.now().strftime('%Y%m%d')}.csv",
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
                result = machine_csv_to_excel(uploaded_file)
                if result:
                    technician_df, detected_type = result
                    
                    seal_type = "Main Seal" if detected_type == 'main_seal' else "Separation Seal"
                    st.success(f"✅ Successfully converted {len(technician_df)} {seal_type} test steps!")
                    
                    # Preview
                    st.subheader("Converted Data Preview")
                    st.dataframe(technician_df, use_container_width=True)
                    
                    # Create professional Excel for download
                    excel_output = create_professional_excel_from_data(technician_df, detected_type)
                    
                    if excel_output:
                        st.download_button(
                            label="📥 Download Professional Excel",
                            data=excel_output.getvalue(),
                            file_name=f"{detected_type}_professional_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                
            except Exception as e:
                st.error(f"❌ Error converting file: {str(e)}")
    
    elif operation == "👀 View Current Test":
        st.header("Current Test Sequence")
        
        # File selection
        current_file = st.selectbox(
            "Select file to view:",
            ["MainSealSet2.csv", "SeperationSeal.csv", "SeperationSeal_Base.csv"]
        )
        
        try:
            df = pd.read_csv(current_file, delimiter=';')
            
            # ⬇️⬇️ ADD THE FIX HERE TOO - Clean NaN/INF values ⬇️⬇️
            df = df.fillna(0)  # Replace NaN with 0
            df = df.replace([np.inf, -np.inf], 0)  # Replace INF with 0
            # ⬆️⬆️ ADD THE FIX HERE TOO ⬆️
