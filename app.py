import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math

# =====================================================
# SAFE CSV READER
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
                    na_values=['NaN','NAN','nan','INF','INFINITY','inf','infinity','',' ','NULL','null'],
                    keep_default_na=True,
                    skipinitialspace=True
                )
                return df.replace([np.nan, math.inf, -math.inf], 0)
            except Exception:
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
    if 'TST_CellPresDemand' in cols or 'Cell_Pressure_bar' in cols:
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
            }
        }

    return None

# =====================================================
# CONVERSIONS
# =====================================================

def convert_machine_to_technician(df, file_type):
    mapping = get_column_mapping(file_type)
    tech_df = df.rename(columns=mapping['machine_to_technician'])
    tech_df.insert(0, 'Step', range(1, len(tech_df) + 1))
    if 'Notes' not in tech_df.columns:
        tech_df['Notes'] = ''
    return tech_df

# =====================================================
# EDITABLE DATAFRAME
# =====================================================

def editable_dataframe(df, key, height=500):
    if key not in st.session_state:
        st.session_state[key] = df.copy()

    with st.form(f"form_{key}"):
        edited = st.data_editor(
            st.session_state[key],
            use_container_width=True,
            height=height,
            num_rows="fixed"
        )
        submitted = st.form_submit_button("✅ Apply changes")

    if submitted:
        st.session_state[key] = edited
        st.success("Changes applied")

    return st.session_state[key]

# =====================================================
# EXCEL EXPORT (SAFE IMAGE HANDLING)
# =====================================================

def create_professional_excel_from_data(
    technician_df,
    file_type,
    customer_name="",
    job_number="",
    logo_file=None
):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        technician_df.to_excel(writer, sheet_name='TEST_SEQUENCE', index=False)

        wb = writer.book
        ws = writer.sheets['TEST_SEQUENCE']

        header = wb.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
            'fg_color': '#366092',
            'font_color': 'white'
        })
        cell = wb.add_format({'border': 1, 'align': 'center'})
        notes = wb.add_format({'border': 1, 'align': 'left'})

        for c, col in enumerate(technician_df.columns):
            ws.write(0, c, col, header)

        for r in range(1, len(technician_df) + 1):
            for c, col in enumerate(technician_df.columns):
                ws.write(
                    r,
                    c,
                    technician_df.iloc[r - 1, c],
                    notes if col == 'Notes' else cell
                )

        ws.set_column(0, len(technician_df.columns) - 1, 18)

        # ---------------- INSTRUCTIONS SHEET ----------------
        instr = wb.add_worksheet('INSTRUCTIONS')

        # SAFE IMAGE EMBED
        if logo_file is not None:
            image_bytes = io.BytesIO(logo_file.getvalue())
            image_bytes.seek(0)

            instr.set_column('A:A', 35)
            instr.set_row(0, 120)

            instr.insert_image(
                'A1',
                'logo.png',  # dummy name
                {
                    'image_data': image_bytes,
                    'x_offset': 10,
                    'y_offset': 10,
                    'x_scale': 0.6,
                    'y_scale': 0.6
                }
            )

        meta_fmt = wb.add_format({'bold': True})
        header_fmt = wb.add_format({'bold': True})

        instr.write('A10', 'Customer Name:', meta_fmt)
        instr.write('B10', customer_name)

        instr.write('A11', 'Job Number:', meta_fmt)
        instr.write('B11', job_number)

        instr.write('A12', 'Export Date:', meta_fmt)
        instr.write('B12', datetime.now().strftime('%Y-%m-%d'))

        instructions = [
            "",
            "HOW TO USE THIS FILE:",
            "1. This Excel file was generated from a machine CSV",
            "2. Edit only the TEST_SEQUENCE sheet",
            "3. Do not modify metadata fields",
            "4. Upload back to the app to regenerate CSV",
            "",
            "FIELD DESCRIPTIONS:"
        ] + list(technician_df.columns)

        start_row = 14
        for i, text in enumerate(instructions):
            row = start_row + i
            if text in ["HOW TO USE THIS FILE:", "FIELD DESCRIPTIONS:"]:
                instr.write(row, 0, text, header_fmt)
            else:
                instr.write(row, 0, text)

        instr.set_column('A:A', 80)

    output.seek(0)
    return output

# =====================================================
# MAIN APP
# =====================================================

def main():
    st.title("⚙️ Universal Seal Test Manager")

    st.markdown("### 📄 Excel Information")
    customer_name = st.text_input("Customer Name")
    job_number = st.text_input("Job Number")

    logo_file = st.file_uploader("Logo (PNG)", type=["png"])

    if logo_file is not None:
        st.image(
            logo_file,
            caption="Uploaded logo (will be embedded in Excel)",
            width=250
        )

    st.divider()

    uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

    if uploaded:
        df = safe_read_csv(uploaded)
        file_type = detect_file_type(df)

        st.info(f"Detected: **{file_type.replace('_', ' ').upper()}**")

        edited = editable_dataframe(
            convert_machine_to_technician(df, file_type),
            "csv_editor"
        )

        excel = create_professional_excel_from_data(
            edited,
            file_type,
            customer_name,
            job_number,
            logo_file
        )

        st.download_button(
            "📥 Download Excel",
            excel.getvalue(),
            file_name=f"{file_type}_professional.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
