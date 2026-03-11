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

        header_row = None

        # --------------------------------------------------
        # Locate table header
        # --------------------------------------------------

        for i, r in df.iterrows():

            text = str(r[0]).lower()

            if "test step" in text:
                header_row = i
                break

        if header_row is None:
            continue

        # --------------------------------------------------
        # Read rows after header
        # --------------------------------------------------

        for i in range(header_row + 2, len(df)):

            r = df.iloc[i]

            step = r[0]

            # Stop at end of table
            if pd.isna(step):
                break

            if "end of" in str(step).lower():
                break

            try:
                spec_step = int(step)
            except:
                continue

            primary = r[1]
            secondary = r[2]
            speed = r[3]
            temp = r[4]
            hold = r[5]
            remarks = r[8] if len(r) > 8 else ""

            # Safe numeric conversion
            try:
                secondary = float(secondary)
            except:
                continue

            try:
                primary = float(primary)
            except:
                primary = secondary + 5

            try:
                speed = float(speed)
            except:
                speed = 0

            if str(temp).upper() == "AMB":
                temp = 60

            hold = 0 if pd.isna(hold) else hold
            duration = int(hold * 60)

            rows.append({

                "spec_step": spec_step,
                "Speed_RPM": speed,
                "Primary seal Gas Pressure (barg)": primary,
                "Interspace_Pressure_bar": 0,
                "BackPressure_Drive_End_bar": secondary,
                "BackPressure_Non_Drive_End_bar": secondary,
                "Gas_Injection_bar": 0,
                "Duration_s": duration,
                "Acceptance point": 1 if "acceptance" in str(remarks).lower() else 0,
                "Temperature_C": temp,
                "Gas_Type": "Air",
                "Test_Mode": 1,
                "Measurement": 1,
                "Torque_Check": 0,
                "Notes": remarks,
                "Test_Name": sheet_name

            })

    if not rows:
        raise ValueError("No test procedure tables found in the spec")

    df = pd.DataFrame(rows)

    df = df.sort_values("spec_step")

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["spec_step"])

    return df
