import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math
import os

# =====================================================
# SAFETY LIMITS
# =====================================================
MAX_CELL_PRESSURE = 450.0
MAX_SPEED_RPM = 32000.0
DIFF_TARGET = 0.95 

# =====================================================
# UTILITIES
# =====================================================

def safe_read_csv(file_path_or_buffer):
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                df = pd.read_csv(
                    file_path_or_buffer,
                    delimiter=';',
                    encoding=enc,
                    na_values=['NaN','NAN','nan','inf',''],
                    keep_default_na=True
                )
                return df.replace([np.nan, math.inf, -math.inf], 0)
            except:
                continue
        return pd.read_csv(file_path_or_buffer, delimiter=';')
    except Exception as e:
        st.error(f"Read error: {e}")
        return pd.DataFrame()

def detect_file_type(df):
    if 'TST_CellPresDemand' in df.columns or 'Cell_Pressure_bar' in df.columns:
        return 'main_seal'
    return 'separation_seal'

def get_column_mapping(file_type):
    if file_type == 'main_seal':
        return {
            'm_to_t': {
                'TST_SpeedDem': 'Speed_RPM',
                'TST_CellPresDemand': 'Cell_Pressure_bar',
                'TST_InterPresDemand': 'Interface_Pressure_bar',
                'TST_InterBPDemand_DE': 'BP_Drive_End_bar',
                'TST_InterBPDemand_NDE': 'BP_Non_Drive_End_bar',
                'TST_GasInjectionDemand': 'Gas_Injection_bar',
                'TST_StepDuration': 'Duration_s',
                'TST_APFlag': 'Auto_Proceed',
                'TST_TempDemand': 'Temperature_C',
                'TST_GasType': 'Gas_Type',
                'TST_TestMode': 'Test_Mode',
                'TST_MeasurementReq': 'Measurement',
                'TST_TorqueCheck': 'Torque_Check'
            },
            't_to_m': {
                'Speed_RPM': 'TST_SpeedDem',
                'Cell_Pressure_bar': 'TST_CellPresDemand',
                'Interface_Pressure_bar': 'TST_InterPresDemand',
                'BP_Drive_End_bar': 'TST_InterBPDemand_DE',
                'BP_Non_Drive_End_bar': 'TST_InterBPDemand_NDE',
                'Gas_Injection_bar': 'TST_GasInjectionDemand',
                'Duration_s': 'TST_StepDuration',
                'Auto_Proceed': 'TST_APFlag',
                'Temperature_C': 'TST_TempDemand',
                'Gas_Type': 'TST_GasType',
                'Test_Mode': 'TST_TestMode',
                'Measurement': 'TST_MeasurementReq',
                'Torque_Check': 'TST_TorqueCheck'
            }
        }
    # (Separation seal mapping logic remains identical)
    return None

# =====================================================
# SAFETY HIGHLIGHTING
# =====================================================

def apply_safety_styles(row):
    styles = [''] * len(row)
    cols = row.index.tolist()
    if 'Speed_RPM' in cols and row['Speed_RPM'] > MAX_SPEED_RPM:
        styles[cols.index('Speed_RPM')] = 'background-color: #9e1a1a; color: white;'
    if 'Cell_Pressure_bar' in cols and row['Cell_Pressure_bar'] > MAX_CELL_PRESSURE:
        styles[cols.index('Cell_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
    if 'Cell_Pressure_bar' in cols and 'Interface_Pressure_bar' in cols:
        expected = row['Cell_Pressure_bar'] * DIFF_TARGET
        if abs(row['Interface_Pressure_bar'] - expected) > 0.5:
            styles[cols.index('Interface_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
    return styles

# =====================================================
# THE FIX: PERSISTENT EDITOR
# =====================================================

def persistent_editor(df, key):
    # Only load data into state if it's the first time or a NEW file is uploaded
    if key not in st.session_state:
        st.session_state[key] = df.copy()

    st.write("### 🛡️ Safety Preview")
    # Show the highlighted view (Static)
    st.dataframe(st.session_state[key].style.apply(apply_safety_styles, axis=1), use_container_width=True)

    with st.form(f"form_{key}"):
        # Edit the copy in session state
        edited = st.data_editor(
            st.session_state[key],
            use_container_width=True,
            num_rows="dynamic",
            key=f"widget_{key}"
        )
        save_btn = st.form_submit_button("✅ Save Changes & Verify")

    if save_btn:
        st.session_state[key] = edited
        st.success("Changes Saved Locally!")
        st.rerun()

    return st.session_state[key]

# =====================================================
# MAIN APP
# =====================================================

def main():
    st.set_page_config(layout="wide")
    st.title("⚙️ Universal Seal Test Manager")

    operation = st.sidebar.radio("Operation", ["📥 Download Template", "🔄 Excel to Machine CSV", "📤 Machine CSV to Excel", "👀 View Current Test"])

    if operation == "📥 Download Template":
        seal = st.selectbox("Seal Type", ["Main Seal", "Separation Seal"])
        csv_file = "MainSealSet2.csv" if seal == "Main Seal" else "SeperationSeal.csv"
        if os.path.exists(csv_file):
            df = safe_read_csv(csv_file)
            st.download_button("📥 Download Excel Template", df.to_csv(index=False, sep=';'), "template.csv")

    elif operation == "🔄 Excel to Machine CSV":
        uploaded = st.file_uploader("Upload Excel", type=['xlsx'])
        if uploaded:
            # We use a combined key of file name + size to detect a NEW upload
            state_key = f"data_{uploaded.name}"
            raw_df = pd.read_excel(uploaded, sheet_name='TEST_SEQUENCE')
            
            # The editor handles saving to session_state
            working_df = persistent_editor(raw_df, state_key)
            
            f_type = detect_file_type(working_df)
            mapping = get_column_mapping(f_type)
            
            if st.button("🚀 Prepare Machine Download"):
                # Ensure we map back to TST_ codes before download
                final_csv = working_df.rename(columns=mapping['t_to_m']).to_csv(index=False, sep=';')
                st.download_button("📥 Click here to Download CSV", final_csv, f"{f_type}_final.csv")

    elif operation == "👀 View Current Test":
        seal = st.selectbox("Seal Type", ["Main Seal", "Separation Seal"])
        csv_file = "MainSealSet2.csv" if seal == "Main Seal" else "SeperationSeal.csv"
        if os.path.exists(csv_file):
            raw_df = safe_read_csv(csv_file)
            # Use a static key so edits persist while clicking around
            persistent_editor(raw_df, f"view_{seal}")

if __name__ == "__main__":
    main()
