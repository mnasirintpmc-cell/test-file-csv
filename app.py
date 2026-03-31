import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import hashlib
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
# BUILD MACHINE CSV
# =====================================================

def build_machine_csv(df):

    df = df.copy()

    machine_df = pd.DataFrame({

        "TST_SpeedDem": df.get("Speed_RPM", 0),
        "TST_CellPresDemand": df.get("Primary seal Gas Pressure (barg)", 0),
        "TST_InterPresDemand": df.get("Interspace_Pressure_bar", 0),
        "TST_InterBPDemand_DE": df.get("BackPressure_Drive_End_bar", 0),
        "TST_InterBPDemand_NDE": df.get("BackPressure_Non_Drive_End_bar", 0),
        "TST_GasInjectionDemand": df.get("Gas_Injection_bar", 0),
        "TST_StepDuration": df.get("Duration_s", 0),
        "TST_APFlag": df.get("Acceptance point", 0),
        "TST_TempDemand": df.get("Temperature_C", 0),
        "TST_GasType": df.get("Gas_Type", "Air"),
        "TST_TestMode": df.get("Test_Mode", 1),
        "TST_MeasurementReq": df.get("Measurement", 1),
        "TST_TorqueCheck": df.get("Torque_Check", 0)

    })

    numeric_cols = [
        "TST_SpeedDem","TST_CellPresDemand","TST_InterPresDemand",
        "TST_InterBPDemand_DE","TST_InterBPDemand_NDE",
        "TST_GasInjectionDemand","TST_StepDuration",
        "TST_APFlag","TST_TempDemand",
        "TST_TestMode","TST_MeasurementReq","TST_TorqueCheck"
    ]

    for col in numeric_cols:
        machine_df[col] = (
            machine_df[col]
            .astype(str)
            .str.replace("≥","",regex=False)
            .str.replace(">=","",regex=False)
            .str.replace("<=","",regex=False)
            .str.replace(">","",regex=False)
            .str.replace("<","",regex=False)
            .str.strip()
        )
        machine_df[col] = pd.to_numeric(machine_df[col],errors="coerce").fillna(0)

    machine_df["TST_GasType"] = machine_df["TST_GasType"].fillna("Air")

    extra_cols = [col for col in df.columns if col.startswith("TST_")]

    for col in extra_cols:
        if col not in machine_df.columns:
            machine_df[col] = df[col]

    return machine_df


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
    }


# =====================================================
# EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(df,file_type,user_name="",source_name=""):

    df = df.replace({np.nan:""})
    output = io.BytesIO()

    logo_path = os.path.join(os.path.dirname(__file__),"company_logo.png")

    with pd.ExcelWriter(output,engine="xlsxwriter") as writer:

        df.to_excel(writer,sheet_name="TEST_SEQUENCE",index=False)

        wb = writer.book
        ws = writer.sheets["TEST_SEQUENCE"]

        header = wb.add_format({
            "bold":True,"align":"center","border":1,
            "fg_color":"#366092","font_color":"white"
        })

        cell = wb.add_format({"border":1,"align":"center"})
        notes = wb.add_format({"border":1,"align":"left"})

        for c,col in enumerate(df.columns):
            ws.write(0,c,col,header)

        for r in range(1,len(df)+1):
            for c,col in enumerate(df.columns):
                val = df.iloc[r-1,c]
                if pd.isna(val):
                    val = ""
                ws.write(r,c,val,notes if col=="Notes" else cell)

        ws.set_column(0,len(df.columns)-1,18)

        instr = wb.add_worksheet("INSTRUCTIONS")

        if os.path.exists(logo_path):
            instr.set_row(0,120)
            instr.insert_image("A1",logo_path,{"x_scale":0.6,"y_scale":0.6})

        instr.write(10,1,f"Operator: {user_name}")
        instr.write(11,1,f"Source File: {source_name}")
        instr.write(12,1,"SEAL TEST SEQUENCE")
        instr.write(14,1,"1. Edit sequence as required")
        instr.write(15,1,"2. Maintain safe pressure relationships")
        instr.write(16,1,"3. Upload file back to system")

        instr.protect()

    output.seek(0)
    return output


# =====================================================
# EDITABLE TABLE
# =====================================================

def editable_dataframe(df):

    if st.session_state.df_state is None:
        st.session_state.df_state = df.copy()

    new_col = st.text_input("Add new TST column (exact name)")

    if st.button("Add Column"):

        if new_col:

            new_col = new_col.strip()

            if not new_col.startswith("TST_"):
                st.warning("Column must start with TST_")

            elif new_col in st.session_state.df_state.columns:
                st.warning("Column already exists")

            else:
                st.session_state.df_state[new_col] = 0
                st.success(f"{new_col} added")

    edited = st.data_editor(
        st.session_state.df_state,
        use_container_width=True,
        key="data_editor"
    )

    st.session_state.df_state = edited

    warnings = validate_sequence(edited)

    if warnings:
        st.error("Safety interlock violations detected")
        for w in warnings:
            st.warning(w)

    return edited


# =====================================================
# MAIN APP
# =====================================================

def main():

    st.title("⚙️ DGS Test Manager")

    if "df_state" not in st.session_state:
        st.session_state.df_state = None

    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    user_name = st.sidebar.text_input("Operator Name")

    operation = st.sidebar.radio(
        "Operation",
        ["CSV → Excel","Excel → CSV","Spec → Technician Excel"]
    )

# CSV → Excel
    if operation=="CSV → Excel":

        uploaded = st.file_uploader("Upload Machine CSV",type=["csv"])

        if uploaded:

            df = safe_read_csv(uploaded)

            excel = create_professional_excel_from_data(
                df,"main_seal",
                user_name=user_name,
                source_name=uploaded.name
            )

            st.download_button(
                "Download Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )

# Excel → CSV
    elif operation=="Excel → CSV":

        uploaded = st.file_uploader("Upload Technician Excel",type=["xlsx"])

        if uploaded:

            df = pd.read_excel(uploaded)

            file_hash = hashlib.md5(uploaded.getvalue()).hexdigest()

            if st.session_state.last_uploaded_file != file_hash:
                st.session_state.df_state = df.copy()
                st.session_state.last_uploaded_file = file_hash

            edited = editable_dataframe(df)

            machine_df = build_machine_csv(edited)

            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False, sep=";"),
                file_name="machine_sequence.csv"
            )

# Spec → Technician
    elif operation=="Spec → Technician Excel":

        uploaded = st.file_uploader(
            "Upload Spec (.xlsb, .xlsm, .xlsx)",
            type=["xlsb","xlsm","xlsx"]
        )

        if uploaded:

            spec_df = scan_spec(uploaded)

            file_hash = hashlib.md5(uploaded.getvalue()).hexdigest()

            if st.session_state.last_uploaded_file != file_hash:
                st.session_state.df_state = spec_df.copy()
                st.session_state.last_uploaded_file = file_hash

            edited = editable_dataframe(spec_df)

            excel = create_professional_excel_from_data(
                edited,
                "main_seal",
                user_name=user_name,
                source_name=uploaded.name
            )

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )


if __name__=="__main__":
    main()
