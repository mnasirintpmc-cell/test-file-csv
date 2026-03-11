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
        "📄 Spec → Technician Excel"

    ]

)


def format_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        df.to_excel(writer, index=False, sheet_name="Test Sequence")

        workbook = writer.book
        worksheet = writer.sheets["Test Sequence"]

        header_format = workbook.add_format({

            "bold": True,
            "text_wrap": True,
            "valign": "middle",
            "align": "center",
            "fg_color": "#0070C0",
            "font_color": "white",
            "border": 1

        })

        cell_format = workbook.add_format({

            "border": 1,
            "valign": "middle"

        })

        for col_num, column in enumerate(df.columns):
            worksheet.write(0, col_num, column, header_format)

        for i, col in enumerate(df.columns):

            max_len = max(

                df[col].astype(str).map(len).max(),
                len(col)

            ) + 3

            worksheet.set_column(i, i, max_len, cell_format)

        worksheet.freeze_panes(1, 0)

    return output.getvalue()


# --------------------------------------------------
# CSV → TECHNICIAN EXCEL
# --------------------------------------------------

if operation == "📤 Machine CSV → Technician Excel":

    uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

    if uploaded:

        df = pd.read_csv(uploaded, delimiter=";")

        df.insert(0, "Step", range(1, len(df)+1))

        edited = st.data_editor(df, use_container_width=True)

        excel_file = format_excel(edited)

        st.download_button(

            "Download Technician Excel",
            excel_file,
            "technician_sequence.xlsx"

        )


# --------------------------------------------------
# SPEC → TECHNICIAN EXCEL
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

        excel_file = format_excel(edited)

        st.download_button(

            "Download Technician Excel",
            excel_file,
            "technician_sequence.xlsx"

        )
