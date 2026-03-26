import streamlit as st
import pandas as pd
import numpy as np
import io
import os
from spec_scanner import scan_spec
from validator import validate_sequence

# =========================
# USER INPUT (NEW)
# =========================
def get_user():
    return st.sidebar.text_input("Operator Name", "")


# =========================
# EXCEL EXPORT (UPDATED)
# =========================
def create_professional_excel_from_data(df, file_type, user_name="", source_name=""):

    df = df.replace({np.nan:""})

    output = io.BytesIO()
    logo_path = os.path.join(os.path.dirname(__file__),"company_logo.png")

    with pd.ExcelWriter(output,engine="xlsxwriter") as writer:

        df.to_excel(writer,sheet_name="TEST_SEQUENCE",index=False)

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

        for c,col in enumerate(df.columns):
            ws.write(0,c,col,header)

        for r in range(1,len(df)+1):
            for c,col in enumerate(df.columns):
                val = df.iloc[r-1,c]
                if pd.isna(val):
                    val = ""
                ws.write(r,c,val,notes if col=="Notes" else cell)

        ws.set_column(0,len(df.columns)-1,18)

        # =========================
        # INSTRUCTIONS (UPDATED)
        # =========================
        instr = wb.add_worksheet("INSTRUCTIONS")

        if os.path.exists(logo_path):
            instr.set_row(0,120)
            instr.insert_image("A1",logo_path,{"x_scale":0.6,"y_scale":0.6})

        instr.write(10,1,f"Operator: {user_name}")
        instr.write(11,1,f"Source File: {source_name}")

        instr.write(12,1,"SEAL TEST SEQUENCE")
        instr.write(14,1,"1. Edit sequence as required")
        instr.write(15,1,"2. Maintain safe pressure relationships")
        instr.write(16,1,"3. Upload file back to system")

        instr.protect()

    output.seek(0)
    return output


# =========================
# MAIN
# =========================
def main():

    st.title("⚙️ DGS Test Manager")

    user_name = get_user()

    uploaded = st.file_uploader("Upload Spec", type=["xlsb","xlsm","xlsx"])

    if uploaded:

        source_name = uploaded.name

        df = scan_spec(uploaded)

        warnings = validate_sequence(df)

        if warnings:
            st.error("Fix errors before download")

        excel = create_professional_excel_from_data(
            df,
            "main_seal",
            user_name=user_name,
            source_name=source_name
        )

        st.download_button(
            "Download Excel",
            excel.getvalue(),
            file_name="technician_sequence.xlsx"
        )


if __name__ == "__main__":
    main()
