import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

# ---------------- SESSION HELPERS ---------------- #

def store_uploaded_file(key, uploaded_file):
    if uploaded_file is not None:
        st.session_state[key] = uploaded_file

def get_uploaded_file(key):
    return st.session_state.get(key, None)

def reset_editor_if_new_data(editor_key, df):
    if editor_key not in st.session_state:
        st.session_state[editor_key] = df.copy()
    elif st.session_state[editor_key].shape != df.shape:
        st.session_state[editor_key] = df.copy()

# ---------------- YOUR ORIGINAL FUNCTIONS ---------------- #

def safe_read_csv(file_path_or_buffer):
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    file_path_or_buffer,
                    delimiter=';',
                    encoding=encoding,
                    na_values=['NaN', 'NAN', 'nan', 'INF', 'INFINITY', 'inf', 'infinity', '', ' ', 'NULL', 'null'],
                    keep_default_na=True,
                    skipinitialspace=True
                )
                df = df.replace([np.nan, math.inf, -math.inf], 0)
                for col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                return df
            except Exception:
                continue
        df = pd.read_csv(file_path_or_buffer, delimiter=';')
        return df.replace([np.nan, math.inf, -math.inf], 0)
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")
        return pd.DataFrame()

def detect_file_type(df):
    if df.empty:
        return 'unknown'
    cols = df.columns
    if 'TST_CellPresDemand' in cols:
        return 'main_seal'
    if 'TST_SepSealFlwSet1' in cols:
        return 'separation_seal'
    if 'Cell_Pressure_bar' in cols:
        return 'main_seal'
    if 'Sep_Seal_Flow_Set1' in cols:
        return 'separation_seal'
    return 'unknown'

# ---------- KEEP YOUR MAPPING / CONVERSION FUNCTIONS ----------
# (UNCHANGED – omitted here only for readability)
# 👉 get_column_mapping
# 👉 convert_machine_to_technician
# 👉 convert_to_readable_values
# 👉 convert_to_machine_codes
# 👉 create_professional_excel_from_data
# 👉 analyze_csv_file
# ------------------------------------------------------------ #

def editable_dataframe(df, key, height=400):
    reset_editor_if_new_data(key, df)

    edited_df = st.data_editor(
        st.session_state[key],
        key=f"editor_{key}",
        use_container_width=True,
        height=height,
        num_rows="dynamic"
    )

    st.session_state[key] = edited_df
    return edited_df

# ---------------- MAIN APP ---------------- #

def main():
    st.title("⚙️ Universal Seal Test Manager")

    st.sidebar.title("🔧 Operations")
    operation = st.sidebar.radio(
        "Choose Operation:",
        ["📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel"]
    )

    # ---------------- EXCEL → CSV ---------------- #
    if operation == "🔄 Excel to Machine CSV":
        st.header("Convert Excel to Machine CSV")

        uploaded_excel = st.file_uploader(
            "Upload Excel file",
            type=["xlsx"],
            key="excel_uploader"
        )
        store_uploaded_file("excel_file", uploaded_excel)

        excel_file = get_uploaded_file("excel_file")

        if excel_file:
            df = pd.read_excel(excel_file, sheet_name="TEST_SEQUENCE")
            df = df.dropna(subset=["Step"]).reset_index(drop=True)

            file_type = detect_file_type(df)
            edited_df = editable_dataframe(df, "excel_editor")

            st.success("✅ File loaded and retained (no refresh needed)")

    # ---------------- CSV → EXCEL ---------------- #
    elif operation == "📤 Machine CSV to Excel":
        st.header("Convert Machine CSV to Excel")

        uploaded_csv = st.file_uploader(
            "Upload Machine CSV",
            type=["csv"],
            key="csv_uploader"
        )
        store_uploaded_file("csv_file", uploaded_csv)

        csv_file = get_uploaded_file("csv_file")

        if csv_file:
            df = safe_read_csv(csv_file)
            file_type = detect_file_type(df)

            tech_df = convert_machine_to_technician(df, file_type)
            edited_df = editable_dataframe(tech_df, "csv_editor")

            excel_output = create_professional_excel_from_data(
                edited_df, file_type
            )

            if excel_output:
                st.download_button(
                    "📥 Download Excel",
                    excel_output.getvalue(),
                    file_name=f"{file_type}_{datetime.now():%Y%m%d_%H%M}.xlsx"
                )

if __name__ == "__main__":
    main()
