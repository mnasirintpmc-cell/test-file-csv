import pandas as pd


def scan_spec(file):

    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    for sheet_name, df in sheets.items():

        mode = 1
        header_found = False

        for _, r in df.iterrows():

            text = str(r[0]).lower()

            if "primary" in text:
                mode = 1
                continue

            if "secondary" in text:
                mode = 2
                continue

            if "test step" in text:
                header_found = True
                continue

            if not header_found:
                continue

            try:

                spec_step = int(r[0])
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

            # Primary pressure logic
            if "secondary seal gas pressure" in str(primary_spec).lower():
                primary = secondary + 5
            else:
                try:
                    primary = float(primary_spec)
                except:
                    primary = secondary + 5

            if str(temp).upper() == "AMB":
                temp = 60

            # Pressure rules
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

    df = df.sort_values("spec_step")

    df.insert(0, "Step", range(1, len(df)+1))

    df = df.drop(columns=["spec_step"])

    return df
