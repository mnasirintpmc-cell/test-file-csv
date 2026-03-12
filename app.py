import streamlit as st
import pandas as pd
import io
import numpy as np
import math
import os
from datetime import datetime
from spec_scanner import scan_spec


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
                    na_values=[
                        'NaN','NAN','nan',
                        'INF','INFINITY','inf','infinity',
                        '',' ','NULL','null'
                    ],
                    keep_default_na=True,
                    skipinitialspace=True
                )

                return df.replace([np.nan, math.inf, -math.inf], 0)

            except:
                continue

        return pd.read_csv(file_path_or_buffer, delimiter=';')

    except Exception as e:

        st.error(f"CSV read error: {e}")
        return pd.DataFrame()


# =====================================================
# SAFETY VALIDATION
# =====================================================

def validate_safety(df):

    warnings = []

    if "Primary seal Gas Pressure (barg)" not in df.columns:
        return warnings

    for i,row in df.iterrows():

        step = row.get("Step", i+1)

        try:
            primary = float(row.get("Primary seal Gas Pressure (barg)",0))
        except:
            primary = 0

        try:
            inter = float(row.get("Interspace_Pressure_bar",0))
        except:
            inter = 0

        if inter > primary:
            warnings.append(f"Step {step}: Interspace pressure > primary")

        if primary - inter < 0.2 and inter > 0:
            warnings.append(f"Step {step}: Differential pressure < 0.2 bar")

    return warnings


# =====================================================
# PROFESSIONAL EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(technician_df,file_type):

    output = io.BytesIO()

    logo_path = os.path.join(os.path.dirname(__file__),"company_logo.png")

    with pd.ExcelWriter(output,engine="xlsxwriter") as writer:

        technician_df.to_excel(writer,sheet_name="TEST_SEQUENCE",index=False)

        wb = writer.book
        ws = writer.sheets["TEST_SEQUENCE"]

        header = wb.add_format({
            "bold":True,
            "align":"center",
            "border":1,
            "fg_color":"#366092",
            "font_color":"white"
        })

        cell = wb.add_format({"border":1,"align":"center"})
        notes = wb.add_format({"border":1,"align":"left"})

        for c,col in enumerate(technician_df.columns):
            ws.write(0,c,col,header)

        for r in range(1,len(technician_df)+1):

            for c,col in enumerate(technician_df.columns):

                val = technician_df.iloc[r-1,c]

                if col=="Notes":
                    ws.write(r,c,val,notes)
                else:
                    ws.write(r,c,val,cell)

        ws.set_column(0,len(technician_df.columns)-1,18)

        instr = wb.add_worksheet("INSTRUCTIONS")

        if os.path.exists(logo_path):

            instr.set_row(0,120)

            instr.insert_image("A1",logo_path,
                {"x_scale":0.6,"y_scale":0.6})

        instr.write(12,1,"SEAL TEST SEQUENCE")
        instr.write(14,1,"1. Edit sequence as required")
        instr.write(15,1,"2. Maintain safe pressure relationships")
        instr.write(16,1,"3. Upload file back to system")

    output.seek(0)

    return output


# =====================================================
# EDITABLE TABLE
# =====================================================

def editable_dataframe(df):

    edited = st.data_editor(df,use_container_width=True)

    warnings = validate_safety(edited)

    if warnings:

        st.error("Safety interlock violations detected")

        for w in warnings:
            st.warning(w)

    return edited


# =====================================================
# MAIN APP
# =====================================================

def main():

    st.title("⚙️ Seal Test Manager")

    operation = st.sidebar.radio(

        "Operation",

        [

            "Download Template",
            "Machine CSV → Technician Excel",
            "Technician Excel → Machine CSV",
            "View Current Test",
            "Spec → Technician Excel"

        ]

    )

    base_dir = os.path.dirname(__file__)


# -----------------------------------------------------
# DOWNLOAD TEMPLATE
# -----------------------------------------------------

    if operation=="Download Template":

        seal = st.selectbox("Seal Type",["Main Seal","Separation Seal"])

        template="MainSealSet2.csv" if seal=="Main Seal" else "SeperationSeal.csv"

        file_type="main_seal" if seal=="Main Seal" else "separation_seal"

        df = safe_read_csv(os.path.join(base_dir,template))

        tech_df = convert_machine_to_technician(df,file_type)

        excel = create_professional_excel_from_data(tech_df,file_type)

        st.download_button("Download Template",
            excel.getvalue(),
            file_name="template.xlsx")


# -----------------------------------------------------
# SPEC → TECHNICIAN
# -----------------------------------------------------

    elif operation=="Spec → Technician Excel":

        uploaded = st.file_uploader("Upload Spec (.xlsb)",type=["xlsb"])

        if uploaded:

            spec_df = scan_spec(uploaded)

            edited = editable_dataframe(spec_df)

            excel = create_professional_excel_from_data(edited,"main_seal")

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )


if __name__=="__main__":
    main()
