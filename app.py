import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import hashlib
from spec_scanner import scan_spec
from validator import validate_sequence


# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path_or_buffer):

    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for enc in encodings:
        try:
            df = pd.read_csv(file_path_or_buffer, delimiter=";", encoding=enc)
            return df
        except:
            continue

    st.error("CSV read error")
    return pd.DataFrame()


# =====================================================
# BUILD MACHINE CSV with FlowLimits mapping
# =====================================================

def build_machine_csv(df):

    df = df.copy()

    def safe_col(name):
        return df[name] if name in df.columns else pd.Series([np.nan] * len(df))

    machine_df = pd.DataFrame({
        "TST_SpeedDem": safe_col("Speed_RPM"),
        "TST_CellPresDemand": safe_col("Primary seal Gas Pressure (barg)"),
        "TST_InterPresDemand": safe_col("Interspace_Pressure_bar"),
        "TST_InterBPDemand_DE": safe_col("BackPressure_Drive_End_bar"),
        "TST_InterBPDemand_NDE": safe_col("BackPressure_Non_Drive_End_bar"),
        "TST_GasInjectionDemand": safe_col("Gas_Injection_bar"),
        "TST_StepDuration": safe_col("Duration_s"),
        "TST_APFlag": safe_col("Acceptance point"),
        "TST_TempDemand": safe_col("Temperature_C"),
        "TST_GasType": safe_col("Gas_Type"),
        "TST_TestMode": safe_col("Test_Mode"),
        "TST_MeasurementReq": safe_col("Measurement"),
        "TST_TorqueCheck": safe_col("Torque_Check"),
    })

    # --- Add Flow Limits if they exist ---
    if "ISFlowLimits" in df.columns:
        machine_df["TST_ISFlowLimits"] = df["ISFlowLimits"]
    if "OBFlowLimits" in df.columns:
        machine_df["TST_OBFlowLimits"] = df["OBFlowLimits"]

    numeric_cols = [
        "TST_SpeedDem", "TST_CellPresDemand", "TST_InterPresDemand",
        "TST_InterBPDemand_DE", "TST_InterBPDemand_NDE",
        "TST_GasInjectionDemand", "TST_StepDuration", "TST_APFlag",
        "TST_TempDemand", "TST_TestMode", "TST_MeasurementReq", "TST_TorqueCheck"
    ]

    for col in numeric_cols:

        series = machine_df[col].astype(str).str.strip()

        if col == "TST_TempDemand":

            series = series.replace({"AMB": "30", "amb": "30"})
            greater_mask = series.str.contains(">", regex=False)
            less_mask = series.str.contains("<", regex=False)

            series = (
                series.str.replace("≥", "", regex=False)
                .str.replace(">=", "", regex=False)
                .str.replace("<=", "", regex=False)
                .str.replace(">", "", regex=False)
                .str.replace("<", "", regex=False)
            )

            series = pd.to_numeric(series, errors="coerce")
            series.loc[greater_mask] = series.loc[greater_mask] + 1
            series.loc[less_mask] = series.loc[less_mask] - 1
            machine_df[col] = series

        else:
            series = (
                series.str.replace("≥", "", regex=False)
                .str.replace(">=", "", regex=False)
                .str.replace("<=", "", regex=False)
                .str.replace(">", "", regex=False)
                .str.replace("<", "", regex=False)
            )
            machine_df[col] = pd.to_numeric(series, errors="coerce")

    machine_df["TST_GasType"] = machine_df["TST_GasType"].fillna("Air")

    # preserve extra TST columns
    extra_cols = [col for col in df.columns if col.startswith("TST_")]
    for col in extra_cols:
        if col not in machine_df.columns:
            machine_df[col] = df[col]

    return machine_df


# =====================================================
# SUPPORTING MAPPINGS
# =====================================================

def detect_file_type(df):
    cols = df.columns.tolist()
    if "TST_CellPresDemand" in cols or "Primary seal Gas Pressure (barg)" in cols:
        return "main_seal"
    return "unknown"


def get_column_mapping():
    return {
        "TST_SpeedDem": "Speed_RPM",
        "TST_CellPresDemand": "Primary seal Gas Pressure (barg)",
        "TST_InterPresDemand": "Interspace_Pressure_bar",
        "TST_InterBPDemand_DE": "BackPressure_Drive_End_bar",
        "TST_InterBPDemand_NDE": "BackPressure_Non_Drive_End_bar",
        "TST_GasInjectionDemand": "Gas_Injection_bar",
        "TST_StepDuration": "Duration_s",
        "TST_APFlag": "Acceptance point",
        "TST_TempDemand": "Temperature_C",
        "TST_GasType": "Gas_Type",
        "TST_TestMode": "Test_Mode",
        "TST_MeasurementReq": "Measurement",
        "TST_TorqueCheck": "Torque_Check",
    }


# =====================================================
# EXCEL CREATOR – ensures FlowLimits visible columns
# =====================================================

def create_professional_excel_from_data(df, file_type, user_name="", source_name=""):

    df = df.replace({np.nan: ""})

    # ensure columns exist and visible
    if "ISFlowLimits" in df.columns or "OBFlowLimits" in df.columns:
        base_cols = df.columns.tolist()
        for col in ["ISFlowLimits", "OBFlowLimits"]:
            if col not in base_cols:
                df[col] = ""
        if not base_cols[-2:] == ["ISFlowLimits", "OBFlowLimits"]:
            df = df[[c for c in base_cols if c not in ["ISFlowLimits", "OBFlowLimits"]] + ["ISFlowLimits", "OBFlowLimits"]]

    output = io.BytesIO()
    logo_path = os.path.join(os.path.dirname(__file__), "company_logo.png")

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="TEST_SEQUENCE", index=False)
        wb = writer.book
        ws = writer.sheets["TEST_SEQUENCE"]

        header = wb.add_format({
            "bold": True, "align": "center", "border": 1,
            "fg_color": "#366092", "font_color": "white"
        })
        cell = wb.add_format({"border": 1, "align": "center"})
        notes = wb.add_format({"border": 1, "align": "left"})

        for c, col in enumerate(df.columns):
            ws.write(0, c, col, header)

        for r in range(1, len(df) + 1):
            for c, col in enumerate(df.columns):
                val = df.iloc[r - 1, c]
                if pd.isna(val):
                    val = ""
                ws.write(r, c, val, notes if col == "Notes" else cell)

        ws.set_column(0, len(df.columns) - 1, 18)

        instr = wb.add_worksheet("INSTRUCTIONS")

        if os.path.exists(logo_path):
            instr.set_row(0, 120)
            instr.insert_image("A1", logo_path, {"x_scale": 0.6, "y_scale": 0.6})

        instr.write(10, 1, f"Operator: {user_name}")
        instr.write(11, 1, f"Source File: {source_name}")
        instr.write(12, 1, "SEAL TEST SEQUENCE")
        instr.write(14, 1, "1. Edit sequence as required")
        instr.write(15, 1, "2. Maintain safe pressure relationships")
        instr.write(16, 1, "3. Upload file back to system")

        instr.protect()

    output.seek(0)
    return output


# =====================================================
# EDITABLE STREAMLIT DF
# =====================================================

def editable_dataframe(df):

    if st.session_state.master_df is None:
        st.session_state.master_df = df.copy()

    new_col = st.text_input("Add new TST column (exact name)")

    if st.button("Add Column"):

        if new_col:
            new_col = new_col.strip()
            if not new_col.startswith("TST_"):
                st.warning("Column must start with TST_")
            elif new_col in st.session_state.master_df.columns:
                st.warning("Column already exists")
            else:
                st.session_state.master_df[new_col] = 0
                st.success(f"{new_col} added")

    edited = st.data_editor(
        st.session_state.master_df.copy(),
        use_container_width=True,
        key="data_editor",
        num_rows="dynamic",
    )

    master = st.session_state.master_df.copy()
    for col in edited.columns:
        if col not in master.columns:
            master[col] = edited[col]
    for col in master.columns:
        if col not in edited.columns:
            edited[col] = master[col]
    edited = edited[master.columns]

    st.session_state.master_df = edited.copy()

    warnings = validate_sequence(edited)
    if warnings:
        st.error("Safety interlock violations detected")
        for w in warnings:
            st.warning(w)

    return edited


# =====================================================
# MAIN STREAMLIT APP
# =====================================================

def main():
    st.title("⚙️ DGS Test Manager")

    if "master_df" not in st.session_state:
        st.session_state.master_df = None
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    user_name = st.sidebar.text_input("Operator Name")

    operation = st.sidebar.radio(
        "Operation",
        ["CSV → Excel", "Excel → CSV", "Spec → Technician Excel"]
    )

    if operation == "CSV → Excel":
        uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])
        if uploaded:
            df = safe_read_csv(uploaded)
            excel = create_professional_excel_from_data(
                df, "main_seal", user_name=user_name, source_name=uploaded.name
            )
            st.download_button(
                "Download Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )

    elif operation == "Excel → CSV":
        uploaded = st.file_uploader("Upload Technician Excel", type=["xlsx"])
        if uploaded:
            df = pd.read_excel(uploaded)
            file_hash = hashlib.md5(uploaded.getvalue()).hexdigest()
            if st.session_state.last_uploaded_file != file_hash:
                st.session_state.master_df = df.copy()
                st.session_state.last_uploaded_file = file_hash
            edited = editable_dataframe(df)
            machine_df = build_machine_csv(edited)
            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False, sep=";"),
                file_name="machine_sequence.csv"
            )

    elif operation == "Spec → Technician Excel":
        uploaded = st.file_uploader(
            "Upload Spec (.xlsb, .xlsm, .xlsx)", type=["xlsb", "xlsm", "xlsx"]
        )
        if uploaded:
            spec_df = scan_spec(uploaded)
            file_hash = hashlib.md5(uploaded.getvalue()).hexdigest()
            if st.session_state.last_uploaded_file != file_hash:
                st.session_state.master_df = spec_df.copy()
                st.session_state.last_uploaded_file = file_hash
            edited = editable_dataframe(spec_df)
            excel = create_professional_excel_from_data(
                edited, "main_seal", user_name=user_name, source_name=uploaded.name
            )
            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )


if __name__ == "__main__":
    main()
