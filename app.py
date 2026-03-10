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

        try:
            df = pd.read_csv(uploaded, delimiter=";")
        except Exception as e:
            st.error(f"CSV read error: {e}")
            st.stop()

        df.insert(0, "Step", range(1, len(df)+1))

        edited = st.data_editor(df, use_container_width=True)

        edited["Step"] = range(1, len(edited)+1)

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

        try:
            df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Excel read error: {e}")
            st.stop()

        edited = st.data_editor(df, use_container_width=True)

        edited["Step"] = range(1, len(edited)+1)

        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))
        else:
            st.success("Sequence validation passed ✔")

        machine_df = edited.drop(columns=["Step","Notes"], errors="ignore")

        machine_df = machine_df.fillna("")

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

        try:
            spec_df = scan_spec(uploaded)
        except Exception as e:
            st.error(f"Spec read error: {e}")
            st.stop()

        edited = st.data_editor(spec_df, use_container_width=True)

        edited["Step"] = range(1, len(edited)+1)

        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))
        else:
            st.success("Sequence validation passed ✔")

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            edited.to_excel(writer, index=False)

        st.download_button(
            "Download Technician Excel",
            output.getvalue(),
            "technician_sequence.xlsx"
        )

        machine_df = edited.drop(columns=["Step","Notes"], errors="ignore")

        machine_df = machine_df.fillna("")

        csv = machine_df.to_csv(index=False, sep=";")

        st.download_button(
            "Download Machine CSV",
            csv,
            "machine_sequence.csv"
        )
