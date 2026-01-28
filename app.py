import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

# =========================================================
# SESSION HELPERS (MINIMAL & SAFE)
# =========================================================

def persist(key, value):
    if value is not None:
        st.session_state[key] = value

def get(key):
    return st.session_state.get(key, None)

def reset_editor(key, df):
    if key not in st.session_state or st.session_state[key].shape != df.shape:
        st.session_state[key] = df.copy()

# =========================================================
# CSV SAFE READER
# =========================================================

def safe_read_csv(file_path_or_buffer):
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    file_path_or_buffer,
                    delimiter=';',
                    encoding=encoding,
                    na_values=['NaN','NAN','nan','INF','INFINITY','inf','infinity','',' ','NULL','null'],
                    keep_default_na=True,
                    skipinitialspace=True
                )
                df = df.replace([np.nan, math.inf, -math.inf], 0)
                return df
            except Exception:
                continue

        df = pd.read_csv(file_path_or_buffer, delimiter=';')
        return df.replace([np.nan, math.inf, -math.inf], 0)

    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")
        return pd.DataFrame()

# =========================================================
# FILE TYPE DETECTION
# =========================================================

def detect_file_type(df):
    if df.empty:
        return "unknown"

    cols = df.columns.tolist()

    if "TST_CellPresDemand" in cols:
        return "main_seal"
    if "TST_SepSealFlwSet1" in cols:
        return "separation_seal"
    if "Cell_Pressure_bar" in cols:
        return "main_seal"
    if "Sep_Seal_Flow_Set1" in cols:
        return "separation_seal"

    return "unknown"

# =========================================================
# COLUMN MAPPINGS (UNCHANGED LOGIC)
# =========================================================

def get_column_mapping(file_type):
    if file_type == "main_seal":
        return {
            "technician_to_machine": {
                "Speed_RPM": "TST_SpeedDem",
                "Cell_Pressure_bar": "TST_CellPresDemand",
                "Interface_Pressure_bar": "TST_InterPresDemand",
                "BP_Drive_End_bar": "TST_InterBPDemand_DE",
                "BP_Non_Drive_End_bar": "TST_InterBPDemand_NDE",
                "Gas_Injection_bar": "TST_GasInjectionDemand",
                "Duration_s": "TST_StepDuration",
                "Auto_Proceed": "TST_APFlag",
                "Temperature_C": "TST_TempDemand",
                "Gas_Type": "TST_GasType",
                "Test_Mode": "TST_TestMode",
                "Measurement": "TST_MeasurementReq",
                "Torque_Check": "TST_TorqueCheck"
            },
            "machine_to_technician": {
                "TST_SpeedDem": "Speed_RPM",
                "TST_CellPresDemand": "Cell_Pressure_bar",
                "TST_InterPresDemand": "Interface_Pressure_bar",
                "TST_InterBPDemand_DE": "BP_Drive_End_bar",
                "TST_InterBPDemand_NDE": "BP_Non_Drive_End_bar",
                "TST_GasInjectionDemand": "Gas_Injection_bar",
                "TST_StepDuration": "Duration_s",
                "TST_APFlag": "Auto_Proceed",
                "TST_TempDemand": "Temperature_C",
                "TST_GasType": "Gas_Type",
                "TST_TestMode": "Test_Mode",
                "TST_MeasurementReq": "Measurement",
                "TST_TorqueCheck": "Torque_Check"
            }
        }

    if file_type == "separation_seal":
        return {
            "technician_to_machine": {
                "Speed_RPM": "TST_SpeedDem",
                "Sep_Seal_Flow_Set1": "TST_SepSealFlwSet1",
                "Sep_Seal_Flow_Set2": "TST_SepSealFlwSet2",
                "Sep_Seal_Pressure_Set1": "TST_SepSealPSet1",
                "Sep_Seal_Pressure_Set2": "TST_SepSealPSet2",
                "Sep_Seal_Control_Type": "TST_SepSealControlTyp",
                "Duration_s": "TST_StepDuration",
                "Auto_Proceed": "TST_APFlag",
                "Temperature_C": "TST_TempDemand",
                "Gas_Type": "TST_GasType",
                "Measurement": "TST_MeasurementReq",
                "Torque_Check": "TST_TorqueCheck"
            },
            "machine_to_technician": {
                "TST_SpeedDem": "Speed_RPM",
                "TST_SepSealFlwSet1": "Sep_Seal_Flow_Set1",
                "TST_SepSealFlwSet2": "Sep_Seal_Flow_Set2",
                "TST_SepSealPSet1": "Sep_Seal_Pressure_Set1",
                "TST_SepSealPSet2": "Sep_Seal_Pressure_Set2",
                "TST_SepSealControlTyp": "Sep_Seal_Control_Type",
                "TST_StepDuration": "Duration_s",
                "TST_APFlag": "Auto_Proceed",
                "TST_TempDemand": "Temperature_C",
                "TST_GasType": "Gas_Type",
                "TST_MeasurementReq": "Measurement",
                "TST_TorqueCheck": "Torque_Check"
            }
        }

    return None

# =========================================================
# VALUE CONVERSIONS
# =========================================================

def convert_to_readable_values(df, file_type):
    df = df.copy()

    for col in ["Auto_Proceed", "Measurement", "Torque_Check"]:
        if col in df.columns:
            df[col] = df[col].map({0: "No", 1: "Yes", "0": "No", "1": "Yes"}).fillna("No")

    if file_type == "main_seal" and "Test_Mode" in df.columns:
        df["Test_Mode"] = df["Test_Mode"].map({1: "Mode 1", 2: "Mode 2"}).fillna("Mode 1")

    return df

def convert_to_machine_codes(df, file_type):
    df = df.copy()

    for col in ["TST_APFlag", "TST_MeasurementReq", "TST_TorqueCheck"]:
        if col in df.columns:
            df[col] = df[col].map({"Yes": 1, "No": 0}).fillna(0)

    if file_type == "main_seal" and "TST_TestMode" in df.columns:
        df["TST_TestMode"] = df["TST_TestMode"].map({"Mode 1": 1, "Mode 2": 2}).fillna(1)

    return df

# =========================================================
# CONVERSION FUNCTIONS
# =========================================================

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    tech_df = df.rename(columns=mapping["machine_to_technician"])
    tech_df = convert_to_readable_values(tech_df, file_type)

    tech_df.insert(0, "Step", range(1, len(tech_df) + 1))
    if "Notes" not in tech_df.columns:
        tech_df["Notes"] = ""

    return tech_df

# =========================================================
# EDITABLE DATAFRAME (FIXED)
# =========================================================

def editable_dataframe(df, key, height=400):
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

# =========================================================
# MAIN APP
# =========================================================

def main():
    st.title("⚙️ Universal Seal Test Manager")

    st.sidebar.title("🔧 Operations")
    operation = st.sidebar.radio(
        "Choose Operation:",
        [
            "🔄 Excel to Machine CSV",
            "📤 Machine CSV to Excel",
            "👀 View Current Test"
        ]
    )

    # =====================================================
    # EXCEL → MACHINE CSV
    # =====================================================

    if operation == "🔄 Excel to Machine CSV":
        st.header("Excel → Machine CSV")

        uploaded_excel = st.file_uploader(
            "Upload Excel Template",
            type=["xlsx"],
            key="excel_upload"
        )
        persist("excel_file", uploaded_excel)

        excel_file = get("excel_file")
        if excel_file:
            df = pd.read_excel(excel_file, sheet_name="TEST_SEQUENCE")
            df = df.dropna(subset=["Step"]).reset_index(drop=True)

            file_type = detect_file_type(df)
            mapping = get_column_mapping(file_type)

            st.subheader("✏️ Editable Data")
            edited_df = editable_dataframe(df, "excel_editor")

            rename_dict = {
                tech: mach
                for tech, mach in mapping["technician_to_machine"].items()
                if tech in edited_df.columns
            }

            machine_df = edited_df.rename(columns=rename_dict)
            machine_df = convert_to_machine_codes(machine_df, file_type)
            machine_df = machine_df.drop(
                [c for c in ["Step", "Notes"] if c in machine_df.columns],
                axis=1
            )

            st.subheader("Machine CSV Preview")
            st.dataframe(machine_df, use_container_width=True)

            csv_data = machine_df.to_csv(index=False, sep=";")
            st.download_button(
                "📥 Download Machine CSV",
                csv_data,
                file_name=f"{file_type}_sequence_{datetime.now():%Y%m%d}.csv",
                mime="text/csv"
            )

    # =====================================================
    # MACHINE CSV → EXCEL
    # =====================================================

    elif operation == "📤 Machine CSV to Excel":
        st.header("Machine CSV → Excel")

        uploaded_csv = st.file_uploader(
            "Upload Machine CSV",
            type=["csv"],
            key="csv_upload"
        )
        persist("csv_file", uploaded_csv)

        csv_file = get("csv_file")
        if csv_file:
            df = safe_read_csv(csv_file)
            file_type = detect_file_type(df)

            tech_df = convert_machine_to_technician(df, file_type)

            st.subheader("✏️ Editable Data")
            edited_df = editable_dataframe(tech_df, "csv_editor")

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                edited_df.to_excel(writer, index=False, sheet_name="TEST_SEQUENCE")
            output.seek(0)

            st.download_button(
                "📥 Download Excel",
                output.getvalue(),
                file_name=f"{file_type}_professional_{datetime.now():%Y%m%d_%H%M}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # =====================================================
    # VIEW CURRENT TEST
    # =====================================================

    elif operation == "👀 View Current Test":
        st.header("View Current Test")

        file_name = st.selectbox(
            "Select Test File",
            ["MainSealSet2.csv", "SeperationSeal.csv", "SeperationSeal_Base.csv"]
        )

        if (
            "current_test_name" not in st.session_state
            or st.session_state["current_test_name"] != file_name
        ):
            df = safe_read_csv(file_name)
            st.session_state["current_test_df"] = df
            st.session_state["current_test_name"] = file_name

        df = st.session_state["current_test_df"]
        file_type = detect_file_type(df)

        tech_df = convert_machine_to_technician(df, file_type)
        edited_df = editable_dataframe(tech_df, "current_test_editor", height=500)

        st.success(f"Loaded {file_name} ({len(df)} steps)")

# =========================================================

if __name__ == "__main__":
    main()
