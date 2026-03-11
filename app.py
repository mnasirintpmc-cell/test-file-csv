import streamlit as st
import pandas as pd
import io

from spec_scanner import scan_spec

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

        header = workbook.add_format({

            "bold": True,
            "align": "center",
            "valign": "middle",
            "fg_color": "#0070C0",
            "font_color": "white",
            "border": 1

        })

        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header)

        for i, col in enumerate(df.columns):

            width = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 3

            worksheet.set_column(i, i, width)

        worksheet.freeze_panes(1, 0)

    return output.getvalue()


def validate_sequence(df):

    warnings = []

    for _, row in df.iterrows():

        step = row.get("Step")

        try:
            primary = float(row["Primary seal Gas Pressure (barg)"])
        except:
            continue

        try:
            inter = float(row["Interspace_Pressure_bar"])
        except:
            inter = 0

        if primary < inter:

            warnings.append(
                f"Step {step}: Primary pressure lower than interspace"
            )

        if inter > 0 and primary - inter < 0.2:

            warnings.append(
                f"Step {step}: ΔP < 0.2 bar"
            )

    return warnings


# --------------------------------------------------
# CSV → TECHNICIAN
# --------------------------------------------------

if operation == "📤 Machine CSV → Technician Excel":

    uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

    if uploaded:

        df = pd.read_csv(uploaded, delimiter=";")

        if "edited_df" not in st.session_state:
            st.session_state.edited_df = df

        edited = st.data_editor(
            st.session_state.edited_df,
            use_container_width=True,
            num_rows="dynamic"
        )

        st.session_state.edited_df = edited

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

        if "edited_df" not in st.session_state:
            st.session_state.edited_df = df

        edited = st.data_editor(
            st.session_state.edited_df,
            use_container_width=True,
            num_rows="dynamic"
        )

        st.session_state.edited_df = edited

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

        if "edited_df" not in st.session_state:
            st.session_state.edited_df = spec_df

        edited = st.data_editor(
            st.session_state.edited_df,
            use_container_width=True,
            num_rows="dynamic"
        )

        st.session_state.edited_df = edited

        warnings = validate_sequence(edited)

        if warnings:
            st.warning("\n".join(warnings))

        excel = format_excel(edited)

        st.download_button(
            "Download Technician Excel",
            excel,
            "technician_sequence.xlsx"
        )
