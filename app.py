import streamlit as st
import pandas as pd
from spec_scanner import scan_spec_sheet
from validator import validate_sequence


st.set_page_config(layout="wide")

st.title("Seal Test Spec → Technician Converter")


uploaded = st.file_uploader(
    "Upload Specification Excel",
    type=["xlsx"]
)


if uploaded:

    st.subheader("Scanning specification...")

    tech_df = scan_spec_sheet(uploaded)

    st.subheader("Generated Technician Table")

    st.dataframe(tech_df)


    warnings = validate_sequence(tech_df)

    if warnings:

        st.warning("Validation warnings")

        for w in warnings:
            st.write(w)


    csv = tech_df.to_csv(index=False, sep=";")


    st.download_button(

        "Download Machine CSV",
        csv,
        file_name="seal_test_sequence.csv",
        mime="text/csv"
    )


    excel_buffer = tech_df.to_excel(
        "technician_output.xlsx",
        index=False
    )


    st.download_button(

        "Download Technician Excel",
        open("technician_output.xlsx", "rb"),
        file_name="technician_output.xlsx"
    )
