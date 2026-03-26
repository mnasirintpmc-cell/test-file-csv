import streamlit as st
import pandas as pd
import numpy as np
import io
import os
from datetime import datetime
from spec_scanner import scan_spec
from validator import validate_sequence

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file_path_or_buffer):

    encodings = ["utf-8","latin-1","cp1252","iso-8859-1"]

    for enc in encodings:
        try:
            df = pd.read_csv(
                file_path_or_buffer,
                delimiter=";",
                encoding=enc
            )
            return df
        except:
            continue

    st.error("CSV read error")
    return pd.DataFrame()


# =====================================================
# FILE TYPE DETECTION
# =====================================================

def detect_file_type(df):

    cols = df.columns.tolist()

    if "TST_CellPresDemand" in cols or "Primary seal Gas Pressure (barg)" in cols:
        return "main_seal"

    if "TST_SepSealFlwSet1" in cols or "Sep_Seal_Flow_Set1" in cols:
        return "separation_seal"

    return "unknown"


# =====================================================
# COLUMN MAPPING (UNCHANGED)
# =====================================================

def get_column_mapping(file_type):

    if file_type == "main_seal":

        return {
            "machine_to_technician":{
                "TST_SpeedDem":"Speed_RPM",
                "TST_CellPresDemand":"Primary seal Gas Pressure (barg)",
                "TST_InterPresDemand":"Interspace_Pressure_bar",
                "TST_InterBPDemand_DE":"BackPressure_Drive_End_bar",
                "TST_InterBPDemand_NDE":"BackPressure_Non_Drive_End_bar",
                "TST_GasInjectionDemand":"Gas_Injection_bar",
                "TST_StepDuration":"Duration_s",
                "TST_APFlag":"Acceptance point",
                "TST_TempDemand":"Temperature_C",
                "TST_GasType":"Gas_Type",
                "TST_TestMode":"Test_Mode",
                "TST_MeasurementReq":"Measurement",
                "TST_TorqueCheck":"Torque_Check"
            },

            "technician_to_machine":{
                "Speed_RPM":"TST_SpeedDem",
                "Primary seal Gas Pressure (barg)":"TST_CellPresDemand",
                "Interspace_Pressure_bar":"TST_InterPresDemand",
                "BackPressure_Drive_End_bar":"TST_InterBPDemand_DE",
                "BackPressure_Non_Drive_End_bar":"TST_InterBPDemand_NDE",
                "Gas_Injection_bar":"TST_GasInjectionDemand",
                "Duration_s":"TST_StepDuration",
                "Acceptance point":"TST_APFlag",
                "Temperature_C":"TST_TempDemand",
                "Gas_Type":"TST_GasType",
                "Test_Mode":"TST_TestMode",
                "Measurement":"TST_MeasurementReq",
                "Torque_Check":"TST_TorqueCheck"
            }
        }

    return None


# =====================================================
# CONVERSION
# =====================================================

def convert_machine_to_technician(df,file_type):

    mapping = get_column_mapping(file_type)

    tech_df = df.rename(columns=mapping["machine_to_technician"])

    tech_df.insert(0,"Step",range(1,len(tech_df)+1))

    if "Notes" not in tech_df.columns:
        tech_df["Notes"] = ""

    return tech_df


# =====================================================
# EXCEL EXPORT (ENHANCED ONLY)
# =====================================================

def create_professional_excel_from_data(df,file_type,user_name="",source_name=""):

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

        # ======================
        # INSTRUCTION SHEET
        # ======================
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


# =====================================================
# MAIN APP (FULL RESTORED)
# =====================================================

def main():

    st.title("⚙️ DGS Test Manager")

    # ✅ NEW (NON-DESTRUCTIVE)
    user_name = st.sidebar.text_input("Operator Name")

    operation = st.sidebar.radio(
        "Operation",
        [
            "Download Template",
            "CSV → Excel",
            "Excel → CSV",
            "View Current Test",
            "Spec → Technician Excel"
        ]
    )

    base_dir = os.path.dirname(__file__)

# -----------------------------------------------------
# SPEC → TECHNICIAN
# -----------------------------------------------------

    if operation=="Spec → Technician Excel":

        uploaded = st.file_uploader(
            "Upload Spec (.xlsb, .xlsm, .xlsx)",
            type=["xlsb","xlsm","xlsx"]
        )

        if uploaded:

            source_name = uploaded.name  # ✅ NEW

            spec_df = scan_spec(uploaded)

            warnings = validate_sequence(spec_df)

            if warnings:
                st.error("Safety issues detected")
                for w in warnings:
                    st.warning(w)

            excel = create_professional_excel_from_data(
                spec_df,
                "main_seal",
                user_name=user_name,
                source_name=source_name
            )

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )


if __name__=="__main__":
    main()
