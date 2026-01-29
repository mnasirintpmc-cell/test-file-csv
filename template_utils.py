import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

# =====================================================
# IMPORT TEMPLATE UTILITIES (SOURCE OF TRUTH)
# =====================================================

from template_utils import (
    create_smart_template,
    create_example_sequence,
    safe_read_csv
)

# =====================================================
# SESSION HELPERS
# =====================================================

def reset_editor(key, df):
    if key not in st.session_state or st.session_state[key].shape != df.shape:
        st.session_state[key] = df.copy()

# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):
    cols = df.columns.tolist()
    if 'TST_CellPresDemand' in cols:
        return 'main_seal'
    if 'TST_SepSealFlwSet1' in cols:
        return 'separation_seal'
    return 'unknown'

# =====================================================
# COLUMN MAPPINGS
# =====================================================

def get_column_mapping(file_type):
    if file_type == 'main_seal':
        return {
            'technician_to_machine': {
                'Speed_RPM':'TST_SpeedDem',
                'Cell_Pressure_bar':'TST_CellPresDemand',
                'Interface_Pressure_bar':'TST_InterPresDemand',
                'BP_Drive_End_bar':'TST_InterBPDemand_DE',
                'BP_Non_Drive_End_bar':'TST_InterBPDemand_NDE',
                'Gas_Injection_bar':'TST_GasInjectionDemand',
                'Duration_s':'TST_StepDuration',
                'Auto_Proceed':'TST_APFlag',
                'Temperature_C':'TST_TempDemand',
                'Gas_Type':'TST_GasType',
                'Test_Mode':'TST_TestMode',
                'Measurement':'TST_MeasurementReq',
                'Torque_Check':'TST_TorqueCheck'
            }
        }

    if file_type == 'separation_seal':
        return {
            'technician_to_machine': {
                'Speed_RPM':'TST_SpeedDem',
                'Sep_Seal_Flow_Set1':'TST_SepSealFlwSet1',
                'Sep_Seal_Flow_Set2':'TST_SepSealFlwSet2',
                'Sep_Seal_Pressure_Set1':'TST_SepSealPSet1',
                'Sep_Seal_Pressure_Set2':'TST_SepSealPSet2',
                'Sep_Seal_Control_Type':'TST_SepSealControlTyp',
                'Duration_s':'TST_StepDuration',
                'Auto_Proceed':'TST_APFlag',
                'Temperature_C':'TST_TempDemand',
                'Gas_Type':'TST_GasType',
                'Measurement':'TST_MeasurementReq',
                'Torque_Check':'TST_TorqueCheck'
            }
        }

    return None

# =====================================================
# MACHINE ↔ TECH CONVERSION
# =====================================================

def convert_to_machine_codes(df):
    df = df.copy()
    for col in df.columns:
        if col in ['Auto_Proceed', 'Measurement', 'Torque_Check']:
            df[col] = df[col].map({'Yes': 1, 'No': 0}).fillna(0)
    return df

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    tech_df = df.rename(columns={v: k for k, v in mapping['technician_to_machine'].items()})
    tech_df.insert(0, 'Step', range(1, len(tech_df) + 1))
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
        key=f"editor_{key}",
        use_container_width=True,
        height=height,
        num_rows="dynamic"
    )
    st.session_state[key] = edited
    return edited

# =====================================================
# PROFESSIONAL EXCEL EXPORT (WITH INSTRUCTIONS)
# =====================================================

def create_professional_excel_from_data(technician_df, file_type):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as workbook:
        technician_df.to_excel(workbook, sheet_name='TEST_SEQUENCE', index=False)

        wb = workbook.book
        ws = workbook.sheets['TEST_SEQUENCE']

        header = wb.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
            'fg_color': '#366092',
            'font_color': 'white'
        })
        cell = wb.add_format({'border': 1, 'align': 'center'})
        notes = wb.add_format({'border': 1, 'align': 'left'})

        for c, col in enumerate(technician_df.columns):
            ws.write(0, c, col, header)

        for r in range(1, len(technician_df) + 1):
            for c, col in enumerate(technician_df.columns):
                fmt = notes if col == 'Notes' else cell
                ws.write(r, c, technician_df.iloc[r - 1, c], fmt)

        ws.set_column(0, len(technician_df.columns) - 1, 18)

        # ---------------- INSTRUCTIONS ----------------
        instr = wb.add_worksheet('INSTRUCTIONS')
        date = datetime.now().strftime('%Y-%m-%d')

        title = (
            f"{'MAIN SEAL' if file_type == 'main_seal' else 'SEPARATION SEAL'} "
            f"TEST SEQUENCE - EXPORTED {date}"
        )

        instructions = [
            title, "",
            "HOW TO USE THIS FILE:",
            "1. This file contains your current test sequence",
            "2. All cells have proper borders and formatting",
            "3. Dropdown menus are included for standardized inputs",
            "4. You can edit this file and upload it back to the web app",
            "5. Use the conversion tool to generate machine CSV files",
            "",
            "FIELD DESCRIPTIONS:"
        ] + [f"{c}: Field description" for c in technician_df.columns]

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

    # ================= TEMPLATE DOWNLOAD =================
    if operation == "📥 Download Template":
        template_type = st.selectbox(
            "Template Type",
            ["Smart Blank Template", "Example Test Sequence"]
        )

        if template_type == "Smart Blank Template":
            machine_df = create_smart_template()
        else:
            machine_df = create_example_sequence()

        file_type = detect_file_type(machine_df)
        if file_type == "unknown":
            st.error("Unable to detect seal type from template")
            st.stop()

        tech_df = convert_machine_to_technician(machine_df, file_type)
        excel = create_professional_excel_from_data(tech_df, file_type)

        st.download_button(
            "📥 Download Excel Template",
            excel.getvalue(),
            file_name=f"{file_type}_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ================= EXCEL → CSV =================
    elif operation == "🔄 Excel to Machine CSV":
        uploaded = st.file_uploader("Upload Excel", type=['xlsx'])
        if uploaded:
            df = pd.read_excel(uploaded, sheet_name='TEST_SEQUENCE')
            edited = editable_dataframe(df, "excel_editor")
            file_type = detect_file_type(edited)
            mapping = get_column_mapping(file_type)

            machine_df = edited.rename(columns=mapping['technician_to_machine'])
            machine_df = convert_to_machine_codes(machine_df)
            machine_df = machine_df.drop(
                columns=[c for c in ['Step', 'Notes'] if c in machine_df.columns]
            )

            st.download_button(
                "📥 Download Machine CSV",
                machine_df.to_csv(index=False, sep=';'),
                mime="text/csv"
            )

    # ================= CSV → EXCEL =================
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
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ================= VIEW CURRENT =================
    elif operation == "👀 View Current Test":
        st.info("Load, edit, and export existing test files")

if __name__ == "__main__":
    main()
