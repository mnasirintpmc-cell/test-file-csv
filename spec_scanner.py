import pandas as pd

try:
    import pyxlsb
except ImportError:
    raise ImportError(
        "Missing dependency 'pyxlsb'. Install with: pip install pyxlsb"
    )


def scan_spec(file):

    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    for sheet_name, df in sheets.items():

        name = sheet_name.lower()

        # --------------------------------------------------
        # Only process TEST sheets
        # --------------------------------------------------

        if "test" not in name:
            continue

        mode = 1

        for _, r in df.iterrows():

            text = str(r[0]).lower()

            if "primary" in text:
                mode = 1
                continue

            if "secondary" in text:
                mode = 2
                continue

            # --------------------------------------------------
            # Detect numeric test step
            # --------------------------------------------------

            try:
                spec_step = int(r[0])
            except:
                continue

            primary_spec = r[1]
            secondary = r[2]
            speed = r[3]
            temp = r[4]
            hold = r[5]

            remarks = ""
            if len(r) > 8:
                remarks = str(r[8])

            if pd.isna(secondary):
                continue

            secondary = float(secondary)

            # Primary pressure rule
            if "secondary seal gas pressure" in str(primary_spec).lower():
                primary = secondary + 5
            else:
                try:
                    primary = float(primary_spec)
                except:
                    primary = secondary + 5

            if str(temp).upper() == "AMB":
                temp = 60

            try:
                speed = float(speed)
            except:
                speed = 0

            hold = 0 if pd.isna(hold) else hold
            duration = int(hold * 60)

            if mode == 1:

                interspace = 0
                bp_de = secondary
                bp_nde = secondary

            else:

                interspace = secondary
                bp_de = 0
                bp_nde = 0

            ap = 1 if "acceptance" in remarks.lower() else 0

            rows.append({

                "spec_step": spec_step,
                "Speed_RPM": speed,
                "Primary seal Gas Pressure (barg)": primary,
                "Interspace_Pressure_bar": interspace,
                "BackPressure_Drive_End_bar": bp_de,
                "BackPressure_Non_Drive_End_bar": bp_nde,
                "Gas_Injection_bar": 0,
                "Duration_s": duration,
                "Acceptance point": ap,
                "Temperature_C": temp,
                "Gas_Type": "Air",
                "Test_Mode": mode,
                "Measurement": ap,
                "Torque_Check": 0,
                "Notes": remarks,
                "Spec_Sheet": sheet_name

            })

    if not rows:
        raise ValueError(
            "No test steps found in sheets containing 'Test'"
        )

    df = pd.DataFrame(rows)

    df = df.sort_values("spec_step")

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["spec_step"])

    return df
