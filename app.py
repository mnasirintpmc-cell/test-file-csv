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

def safe_read_csv(file):

    encodings = ['utf-8','latin-1','cp1252']

    for enc in encodings:
        try:
            df = pd.read_csv(
                file,
                delimiter=';',
                encoding=enc,
                skipinitialspace=True
            )
            return df.replace([np.nan, math.inf, -math.inf],0)
        except:
            pass

    st.error("CSV read failed")
    return pd.DataFrame()

# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):

    cols = df.columns.tolist()

    if "TST_CellPresDemand" in cols or "Primary seal Gas Pressure (barg)" in cols:
        return "main_seal"

    return "unknown"

# =====================================================
# COLUMN MAPPING
# =====================================================

def get_column_mapping():

    return {
        "machine_to_technician":{
            "TST_SpeedDem":"Speed_RPM",
            "TST_CellPresDemand":"Primary seal Gas Pressure (barg)",
            "TST_InterPresDemand":"Interspace_Pressure_bar",
            "TST_InterBPDemand_DE":"BackPressure_Drive_End_bar",
            "TST_InterBPDemand_NDE":"BackPressure_Non_Drive_End_bar",
            "TST_GasInjectionDemand":"Gas_Injection",
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
            "Gas_Injection":"TST_GasInjectionDemand",
            "Duration_s":"TST_StepDuration",
            "Acceptance point":"TST_APFlag",
            "Temperature_C":"TST_TempDemand",
            "Gas_Type":"TST_GasType",
            "Test_Mode":"TST_TestMode",
            "Measurement":"TST_MeasurementReq",
            "Torque_Check":"TST_TorqueCheck"
        }
    }

# =====================================================
# MACHINE → TECHNICIAN
# =====================================================

def convert_machine_to_technician(df):

    mapping = get_column_mapping()

    tech_df = df.rename(columns=mapping["machine_to_technician"])

    tech_df.insert(0,"Step",range(1,len(tech_df)+1))

    if "Notes" not in tech_df.columns:
        tech_df["Notes"] = ""

    return tech_df

# =====================================================
# VALIDATION + MODE LOGIC
# =====================================================

def apply_test_logic(df):

    warnings = []

    for i,row in df.iterrows():

        cell = float(row.get("TST_CellPresDemand",0))
        inter = float(row.get("TST_InterPresDemand",0))
        bp_de = float(row.get("TST_InterBPDemand_DE",0))
        bp_nde = float(row.get("TST_InterBPDemand_NDE",0))
        mode = int(row.get("TST_TestMode",1))

        # ----------------------------
        # Pressure validation
        # ----------------------------

        if cell < inter:
            warnings.append(f"Step {i+1}: Cell pressure lower than interspace")

        # ----------------------------
        # If technician entered BP
        # ----------------------------

        if bp_de > 0 or bp_nde > 0:
            continue

        # ----------------------------
        # INBOARD MODE
        # ----------------------------

        if mode == 1:

            if inter > 0:
                df.at[i,"TST_InterBPDemand_DE"] = inter
                df.at[i,"TST_InterBPDemand_NDE"] = inter
                df.at[i,"TST_InterPresDemand"] = 0

        # ----------------------------
        # OUTBOARD MODE
        # ----------------------------

        if mode == 2:

            df.at[i,"TST_InterBPDemand_DE"] = 0
            df.at[i,"TST_InterBPDemand_NDE"] = 0

    return df,warnings

# =====================================================
# EXCEL EXPORT (PROFESSIONAL FORMAT)
# =====================================================

def create_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(output,engine="xlsxwriter") as writer:

        df.to_excel(writer,sheet_name="TEST_SEQUENCE",index=False)

        wb = writer.book
        ws = writer.sheets["TEST_SEQUENCE"]

        header = wb.add_format({
            "bold":True,
            "border":1,
            "align":"center",
            "fg_color":"#366092",
            "font_color":"white"
        })

        cell = wb.add_format({
            "border":1,
            "align":"center"
        })

        for col,colname in enumerate(df.columns):
            ws.write(0,col,colname,header)

        for r in range(1,len(df)+1):
            for c in range(len(df.columns)):
                ws.write(r,c,df.iloc[r-1,c],cell)

        ws.set_column(0,len(df.columns)-1,18)

    output.seek(0)

    return output

# =====================================================
# STREAMLIT EDITOR
# =====================================================

def editable_dataframe(df,key):

    if key not in st.session_state:
        st.session_state[key] = df.copy()

    edited = st.data_editor(
        st.session_state[key],
        use_container_width=True,
        num_rows="fixed"
    )

    st.session_state[key] = edited

    return edited

# =====================================================
# MAIN APP
# =====================================================

def main():

    st.title("⚙️ Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        [
            "Machine CSV → Excel",
            "Excel → Machine CSV"
        ]
    )

# =====================================================
# CSV → EXCEL
# =====================================================

    if operation == "Machine CSV → Excel":

        file = st.file_uploader("Upload Machine CSV",type=["csv"])

        if file:

            df = safe_read_csv(file)

            tech_df = convert_machine_to_technician(df)

            edited = editable_dataframe(tech_df,"csv_editor")

            excel = create_excel(edited)

            st.download_button(
                "Download Excel",
                excel,
                "technician_test_sequence.xlsx"
            )

# =====================================================
# EXCEL → CSV
# =====================================================

    if operation == "Excel → Machine CSV":

        file = st.file_uploader("Upload Excel",type=["xlsx"])

        if file:

            df = pd.read_excel(file)

            df = df.dropna(subset=["Step"]).reset_index(drop=True)

            edited = editable_dataframe(df,"excel_editor")

            mapping = get_column_mapping()

            machine = edited.rename(
                columns=mapping["technician_to_machine"]
            )

            machine = machine.drop(columns=["Step","Notes"],errors="ignore")

            machine,warnings = apply_test_logic(machine)

            if warnings:

                st.warning("Pressure warnings detected")

                for w in warnings:
                    st.write(w)

            csv = machine.to_csv(index=False,sep=";")

            st.download_button(
                "Download Machine CSV",
                csv,
                "seal_test_sequence.csv"
            )

# =====================================================

if __name__ == "__main__":
    main()
