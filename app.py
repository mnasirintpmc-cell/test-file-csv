import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math
import os

from validator import validate_test_sequence

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path_or_buffer):

    try:

        encodings = ['utf-8','latin-1','cp1252','iso-8859-1']

        for enc in encodings:

            try:

                df = pd.read_csv(
                    file_path_or_buffer,
                    delimiter=';',
                    encoding=enc,
                    na_values=['NaN','NAN','nan','INF','INFINITY','inf','infinity','',' ','NULL','null'],
                    keep_default_na=True,
                    skipinitialspace=True
                )

                return df.replace([np.nan, math.inf, -math.inf],0)

            except:
                continue

        return pd.read_csv(file_path_or_buffer, delimiter=';')

    except Exception as e:

        st.error(f"CSV read error: {e}")
        return pd.DataFrame()

# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):

    cols = df.columns.tolist()

    if 'TST_CellPresDemand' in cols or 'Primary seal Gas Pressure (barg)' in cols:
        return 'main_seal'

    if 'TST_SepSealFlwSet1' in cols or 'Sep_Seal_Flow_Set1' in cols:
        return 'separation_seal'

    return 'unknown'

# =====================================================
# COLUMN MAPPINGS
# =====================================================

def get_column_mapping(file_type):

    if file_type == 'main_seal':

        return {

            'machine_to_technician':{

                'TST_SpeedDem':'Speed_RPM',
                'TST_CellPresDemand':'Primary seal Gas Pressure (barg)',
                'TST_InterPresDemand':'Interspace_Pressure_bar',
                'TST_InterBPDemand_DE':'BackPressure_Drive_End_bar',
                'TST_InterBPDemand_NDE':'BackPressure_Non_Drive_End_bar',
                'TST_GasInjectionDemand':'Gas_Injection_bar',
                'TST_StepDuration':'Duration_s',
                'TST_APFlag':'Acceptance point',
                'TST_TempDemand':'Temperature_C',
                'TST_GasType':'Gas_Type',
                'TST_TestMode':'Test_Mode',
                'TST_MeasurementReq':'Measurement',
                'TST_TorqueCheck':'Torque_Check'

            },

            'technician_to_machine':{

                'Speed_RPM':'TST_SpeedDem',
                'Primary seal Gas Pressure (barg)':'TST_CellPresDemand',
                'Interspace_Pressure_bar':'TST_InterPresDemand',
                'BackPressure_Drive_End_bar':'TST_InterBPDemand_DE',
                'BackPressure_Non_Drive_End_bar':'TST_InterBPDemand_NDE',
                'Gas_Injection_bar':'TST_GasInjectionDemand',
                'Duration_s':'TST_StepDuration',
                'Acceptance point':'TST_APFlag',
                'Temperature_C':'TST_TempDemand',
                'Gas_Type':'TST_GasType',
                'Test_Mode':'TST_TestMode',
                'Measurement':'TST_MeasurementReq',
                'Torque_Check':'TST_TorqueCheck'

            }

        }

    return None

# =====================================================
# CONVERSIONS
# =====================================================

def convert_machine_to_technician(df,file_type):

    mapping = get_column_mapping(file_type)

    tech_df = df.rename(columns=mapping['machine_to_technician'])

    tech_df.insert(0,'Step',range(1,len(tech_df)+1))

    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''

    return tech_df

def convert_to_machine_codes(df):

    df = df.copy()

    for col in ['TST_APFlag','TST_MeasurementReq','TST_TorqueCheck']:

        if col in df.columns:

            df[col] = df[col].map({'Yes':1,'No':0}).fillna(df[col])

    if 'TST_TestMode' in df.columns:

        df['TST_TestMode'] = df['TST_TestMode'].map({'Mode 1':1,'Mode 2':2}).fillna(df['TST_TestMode'])

    return df

# =====================================================
# EDITABLE DATAFRAME
# =====================================================

def editable_dataframe(df,key,height=500):

    if key not in st.session_state:
        st.session_state[key] = df.copy()

    with st.form(f"form_{key}"):

        edited = st.data_editor(
            st.session_state[key],
            use_container_width=True,
            height=height,
            num_rows="fixed"
        )

        submitted = st.form_submit_button("Apply changes")

    if submitted:

        st.session_state[key] = edited
        st.success("Changes applied")

    return st.session_state[key]

# =====================================================
# PROFESSIONAL EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(technician_df,file_type):

    output = io.BytesIO()

    logo_path = os.path.join(os.path.dirname(__file__),"company_logo.png")

    with pd.ExcelWriter(output,engine='xlsxwriter') as workbook:

        technician_df.to_excel(workbook,sheet_name='TEST_SEQUENCE',index=False)

        wb = workbook.book
        ws = workbook.sheets['TEST_SEQUENCE']

        header = wb.add_format({
            'bold':True,
            'text_wrap':True,
            'align':'center',
            'border':1,
            'fg_color':'#366092',
            'font_color':'white'
        })

        cell = wb.add_format({'border':1,'align':'center'})
        notes = wb.add_format({'border':1,'align':'left'})

        for c,col in enumerate(technician_df.columns):
            ws.write(0,c,col,header)

        for r in range(1,len(technician_df)+1):

            for c,col in enumerate(technician_df.columns):

                ws.write(
                    r,
                    c,
                    technician_df.iloc[r-1,c],
                    notes if col=='Notes' else cell
                )

        ws.set_column(0,len(technician_df.columns)-1,18)

        instr = workbook.add_worksheet('INSTRUCTIONS')

        if os.path.exists(logo_path):

            instr.set_column('A:A',32)
            instr.set_row(0,120)

            instr.insert_image(
                'A1',
                logo_path,
                {'x_offset':10,'y_offset':10,'x_scale':0.6,'y_scale':0.6}
            )

        date = datetime.now().strftime('%Y-%m-%d')

        instr.write('B13',f"{file_type.upper()} TEST SEQUENCE - {date}")

    output.seek(0)

    return output

# =====================================================
# MAIN APP
# =====================================================

def main():

    st.title("Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        [
            "Download Template",
            "Excel to Machine CSV",
            "Machine CSV to Excel",
            "View Current Test"
        ]
    )

# -----------------------------------------------------

    if operation == "Download Template":

        seal = st.selectbox("Seal Type",["Main Seal"])

        file_type = "main_seal"
        csv_file = "MainSealSet2.csv"

        df = safe_read_csv(csv_file)

        tech_df = convert_machine_to_technician(df,file_type)

        excel = create_professional_excel_from_data(tech_df,file_type)

        st.download_button(
            "Download Template",
            excel.getvalue(),
            file_name=f"{file_type}_template.xlsx"
        )

# -----------------------------------------------------

    elif operation == "Excel to Machine CSV":

        uploaded = st.file_uploader("Upload Excel",type=['xlsx'])

        if uploaded:

            df = pd.read_excel(uploaded,sheet_name='TEST_SEQUENCE')

            df = df.dropna(subset=['Step']).reset_index(drop=True)

            file_type = detect_file_type(df)

            edited = editable_dataframe(df,"excel_editor")

            mapping = get_column_mapping(file_type)

            machine_df = convert_to_machine_codes(
                edited.rename(columns=mapping['technician_to_machine'])
            ).drop(columns=['Step','Notes'],errors='ignore')

            warnings = validate_test_sequence(edited)

            if warnings:

                st.warning("Validation warnings detected")

                for w in warnings:
                    st.write("⚠️",w)

            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False,sep=';'),
                file_name=f"{file_type}_sequence.csv"
            )

# -----------------------------------------------------

    elif operation == "Machine CSV to Excel":

        uploaded = st.file_uploader("Upload CSV",type=['csv'])

        if uploaded:

            df = safe_read_csv(uploaded)

            file_type = detect_file_type(df)

            edited = editable_dataframe(
                convert_machine_to_technician(df,file_type),
                "csv_editor"
            )

            excel = create_professional_excel_from_data(edited,file_type)

            st.download_button(
                "Download Excel",
                excel.getvalue(),
                file_name=f"{file_type}_professional.xlsx"
            )

# -----------------------------------------------------

    elif operation == "View Current Test":

        csv_file = "MainSealSet2.csv"
        file_type = "main_seal"

        df = safe_read_csv(csv_file)

        edited = editable_dataframe(
            convert_machine_to_technician(df,file_type),
            "current_editor"
        )

        excel = create_professional_excel_from_data(edited,file_type)

        st.download_button(
            "Download Excel",
            excel.getvalue(),
            file_name="current_test.xlsx"
        )

# =====================================================

if __name__ == "__main__":
    main()
