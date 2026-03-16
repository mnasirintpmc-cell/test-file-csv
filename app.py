import streamlit as st
import pandas as pd
import numpy as np
import io
import os
from datetime import datetime
from spec_scanner import scan_spec


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

        if primary - inter < 0.2 and inter > 0:
            warnings.append(
                f"Step {step}: Differential pressure < 0.2 bar"
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
                "BackPressure_Drive_End_bar
