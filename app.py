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
# COLUMN MAPPINGS (FIXED)
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

    if file_type == 'separation_seal':
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
    if mapping is None:
        st.error("Unsupported seal type")
        return pd.DataFrame()

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
# PROFESSIONAL EXCEL EXPORT (UNCHANGED)
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

        instr = wb.add_worksheet('INSTRUCTIONS')
        export_date = datetime.now().strftime('%Y-%m-%d')

        instructions = [
            f"{'MAIN SEAL' if file_type=='main_seal' else 'SEPARATION SEAL'} TEST SEQUENCE - EXPORTED {export_date}",
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
            "Speed_RPM: Rotational speed",
            "Cell_Pressure_bar: Main chamber pressure",
            "Interface_Pressure_bar: Interface pressure",
            "BP_Drive_End_bar: Back pressure drive end",
            "BP_Non_Drive_End_bar: Back pressure non-drive end",
            "Gas_Injection_bar: Gas injection pressure",
            "Duration_s: Step duration in seconds",
            "Auto_Proceed: Automatic step progression",
            "Temperature_C: Test temperature",
            "Gas_Type: Test gas type",
            "Test_Mode: Operating mode",
            "Measurement: Take measurements",
            "Torque_Check: Perform torque check",
            "Notes: Additional comments"
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
        [
            "📥 Download Template",
            "🔄 Excel to Machine CSV",
            "📤 Machine CSV to Excel",
            "👀 View Current Test"
        ]
    )

    # -------- DOWNLOAD TEMPLATE --------
    if operation == "📥 Download Template":
        seal = st.selectbox("Select Seal Type", ["Main Seal", "Separation Seal"])

        if seal == "Main Seal":
            df = safe_read_csv("MainSealSet2.csv")
            file_type = "main_seal"
        else:
            df = safe_read_csv("SeperationSeal.csv")
            file_type = "separation_seal"

        st.info(f"📄 Template Seal Type: **{seal.upper()}**")

        tech_df = convert_machine_to_technician(df, file_type)
        excel = create_professional_excel_from_data(tech_df, file_type)

        st.download_button(
            f"📥 Download {seal} Excel Template",
            excel.getvalue(),
            file_name=f"{file_type}_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # -------- EXCEL → CSV --------
    elif operation == "🔄 Excel to Machine CSV":
        uploaded = st.file_uploader("Upload Excel Template", type=['xlsx'])
        if uploaded:
            df = pd.read_excel(uploaded, sheet_name='TEST_SEQUENCE')
            df = df.dropna(subset=['Step']).reset_index(drop=True)
            file_type = detect_file_type(df)

            edited = editable_dataframe(df, "excel_editor")
            mapping = get_column_mapping(file_type)
            rename = {k:v for k,v in mapping['technician_to_machine'].items() if k in edited.columns}

            machine_df = convert_to_machine_codes(edited.rename(columns=rename), file_type)
            machine_df = machine_df.drop(columns=[c for c in ['Step','Notes'] if c in machine_df.columns])

            st.download_button(
                "📥 Download Machine CSV",
                machine_df.to_csv(index=False, sep=';'),
                file_name=f"{file_type}_sequence.csv",
                mime="text/csv"
            )

    # -------- CSV → EXCEL --------
    elif operation == "📤 Machine CSV to Excel":
        uploaded = st.file_uploader("Upload Machine CSV", type=['csv'])
        if uploaded:
            df = safe_read_csv(uploaded)
            file_type = detect_file_type(df)

            st.info(f"🔍 Detected Seal Type: **{file_type.replace('_',' ').upper()}**")

            edited = editable_dataframe(convert_machine_to_technician(df, file_type), "csv_editor")
            excel = create_professional_excel_from_data(edited, file_type)

            st.download_button(
                "📥 Download Excel",
                excel.getvalue(),
                file_name=f"{file_type}_professional.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # -------- VIEW CURRENT --------
    elif operation == "👀 View Current Test":
        seal = st.selectbox("Select Seal Type", ["Main Seal", "Separation Seal"])

        if seal == "Main Seal":
            df = safe_read_csv("MainSealSet2.csv")
            file_type = "main_seal"
        else:
            df = safe_read_csv("SeperationSeal.csv")
            file_type = "separation_seal"

        st.success(f"👀 Viewing **{seal.upper()}** test")

        edited = editable_dataframe(convert_machine_to_technician(df, file_type), "current_editor")

        excel = create_professional_excel_from_data(edited, file_type)
        st.download_button(
            "📥 Download Excel",
            excel.getvalue(),
            file_name=f"current_{file_type}_test.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
