import streamlit as st
import pandas as pd
from test_rules import TEST_RULES


def test_builder_ui():

    st.subheader("Test Sequence Builder")

    available_tests = list(TEST_RULES.keys())

    if "selected_tests" not in st.session_state:
        st.session_state.selected_tests = []

    col1, col2 = st.columns(2)

    with col1:

        selected_test = st.selectbox(
            "Select test to add",
            available_tests
        )

        if st.button("Add Test"):

            st.session_state.selected_tests.append(selected_test)

    with col2:

        if st.button("Clear Sequence"):
            st.session_state.selected_tests = []

    st.write("### Test Order")

    for i, t in enumerate(st.session_state.selected_tests, 1):
        st.write(f"{i}. {t}")

    if st.button("Generate Test Table"):

        df = generate_test_table(st.session_state.selected_tests)

        st.session_state.generated_test = df

        st.dataframe(df)


def generate_test_table(test_list):

    rows = []
    step = 1

    for test in test_list:

        rule = TEST_RULES[test]

        rows.append({

            "Step": step,
            "Test_Name": test,
            "Speed_RPM": rule.get("rpm", 0),
            "Primary seal Gas Pressure (barg)": 0,
            "Interspace_Pressure_bar": 0,
            "BackPressure_Drive_End_bar": 0,
            "BackPressure_Non_Drive_End_bar": 0,
            "Temperature_C": 60 if rule.get("temperature") == "AMB" else 160,
            "Gas_Type": "Air",
            "Test_Mode": rule.get("mode", 1),
            "Duration_s": 2,
            "Acceptance point": 0,
            "Measurement": 0,
            "Torque_Check": rule.get("torque", 0),
            "Gas_Injection": 0,
            "Notes": ""
        })

        step += 1

    return pd.DataFrame(rows)
