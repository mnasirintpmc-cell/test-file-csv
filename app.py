import streamlit as st
import pandas as pd
import io


# ------------------------------------------------
# Read Excel (.xlsx or .xlsb)
# ------------------------------------------------
def read_excel_auto(file):

    name = file.name.lower()

    if name.endswith(".xlsb"):

        return pd.read_excel(
            file,
            header=None,
            engine="pyxlsb"
        )

    return pd.read_excel(file, header=None)


# ------------------------------------------------
# Detect mode
# ------------------------------------------------
def detect_mode(title):

    title = str(title).lower()

    if "secondary" in title:
        return 2

    if "primary" in title:
        return 1

    return 1


# ------------------------------------------------
# Compute primary pressure
# ------------------------------------------------
def compute_primary(primary_spec, secondary):

    text = str(primary_spec).lower()

    if "secondary" in text:
        return float(secondary) + 5

    try:
        return float(primary_spec)
    except:
        return float(secondary) + 5


# ------------------------------------------------
# Apply BP / interspace rule
# ------------------------------------------------
def apply_pressure_rules(mode, secondary):

    if mode == 1:

        interspace = 0
        bp_de = secondary
        bp_nde = secondary

    else:

        interspace = secondary
        bp_de = 0
        bp_nde = 0

    return interspace, bp_de, bp_nde


# ------------------------------------------------
# Scan specification sheet
# ------------------------------------------------
def scan_spec_sheet(file):

    raw = read_excel_auto(file)

    rows = []

    current_mode = 1
    header_found = False

    for _, r in raw.iterrows():

        text = str(r[0])

        if "primary" in text.lower() or "secondary" in text.lower():

            current_mode = detect_mode(text)
            continue


        if "test step" in text.lower():

            header_found = True
            continue


        if not header_found:
            continue


        try:

            primary_spec = r[1]
            secondary = r[2]
            speed = r[3]
            temp = r[4]
            hold = r[5]
            remarks = str(r[8])

        except:
            continue


        if pd.isna(secondary):
            continue


        secondary = float(secondary)

        primary = compute_primary(primary_spec, secondary)

        interspace, bp_de, bp_nde = apply_pressure_rules(
            current_mode,
            secondary
        )


        if str(temp).upper() == "AMB":
            temp = 60


        ap_flag = 1 if "acceptance" in remarks.lower() else 0


        rows.append({

            "Speed_RPM": speed,
            "Primary seal Gas Pressure (barg)": primary,
            "Interspace_Pressure_bar": interspace,
            "BackPressure_Drive_End_bar": bp_de,
            "BackPressure_Non_Drive_End_bar": bp_nde,
            "Gas_Injection_bar": 0,
            "Duration_s": float(hold) * 60,
            "Acceptance point": ap_flag,
            "Temperature_C": temp,
            "Gas_Type": "Air",
            "Test_Mode": current_mode,
            "Measurement": ap_flag,
            "Torque_Check": 0,
            "Notes": remarks

        })


    df = pd.DataFrame(rows)

    df.insert(0, "Step", range(1, len(df)+1))

    return df


# ------------------------------------------------
# Streamlit UI
# ------------------------------------------------

st.set_page_config(layout="wide")

st.title("Seal Test Manager")


operation = st.sidebar.radio(

    "Select Operation",

    [

        "Machine CSV → Technician Excel",
        "Technician Excel → Machine CSV",
        "Spec Excel → Technician Excel"

    ]

)


# ------------------------------------------------
# CSV → Technician Excel
# ------------------------------------------------
if operation == "Machine CSV → Technician Excel":

    uploaded = st.file_uploader("Upload Machine CSV", type=["csv"])

    if uploaded:

        df = pd.read_csv(uploaded, delimiter=";")

        df.insert(0, "Step", range(1, len(df)+1))

        st.dataframe(df)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

            df.to_excel(writer, index=False)

        st.download_button(

            "Download Technician Excel",

            output.getvalue(),

            "technician_sequence.xlsx"

        )


# ------------------------------------------------
# Technician Excel → CSV
# ------------------------------------------------
elif operation == "Technician Excel → Machine CSV":

    uploaded = st.file_uploader("Upload Technician Excel", type=["xlsx"])

    if uploaded:

        df = pd.read_excel(uploaded)

        machine_df = df.drop(columns=["Step","Notes"], errors="ignore")

        st.dataframe(machine_df)

        csv = machine_df.to_csv(index=False, sep=";")

        st.download_button(

            "Download Machine CSV",

            csv,

            "machine_sequence.csv"

        )


# ------------------------------------------------
# Spec → Technician Excel
# ------------------------------------------------
elif operation == "Spec Excel → Technician Excel":

    uploaded = st.file_uploader(

        "Upload Specification File",

        type=["xlsx","xlsb"]

    )

    if uploaded:

        tech_df = scan_spec_sheet(uploaded)

        st.subheader("Generated Technician Table")

        st.dataframe(tech_df)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

            tech_df.to_excel(writer, index=False)

        st.download_button(

            "Download Technician Excel",

            output.getvalue(),

            "spec_converted.xlsx"

        )

        csv = tech_df.to_csv(index=False, sep=";")

        st.download_button(

            "Download Machine CSV",

            csv,

            "spec_converted.csv"

        )
