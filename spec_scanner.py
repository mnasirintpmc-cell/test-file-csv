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

        # Only process sheets that are actual tests
        if not any(x in name for x in [
            "test",
            "mrt",
            "pressure",
            "static"
        ]):
            continue

        header_row = None
        step_col = None

        # --------------------------------------------------
        # Locate header row containing "Test Step"
        # --------------------------------------------------

        for i in range(len(df)):
            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                if "test step" in cell:

                    header_row = i
                    step_col = j
                    break

            if header_row is not None:
                break

        if header_row is None:
            continue

        # --------------------------------------------------
        # Read rows under the header
        # --------------------------------------------------

        for i in range(header_row + 1, len(df)):

            step_value = df.iloc[i, step_col]

            if pd.isna(step_value):
                break

            if "end of" in str(step_value).lower():
                break

            try:
                spec_step = int(float(step_value))
            except:
                continue

            primary = df.iloc[i, step_col + 1] if step_col + 1 < len(df.columns) else None
            secondary = df.iloc[i, step_col + 2] if step_col + 2 < len(df.columns) else None
            speed = df.iloc[i, step_col + 3] if step_col + 3 < len(df.columns) else 0
            temp = df.iloc[i, step_col + 4] if step_col + 4 < len(df.columns) else 60
            hold = df.iloc[i, step_col + 5] if step_col + 5 < len(df.columns) else 0
            remarks = df.iloc[i, step_col + 8] if step_col + 8 < len(df.columns) else ""

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
        raise ValueError(
            "No test procedure tables detected in the test sheets"
        )

    df = pd.DataFrame(rows)

    df = df.sort_values("spec_step")

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["spec_step"])

    return df
