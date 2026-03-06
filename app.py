import streamlit as st
import pandas as pd
import io
from datetime import datetime
import numpy as np
import math
import os

# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file):

    encodings = ["utf-8","latin-1","cp1252"]

    for enc in encodings:
        try:
            df = pd.read_csv(file,delimiter=";",encoding=enc)
            return df.replace([np.nan,math.inf,-math.inf],0)
        except:
            pass

    return pd.DataFrame()


# =====================================================
# COLUMN MAPPING
# =====================================================

def get_column_mapping():

    return {

        "machine_to_technician":{

            "TST_SpeedDem":"Speed_RPM",
            "TST_CellPresDemand":"Primary seal Gas Pressure (barg)",
            "TST_InterPresDemand":"Interspace_Pressure_bar",
            "TST_InterBPDemand_DE":"BackPressure_Drive_End_bar",
            "TST_InterBPDemand_NDE":"BackPressure_Non_Drive_End_bar",
            "TST_GasInjectionDemand":"Gas_Injection",
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
            "Gas_Injection":"TST_GasInjectionDemand",
            "Duration_s":"TST_StepDuration",
            "Acceptance point":"TST_APFlag",
            "Temperature_C":"TST_TempDemand",
            "Gas_Type":"TST_GasType",
            "Test_Mode":"TST_TestMode",
            "Measurement":"TST_MeasurementReq",
            "Torque_Check":"TST_TorqueCheck"

        }

    }


# =====================================================
# MACHINE → TECHNICIAN
# =====================================================

def convert_machine_to_technician(df):

    mapping = get_column_mapping()

    tech_df = df.rename(columns=mapping["machine_to_technician"])

    tech_df.insert(0,"Step",range(1,len(tech_df)+1))

    if "Notes" not in tech_df.columns:
        tech_df["Notes"] = ""

    return tech_df


# =====================================================
# PRESSURE VALIDATION
# =====================================================

def validate_pressure_logic(df):

    issues = []

    for i,row in df.iterrows():

        cell = float(row.get("Primary seal Gas Pressure (barg)",0))
        inter = float(row.get("Interspace_Pressure_bar",0))

        if cell < inter:

            issues.append(
                f"Step {i+1}: Cell ({cell}) < Interspace ({inter})"
            )

    if issues:

        st.warning("⚠ Pressure validation warnings")

        for msg in issues:
            st.write(msg)

        return False

    return True


# =====================================================
# TEST MODE ROUTING
# =====================================================

def apply_test_mode_logic(df):

    df = df.copy()

    for i,row in df.iterrows():

        mode = int(row.get("TST_TestMode",1))
        inter = float(row.get("TST_InterPresDemand",0))

        # INBOARD
        if mode == 1:

            df.at[i,"TST_InterBPDemand_DE"] = inter
            df.at[i,"TST_InterBPDemand_NDE"] = inter
            df.at[i,"TST_InterPresDemand"] = 0

        # OUTBOARD
        elif mode == 2:

            df.at[i,"TST_InterBPDemand_DE"] = 0
            df.at[i,"TST_InterBPDemand_NDE"] = 0
            df.at[i,"TST_InterPresDemand"] = inter

    return df


# =====================================================
# MACHINE CODE CONVERSION
# =====================================================

def convert_to_machine_codes(df):

    df = df.copy()

    df["TST_APFlag"] = pd.to_numeric(df["TST_APFlag"],errors="coerce").fillna(0).astype(int)

    # Measurement triggered by acceptance point
    df["TST_MeasurementReq"] = df["TST_APFlag"]

    df["TST_TestMode"] = pd.to_numeric(df["TST_TestMode"],errors="coerce").fillna(1).astype(int)

    return df


# =====================================================
# PROFESSIONAL EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(df):

    output = io.BytesIO()

    logo_path = os.path.join(os.path.dirname(__file__),"company_logo.png")

    with pd.ExcelWriter(output,engine="xlsxwriter") as writer:

        df.to_excel(writer,sheet_name="TEST_SEQUENCE",index=False)

        workbook = writer.book
        ws = writer.sheets["TEST_SEQUENCE"]

        header = workbook.add_format({
            "bold":True,
            "text_wrap":True,
            "align":"center",
            "border":1,
            "fg_color":"#366092",
            "font_color":"white"
        })

        cell = workbook.add_format({
            "border":1,
            "align":"center"
        })

        for c,col in enumerate(df.columns):
            ws.write(0,c,col,header)

        for r in range(1,len(df)+1):
            for c,col in enumerate(df.columns):
                ws.write(r,c,df.iloc[r-1,c],cell)

        ws.set_column(0,len(df.columns)-1,18)

        instr = workbook.add_worksheet("INSTRUCTIONS")

        if os.path.exists(logo_path):
            instr.insert_image("A1",logo_path)

        date = datetime.now().strftime("%Y-%m-%d")
        instr.write(10,1,f"Generated {date}")

    output.seek(0)

    return output


# =====================================================
# MAIN APP
# =====================================================

def main():

    st.title("⚙ Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        ["Excel → Machine CSV","Machine CSV → Excel"]
    )

# =====================================================
# EXCEL → CSV
# =====================================================

    if operation == "Excel → Machine CSV":

        uploaded = st.file_uploader("Upload Excel",type="xlsx")

        if uploaded:

            df = pd.read_excel(uploaded,sheet_name="TEST_SEQUENCE")

            df = df.dropna(subset=["Step"]).reset_index(drop=True)

            edited = st.data_editor(df,use_container_width=True)

            validate_pressure_logic(edited)

            mapping = get_column_mapping()

            machine = edited.rename(columns=mapping["technician_to_machine"])

            machine = convert_to_machine_codes(machine)

            machine = apply_test_mode_logic(machine)

            machine = machine.drop(columns=["Step","Notes"],errors="ignore")

            st.download_button(
                "Download Machine CSV",
                machine.to_csv(index=False,sep=";"),
                file_name="test_sequence.csv",
                mime="text/csv"
            )


# =====================================================
# CSV → EXCEL
# =====================================================

    if operation == "Machine CSV → Excel":

        uploaded = st.file_uploader("Upload CSV",type="csv")

        if uploaded:

            df = safe_read_csv(uploaded)

            tech = convert_machine_to_technician(df)

            excel = create_professional_excel_from_data(tech)

            st.download_button(
                "Download Professional Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


if __name__ == "__main__":
    main()
