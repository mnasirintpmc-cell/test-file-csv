import streamlit as st
import pandas as pd
import io

from spec_scanner import scan_spec
from test_builder import TestBuilder
from validator import validate_sequence


st.set_page_config(layout="wide")

st.title("⚙️ Seal Test Manager")


operation = st.sidebar.radio(

    "Operation",

    [

        "📤 Machine CSV → Technician Excel",
        "🔄 Technician Excel → Machine CSV",
        "📄 Spec → Technician Excel"

    ]

)


# --------------------------------------------------
# CSV → TECHNICIAN
# --------------------------------------------------

if operation == "📤 Machine CSV → Technician Excel":

    uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

    if uploaded:

        df = pd.read_csv(uploaded, delimiter=";")

        df.insert(0, "Step", range(1, len(df)+1))

        edited = st.data_editor(df, use_container_width=True)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            edited.to_excel(writer, index=False)

        st.download_button(
            "Download Technician Excel",
            output.getvalue(),
            "technician_sequence.xlsx"
        )


# --------------------------------------------------
# TECHNICIAN → CSV
# --------------------------------------------------

elif operation == "🔄 Technician Excel → Machine CSV":

    uploaded = st.file_uploader("Upload Technician Excel", type=["xlsx"])

    if uploaded:

        df = pd.read_excel(uploaded)

        edited = st.data_editor(df, use_container_width=True)

        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))

        machine_df = edited.drop(columns=["Step","Notes"], errors="ignore")

        csv = machine_df.to_csv(index=False, sep=";")

        st.download_button(
            "Download Machine CSV",
            csv,
            "machine_sequence.csv"
        )


# --------------------------------------------------
# SPEC → TECHNICIAN
# --------------------------------------------------

elif operation == "📄 Spec → Technician Excel":

    uploaded = st.file_uploader(
        "Upload Spec (.xlsb)",
        type=["xlsb"]
    )

    if uploaded:

        spec_df = scan_spec(uploaded)

        edited = st.data_editor(spec_df, use_container_width=True)

        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            edited.to_excel(writer, index=False)

        st.download_button(
            "Download Technician Excel",
            output.getvalue(),
            "technician_sequence.xlsx"
        )

        csv = edited.drop(columns=["Step","Notes"]).to_csv(
            index=False,
            sep=";"
        )

        st.download_button(
            "Download Machine CSV",
            csv,
            "machine_sequence.csv"
        )
