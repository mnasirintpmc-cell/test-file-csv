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
        "📤 Machine CSV → Technician Excel",
        "🔄 Technician Excel → Machine CSV",
        "📄 Spec → Technician Excel"
    ]

)


def format_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        df.to_excel(writer, index=False)

        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        header_format = workbook.add_format({

            "bold": True,
            "align": "center",
            "valign": "middle",
            "fg_color": "#0070C0",
            "font_color": "white",
            "border": 1

        })

        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_format)

        for i, col in enumerate(df.columns):

            width = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 3

            worksheet.set_column(i, i, width)

        worksheet.freeze_panes(1, 0)

    return output.getvalue()


# --------------------------------------------------
# CSV → TECHNICIAN
# --------------------------------------------------

if operation == "📤 Machine CSV → Technician Excel":

    uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

    if uploaded:

        df = pd.read_csv(uploaded, delimiter=";")

        df.insert(0, "Step", range(1, len(df)+1))

        edited = st.data_editor(df, use_container_width=True)

        excel = format_excel(edited)

        st.download_button(
            "Download Technician Excel",
            excel,
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

        machine_df = edited.drop(columns=["Notes"], errors="ignore")

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

    uploaded = st.file_uploader("Upload Spec (.xlsb)", type=["xlsb"])

    if uploaded:

        try:
            spec_df = scan_spec(uploaded)
        except Exception as e:
            st.error(f"Spec read error: {e}")
            st.stop()

        edited = st.data_editor(spec_df, use_container_width=True)

        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))

        excel = format_excel(edited)

        st.download_button(
            "Download Technician Excel",
            excel,
            "technician_sequence.xlsx"
        )
