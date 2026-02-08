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
DIFF_TARGET = 0.95 

# STRICT PLC COLUMN SEQUENCES
PLC_MAPS = {
    'main_seal': [
        'TST_SpeedDem', 'TST_CellPresDemand', 'TST_InterPresDemand', 
        'TST_InterBPDemand_DE', 'TST_InterBPDemand_NDE', 'TST_GasInjectionDemand',
        'TST_StepDuration', 'TST_APFlag', 'TST_TempDemand', 'TST_GasType',
        'TST_TestMode', 'TST_MeasurementReq', 'TST_TorqueCheck'
    ],
    'separation_seal': [
        'TST_SpeedDem', 'TST_SepSealFlwSet1', 'TST_SepSealFlwSet2',
        'TST_SepSealPSet1', 'TST_SepSealPSet2', 'TST_SepSealControlTyp',
        'TST_StepDuration', 'TST_APFlag', 'TST_TempDemand', 'TST_GasType',
        'TST_MeasurementReq', 'TST_TorqueCheck'
    ]
}

# USER-FRIENDLY NAMES
TECH_MAPS = {
    'main_seal': {
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
    'separation_seal': {
        'TST_SpeedDem': 'Speed_RPM',
        'TST_SepSealFlwSet1': 'Sep_Seal_Flow_Set1',
        'TST_SepSealFlwSet2': 'Sep_Seal_Flow_Set2',
        'TST_SepSealPSet1': 'Sep_Seal_Pressure_Set1',
        'TST_SepSealPSet2': 'Sep_Seal_Pressure_Set2',
        'TST_SepSealControlTyp': 'Sep_Seal_Control_Type',
        'TST_StepDuration': 'Duration_s',
        'TST_APFlag': 'Auto_Proceed',
        'TST_TempDemand': 'Temperature_C',
        'TST_GasType': 'Gas_Type',
        'TST_MeasurementReq': 'Measurement',
        'TST_TorqueCheck': 'Torque_Check'
    }
}

# =====================================================
# CORE UTILITIES
# =====================================================

def highlight_errors(row, seal_type):
    formats = [''] * len(row)
    cols = row.index.tolist()
    
    # Speed & Cell Check (Only for Main Seal / Standard columns)
    if 'Speed_RPM' in cols and row['Speed_RPM'] > MAX_SPEED_RPM:
        formats[cols.index('Speed_RPM')] = 'background-color: #9e1a1a; color: white;'
    
    if 'Cell_Pressure_bar' in cols:
        if row['Cell_Pressure_bar'] > MAX_CELL_PRESSURE:
            formats[cols.index('Cell_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
        
        # Differential Check (95% of Cell)
        if 'Interface_Pressure_bar' in cols:
            expected = row['Cell_Pressure_bar'] * DIFF_TARGET
            if abs(row['Interface_Pressure_bar'] - expected) > 0.5:
                formats[cols.index('Interface_Pressure_bar')] = 'background-color: #9e1a1a; color: white;'
        
    return formats

def safe_read_csv(file):
    try:
        df = pd.read_csv(file, delimiter=';', encoding='utf-8').fillna(0)
    except:
        df = pd.read_csv(file, delimiter=';', encoding='latin-1').fillna(0)
    return df

def detect_type(df):
    if 'TST_CellPresDemand' in df.columns or 'Cell_Pressure_bar' in df.columns:
        return 'main_seal'
    return 'separation_seal'

def convert_to_machine(df, seal_type):
    mapping = TECH_MAPS[seal_type]
    rev_map = {v: k for k, v in mapping.items()}
    m_df = df.rename(columns=rev_map)
    
    # Logic Fix
    for col in ['TST_APFlag', 'TST_MeasurementReq', 'TST_TorqueCheck']:
        if col in m_df.columns:
            m_df[col] = m_df[col].map({'Yes': 1, 'No': 0, 1: 1, 0: 0}).fillna(0).astype(int)

    final_df = pd.DataFrame()
    for col in PLC_MAPS[seal_type]:
        final_df[col] = m_df[col] if col in m_df.columns else 0
    return final_df

# =====================================================
# MAIN APP UI
# =====================================================

def main():
    st.set_page_config(page_title="Universal Seal Manager", layout="wide")
    st.title("⚙️ Universal Seal Test Manager")

    op = st.sidebar.radio("Operation", [
        "📥 Download Template", 
        "🔄 Excel to Machine CSV", 
        "📤 Machine CSV to Excel", 
        "👀 View Current Test"
    ])

    # --- OPERATION: DOWNLOAD TEMPLATE ---
    if op == "📥 Download Template":
        st.subheader("Get Hardware-Ready Templates")
        seal = st.selectbox("Seal Type", ["Main Seal", "Separation Seal"])
        s_type = "main_seal" if seal == "Main Seal" else "separation_seal"
        
        # Create empty template based on mapping
        cols = ["Step"] + list(TECH_MAPS[s_type].values()) + ["Notes"]
        template_df = pd.DataFrame(columns=cols)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            template_df.to_excel(writer, index=False, sheet_name='TEST_SEQUENCE')
        
        st.download_button("📥 Download Excel Template", output.getvalue(), f"{s_type}_template.xlsx")

    # --- OPERATION: EXCEL TO CSV ---
    elif op == "🔄 Excel to Machine CSV":
        st.subheader("Convert Technician Design to Test Bed CSV")
        uploaded = st.file_uploader("Upload Excel", type=['xlsx'])
        if uploaded:
            df = pd.read_excel(uploaded, sheet_name='TEST_SEQUENCE')
            s_type = detect_type(df)
            st.info(f"Detected: {s_type.replace('_', ' ').title()}")
            
            # Maintenance Tool
            if st.button("🛠️ Fix 5% Differential (Main Seal Only)") and s_type == 'main_seal':
                df['Interface_Pressure_bar'] = df['Cell_Pressure_bar'] * DIFF_TARGET
            
            edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
            
            # Safety Preview
            st.write("### Safety Check Preview")
            st.dataframe(edited.style.apply(highlight_errors, axis=1, seal_type=s_type), use_container_width=True)
            
            machine_df = convert_to_machine(edited, s_type)
            st.download_button("📥 Download Machine CSV", machine_df.to_csv(index=False, sep=';'), f"{s_type}_sequence.csv")

    # --- OPERATION: CSV TO EXCEL ---
    elif op == "📤 Machine CSV to Excel":
        st.subheader("Convert Test Bed File to Readable Excel")
        uploaded = st.file_uploader("Upload Machine CSV", type=['csv'])
        if uploaded:
            raw_df = safe_read_csv(uploaded)
            s_type = detect_type(raw_df)
            
            # Map to tech names
            tech_df = raw_df.rename(columns=TECH_MAPS[s_type])
            tech_df.insert(0, 'Step', range(1, len(tech_df)+1))
            
            edited = st.data_editor(tech_df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited.to_excel(writer, index=False, sheet_name='TEST_SEQUENCE')
            st.download_button("📥 Download Professional Excel", output.getvalue(), "converted_test.xlsx")

    # --- OPERATION: VIEW CURRENT ---
    elif op == "👀 View Current Test":
        st.subheader("System Default Sequences")
        seal = st.selectbox("Select File", ["MainSealSet2.csv", "SeperationSeal.csv"])
        
        if os.path.exists(seal):
            df = safe_read_csv(seal)
            s_type = detect_type(df)
            tech_df = df.rename(columns=TECH_MAPS[s_type])
            
            st.write(f"Showing: {seal}")
            st.dataframe(tech_df.style.apply(highlight_errors, axis=1, seal_type=s_type), use_container_width=True)
        else:
            st.error(f"File {seal} not found in root directory.")

if __name__ == "__main__":
    main()
