elif operation == "👀 View Current Test":
    st.header("👀 View & Edit Current Test")

    file_name = st.selectbox(
        "Select Test File",
        ["MainSealSet2.csv", "SeperationSeal.csv", "SeperationSeal_Base.csv"]
    )

    # Load CSV only when file changes
    if (
        "current_test_name" not in st.session_state
        or st.session_state["current_test_name"] != file_name
    ):
        df = safe_read_csv(file_name)
        st.session_state["current_test_df"] = df
        st.session_state["current_test_name"] = file_name

    df = st.session_state["current_test_df"]
    file_type = detect_file_type(df)

    if file_type == "unknown":
        st.error("❌ Unknown file type")
        st.stop()

    # Convert to technician format
    technician_df = convert_machine_to_technician(df, file_type)

    # Editable table (LIVE)
    st.subheader("✏️ Edit Test Sequence")
    edited_df = editable_dataframe(
        technician_df,
        key="current_test_editor",
        height=500
    )

    st.success(f"Loaded {file_name} ({len(edited_df)} steps)")

    # =====================================================
    # 🔽 LIVE DOWNLOAD SECTION
    # =====================================================

    st.subheader("💾 Download Edited Test (Live)")

    col1, col2 = st.columns(2)

    # ---------- EXCEL DOWNLOAD ----------
    with col1:
        excel_output = create_professional_excel_from_data(
            edited_df,
            file_type
        )

        if excel_output:
            st.download_button(
                label="📥 Download as Excel",
                data=excel_output.getvalue(),
                file_name=f"edited_{file_type}_test_{datetime.now():%Y%m%d_%H%M}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ---------- MACHINE CSV DOWNLOAD ----------
    with col2:
        mapping = get_column_mapping(file_type)

        rename_dict = {
            tech: mach
            for tech, mach in mapping["technician_to_machine"].items()
            if tech in edited_df.columns
        }

        machine_df = edited_df.rename(columns=rename_dict)
        machine_df = convert_to_machine_codes(machine_df, file_type)
        machine_df = machine_df.drop(
            [c for c in ["Step", "Notes"] if c in machine_df.columns],
            axis=1
        )

        csv_data = machine_df.to_csv(index=False, sep=";")

        st.download_button(
            label="📥 Download as Machine CSV",
            data=csv_data,
            file_name=f"edited_{file_type}_test_{datetime.now():%Y%m%d}.csv",
            mime="text/csv"
        )
