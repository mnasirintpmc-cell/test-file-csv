import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

# =====================================================
# SESSION HELPERS
# =====================================================

def persist(key, value):
    if value is not None:
        st.session_state[key] = value

def reset_editor(key, df):
    if key not in st.session_state or st.session_state[key].shape != df.shape:
        st.session_state[key] = df.copy()

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path_or_buffer):
    try:
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
        for enc in encodings:
            try:
                df = pd.read_csv(
                    file_path_or_buffer,
                    sep=";",
                    encoding=enc,
                    na_values=["NaN","NAN","nan","INF","INFINITY","inf","", "NULL", "null"]
                )
                return df.replace([np.nan, math.inf, -math.inf], 0)
            except Exception:
                pass
        return pd.read_csv(file_path_or_buffer, sep=";")
    except Exception as e:
        st.error(str(e))
        return pd.DataFrame()

# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):
    cols = df.columns.tolist()
    if "TST_CellPresDemand" in cols or "Cell_Pressure_bar" in cols:
        return "main_seal"
    if "TST_SepSealFlwSet1" in cols or "Sep_Seal_Flow_Set1" in cols:
        return "separation_seal"
    return "unknown"

# =====================================================
# COLUMN MAPPINGS
# =====================================================

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

# =====================================================
# VALUE CONVERSIONS
# =====================================================

def convert_to_machine_codes(df, file_type):
    df = df.copy()
    for col in ["TST_APFlag", "TST_MeasurementReq", "TST_TorqueCheck"]:
        if col in df.columns:
            df[col] = df[col].map({"Yes": 1, "No": 0}).fillna(0)
    if "TST_TestMode" in df.columns:
        df["TST_TestMode"] = df["TST_TestMode"].map({"Mode 1": 1, "Mode 2": 2}).fillna(1)
    return df

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    tech_df = df.rename(columns=mapping["machine_to_technician"])
    tech_df.insert(0, "Step", range(1, len(tech_df) + 1))
    if "Notes" not in tech_df.columns:
        tech_df["Notes"] = ""
    return tech_df

# =====================================================
# EDITABLE DATAFRAME
# =====================================================

def editable_dataframe(df, key, height=450):
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
# SIMPLE EXCEL EXPORT
# =====================================================

def export_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="TEST_SEQUENCE")
    buf.seek(0)
    return buf

# =====================================================
# MAIN APP
# =====================================================

def main():
    st.title("⚙️ Universal Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        [
            "🔄 Excel to Machine CSV",
            "📤 Machine CSV to Excel",
            "👀 View Current Test"
        ]
    )

    # =================================================
    # EXCEL → MACHINE CSV
    # =================================================
    if operation == "🔄 Excel to Machine CSV":
        uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
        persist("excel_file", uploaded)

        if "excel_file" in st.session_state:
            df = pd.read_excel(st.session_state["excel_file"], sheet_name="TEST_SEQUENCE")
            df = df.dropna(subset=["Step"]).reset_index(drop=True)
            file_type = detect_file_type(df)
            mapping = get_column_mapping(file_type)

            edited_df = editable_dataframe(df, "excel_editor")

            rename = {k: v for k, v in mapping["technician_to_machine"].items() if k in edited_df.columns}
            machine_df = edited_df.rename(columns=rename)
            machine_df = convert_to_machine_codes(machine_df, file_type)
            machine_df = machine_df.drop(columns=[c for c in ["Step", "Notes"] if c in machine_df.columns])

            st.download_button(
                "📥 Download Machine CSV",
                machine_df.to_csv(index=False, sep=";"),
                file_name="machine_sequence.csv",
                mime="text/csv"
            )

    # =================================================
    # MACHINE CSV → EXCEL
    # =================================================
    elif operation == "📤 Machine CSV to Excel":
        uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])
        persist("csv_file", uploaded)

        if "csv_file" in st.session_state:
            df = safe_read_csv(st.session_state["csv_file"])
            file_type = detect_file_type(df)

            tech_df = convert_machine_to_technician(df, file_type)
            edited_df = editable_dataframe(tech_df, "csv_editor")

            excel = export_excel(edited_df)
            st.download_button(
                "📥 Download Excel",
                excel,
                file_name="converted_test.xlsx"
            )

    # =================================================
    # VIEW + EDIT CURRENT TEST (LIVE DOWNLOAD)
    # =================================================
    elif operation == "👀 View Current Test":
        file_name = st.selectbox(
            "Select CSV",
            ["MainSealSet2.csv", "SeperationSeal.csv", "SeperationSeal_Base.csv"]
        )

        if "current_name" not in st.session_state or st.session_state["current_name"] != file_name:
            st.session_state["current_df"] = safe_read_csv(file_name)
            st.session_state["current_name"] = file_name

        df = st.session_state["current_df"]
        file_type = detect_file_type(df)

        tech_df = convert_machine_to_technician(df, file_type)
        edited_df = editable_dataframe(tech_df, "current_editor", 500)

        col1, col2 = st.columns(2)

        with col1:
            excel = export_excel(edited_df)
            st.download_button(
                "📥 Download Excel (Edited)",
                excel,
                file_name="edited_current_test.xlsx"
            )

        with col2:
            mapping = get_column_mapping(file_type)
            rename = {k: v for k, v in mapping["technician_to_machine"].items() if k in edited_df.columns}
            machine_df = edited_df.rename(columns=rename)
            machine_df = convert_to_machine_codes(machine_df, file_type)
            machine_df = machine_df.drop(columns=[c for c in ["Step", "Notes"] if c in machine_df.columns])

            st.download_button(
                "📥 Download Machine CSV (Edited)",
                machine_df.to_csv(index=False, sep=";"),
                file_name="edited_current_test.csv",
                mime="text/csv"
            )

# =====================================================

if __name__ == "__main__":
    main()
