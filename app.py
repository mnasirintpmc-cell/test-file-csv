import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

def safe_read_csv(file_path_or_buffer):
    """Safely read CSV files with NaN/INF value handling and proper encoding"""
    try:
        # Try reading with different encodings and delimiters
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                # Read with semicolon delimiter and handle NaN/INF
                df = pd.read_csv(
                    file_path_or_buffer, 
                    delimiter=';',
                    encoding=encoding,
                    na_values=['NaN', 'NAN', 'nan', 'INF', 'INFINITY', 'inf', 'infinity', '', ' ', 'NULL', 'null'],
                    keep_default_na=True,
                    skipinitialspace=True
                )
                
                # Replace any remaining NaN/INF values with 0
                df = df.replace([np.nan, math.inf, -math.inf], 0)
                
                # Convert all numeric columns to appropriate types
                for col in df.columns:
                    if df[col].dtype == 'object':
                        try:
                            df[col] = pd.to_numeric(df[col], errors='ignore')
                        except:
                            pass
                
                st.success(f"✅ File read successfully with {encoding} encoding")
                return df
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        
        # If all encodings fail, try with default settings
        st.warning("⚠️ Using fallback CSV reader")
        df = pd.read_csv(file_path_or_buffer, delimiter=';')
        df = df.replace([np.nan, math.inf, -math.inf], 0)
        return df
        
    except Exception as e:
        st.error(f"❌ Error reading CSV file: {str(e)}")
        return pd.DataFrame()

def detect_file_type(df):
    """Detect whether it's a Main Seal or Separation Seal file"""
    if df.empty:
        return 'unknown'
    
    columns = df.columns.tolist()
    
    # Check for machine column names
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

def analyze_csv_file(uploaded_file):
    """Analyze and display detailed information about the CSV file"""
    
    st.header("🔍 CSV File Analysis")
    
    # Read the file with safe reader
    df = safe_read_csv(uploaded_file)
    
    if df.empty:
        st.error("❌ Could not read the CSV file")
        return None, 'unknown'
    
    # Display file information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", len(df))
    with col2:
        st.metric("Total Columns", len(df.columns))
    with col3:
        file_type = detect_file_type(df)
        seal_type = "Main Seal" if file_type == 'main_seal' else "Separation Seal" if file_type == 'separation_seal' else "Unknown"
        st.metric("File Type", seal_type)
    
    # Show raw data preview
    st.subheader("📊 Raw Data Preview")
    st.dataframe(df, use_container_width=True)
    
    # Show column information
    st.subheader("📋 Column Details")
    col_info = []
    for col in df.columns:
        col_info.append({
            'Column Name': col,
            'Data Type': str(df[col].dtype),
            'Non-Null Values': df[col].count(),
            'Null Values': df[col].isnull().sum(),
            'Sample Values': str(df[col].head(3).tolist())
        })
    
    col_df = pd.DataFrame(col_info)
    st.dataframe(col_df, use_container_width=True)
    
    return df, file_type

def convert_machine_to_technician(df, file_type):
    """Convert machine CSV to technician-friendly format"""
    
    mapping = get_column_mapping(file_type)
    if not mapping:
        st.error("❌ Unsupported file format")
        return None
    
    # Create a copy to avoid modifying original
    tech_df = df.copy()
    
    # Rename columns
    machine_to_tech = mapping['machine_to_technician']
    tech_df = tech_df.rename(columns=machine_to_tech)
    
    # Convert machine codes to readable values
    tech_df = convert_to_readable_values(tech_df, file_type)
    
    # Add Step numbers and Notes column
    tech_df.insert(0, 'Step', range(1, len(tech_df) + 1))
    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''
    
    return tech_df

def convert_to_readable_values(df, file_type):
    """Convert machine codes to readable values"""
    
    df = df.copy()
    
    # Common conversions
    if 'Auto_Proceed' in df.columns:
        df['Auto_Proceed'] = df['Auto_Proceed'].map({0: 'No', 1: 'Yes', '0': 'No', '1': 'Yes'})
        df['Auto_Proceed'] = df['Auto_Proceed'].fillna('No')
    
    if 'Measurement' in df.columns:
        df['Measurement'] = df['Measurement'].map({0: 'No', 1: 'Yes', '0': 'No', '1': 'Yes'})
        df['Measurement'] = df['Measurement'].fillna('No')
    
    if 'Torque_Check' in df.columns:
        df['Torque_Check'] = df['Torque_Check'].map({0: 'No', 1: 'Yes', '0': 'No', '1': 'Yes'})
        df['Torque_Check'] = df['Torque_Check'].fillna('No')
    
    # Type-specific conversions
    if file_type == 'main_seal' and 'Test_Mode' in df.columns:
        df['Test_Mode'] = df['Test_Mode'].map({1: 'Mode 1', 2: 'Mode 2', '1': 'Mode 1', '2': 'Mode 2'})
        df['Test_Mode'] = df['Test_Mode'].fillna('Mode 1')
    
    # Handle Gas_Type conversions
    if 'Gas_Type' in df.columns:
        df['Gas_Type'] = df['Gas_Type'].replace({'Air': 'Air', 'N2': 'N2', 'He': 'He'})
    
    return df

def main():
    st.title("⚙️ Universal Seal Test Manager")
    st.markdown("### Enhanced with NaN/INF Handling & File Analysis")
    
    # Sidebar
    st.sidebar.title("🔧 Operations")
    operation = st.sidebar.radio(
        "Choose Operation:",
        ["📥 Download Template", "🔍 Analyze & Convert CSV", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
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
    
    elif operation == "🔍 Analyze & Convert CSV":
        st.header("Analyze & Convert CSV Files")
        st.info("""
        **This feature will:**
        - 🔍 **Analyze** your CSV file structure
        - 🛡️ **Handle NaN/INF** values automatically  
        - 🔄 **Detect file type** (Main Seal or Separation Seal)
        - 📊 **Show detailed information** about your data
        - 💾 **Convert to technician-friendly format**
        """)
        
        uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])
        
        if uploaded_file:
            # Analyze the file
            df, file_type = analyze_csv_file(uploaded_file)
            
            if df is not None and not df.empty:
                seal_type = "Main Seal" if file_type == 'main_seal' else "Separation Seal" if file_type == 'separation_seal' else "Unknown"
                
                if file_type != 'unknown':
                    st.success(f"✅ Detected: {seal_type} file with {len(df)} steps")
                    
                    # Convert to technician format
                    st.subheader("🔄 Converted Technician Format")
                    tech_df = convert_machine_to_technician(df, file_type)
                    
                    if tech_df is not None:
                        st.dataframe(tech_df, use_container_width=True)
                        
                        # Download options
                        st.subheader("💾 Download Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Download as CSV
                            csv_data = tech_df.to_csv(index=False, sep=';')
                            st.download_button(
                                label="📥 Download as CSV",
                                data=csv_data,
                                file_name=f"converted_{file_type}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        
                        with col2:
                            # Download as Excel
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                tech_df.to_excel(writer, index=False, sheet_name='TEST_SEQUENCE')
                            output.seek(0)
                            
                            st.download_button(
                                label="📥 Download as Excel",
                                data=output.getvalue(),
                                file_name=f"converted_{file_type}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                
                else:
                    st.warning("⚠️ Could not automatically detect file type. Showing raw data.")
                    st.dataframe(df, use_container_width=True)
    
    elif operation == "🔄 Excel to Machine CSV":
        st.header("Convert Excel to Machine CSV")
        # ... (keep your existing Excel to CSV code here)
        
    elif operation == "📤 Machine CSV to Excel":
        st.header("Convert Machine CSV to Excel")
        # ... (keep your existing CSV to Excel code here)
        
    elif operation == "👀 View Current Test":
        st.header("Current Test Sequence")
        # ... (keep your existing view current test code here)

if __name__ == "__main__":
    main()
