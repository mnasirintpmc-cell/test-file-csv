import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

# =====================================================
# SESSION HELPERS
# =====================================================

def reset_editor(key, df):
    if key not in st.session_state or st.session_state[key].shape != df.shape:
        st.session_state[key] = df.copy()

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
            }
        }
    return None

# =====================================================
# VALUE CONVERSIONS
# =====================================================

def convert_to_machine_codes(df, file_type):
    df = df.copy()
    for col in ['TST_APFlag','TST_MeasurementReq','TST_TorqueCheck']:
        if col in df.columns:
            df[col] = df[col].map({'Yes':1,'No':0}).fillna(0)
    if 'TST_TestMode' in df.columns:
        df['TST_TestMode'] = df['TST_TestMode'].map({'Mode 1':1,'Mode 2':2}).fillna(1)
    return df

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    tech_df = df.rename(columns=mapping['machine_to_technician'])
    tech_df.insert(0, 'Step', range(1, len(tech_df)+1))
    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''
    return tech_df

# =====================================================
# EDITABLE DATAFRAME
# =====================================================

def editable_dataframe(df, key, height=500):
    reset_editor(key, df)
    edited = st.data_editor(
        st.session_state[key],
        key=f'editor_{key}',
        use_container_width=True,
        height=height,
        num_rows='dynamic'
    )
    st.session_state[key] = edited
    return edited

# =====================================================
# PROFESSIONAL EXCEL EXPORT (TEMPLATE + INSTRUCTIONS)
# =====================================================

def create_professional_excel_from_data(technician_df, file_type):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as workbook:
        technician_df.to_excel(workbook, sheet_name='TEST_SEQUENCE', index=False)

        wb = workbook.book
        ws = workbook.sheets['TEST_SEQUENCE']

        header = wb.add_format({
            'bold': True,
            'text_wrap': True,
            'align': 'center',
            'border': 1,
            'fg_color': '#366092',
            'font_color': 'white'
        })
        cell = wb.add_format({'border': 1, 'align': 'center'})
        notes = wb.add_format({'border': 1, 'align': 'left'})

        for c, col in enumerate(technician_df.columns):
            ws.write(0, c, col, header)

        for r in range(1, len(technician_df)+1):
            for c, col in enumerate(technician_df.columns):
                fmt = notes if col == 'Notes' else cell
                ws.write(r, c, technician_df.iloc[r-1, c], fmt)

        ws.set_column(0, len(technician_df.columns)-1, 18)

        # ================= INSTRUCTIONS =================
        instr = wb.add_worksheet('INSTRUCTIONS')
        export_date = datetime.now().strftime('%Y-%m-%d')

        instructions = [
            f"MAIN SEAL TEST SEQUENCE - EXPORTED {export_date}",
            "",
            "HOW TO USE THIS FILE:",
            "1. This file contains your current test sequence",
            "2. All cells have proper borders and formatting",
            "3. Dropdown menus are included for standardized inputs",
            "4. You can edit this file and upload it back to the web app",
            "5. Use the conversion tool to generate machine CSV files",
            "",
            "FIELD DESCRIPTIONS:",
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
        ]

        title_fmt = wb.add_format({'bold': True, 'font_size': 14, 'font_color': '#366092'})
        header_fmt = wb.add_format({'bold': True, 'font_color': '#366092'})

        for r, text in enumerate(instructions):
            if r == 0:
                instr.write(r, 0, text, title_fmt)
            elif text in ["HOW TO USE THIS FILE:", "FIELD DESCRIPTIONS:"]:
                instr.write(r, 0, text, header_fmt)
            else:
                instr.write(r, 0, text)

        instr.set_column('A:A', 75)

    output.seek(0)
    return output

# =====================================================
# MAIN APP
# =====================================================

def main():
    st.title("⚙️ Universal Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        ["🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"]
    )

    if operation == "🔄 Excel to Machine CSV":
        uploaded = st.file_uploader("Upload Excel Template", type=['xlsx'])
        if uploaded:
            df = pd.read_excel(uploaded, sheet_name='TEST_SEQUENCE')
            df = df.dropna(subset=['Step']).reset_index(drop=True)
            file_type = detect_file_type(df)

            edited = editable_dataframe(df, "excel_editor")

            mapping = get_column_mapping(file_type)
            rename = {k:v for k,v in mapping['technician_to_machine'].items() if k in edited.columns}
            machine_df = edited.rename(columns=rename)
            machine_df = convert_to_machine_codes(machine_df, file_type)
            machine_df = machine_df.drop(columns=[c for c in ['Step','Notes'] if c in machine_df.columns])

            st.download_button(
                "📥 Download Machine CSV",
                machine_df.to_csv(index=False, sep=';'),
                file_name=f"{file_type}_sequence.csv",
                mime="text/csv"
            )

    elif operation == "📤 Machine CSV to Excel":
        uploaded = st.file_uploader("Upload Machine CSV", type=['csv'])
        if uploaded:
            df = safe_read_csv(uploaded)
            file_type = detect_file_type(df)

            tech_df = convert_machine_to_technician(df, file_type)
            edited = editable_dataframe(tech_df, "csv_editor")

            excel = create_professional_excel_from_data(edited, file_type)
            st.download_button(
                "📥 Download Excel",
                excel.getvalue(),
                file_name=f"{file_type}_professional.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    elif operation == "👀 View Current Test":
        file_name = st.selectbox(
            "Select test CSV",
            ["MainSealSet2.csv","SeperationSeal.csv","SeperationSeal_Base.csv"]
        )

        if "current_name" not in st.session_state or st.session_state["current_name"] != file_name:
            st.session_state["current_df"] = safe_read_csv(file_name)
            st.session_state["current_name"] = file_name

        df = st.session_state["current_df"]
        file_type = detect_file_type(df)
        tech_df = convert_machine_to_technician(df, file_type)
        edited = editable_dataframe(tech_df, "current_editor")

        col1, col2 = st.columns(2)

        with col1:
            excel = create_professional_excel_from_data(edited, file_type)
            st.download_button(
                "📥 Download Excel (Template)",
                excel.getvalue(),
                file_name=f"current_{file_type}_test.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col2:
            mapping = get_column_mapping(file_type)
            rename = {k:v for k,v in mapping['technician_to_machine'].items() if k in edited.columns}
            machine_df = edited.rename(columns=rename)
            machine_df = convert_to_machine_codes(machine_df, file_type)
            machine_df = machine_df.drop(columns=[c for c in ['Step','Notes'] if c in machine_df.columns])

            st.download_button(
                "📥 Download Machine CSV",
                machine_df.to_csv(index=False, sep=';'),
                file_name=f"current_{file_type}_test.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
