import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

from template_utils import create_smart_template

# =====================================================
# SESSION HELPERS
# =====================================================

def reset_editor(key, df):
    if key not in st.session_state or st.session_state[key].shape != df.shape:
        st.session_state[key] = df.copy()

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path_or_buffer):
    try:
        df = pd.read_csv(file_path_or_buffer, delimiter=';')
        return df.replace([np.nan, math.inf, -math.inf], 0)
    except Exception as e:
        st.error(f"CSV read error: {e}")
        return pd.DataFrame()

# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):
    cols = df.columns.tolist()
    if 'TST_CellPresDemand' in cols:
        return 'main_seal'
    if 'TST_SepSealFlwSet1' in cols:
        return 'separation_seal'
    return 'unknown'

# =====================================================
# COLUMN MAPPINGS
# =====================================================

def get_column_mapping(file_type):

    if file_type == 'main_seal':
        return {
            'machine_to_technician': {
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
            'technician_to_machine': {
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

    if file_type == 'separation_seal':
        return {
            'machine_to_technician': {
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
            },
            'technician_to_machine': {
                'Speed_RPM': 'TST_SpeedDem',
                'Sep_Seal_Flow_Set1': 'TST_SepSealFlwSet1',
                'Sep_Seal_Flow_Set2': 'TST_SepSealFlwSet2',
                'Sep_Seal_Pressure_Set1': 'TST_SepSealPSet1',
                'Sep_Seal_Pressure_Set2': 'TST_SepSealPSet2',
                'Sep_Seal_Control_Type': 'TST_SepSealControlTyp',
                'Duration_s': 'TST_StepDuration',
                'Auto_Proceed': 'TST_APFlag',
                'Temperature_C': 'TST_TempDemand',
                'Gas_Type': 'TST_GasType',
                'Measurement': 'TST_MeasurementReq',
                'Torque_Check': 'TST_TorqueCheck'
            }
        }

    return None

# =====================================================
# CONVERSIONS
# =====================================================

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    if mapping is None:
        st.error("Unsupported seal type")
        return pd.DataFrame()

    tech_df = df.rename(columns=mapping['machine_to_technician'])
    tech_df.insert(0, 'Step', range(1, len(tech_df) + 1))
    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''
    return tech_df

def convert_to_machine_codes(df):
    df = df.copy()
    for col in ['TST_APFlag','TST_MeasurementReq','TST_TorqueCheck']:
        if col in df.columns:
            df[col] = df[col].map({'Yes':1,'No':0}).fillna(0)
    return df

# =====================================================
# EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(technician_df, file_type):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        technician_df.to_excel(writer, sheet_name='TEST_SEQUENCE', index=False)

        wb = writer.book
        ws = writer.sheets['TEST_SEQUENCE']

        header = wb.add_format({'bold':True,'border':1,'align':'center'})
        cell = wb.add_format({'border':1,'align':'center'})

        for c,col in enumerate(technician_df.columns):
            ws.write(0,c,col,header)

        for r in range(1,len(technician_df)+1):
            for c,col in enumerate(technician_df.columns):
                ws.write(r,c,technician_df.iloc[r-1,c],cell)

        instr = wb.add_worksheet('INSTRUCTIONS')
        seal = "MAIN SEAL" if file_type == "main_seal" else "SEPARATION SEAL"
        instr.write(0,0,f"{seal} TEST SEQUENCE")

    output.seek(0)
    return output

# =====================================================
# MAIN
# =====================================================

def main():
    st.title("⚙️ Universal Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        ["📥 Download Template","👀 View Current Test"]
    )

    # -------- TEMPLATE DOWNLOAD --------
    if operation == "📥 Download Template":
        seal_ui = st.selectbox("Select Seal Type",["Main Seal","Separation Seal"])
        file_type = "main_seal" if seal_ui=="Main Seal" else "separation_seal"

        if file_type == "main_seal":
            machine_df = create_smart_template()
        else:
            machine_df = safe_read_csv("SeparationSeal.csv")

        st.success(f"Template Seal Type: {seal_ui.upper()}")

        tech_df = convert_machine_to_technician(machine_df, file_type)
        excel = create_professional_excel_from_data(tech_df, file_type)

        st.download_button(
            "Download Excel Template",
            excel.getvalue(),
            file_name=f"{file_type}_template.xlsx"
        )

    # -------- VIEW CURRENT --------
    elif operation == "👀 View Current Test":
        file_name = st.selectbox(
            "Select CSV",
            ["MainSealSet2.csv","SeparationSeal.csv"]
        )

        df = safe_read_csv(file_name)
        file_type = detect_file_type(df)

        st.success(f"Viewing {file_type.replace('_',' ').upper()}")

        tech_df = convert_machine_to_technician(df, file_type)
        st.data_editor(tech_df, use_container_width=True)

if __name__ == "__main__":
    main()
