import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math
import os

# =====================================================
# SAFETY LIMITS (THE RED HIGHLIGHT RULES)
# =====================================================
MAX_CELL_PRESSURE = 450.0
MAX_SPEED_RPM = 32000.0
DIFF_TARGET = 0.95 

def apply_safety_styles(row):
    """Adds red highlighting to safety violations without changing data."""
    styles = [''] * len(row)
    cols = row.index.tolist()
    
    # Speed Violation
    if 'Speed_RPM' in cols and row['Speed_RPM'] > MAX_SPEED_RPM:
        styles[cols.index('Speed_RPM')] = 'background-color: #9e1a1a; color: white;'
    
    # Cell Pressure Violation
    if 'Cell_Pressure_bar' in cols and row['Cell_Pressure_bar'] > MAX_CELL_PRESSURE:
        styles[cols.index('Cell_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
        
    # Differential Violation (Must be 95% of Cell)
    if 'Cell_Pressure_bar' in cols and 'Interface_Pressure_bar' in cols:
        expected = row['Cell_Pressure_bar'] * DIFF_TARGET
        if abs(row['Interface_Pressure_bar'] - expected) > 0.5:
            styles[cols.index('Interface_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
            
    return styles

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path_or_buffer):
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                df = pd.read_csv(
                    file_path_or_buffer,
                    delimiter=';',
                    encoding=enc,
                    na_values=['NaN','NAN','nan','INF','INFINITY','inf','infinity','',' ','NULL','null'],
                    keep_default_na=True,
                    skipinitialspace=True
                )
                return df.replace([np.nan, math.inf, -math.inf], 0)
            except Exception:
                continue
        return pd.read_csv(file_path_or_buffer, delimiter=';')
    except Exception as e:
        st.error(f"CSV read error: {e}")
        return pd.DataFrame()

# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):
    cols = df.columns.tolist()
    if 'TST_CellPresDemand' in cols or 'Cell_Pressure_bar' in cols:
        return 'main_seal'
    if 'TST_SepSealFlwSet1' in cols or 'Sep_Seal_Flow_Set1' in cols:
        return 'separation_seal'
    return 'unknown'

# =====================================================
# COLUMN MAPPINGS
# =====================================================

def get_column_mapping(file_type):
    if file_type == 'main_seal':
        return {
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
            }
        }
    if file_type == 'separation_seal':
        return {
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
            }
        }
    return None

# =====================================================
# CONVERSIONS
# =====================================================

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    tech_df = df.rename(columns=mapping['machine_to_technician'])
    if 'Step' not in tech_df.columns:
        tech_df.insert(0, 'Step', range(1, len(tech_df)+1))
    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''
    return tech_df

def convert_to_machine_codes(df):
    df = df.copy()
    for col in ['TST_APFlag','TST_MeasurementReq','TST_TorqueCheck']:
        if col in df.columns:
            df[col] = df[col].map({'Yes':1,'No':0, 1:1, 0:0}).fillna(0)
    if 'TST_TestMode' in df.columns:
        df['TST_TestMode'] = df['TST_TestMode'].map({'Mode 1':1,'Mode 2':2, 1:1, 2:2}).fillna(1)
    return df

# =====================================================
# EDITABLE DATAFRAME WITH HIGHLIGHTING
# =====================================================

def editable_dataframe(df, key, height=500):
    if key not in st.session_state:
        st.session_state[key] = df.copy()

    # VISUAL SAFETY PREVIEW
    st.write("### 🛡️ Safety Validation View")
    st.dataframe(st.session_state[key].style.apply(apply_safety_styles, axis=1), use_container_width=True)

    with st.form(f"form_{key}"):
        edited = st.data_editor(
            st.session_state[key],
            use_container_width=True,
            height=height,
            num_rows="fixed"
        )
        submitted = st.form_submit_button("✅ Apply changes & Validate")

    if submitted:
        st.session_state[key] = edited
        st.rerun()

    return st.session_state[key]

# =====================================================
# PROFESSIONAL EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(technician_df, file_type):
    output = io.BytesIO()
    logo_path = os.path.join(os.path.dirname(__file__), "company_logo.png")

    with pd.ExcelWriter(output, engine='xlsxwriter') as workbook:
        technician_df.to_excel(workbook, sheet_name='TEST_SEQUENCE', index=False)
        wb = workbook.book
        ws = workbook.sheets['TEST_SEQUENCE']

        header = wb.add_format({'bold': True, 'text_wrap': True, 'align': 'center', 'border': 1, 'fg_color': '#366092', 'font_color': 'white'})
        cell = wb.add_format({'border': 1, 'align': 'center'})
        
        for c, col in enumerate(technician_df.columns):
            ws.write(0, c, col, header)
        
        ws.set_column(0, len(technician_df.columns)-1, 18)
        
        instr = wb.add_worksheet('INSTRUCTIONS')
        if os.path.exists(logo_path):
            instr.insert_image('A1', logo_path, {'x_scale': 0.6, 'y_scale': 0.6})
            
        date = datetime.now().strftime('%Y-%m-%d')
        instr.write('B12', f"EXPORTED ON: {date}")
        instr.write('B14', "SAFETY CHECK: CELL < 450 BAR | SPEED < 32000 RPM")

    output.seek(0)
    return output

# =====================================================
# MAIN APP
# =====================================================

def main():
    st.set_page_config(layout="wide")
    st.title("⚙️ Universal Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        ["📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
    )

    if operation == "📥 Download Template":
        seal = st.selectbox("Seal Type", ["Main Seal", "Separation Seal"])
        file_type = "main_seal" if seal == "Main Seal" else "separation_seal"
        csv_file = "MainSealSet2.csv" if seal == "Main Seal" else "SeperationSeal.csv"
        if os.path.exists(csv_file):
            df = safe_read_csv(csv_file)
            tech_df = convert_machine_to_technician(df, file_type)
            excel = create_professional_excel_from_data(tech_df, file_type)
            st.download_button("📥 Download Template", excel.getvalue(), file_name=f"{file_type}_template.xlsx")

    elif operation == "🔄 Excel to Machine CSV":
        uploaded = st.file_uploader("Upload Excel", type=['xlsx'])
        if uploaded:
            df = pd.read_excel(uploaded, sheet_name='TEST_SEQUENCE')
            df = df.dropna(subset=['Step']).reset_index(drop=True)
            file_type = detect_file_type(df)
            
            # The Highlighted Editor
            edited = editable_dataframe(df, "excel_editor")
            mapping = get_column_mapping(file_type)

            # RECONSTRUCT MACHINE CSV - EXACT STRUCTURE
            machine_df = convert_to_machine_codes(
                edited.rename(columns=mapping['technician_to_machine'])
            ).drop(columns=['Step','Notes'], errors='ignore')

            # Fix Column Order for Simulation
            original_cols = list(mapping['machine_to_technician'].keys())
            machine_df = machine_df[original_cols]

            st.download_button(
                "📥 Download Machine CSV (Simulation Ready)",
                machine_df.to_csv(index=False, sep=';'),
                file_name=f"{file_type}_sequence.csv"
            )

    elif operation == "📤 Machine CSV to Excel":
        uploaded = st.file_uploader("Upload CSV", type=['csv'])
        if uploaded:
            df = safe_read_csv(uploaded)
            file_type = detect_file_type(df)
            tech_df = convert_machine_to_technician(df, file_type)
            edited = editable_dataframe(tech_df, "csv_editor")
            excel = create_professional_excel_from_data(edited, file_type)
            st.download_button("📥 Download Excel", excel.getvalue(), file_name=f"{file_type}_professional.xlsx")

    elif operation == "👀 View Current Test":
        seal = st.selectbox("Seal Type", ["Main Seal", "Separation Seal"])
        file_type = "main_seal" if seal == "Main Seal" else "separation_seal"
        csv_file = "MainSealSet2.csv" if seal == "Main Seal" else "SeperationSeal.csv"
        if os.path.exists(csv_file):
            df = safe_read_csv(csv_file)
            tech_df = convert_machine_to_technician(df, file_type)
            edited = editable_dataframe(tech_df, "current_editor")
            excel = create_professional_excel_from_data(edited, file_type)
            st.download_button("📥 Download Excel", excel.getvalue(), file_name=f"current_{file_type}_test.xlsx")

if __name__ == "__main__":
    main()
