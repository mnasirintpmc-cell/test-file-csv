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
                    na_values=[
                        'NaN','NAN','nan',
                        'INF','INFINITY','inf','infinity',
                        '',' ','NULL','null'
                    ],
                    keep_default_na=True,
                    skipinitialspace=True
                )

                return df.replace([np.nan, math.inf, -math.inf], 0)

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

    if 'TST_SepSealFlwSet1' in cols or 'Sep_Seal_Flow_Set1' in cols:
        return 'separation_seal'

    return 'unknown'


# =====================================================
# COLUMN MAPPING
# =====================================================

def get_column_mapping(file_type):

    if file_type == 'main_seal':

        return {

            'machine_to_technician': {

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

            'technician_to_machine': {

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
                'TST_APFlag':'Acceptance point',
                'TST_TempDemand':'Temperature_C',
                'TST_GasType':'Gas_Type',
                'TST_MeasurementReq':'Measurement',
                'TST_TorqueCheck':'Torque_Check'

            },

            'technician_to_machine': {

                'Speed_RPM':'TST_SpeedDem',
                'Sep_Seal_Flow_Set1':'TST_SepSealFlwSet1',
                'Sep_Seal_Flow_Set2':'TST_SepSealFlwSet2',
                'Sep_Seal_Pressure_Set1':'TST_SepSealPSet1',
                'Sep_Seal_Pressure_Set2':'TST_SepSealPSet2',
                'Sep_Seal_Control_Type':'TST_SepSealControlTyp',
                'Duration_s':'TST_StepDuration',
                'Acceptance point':'TST_APFlag',
                'Temperature_C':'TST_TempDemand',
                'Gas_Type':'TST_GasType',
                'Measurement':'TST_MeasurementReq',
                'Torque_Check':'TST_TorqueCheck'

            }

        }

    return None


# =====================================================
# SAFETY VALIDATION
# =====================================================

def validate_safety(df):

    warnings = []

    if 'Primary seal Gas Pressure (barg)' not in df.columns:
        return warnings

    for i,row in df.iterrows():

        step = row.get("Step",i+1)

        try:
            primary = float(row.get('Primary seal Gas Pressure (barg)',0))
        except:
            primary = 0

        try:
            inter = float(row.get('Interspace_Pressure_bar',0))
        except:
            inter = 0

        if inter > primary:
            warnings.append(f"Step {step}: Interspace pressure > Cell pressure")

        if primary - inter < 0.2 and inter > 0:
            warnings.append(f"Step {step}: Differential pressure < 0.2 bar")

        if primary < 0 or inter < 0:
            warnings.append(f"Step {step}: Negative pressure detected")

    return warnings


# =====================================================
# CONVERSIONS
# =====================================================

def convert_machine_to_technician(df,file_type):

    mapping = get_column_mapping(file_type)

    tech_df = df.rename(columns=mapping['machine_to_technician'])

    tech_df.insert(0,'Step',range(1,len(tech_df)+1))

    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''

    return tech_df


def convert_to_machine_codes(df):

    df = df.copy()

    for col in ['TST_APFlag','TST_MeasurementReq','TST_TorqueCheck']:

        if col in df.columns:
            df[col] = df[col].map({'Yes':1,'No':0}).fillna(0)

    if 'TST_TestMode' in df.columns:
        df['TST_TestMode'] = df['TST_TestMode'].map({'Mode 1':1,'Mode 2':2}).fillna(1)

    return df


# =====================================================
# EDITABLE TABLE
# =====================================================

def editable_dataframe(df,key,height=500):

    if key not in st.session_state:
        st.session_state[key] = df.copy()

    edited = st.data_editor(
        st.session_state[key],
        use_container_width=True,
        height=height,
        num_rows="fixed"
    )

    st.session_state[key] = edited

    warnings = validate_safety(edited)

    if warnings:
        st.error("⚠ Safety interlock violations detected")
        for w in warnings:
            st.warning(w)

    return edited


# =====================================================
# MAIN APP
# =====================================================

def main():

    st.title("⚙️ Seal Test Manager")

    operation = st.sidebar.radio(

        "Operation",

        [
            "Download Template",
            "Excel to Machine CSV",
            "Machine CSV to Excel",
            "View Current Test",
            "Spec → Technician Excel"
        ]

    )


# -----------------------------------------------------
# MACHINE CSV → EXCEL
# -----------------------------------------------------

    if operation == "Machine CSV to Excel":

        uploaded = st.file_uploader("Upload Machine CSV",type=['csv'])

        if uploaded:

            df = safe_read_csv(uploaded)

            file_type = detect_file_type(df)

            edited = editable_dataframe(
                convert_machine_to_technician(df,file_type),
                "csv_editor"
            )

            st.download_button(
                "Download Excel",
                edited.to_excel(index=False),
                file_name="technician_sequence.xlsx"
            )


# -----------------------------------------------------
# EXCEL → MACHINE CSV
# -----------------------------------------------------

    elif operation == "Excel to Machine CSV":

        uploaded = st.file_uploader("Upload Technician Excel",type=['xlsx'])

        if uploaded:

            df = pd.read_excel(uploaded)

            file_type = detect_file_type(df)

            edited = editable_dataframe(df,"excel_editor")

            mapping = get_column_mapping(file_type)

            machine_df = convert_to_machine_codes(
                edited.rename(columns=mapping['technician_to_machine'])
            ).drop(columns=['Step','Notes'],errors='ignore')

            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False,sep=';'),
                file_name="machine_sequence.csv"
            )


# -----------------------------------------------------
# TEMPLATE DOWNLOAD
# -----------------------------------------------------

    elif operation == "Download Template":

        st.info("Download a template from your base CSV")

        seal = st.selectbox("Seal Type",["Main Seal","Separation Seal"])

        file = "MainSealSet2.csv" if seal=="Main Seal" else "SeperationSeal.csv"

        df = safe_read_csv(file)

        file_type = detect_file_type(df)

        tech = convert_machine_to_technician(df,file_type)

        st.download_button(
            "Download Excel Template",
            tech.to_excel(index=False),
            file_name="template.xlsx"
        )


# -----------------------------------------------------
# VIEW CURRENT TEST
# -----------------------------------------------------

    elif operation == "View Current Test":

        seal = st.selectbox("Seal Type",["Main Seal","Separation Seal"])

        file = "MainSealSet2.csv" if seal=="Main Seal" else "SeperationSeal.csv"

        df = safe_read_csv(file)

        file_type = detect_file_type(df)

        edited = editable_dataframe(
            convert_machine_to_technician(df,file_type),
            "current_editor"
        )

        st.download_button(
            "Download Excel",
            edited.to_excel(index=False),
            file_name="current_test.xlsx"
        )


# -----------------------------------------------------
# SPEC PLACEHOLDER
# -----------------------------------------------------

    elif operation == "Spec → Technician Excel":

        uploaded = st.file_uploader("Upload Spec (.xlsb)",type=['xlsb'])

        if uploaded:

            st.info("Spec scanner will be added here")

            df = pd.DataFrame({
                "Step":[1],
                "Speed_RPM":[0],
                "Primary seal Gas Pressure (barg)":[0],
                "Interspace_Pressure_bar":[0],
                "Duration_s":[60],
                "Notes":[""]
            })

            edited = editable_dataframe(df,"spec_editor")

            st.download_button(
                "Download Excel",
                edited.to_excel(index=False),
                file_name="spec_sequence.xlsx"
            )


if __name__ == "__main__":
    main()
