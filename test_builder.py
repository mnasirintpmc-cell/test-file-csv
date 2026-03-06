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

def safe_read_csv(file_path_or_buffer):

    try:

        encodings = ['utf-8','latin-1','cp1252','iso-8859-1']

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

                return df.replace([np.nan, math.inf, -math.inf],0)

            except:
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

    if 'TST_CellPresDemand' in cols or 'Primary seal Gas Pressure (barg)' in cols:
        return 'main_seal'

    return 'unknown'

# =====================================================
# COLUMN MAPPING
# =====================================================

def get_column_mapping():

    return {

        'machine_to_technician':{

            'TST_SpeedDem':'Speed_RPM',
            'TST_CellPresDemand':'Primary seal Gas Pressure (barg)',
            'TST_InterPresDemand':'Interspace_Pressure_bar',
            'TST_InterBPDemand_DE':'BackPressure_Drive_End_bar',
            'TST_InterBPDemand_NDE':'BackPressure_Non_Drive_End_bar',
            'TST_GasInjectionDemand':'Gas_Injection_bar',
            'TST_StepDuration':'Duration_s',
            'TST_APFlag':'Acceptance point',
            'TST_TempDemand':'Temperature_C',
            'TST_GasType':'Gas_Type',
            'TST_TestMode':'Test_Mode',
            'TST_MeasurementReq':'Measurement',
            'TST_TorqueCheck':'Torque_Check'

        },

        'technician_to_machine':{

            'Speed_RPM':'TST_SpeedDem',
            'Primary seal Gas Pressure (barg)':'TST_CellPresDemand',
            'Interspace_Pressure_bar':'TST_InterPresDemand',
            'BackPressure_Drive_End_bar':'TST_InterBPDemand_DE',
            'BackPressure_Non_Drive_End_bar':'TST_InterBPDemand_NDE',
            'Gas_Injection_bar':'TST_GasInjectionDemand',
            'Duration_s':'TST_StepDuration',
            'Acceptance point':'TST_APFlag',
            'Temperature_C':'TST_TempDemand',
            'Gas_Type':'TST_GasType',
            'Test_Mode':'TST_TestMode',
            'Measurement':'TST_MeasurementReq',
            'Torque_Check':'TST_TorqueCheck'

        }

    }

# =====================================================
# MACHINE → TECHNICIAN
# =====================================================

def convert_machine_to_technician(df):

    mapping = get_column_mapping()

    tech_df = df.rename(columns=mapping['machine_to_technician'])

    tech_df.insert(0,'Step',range(1,len(tech_df)+1))

    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''

    return tech_df

# =====================================================
# TECHNICIAN → MACHINE
# =====================================================

def convert_to_machine(df):

    mapping = get_column_mapping()

    machine_df = df.rename(columns=mapping['technician_to_machine'])

    machine_df = machine_df.drop(columns=['Step','Notes'],errors='ignore')

    return machine_df

# =====================================================
# PROFESSIONAL EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(technician_df):

    output = io.BytesIO()

    with pd.ExcelWriter(output,engine='xlsxwriter') as workbook:

        technician_df.to_excel(workbook,sheet_name='TEST_SEQUENCE',index=False)

        ws = workbook.sheets['TEST_SEQUENCE']
        wb = workbook.book

        header = wb.add_format({
            'bold':True,
            'align':'center',
            'border':1,
            'fg_color':'#366092',
            'font_color':'white'
        })

        cell = wb.add_format({'border':1,'align':'center'})
        notes = wb.add_format({'border':1,'align':'left'})

        for c,col in enumerate(technician_df.columns):
            ws.write(0,c,col,header)

        for r in range(1,len(technician_df)+1):

            for c,col in enumerate(technician_df.columns):

                ws.write(
                    r,
                    c,
                    technician_df.iloc[r-1,c],
                    notes if col=="Notes" else cell
                )

        ws.set_column(0,len(technician_df.columns)-1,18)

    output.seek(0)

    return output

# =====================================================
# SPEC → TECHNICIAN BUILDER
# =====================================================

def build_from_spec(df):

    rows = []

    for _,r in df.iterrows():

        remarks = str(r.get("Remarks",""))

        ap_flag = 1 if "acceptance" in remarks.lower() else 0

        rows.append({

            "Speed_RPM": r.get("Speed",0),
            "Primary seal Gas Pressure (barg)": r.get("Primary Seal Gas Pressure",0),
            "Interspace_Pressure_bar": r.get("Secondary Seal Gas Pressure",0),
            "BackPressure_Drive_End_bar":0,
            "BackPressure_Non_Drive_End_bar":0,
            "Gas_Injection_bar":0,
            "Duration_s": r.get("Hold Time",0)*60,
            "Acceptance point": ap_flag,
            "Temperature_C": 60 if str(r.get("Temp","")).upper()=="AMB" else r.get("Temp",0),
            "Gas_Type":"Air",
            "Test_Mode":1,
            "Measurement": ap_flag,
            "Torque_Check":0,
            "Notes":remarks

        })

    return pd.DataFrame(rows)

# =====================================================
# MAIN APP
# =====================================================

def main():

    st.title("Seal Test Manager")

    operation = st.sidebar.radio(

        "Operation",

        [
            "Download Template",
            "Excel to Machine CSV",
            "Machine CSV to Excel",
            "Build Technician Test"
        ]

    )

# -----------------------------------------------------

    if operation == "Download Template":

        df = safe_read_csv("MainSealSet2.csv")

        tech_df = convert_machine_to_technician(df)

        excel = create_professional_excel_from_data(tech_df)

        st.download_button(
            "Download Template",
            excel.getvalue(),
            file_name="technician_template.xlsx"
        )

# -----------------------------------------------------

    elif operation == "Excel to Machine CSV":

        uploaded = st.file_uploader("Upload Technician Excel",type=['xlsx'])

        if uploaded:

            df = pd.read_excel(uploaded)

            machine_df = convert_to_machine(df)

            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False,sep=';'),
                file_name="machine_sequence.csv"
            )

# -----------------------------------------------------

    elif operation == "Machine CSV to Excel":

        uploaded = st.file_uploader("Upload Machine CSV",type=['csv'])

        if uploaded:

            df = safe_read_csv(uploaded)

            tech_df = convert_machine_to_technician(df)

            excel = create_professional_excel_from_data(tech_df)

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )

# -----------------------------------------------------

    elif operation == "Build Technician Test":

        st.header("Test Builder")

        if "tests" not in st.session_state:
            st.session_state.tests = []

        uploaded = st.file_uploader("Upload Test Spec Excel",type=['xlsx'])

        if uploaded:

            spec_df = pd.read_excel(uploaded)

            st.dataframe(spec_df)

            if st.button("Add Test"):

                converted = build_from_spec(spec_df)

                st.session_state.tests.append(converted)

                st.success("Test added")

        st.write("Tests loaded:",len(st.session_state.tests))

        if st.button("Generate Technician Excel"):

            if len(st.session_state.tests)==0:
                st.warning("No tests added")
                return

            combined = pd.concat(st.session_state.tests,ignore_index=True)

            combined.insert(0,"Step",range(1,len(combined)+1))

            st.dataframe(combined)

            excel = create_professional_excel_from_data(combined)

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )

# =====================================================

if __name__ == "__main__":
    main()
