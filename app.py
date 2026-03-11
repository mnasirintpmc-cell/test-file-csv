import streamlit as st
import pandas as pd
import io

from spec_scanner import scan_spec
from validator import validate_sequence

st.set_page_config(layout="wide")

st.title("⚙️ Seal Test Manager")

operation = st.sidebar.radio(
    "Operation",
    [
        "📄 Spec → Technician Excel",
        "🔄 Technician Excel → Machine CSV"
    ]
)

# --------------------------------------------------
# SPEC → TECHNICIAN
# --------------------------------------------------

if operation == "📄 Spec → Technician Excel":

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

        st.subheader("Review Extracted Test Sequence")

        edited = st.data_editor(
            spec_df,
            use_container_width=True
        )

        # validation
        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))
        else:
            st.success("Validation passed")

        if st.button("Approve and Generate Technician Excel"):

            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                edited.to_excel(writer, index=False)

            st.download_button(
                "Download Technician Excel",
                output.getvalue(),
                "technician_sequence.xlsx"
            )


# --------------------------------------------------
# TECHNICIAN → MACHINE CSV
# --------------------------------------------------

elif operation == "🔄 Technician Excel → Machine CSV":

    uploaded = st.file_uploader(
        "Upload Technician Excel",
        type=["xlsx"]
    )

    if uploaded:

        df = pd.read_excel(uploaded)

        edited = st.data_editor(df, use_container_width=True)

        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))

        machine_df = edited.drop(columns=["Step", "Notes"], errors="ignore")

        csv = machine_df.to_csv(index=False, sep=";")

        st.download_button(
            "Download Machine CSV",
            csv,
            "machine_sequence.csv"
        )
