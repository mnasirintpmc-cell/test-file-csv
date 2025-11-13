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

def analyze_csv_file(uploaded_file):
    """Analyze and display detailed information about the CSV file"""
    
    st.header("🔍 CSV File Analysis")
    
    # Show file info first
    st.subheader("📁 Uploaded File Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File Name", uploaded_file.name)
    with col2:
        st.metric("File Size", f"{len(uploaded_file.getvalue()) / 1024:.1f} KB")
    with col3:
        st.metric("File Type", "CSV")
    
    # Read the file with safe reader
    st.subheader("📊 Reading File Content...")
    df = safe_read_csv(uploaded_file)
    
    if df.empty:
        st.error("❌ Could not read the CSV file")
        return None, 'unknown'
    
    # Display file structure information
    st.subheader("📋 File Structure Analysis")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Rows", len(df))
    with col2:
        st.metric("Total Columns", len(df.columns))
    with col3:
        file_type = detect_file_type(df)
        seal_type = "Main Seal" if file_type == 'main_seal' else "Separation Seal" if file_type == 'separation_seal' else "Unknown"
        st.metric("Detected Type", seal_type)
    with col4:
        st.metric("Data Points", len(df) * len(df.columns))
    
    # Show raw data preview - THIS IS THE IMPORTANT PART
    st.subheader("📄 Imported File Content (Raw Data)")
    st.info("This is the exact content of your uploaded CSV file:")
    
    # Display the raw data
    st.dataframe(df, use_container_width=True, height=300)
    
    # Show data summary
    with st.expander("🔍 Detailed Data Summary", expanded=True):
        st.write("**First 5 rows:**")
        st.dataframe(df.head(), use_container_width=True)
        
        st.write("**Data Types:**")
        dtype_df = pd.DataFrame({
            'Column': df.columns,
            'Data Type': df.dtypes,
            'Non-Null Count': df.count(),
            'Null Count': df.isnull().sum()
        })
        st.dataframe(dtype_df, use_container_width=True)
    
    # Show column information in detail
    st.subheader("🗂️ Column Details")
    col_info = []
    for col in df.columns:
        col_info.append({
            'Column Name': col,
            'Data Type': str(df[col].dtype),
            'Non-Null Values': df[col].count(),
            'Null Values': df[col].isnull().sum(),
            'Unique Values': df[col].nunique(),
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
    
    # Only rename columns that exist in the DataFrame
    rename_dict = {}
    for machine_col, tech_col in machine_to_tech.items():
        if machine_col in tech_df.columns:
            rename_dict[machine_col] = tech_col
    
    tech_df = tech_df.rename(columns=rename_dict)
    
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
        ["🔍 Analyze & Convert CSV", "📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
    )
    
    # Template type selection
    template_type = st.sidebar.selectbox(
        "Select Seal Type:",
        ["Main Seal", "Separation Seal"]
    )
    
    file_type_map = {"Main Seal": "main_seal", "Separation Seal": "separation_seal"}
    selected_file_type = file_type_map[template_type]
    
    if operation == "🔍 Analyze & Convert CSV":
        st.header("Analyze & Convert CSV Files")
        st.info("""
        **This feature will:**
        - 🔍 **Analyze** your CSV file structure
        - 🛡️ **Handle NaN/INF** values automatically  
        - 🔄 **Detect file type** (Main Seal or Separation Seal)
        - 📊 **Show detailed information** about your data
        - 💾 **Convert to technician-friendly format**
        """)
        
        uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'], key="csv_analyzer")
        
        if uploaded_file is not None:
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
                        st.success("✅ Successfully converted to technician-friendly format!")
                        st.dataframe(tech_df, use_container_width=True, height=400)
                        
                        # Show conversion summary
                        st.subheader("📈 Conversion Summary")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Original Steps", len(df))
                        with col2:
                            st.metric("Converted Steps", len(tech_df))
                        with col3:
                            st.metric("Columns Added", len(tech_df.columns) - len(df.columns))
                        
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
                                mime="text/csv",
                                help="Download the converted data as CSV file"
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
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                help="Download the converted data as Excel file"
                            )
                
                else:
                    st.warning("⚠️ Could not automatically detect file type. Showing raw data.")
                    st.dataframe(df, use_container_width=True)
                    
                    # Still offer download options for unknown files
                    st.subheader("💾 Download Raw Data")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_data = df.to_csv(index=False, sep=';')
                        st.download_button(
                            label="📥 Download Raw CSV",
                            data=csv_data,
                            file_name=f"raw_data_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
    
    elif operation == "📥 Download Template":
        st.header(f"Download {template_type} Template")
        # ... (keep your existing template download code)
        
    elif operation == "🔄 Excel to Machine CSV":
        st.header("Convert Excel to Machine CSV")
        # ... (keep your existing Excel to CSV code)
        
    elif operation == "📤 Machine CSV to Excel":
        st.header("Convert Machine CSV to Excel")
        # ... (keep your existing CSV to Excel code)
        
    elif operation == "👀 View Current Test":
        st.header("Current Test Sequence")
        # ... (keep your existing view current test code)

if __name__ == "__main__":
    main()
