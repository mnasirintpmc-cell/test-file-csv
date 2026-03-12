def main():

    st.title("⚙️ Seal Test Manager")

    operation = st.sidebar.radio(
        "Operation",
        [
            "Download Template",
            "Machine CSV → Technician Excel",
            "Technician Excel → Machine CSV",
            "View Current Test",
            "Spec → Technician Excel"
        ]
    )

    base_dir = os.path.dirname(__file__)

    # -----------------------------------------------------
    # DOWNLOAD TEMPLATE
    # -----------------------------------------------------

    if operation == "Download Template":

        seal = st.selectbox("Seal Type", ["Main Seal", "Separation Seal"])

        template = "MainSealSet2.csv" if seal == "Main Seal" else "SeperationSeal.csv"

        file_type = "main_seal" if seal == "Main Seal" else "separation_seal"

        df = safe_read_csv(os.path.join(base_dir, template))

        tech_df = convert_machine_to_technician(df, file_type)

        excel = create_professional_excel_from_data(tech_df, file_type)

        st.download_button(
            "Download Template",
            excel.getvalue(),
            file_name="template.xlsx"
        )

    # -----------------------------------------------------
    # MACHINE CSV → TECHNICIAN
    # -----------------------------------------------------

    elif operation == "Machine CSV → Technician Excel":

        uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

        if uploaded:

            df = safe_read_csv(uploaded)

            file_type = detect_file_type(df)

            tech = convert_machine_to_technician(df, file_type)

            edited = editable_dataframe(tech)

            excel = create_professional_excel_from_data(edited, file_type)

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )

    # -----------------------------------------------------
    # TECHNICIAN → MACHINE CSV
    # -----------------------------------------------------

    elif operation == "Technician Excel → Machine CSV":

        uploaded = st.file_uploader("Upload Technician Excel", type=["xlsx"])

        if uploaded:

            df = pd.read_excel(uploaded)

            file_type = detect_file_type(df)

            edited = editable_dataframe(df)

            mapping = get_column_mapping(file_type)

            machine_df = convert_to_machine_codes(
                edited.rename(columns=mapping["technician_to_machine"])
            ).drop(columns=["Step", "Notes"], errors="ignore")

            st.download_button(
                "Download Machine CSV",
                machine_df.to_csv(index=False, sep=";"),
                file_name="machine_sequence.csv"
            )

    # -----------------------------------------------------
    # VIEW CURRENT TEST
    # -----------------------------------------------------

    elif operation == "View Current Test":

        seal = st.selectbox("Seal Type", ["Main Seal", "Separation Seal"])

        template = "MainSealSet2.csv" if seal == "Main Seal" else "SeperationSeal.csv"

        df = safe_read_csv(os.path.join(base_dir, template))

        file_type = detect_file_type(df)

        edited = editable_dataframe(
            convert_machine_to_technician(df, file_type)
        )

        excel = create_professional_excel_from_data(edited, file_type)

        st.download_button(
            "Download Excel",
            excel.getvalue(),
            file_name="current_test.xlsx"
        )

    # -----------------------------------------------------
    # SPEC → TECHNICIAN
    # -----------------------------------------------------

    elif operation == "Spec → Technician Excel":

        uploaded = st.file_uploader(
            "Upload Spec (.xlsb, .xlsm, .xls)",
            type=["xlsb", "xlsm", "xls"]
        )

        if uploaded:

            spec_df = scan_spec(uploaded)

            edited = editable_dataframe(spec_df)

            excel = create_professional_excel_from_data(edited, "main_seal")

            st.download_button(
                "Download Technician Excel",
                excel.getvalue(),
                file_name="technician_sequence.xlsx"
            )
