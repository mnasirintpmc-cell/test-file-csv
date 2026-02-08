import streamlit as st
import pandas as pd
import io
import os
import numpy as np
from datetime import datetime

# =====================================================
# HARDWARE SAFETY LIMITS & CONFIG
# =====================================================
MAX_CELL_PRESSURE = 450.0
MAX_SPEED_RPM = 32000.0
DIFF_TARGET = 0.95  # Interface must be 95% of Cell (5% less)

# THE STRICT PLC COLUMN ORDER (DO NOT CHANGE)
MACHINE_COLUMNS = [
    'TST_SpeedDem', 'TST_CellPresDemand', 'TST_InterPresDemand', 
    'TST_InterBPDemand_DE', 'TST_InterBPDemand_NDE', 'TST_GasInjectionDemand',
    'TST_StepDuration', 'TST_APFlag', 'TST_TempDemand', 'TST_GasType',
    'TST_TestMode', 'TST_MeasurementReq', 'TST_TorqueCheck'
]

COLUMN_MAPPING = {
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

# =====================================================
# CORE FUNCTIONS
# =====================================================

def highlight_errors(row):
    """Applies red background to cells violating hardware safety limits."""
    formats = [''] * len(row)
    cols = row.index.tolist()
    
    # Speed Check
    if row['Speed_RPM'] > MAX_SPEED_RPM:
        formats[cols.index('Speed_RPM')] = 'background-color: #9e1a1a; color: white;'
    
    # Cell Pressure Check
    if row['Cell_Pressure_bar'] > MAX_CELL_PRESSURE:
        formats[cols.index('Cell_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
    
    # Differential Check (95% of Cell)
    expected = row['Cell_Pressure_bar'] * DIFF_TARGET
    if abs(row['Interface_Pressure_bar'] - expected) > 0.5:
        formats[cols.index('Interface_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
        
    return formats

def convert_to_machine_safe(df):
    """Reconstructs the CSV in the exact physical index order the PLC expects."""
    # 1. Reverse Map
    rev_map = {v: k for k, v in COLUMN_MAPPING.items()}
    m_df = df.rename(columns=rev_map)
    
    # 2. Logic Clean (Yes/No -> 1/0)
    for col in ['TST_APFlag', 'TST_MeasurementReq', 'TST_TorqueCheck']:
        if col in m_df.columns:
            m_df[col] = m_df[col].map({'Yes': 1, 'No': 0, 1: 1, 0: 0}).fillna(0).astype(int)

    # 3. Force Column Sequence
    final_df = pd.DataFrame()
    for col in MACHINE_COLUMNS:
        final_df[col] = m_df[col] if col in m_df.columns else 0
        
    return final_df

# =====================================================
# STREAMLIT APP
# =====================================================

def main():
    st.set_page_config(page_title="Seal Test Safe-Manager", layout="wide")
    st.title("🛡️ Secure Seal Test Bed Manager")
    
    # Sidebar Info
    st.sidebar.header("Hardware Safety Limits")
    st.sidebar.write(f"🚫 Max Cell: {MAX_CELL_PRESSURE} bar")
    st.sidebar.write(f"🚫 Max Speed: {MAX_SPEED_RPM} RPM")
    st.sidebar.write(f"⚠️ Differential: Interface = {DIFF_TARGET*100}% of Cell")

    # Initial Data state
    if 'test_data' not in st.session_state:
        st.session_state.test_data = pd.DataFrame([{
            'Step': 1, 'Speed_RPM': 0, 'Cell_Pressure_bar': 0, 
            'Interface_Pressure_bar': 0, 'BP_Drive_End_bar': 0, 
            'BP_Non_Drive_End_bar': 0, 'Gas_Injection_bar': 0, 
            'Duration_s': 60, 'Auto_Proceed': 'No', 'Notes': ''
        }])

    # 1. Input Section
    st.subheader("1. Sequence Editor")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("➕ Add Test Step"):
            new_row = st.session_state.test_data.iloc[[-1]].copy()
            new_row['Step'] = len(st.session_state.test_data) + 1
            st.session_state.test_data = pd.concat([st.session_state.test_data, new_row], ignore_index=True)
            st.rerun()
            
        if st.button("🛠️ Auto-Fix Differential"):
            st.session_state.test_data['Interface_Pressure_bar'] = st.session_state.test_data['Cell_Pressure_bar'] * DIFF_TARGET
            st.success("All Interface Pressures set to 95% of Cell Pressure.")
            st.rerun()

    with col1:
        edited_df = st.data_editor(
            st.session_state.test_data, 
            use_container_width=True, 
            num_rows="dynamic",
            key="main_editor"
        )
        st.session_state.test_data = edited_df

    # 2. Safety View (The Highlighted Table)
    st.subheader("2. Safety Verification")
    
    
    styled_df = edited_df.style.apply(highlight_errors, axis=1)
    st.dataframe(styled_df, use_container_width=True)

    # Error Summary
    speed_errs = (edited_df['Speed_RPM'] > MAX_SPEED_RPM).sum()
    press_errs = (edited_df['Cell_Pressure_bar'] > MAX_CELL_PRESSURE).sum()
    
    if speed_errs > 0 or press_errs > 0:
        st.error(f"🚨 HAZARD DETECTED: {speed_errs} Speed violations and {press_errs} Pressure violations marked in RED.")
    else:
        st.success("✅ Sequence is within mechanical design limits.")

    # 3. Export
    st.subheader("3. Hardware Export")
    
    c1, c2 = st.columns(2)
    
    with c1:
        # Machine CSV Export
        machine_df = convert_to_machine_safe(edited_df)
        csv_buffer = machine_df.to_csv(index=False, sep=';')
        st.download_button(
            "📥 Download Machine CSV (PLC-READY)",
            csv_buffer,
            "test_bed_upload.csv",
            "text/csv",
            use_container_width=True
        )
        st.caption("Warning: Ensure columns match your PLC Registry map.")

    with c2:
        # Professional Excel Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='Sequence')
        st.download_button(
            "📥 Download Technician Excel",
            output.getvalue(),
            "technician_report.xlsx",
            "application/vnd.ms-excel",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
