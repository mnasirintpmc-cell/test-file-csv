import streamlit as st
import pandas as pd
import numpy as np
import math
import io

from test_builder import test_builder_ui


# =====================================================
# SAFE CSV READER
# =====================================================

def safe_read_csv(file):

    encodings = ["utf-8", "latin-1", "cp1252"]

    for enc in encodings:
        try:
            df = pd.read_csv(file, delimiter=";", encoding=enc)
            return df.replace([np.nan, math.inf, -math.inf], 0)
        except:
            pass

    st.error("CSV read error")
    return pd.DataFrame()


# =====================================================
# COLUMN MAPPING
# =====================================================

def get_column_mapping():

    return {

        "machine_to_technician": {

            "TST_SpeedDem": "Speed_RPM",
            "TST_CellPresDemand": "Primary seal Gas Pressure (barg)",
            "TST_InterPresDemand": "Interspace_Pressure_bar",
            "TST_InterBPDemand_DE": "BackPressure_Drive_End_bar",
            "TST_InterBPDemand_NDE": "BackPressure_Non_Drive_End_bar",
            "TST_GasInjectionDemand": "Gas_Injection",
            "TST_StepDuration": "Duration_s",
            "TST_APFlag": "Acceptance point",
            "TST_TempDemand": "Temperature_C",
            "TST_GasType": "Gas_Type",
            "TST_TestMode": "Test_Mode",
            "TST_MeasurementReq": "Measurement",
            "TST_TorqueCheck": "Torque_Check"

        },

        "technician_to_machine": {

            "Speed_RPM": "TST_SpeedDem",
            "Primary seal Gas Pressure (barg)": "TST_CellPresDemand",
            "Interspace_Pressure_bar": "TST_InterPresDemand",
            "BackPressure_Drive_End_bar": "TST_InterBPDemand_DE",
            "BackPressure_Non_Drive_End_bar": "TST_InterBPDemand_NDE",
            "Gas_Injection": "TST_GasInjectionDemand",
            "Duration_s": "TST_StepDuration",
            "Acceptance point": "TST_APFlag",
            "Temperature_C": "TST_TempDemand",
            "Gas_Type": "TST_GasType",
            "Test_Mode": "TST_TestMode",
            "Measurement": "TST_MeasurementReq",
            "Torque_Check": "TST_TorqueCheck"

        }
    }


# =====================================================
# APPLY BP LOGIC
# =====================================================

def apply_test_logic(df):

    warnings = []

    for i, row in df.iterrows():

        cell = float(row.get("TST_CellPresDemand", 0))
        inter = float(row.get("TST_InterPresDemand", 0))
        bp_de = float(row.get("TST_InterBPDemand_DE", 0))
        bp_nde = float(row.get("TST_InterBPDemand_NDE", 0))
        mode = int(row.get("TST_TestMode", 1))

        if cell < inter:
            warnings.append(f"Step {i+1}: Cell pressure lower than interspace")

        if bp_de > 0 or bp_nde > 0:
            continue

        if mode == 1:

            if inter > 0:

                df.at[i, "TST_InterBPDemand_DE"] = inter
                df.at[i, "TST_InterBPDemand_NDE"] = inter
                df.at[i, "TST_InterPresDemand"] = 0

        elif mode == 2:

            df.at[i, "TST_InterBPDemand_DE"] = 0
            df.at[i, "TST_InterBPDemand_NDE"] = 0

    return df, warnings


# =====================================================
# EXCEL EXPORT
# =====================================================

def create_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        df.to_excel(writer, sheet_name="TEST_SEQUENCE", index=False)

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
            "Machine CSV → Technician Excel",
            "Technician Excel → Machine CSV",
            "Test Builder"
        ]

    )

    if operation == "Machine CSV → Technician Excel":

        file = st.file_uploader("Upload CSV", type=["csv"])

        if file:

            df = safe_read_csv(file)

            st.dataframe(df)

    elif operation == "Technician Excel → Machine CSV":

        file = st.file_uploader("Upload Excel", type=["xlsx"])

        if file:

            df = pd.read_excel(file)

            mapping = get_column_mapping()

            machine = df.rename(columns=mapping["technician_to_machine"])

            machine, warnings = apply_test_logic(machine)

            if warnings:

                st.warning("Pressure warnings")

                for w in warnings:
                    st.write(w)

            csv = machine.to_csv(index=False, sep=";")

            st.download_button(

                "Download CSV",

                csv,

                file_name="seal_test_sequence.csv"

            )

    elif operation == "Test Builder":

        test_builder_ui()

        if "generated_test" in st.session_state:

            df = st.session_state.generated_test

            excel = create_excel(df)

            st.download_button(

                "Download Generated Excel",

                excel,

                file_name="generated_test_sequence.xlsx"

            )


if __name__ == "__main__":
    main()
