import pandas as pd


def detect_mode(title):

    title = str(title).lower()

    if "primary" in title:
        return 1

    if "secondary" in title:
        return 2

    return 1


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


def compute_primary(primary_spec, secondary):

    text = str(primary_spec).lower()

    if "secondary" in text:
        return float(secondary) + 5

    try:
        return float(primary_spec)
    except:
        return float(secondary) + 5


def scan_spec_sheet(file):

    raw = pd.read_excel(file, header=None)

    rows = []

    mode = 1
    header_found = False

    for i, row in raw.iterrows():

        text = str(row[0])

        if "primary" in text.lower() or "secondary" in text.lower():

            mode = detect_mode(text)
            continue


        if "test step" in text.lower():

            header_found = True
            continue


        if not header_found:
            continue


        try:

            primary_spec = row[1]
            secondary = row[2]
            speed = row[3]
            temp = row[4]
            hold = row[5]
            remarks = str(row[8])

        except:
            continue


        if pd.isna(secondary):
            continue


        secondary = float(secondary)

        primary = compute_primary(primary_spec, secondary)

        interspace, bp_de, bp_nde = apply_pressure_rules(
            mode,
            secondary
        )


        if str(temp).upper() == "AMB":
            temp = 60


        ap = 1 if "acceptance" in remarks.lower() else 0


        rows.append({

            "Speed_RPM": speed,
            "Primary seal Gas Pressure (barg)": primary,
            "Interspace_Pressure_bar": interspace,
            "BackPressure_Drive_End_bar": bp_de,
            "BackPressure_Non_Drive_End_bar": bp_nde,
            "Gas_Injection_bar": 0,
            "Duration_s": hold * 60,
            "Acceptance point": ap,
            "Temperature_C": temp,
            "Gas_Type": "Air",
            "Test_Mode": mode,
            "Measurement": ap,
            "Torque_Check": 0,
            "Notes": remarks

        })


    df = pd.DataFrame(rows)

    df.insert(0, "Step", range(1, len(df)+1))

    return df
