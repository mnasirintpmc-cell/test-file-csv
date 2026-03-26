import streamlit as st
import pandas as pd
import numpy as np
import io
import os
from datetime import datetime
from spec_scanner import scan_spec
from validator import validate_sequence

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path_or_buffer):

    encodings = ["utf-8","latin-1","cp1252","iso-8859-1"]

    for enc in encodings:
        try:
            df = pd.read_csv(
                file_path_or_buffer,
                delimiter=";",
                encoding=enc
            )
            return df
        except:
            continue

    st.error("CSV read error")
    return pd.DataFrame()


# =====================================================
# SAFETY VALIDATION
# =====================================================

def validate_safety(df):

    warnings = []

    if "Primary seal Gas Pressure (barg)" not in df.columns:
        return warnings

    for i,row in df.iterrows():

        step = row.get("Step", i+1)

        try:
            primary = float(row.get("Primary seal Gas Pressure (barg)",0))
        except:
            primary = 0

        try:
            inter = float(row.get("Interspace_Pressure_bar",0))
        except:
            inter = 0

        if inter > primary:
            warnings.append(
                f"Step {step}: Interspace pressure greater than primary"
            )

        if (primary - inter) < 10 and primary > 0 and inter > 0:
            warnings.append(
                f"Step {step}: Differential pressure < 10 bar"
            )

    return warnings


# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):

    cols = df.columns.tolist()

    if "TST_CellPresDemand" in cols or "Primary seal Gas Pressure (barg)" in cols:
        return "main_seal"

    if "TST_SepSealFlwSet1" in cols or "Sep_Seal_Flow_Set1" in cols:
        return "separation_seal"

    return "unknown"


# =====================================================
# COLUMN MAPPING
# =====================================================

def get_column_mapping(file_type):

    if file_type == "main_seal":

        return {

            "machine_to_technician":{

                "TST_SpeedDem":"Speed_RPM",
                "TST_CellPresDemand":"Primary seal Gas Pressure (barg)",
                "TST_InterPresDemand":"Interspace_Pressure_bar",
                "TST_InterBPDemand_DE":"BackPressure_Drive_End_bar",
                "TST_InterBPDemand_NDE":"BackPressure_Non_Drive_End_bar",
                "TST_GasInjectionDemand":"Gas_Injection_bar",
                "TST_StepDuration":"Duration_s",
                "TST_APFlag":"Acceptance point",
                "TST_TempDemand":"Temperature_C",
                "TST_GasType":"Gas_Type",
                "TST_TestMode":"Test_Mode",
                "TST_MeasurementReq":"Measurement",
                "TST_TorqueCheck":"Torque_Check"

            },

            "technician_to_machine":{

                "Speed_RPM":"TST_SpeedDem",
                "Primary seal Gas Pressure (barg)":"TST_CellPresDemand",
                "Interspace_Pressure_bar":"TST_InterPresDemand",
                "BackPressure_Drive_End_bar":"TST_InterBPDemand_DE",
                "BackPressure_Non_Drive_End_bar":"TST_InterBPDemand_NDE",
                "Gas_Injection_bar":"TST_GasInjectionDemand",
                "Duration_s":"TST_StepDuration",
                "Acceptance point":"TST_APFlag",
                "Temperature_C":"TST_TempDemand",
                "Gas_Type":"TST_GasType",
                "Test_Mode":"TST_TestMode",
                "Measurement":"TST_MeasurementReq",
                "Torque_Check":"TST_TorqueCheck"

            }

        }

    if file_type == "separation_seal":

        return {

            "machine_to_technician":{

                "TST_SpeedDem":"Speed_RPM",
                "TST_SepSealFlwSet1":"Sep_Seal_Flow_Set1",
                "TST_SepSealFlwSet2":"Sep_Seal_Flow_Set2",
                "TST_SepSealPSet1":"Sep_Seal_Pressure_Set1",
                "TST_SepSealPSet2":"Sep_Seal_Pressure_Set2",
                "TST_SepSealControlTyp":"Sep_Seal_Control_Type",
                "TST_StepDuration":"Duration_s",
                "TST_APFlag":"Acceptance point",
                "TST_TempDemand":"Temperature_C",
                "TST_GasType":"Gas_Type",
                "TST_MeasurementReq":"Measurement",
                "TST_TorqueCheck":"Torque_Check"

            },

            "technician_to_machine":{

                "Speed_RPM":"TST_SpeedDem",
                "Sep_Seal_Flow_Set1":"TST_SepSealFlwSet1",
                "Sep_Seal_Flow_Set2":"TST_SepSealFlwSet2",
                "Sep_Seal_Pressure_Set1":"TST_SepSealPSet1",
                "Sep_Seal_Pressure_Set2":"TST_SepSealPSet2",
                "Sep_Seal_Control_Type":"TST_SepSealControlTyp",
                "Duration_s":"TST_StepDuration",
                "Acceptance point":"TST_APFlag",
                "Temperature_C":"TST_TempDemand",
                "Gas_Type":"TST_GasType",
                "Measurement":"TST_MeasurementReq",
                "Torque_Check":"TST_TorqueCheck"

            }

        }

    return None


# =====================================================
# CONVERSION
# =====================================================

def convert_machine_to_technician(df,file_type):

    mapping = get_column_mapping(file_type)

    tech_df = df.rename(columns=mapping["machine_to_technician"])

    tech_df.insert(0,"Step",range(1,len(tech_df)+1))

    if "Notes" not in tech_df.columns:
        tech_df["Notes"] = ""

    return tech_df


def convert_to_machine_codes(df):

    df = df.copy()

    for col in ["TST_APFlag","TST_MeasurementReq","TST_TorqueCheck"]:

        if col in df.columns:
            df[col] = df[col].map({"Yes":1,"No":0}).fillna(0)

    return df


# =====================================================
# EDITABLE TABLE (TEST MODE FIX)
# =====================================================

def editable_dataframe(df):

    edited = st.data_editor(df,use_container_width=True)

    if "Primary seal Gas Pressure (barg)" in edited.columns:

        for i,row in edited.iterrows():

            try:
                primary = float(row.get("Primary seal Gas Pressure (barg)",0))
            except:
                primary = 0

            if primary == 0:
                if "Test_Mode" in edited.columns:
                    edited.at[i,"Test_Mode"] = 1

    warnings = validate_sequence(edited)

    if warnings:

        st.error("Safety interlock violations detected")

        for w in warnings:
            st.warning(w)

    return edited


# =====================================================
# MAIN
# =====================================================

def main():

    st.title("⚙️ DGS Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        ["Download Template","CSV → Excel","Excel → CSV","View Current Test","Spec → Technician Excel"]
    )

    base_dir = os.path.dirname(__file__)

    if operation=="Spec → Technician Excel":

        uploaded = st.file_uploader(
            "Upload Spec (.xlsb, .xlsm, .xlsx)",
            type=["xlsb","xlsm","xlsx"]
        )

        if uploaded:

            spec_df = scan_spec(uploaded)

            edited = editable_dataframe(spec_df)

            st.write(edited)


if __name__=="__main__":
    main()
