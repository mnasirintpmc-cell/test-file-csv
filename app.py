import streamlit as st
import pandas as pd
import numpy as np
import io
import os
from datetime import datetime
from spec_scanner import scan_spec


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
            warnings.append(
                f"Step {step}: Interspace pressure greater than primary"
            )

        if primary - inter < 0.2 and inter > 0:
            warnings.append(
                f"Step {step}: Differential pressure < 0.2 bar"
            )

    return warnings


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
# COLUMN MAPPING
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


def convert_to_machine_codes(df):

    df = df.copy()

    for col in ["TST_APFlag","TST_MeasurementReq","TST_TorqueCheck"]:

        if col in df.columns:
            df[col] = df[col].map({"Yes":1,"No":0}).fillna(0)

    return df


# =====================================================
# PROFESSIONAL EXCEL EXPORT
# =====================================================

def create_professional_excel_from_data(df,file_type):

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

                if col == "Notes":
                    ws.write(r,c,str(val),notes)
                else:
                    ws.write(r,c,val,cell)

        ws.set_column(0,len(df.columns)-1,18)

        instr = wb.add_worksheet("INSTRUCTIONS")

        if os.path.exists(logo_path):

            instr.set_row(0,120)

            instr.insert_image(
                "A1",
                logo_path,
                {"x_scale":0.6,"y_scale":0.6}
            )

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

        st.download_button(
            "Download Template",
            excel.getvalue(),
            file_name="template.xlsx"
        )


# -----------------------------------------------------
# MACHINE CSV → TECHNICIAN
# -----------------------------------------------------

    elif operation=="Machine CSV → Technician Excel":

        uploaded = st.file_uploader("Upload Machine CSV",type=["csv"])

        if uploaded:

            df = safe_read_csv(uploaded)

            file_type = detect_file_type(df)

            tech = convert_machine_to_technician(df,file_type)

            edited = editable_dataframe(tech)

            excel = create_professional_excel_from_data(edited,file_type)

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )


# -----------------------------------------------------
# TECHNICIAN → MACHINE CSV
# -----------------------------------------------------

    elif operation=="Technician Excel → Machine CSV":

        uploaded = st.file_uploader("Upload Technician Excel",type=["xlsx"])

        if uploaded:

            df = pd.read_excel(uploaded)

            file_type = detect_file_type(df)

            edited = editable_dataframe(df)

            mapping = get_column_mapping(file_type)

            machine_df = convert_to_machine_codes(
                edited.rename(columns=mapping["technician_to_machine"])
            ).drop(columns=["Step","Notes"],errors="ignore")

            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False,sep=";"),
                file_name="machine_sequence.csv"
            )


# -----------------------------------------------------
# VIEW CURRENT TEST
# -----------------------------------------------------

    elif operation=="View Current Test":

        seal = st.selectbox("Seal Type",["Main Seal","Separation Seal"])

        template="MainSealSet2.csv" if seal=="Main Seal" else "SeperationSeal.csv"

        df = safe_read_csv(os.path.join(base_dir,template))

        file_type = detect_file_type(df)

        edited = editable_dataframe(
            convert_machine_to_technician(df,file_type)
        )

        excel = create_professional_excel_from_data(edited,file_type)

        st.download_button(
            "Download Excel",
            excel.getvalue(),
            file_name="current_test.xlsx"
        )


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
