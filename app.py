# =====================================================
# MAIN STREAMLIT APP
# =====================================================

def main():

    st.title("⚙️ DGS Test Manager")

    if "master_df" not in st.session_state:
        st.session_state.master_df = None

    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    user_name = st.sidebar.text_input("Operator Name")

    operation = st.sidebar.radio(
        "Operation",
        [
            "CSV → Excel",
            "Excel → CSV",
            "Spec → Technician Excel"
        ]
    )

    # -------------------------------------------------
    # CSV → EXCEL
    # -------------------------------------------------

    if operation == "CSV → Excel":

        uploaded = st.file_uploader(
            "Upload Machine CSV",
            type=["csv"]
        )

        if uploaded:

            df = safe_read_csv(uploaded)

            tech_df = convert_machine_to_technician(df)

            excel = create_professional_excel_from_data(
                tech_df,
                "main_seal",
                user_name=user_name,
                source_name=uploaded.name
            )

            st.download_button(
                "Download Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )

    # -------------------------------------------------
    # EXCEL → CSV
    # -------------------------------------------------

    elif operation == "Excel → CSV":

        uploaded = st.file_uploader(
            "Upload Technician Excel",
            type=["xlsx"]
        )

        if uploaded:

            df = pd.read_excel(uploaded)

            file_hash = hashlib.md5(
                uploaded.getvalue()
            ).hexdigest()

            if st.session_state.last_uploaded_file != file_hash:

                st.session_state.master_df = df.copy()
                st.session_state.last_uploaded_file = file_hash

            edited = editable_dataframe(df)

            machine_df = build_machine_csv(edited)

            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False, sep=";"),
                file_name="machine_sequence.csv"
            )

    # -------------------------------------------------
    # SPEC → TECHNICIAN EXCEL
    # -------------------------------------------------

    elif operation == "Spec → Technician Excel":

        uploaded = st.file_uploader(
            "Upload Spec (.xlsb, .xlsm, .xlsx)",
            type=["xlsb", "xlsm", "xlsx"]
        )

        if uploaded:

            spec_df = scan_spec(uploaded)

            file_hash = hashlib.md5(
                uploaded.getvalue()
            ).hexdigest()

            if st.session_state.last_uploaded_file != file_hash:

                st.session_state.master_df = spec_df.copy()
                st.session_state.last_uploaded_file = file_hash

            edited = editable_dataframe(spec_df)

            excel = create_professional_excel_from_data(
                edited,
                "main_seal",
                user_name=user_name,
                source_name=uploaded.name
            )

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )


if __name__ == "__main__":
    main()
