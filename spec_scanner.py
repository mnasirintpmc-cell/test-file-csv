import pandas as pd

try:
    import pyxlsb
except ImportError:
    raise ImportError("Install pyxlsb with: pip install pyxlsb")


def safe_get(row, idx):
    if idx < len(row):
        return row[idx]
    return None


def to_float(v):
    try:
        return float(v)
    except:
        return None


def scan_spec(file):

    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    for sheet_name, df in sheets.items():

        if df.empty:
            continue

        for i in range(len(df)):

            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                if cell == "test step":

                    step_col = j

                    for k in range(i + 1, len(df)):

                        row = df.iloc[k].tolist()

                        step_val = safe_get(row, step_col)

                        if step_val is None:
                            continue

                        if "end of" in str(step_val).lower():
                            break

                        try:
                            spec_step = int(float(step_val))
                        except:
                            continue

                        primary = to_float(safe_get(row, step_col + 1))
                        secondary = to_float(safe_get(row, step_col + 2))
                        speed = to_float(safe_get(row, step_col + 3))
                        temp = safe_get(row, step_col + 4)
                        hold = to_float(safe_get(row, step_col + 5))
                        remarks = safe_get(row, step_col + 8)

                        if primary is None and secondary is not None:
                            primary = secondary + 5

                        if speed is None:
                            speed = 0

                        if isinstance(temp, str) and temp.upper() == "AMB":
                            temp = 60

                        duration = None
                        if hold is not None:
                            duration = int(hold * 60)

                        notes = remarks if remarks not in [None, "", "NA"] else None

                        acceptance = 1 if notes else 0

                        rows.append({

                            "Spec_Step": spec_step,
                            "Test_Name": sheet_name,

                            "Speed_RPM": speed,
                            "Primary seal Gas Pressure (barg)": primary,
                            "Interspace_Pressure_bar": None,
                            "BackPressure_Drive_End_bar": secondary,
                            "BackPressure_Non_Drive_End_bar": secondary,
                            "Gas_Injection_bar": None,

                            "Duration_s": duration,
                            "Temperature_C": temp,

                            "Acceptance point": acceptance,
                            "Measurement": 1,
                            "Torque_Check": None,
                            "Gas_Type": "Air",

                            "Notes": notes
                        })

    if not rows:
        raise ValueError("No test tables detected")

    df = pd.DataFrame(rows)

    df = df.sort_values(["Test_Name", "Spec_Step"])

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["Spec_Step"])

    df = df.fillna("NA")

    return df
