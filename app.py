import streamlit as st
import pandas as pd
import io
from spec_scanner import scan_spec_sheet
from validator import validate_sequence

st.set_page_config(layout="wide")

st.title("Seal Test Manager")

operation = st.sidebar.radio(
    "Operation",
    [
        "📤 Machine CSV → Technician Excel",
        "🔄 Technician Excel → Machine CSV",
        "🧠 Spec Excel → Technician Excel"
    ]
)

# ---------------------------------------------------
# CSV → Technician Excel
# ---------------------------------------------------

if operation == "📤 Machine CSV → Technician Excel":

    uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

    if uploaded:

        df = pd.read_csv(uploaded, delimiter=";")

        tech_df = df.copy()

        tech_df.insert(0,"Step",range(1,len(tech_df)+1))

        st.dataframe(tech_df)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            tech_df.to_excel(writer,index=False)

        st.download_button(
            "Download Technician Excel",
            output.getvalue(),
            "technician_sequence.xlsx"
        )


# ---------------------------------------------------
# Technician Excel → Machine CSV
# ---------------------------------------------------

elif operation == "🔄 Technician Excel → Machine CSV":

    uploaded = st.file_uploader("Upload Technician Excel", type=["xlsx"])

    if uploaded:

        df = pd.read_excel(uploaded)

        machine_df = df.drop(columns=["Step","Notes"], errors="ignore")

        st.dataframe(machine_df)

        csv = machine_df.to_csv(index=False, sep=";")

        st.download_button(
            "Download Machine CSV",
            csv,
            "machine_sequence.csv"
        )


# ---------------------------------------------------
# SPEC → Technician Excel
# ---------------------------------------------------

elif operation == "🧠 Spec Excel → Technician Excel":

    uploaded = st.file_uploader(
        "Upload Spec File",
        type=["xlsx","xlsb"]
    )

    if uploaded:

        tech_df = scan_spec_sheet(uploaded)

        st.subheader("Generated Technician Table")

        st.dataframe(tech_df)

        warnings = validate_sequence(tech_df)

        if warnings:

            st.warning("Validation warnings")

            for w in warnings:
                st.write(w)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            tech_df.to_excel(writer,index=False)

        st.download_button(
            "Download Technician Excel",
            output.getvalue(),
            "spec_converted.xlsx"
        )

        csv = tech_df.to_csv(index=False, sep=";")

        st.download_button(
            "Download Machine CSV",
            csv,
            "spec_converted.csv"
        )
