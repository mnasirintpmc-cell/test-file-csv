import pandas as pd

try:
    import pyxlsb
except ImportError:
    raise ImportError("Install pyxlsb with: pip install pyxlsb")


def safe_get(row, index):
    """Safely get column value or NA"""
    if index < len(row):
        val = row[index]
        if pd.isna(val):
            return "NA"
        return val
    return "NA"


def to_float(val, default="NA"):
    try:
        return float(val)
    except:
        return default


def scan_spec(file):

    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    for sheet_name, df in sheets.items():

        if df is None or df.empty:
            continue

        for i in range(len(df)):

            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                if cell == "test step":

                    step_col = j

                    # read table rows
                    for k in range(i + 1, len(df)):

                        row = df.iloc[k].tolist()

                        step_val = safe_get(row, step_col)

                        text = str(step_val).lower()

                        if "end of" in text:
                            break

                        try:
                            spec_step = int(float(step_val))
                        except:
                            continue

                        primary = safe_get(row, step_col + 1)
                        secondary = safe_get(row, step_col + 2)
                        speed = safe_get(row, step_col + 3)
                        temp = safe_get(row, step_col + 4)
                        hold = safe_get(row, step_col + 5)
                        remarks = safe_get(row, step_col + 8)

                        primary = to_float(primary, "NA")
                        secondary = to_float(secondary, "NA")
                        speed = to_float(speed, "NA")
                        hold = to_float(hold, 0)

                        if temp != "NA":
                            if str(temp).upper() == "AMB":
                                temp = 60

                        duration = "NA"
                        if hold != "NA":
                            duration = int(float(hold) * 60)

                        rows.append({

                            "Spec_Step": spec_step,
                            "Test_Name": sheet_name,

                            "Speed_RPM": speed,
                            "Primary seal Gas Pressure (barg)": primary,
                            "Interspace_Pressure_bar": "NA",
                            "BackPressure_Drive_End_bar": secondary,
                            "BackPressure_Non_Drive_End_bar": secondary,
                            "Gas_Injection_bar": "NA",

                            "Duration_s": duration,
                            "Temperature_C": temp,

                            "Acceptance point": "NA",
                            "Measurement": 1,
                            "Torque_Check": "NA",
                            "Gas_Type": "Air",

                            "Notes": remarks
                        })

    if not rows:
        raise ValueError("No test tables detected")

    df = pd.DataFrame(rows)

    df = df.sort_values(["Test_Name", "Spec_Step"])

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["Spec_Step"])

    return df
