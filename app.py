import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math
import os

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path):
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=';',
                    encoding=enc,
                    na_values=['NaN','NAN','nan','INF','INFINITY','inf','infinity','',' ','NULL','null'],
                    skipinitialspace=True
                )
                return df.replace([np.nan, math.inf, -math.inf], 0)
            except Exception:
                continue
        return pd.read_csv(file_path, sep=';')
    except Exception as e:
        st.error(f"CSV read error: {e}")
        return pd.DataFrame()

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
            'machine_to_technician': {
                'TST_SpeedDem':'Speed_RPM',
                'TST_CellPresDemand':'Cell_Pressure_bar',
                'TST_InterPresDemand':'Interface_Pressure_bar',
                'TST_InterBPDemand_DE':'BP_Drive_End_bar',
                'TST_InterBPDemand_NDE':'BP_Non_Drive_End_bar',
                'TST_GasInjectionDemand':'Gas_Injection_bar',
                'TST_StepDuration':'Duration_s',
                'TST_APFlag':'Auto_Proceed',
                'TST_TempDemand':'Temperature_C',
                'TST_GasType':'Gas_Type',
                'TST_TestMode':'Test_Mode',
                'TST_MeasurementReq':'Measurement',
                'TST_TorqueCheck':'Torque_Check'
            }
        }

    if file_type == 'separation_seal':
        return {
            'machine_to_technician': {
                'TST_SpeedDem':'Speed_RPM',
                'TST_SepSealFlwSet1':'Sep_Seal_Flow_Set1',
                'TST_SepSealFlwSet2':'Sep_Seal_Flow_Set2',
                'TST_SepSealPSet1':'Sep_Seal_Pressure_Set1',
                'TST_SepSealPSet2':'Sep_Seal_Pressure_Set2',
                'TST_SepSealControlTyp':'Sep_Seal_Control_Type',
                'TST_StepDuration':'Duration_s',
                'TST_APFlag':'Auto_Proceed',
                'TST_TempDemand':'Temperature_C',
                'TST_GasType':'Gas_Type',
                'TST_MeasurementReq':'Measurement',
                'TST_TorqueCheck':'Torque_Check'
            }
        }

    return None

# =====================================================
# MACHINE → TECHNICIAN
# =====================================================

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    tech_df = df.rename(columns=mapping['machine_to_technician'])
    tech_df.insert(0, 'Step', range(1, len(tech_df)+1))
    tech_df['Notes'] = ''
    return tech_df

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

        # -------- INSTRUCTIONS --------
        instr = wb.add_worksheet('INSTRUCTIONS')
        date = datetime.now().strftime('%Y-%m-%d')
        title = f"{'MAIN SEAL' if file_type=='main_seal' else 'SEPARATION SEAL'} TEST SEQUENCE - EXPORTED {date}"

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
        ] + [f"{c}: see system documentation" for c in technician_df.columns]

        title_fmt = wb.add_format({'bold': True, 'font_size': 14, 'font_color': '#366092'})
        header_fmt = wb.add_format({'bold': True, 'font_color': '#366092'})

        for r, text in enumerate(instructions):
            if r == 0:
                instr.write(r, 0, text, title_fmt)
            elif text in ["HOW TO USE THIS FILE:", "FIELD DESCRIPTIONS:"]:
                instr.write(r, 0, text, header_fmt)
            else:
                instr.write(r, 0, text)

        instr.set_column('A:A', 80)

    output.seek(0)
    return output

# =====================================================
# MAIN APP
# =====================================================

def main():
    st.title("⚙️ Universal Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        ["📥 Download Template"]
    )

    if operation == "📥 Download Template":
        seal = st.selectbox("Select Template", ["Main Seal", "Separation Seal"])

        csv_file = "MainSealSet2.csv" if seal == "Main Seal" else "SeperationSeal.csv"

        if not os.path.exists(csv_file):
            st.error(f"{csv_file} not found in app directory")
            return

        df = safe_read_csv(csv_file)
        file_type = detect_file_type(df)
        tech_df = convert_machine_to_technician(df, file_type)

        excel = create_professional_excel_from_data(tech_df, file_type)

        st.download_button(
            f"📥 Download {seal} Excel Template",
            excel.getvalue(),
            file_name=f"{file_type}_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
