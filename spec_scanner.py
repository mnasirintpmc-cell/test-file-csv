import pandas as pd

try:
    import pyxlsb
except ImportError:
    raise ImportError("Install pyxlsb: pip install pyxlsb")


def scan_spec(file):

    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    for sheet_name, df in sheets.items():

        for i in range(len(df)):

            # --------------------------------------------------
            # Detect table header
            # --------------------------------------------------
            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                if cell == "test step":

                    step_col = j
                    header_row = i

                    # ------------------------------------------
                    # Read table rows
                    # ------------------------------------------
                    for k in range(header_row + 1, len(df)):

                        step_val = df.iloc[k, step_col]

                        if pd.isna(step_val):
                            continue

                        if "end of" in str(step_val).lower():
                            break

                        try:
                            spec_step = int(float(step_val))
                        except:
                            continue

                        primary = df.iloc[k, step_col + 1]
                        secondary = df.iloc[k, step_col + 2]
                        speed = df.iloc[k, step_col + 3]
                        temp = df.iloc[k, step_col + 4]
                        hold = df.iloc[k, step_col + 5]
                        remarks = df.iloc[k, step_col + 8]

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

                            "Step": None,  # assigned later
                            "Test_Name": sheet_name,
                            "Spec_Step": spec_step,

                            "Speed_RPM": speed,
                            "Primary seal Gas Pressure (barg)": primary,
                            "Interspace_Pressure_bar": 0,
                            "BackPressure_Drive_End_bar": secondary,
                            "BackPressure_Non_Drive_End_bar": secondary,
                            "Gas_Injection_bar": 0,

                            "Temperature_C": temp,
                            "Duration_s": duration,

                            "Acceptance point": 0,
                            "Measurement": 1,
                            "Torque_Check": 0,

                            "Gas_Type": "Air",
                            "Notes": remarks

                        })

    if not rows:
        raise ValueError("No test steps found in any sheet")

    df = pd.DataFrame(rows)

    df = df.sort_values(["Test_Name", "Spec_Step"])

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["Spec_Step"])

    return df
