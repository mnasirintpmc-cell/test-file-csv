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

        if df is None or df.empty:
            continue

        name_lower = sheet_name.lower()

        # determine test mode
        test_mode = 1
        if "secondary" in name_lower:
            test_mode = 2

        for i in range(len(df)):

            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                if cell != "test step":
                    continue

                # ------------------------------------------------
                # Validate this is a REAL test table
                # ------------------------------------------------

                col_primary = str(df.iloc[i, j+1]).lower() if j+1 < len(df.columns) else ""
                col_secondary = str(df.iloc[i, j+2]).lower() if j+2 < len(df.columns) else ""

                if (
                    "primary seal gas pressure" not in col_primary
                    or "secondary seal gas pressure" not in col_secondary
                ):
                    continue

                step_col = j

                # ------------------------------------------------
                # Read table rows
                # ------------------------------------------------

                for k in range(i + 1, len(df)):

                    row = df.iloc[k].tolist()

                    step_val = safe_get(row, step_col)

                    if step_val is None:
                        continue

                    text = str(step_val).lower()

                    if "end of" in text:
                        break

                    try:
                        spec_step = int(float(step_val))
                    except:
                        continue

                    primary_cell = safe_get(row, step_col + 1)
                    secondary = to_float(safe_get(row, step_col + 2))
                    speed = to_float(safe_get(row, step_col + 3))
                    temp = safe_get(row, step_col + 4)
                    hold = to_float(safe_get(row, step_col + 5))
                    remarks = safe_get(row, step_col + 8)

                    # Primary pressure rule
                    primary = None

                    if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                        if secondary is not None:
                            primary = secondary + 5
                    else:
                        primary = to_float(primary_cell)

                    if primary is None and secondary is not None:
                        primary = secondary + 5

                    # Temperature rule
                    if isinstance(temp, str) and temp.upper() == "AMB":
                        temp = 60

                    # Duration
                    duration = None
                    if hold is not None:
                        duration = int(hold * 60)

                    # Acceptance rule
                    notes = remarks if remarks not in [None, "", "NA"] else None
                    acceptance = 1 if notes else 0

                    # Pressure routing
                    interspace = None
                    bp_de = None
                    bp_nde = None

                    if test_mode == 1:
                        bp_de = secondary
                        bp_nde = secondary

                    if test_mode == 2:
                        interspace = secondary

                    rows.append({

                        "Spec_Step": spec_step,
                        "Test_Name": sheet_name,

                        "Speed_RPM": speed,
                        "Primary seal Gas Pressure (barg)": primary,

                        "Interspace_Pressure_bar": interspace,
                        "BackPressure_Drive_End_bar": bp_de,
                        "BackPressure_Non_Drive_End_bar": bp_nde,

                        "Gas_Injection_bar": None,

                        "Duration_s": duration,
                        "Temperature_C": temp,

                        "Test_Mode": test_mode,
                        "Acceptance point": acceptance,
                        "Measurement": 1,
                        "Torque_Check": None,
                        "Gas_Type": "Air",

                        "Notes": notes
                    })

    if not rows:
        raise ValueError("No valid test tables detected in the file")

    df = pd.DataFrame(rows)

    df = df.sort_values(["Test_Name", "Spec_Step"])

    df["Step"] = df["Spec_Step"]

    df = df.drop(columns=["Spec_Step"])

    df = df.fillna("NA")

    df = df[["Step"] + [c for c in df.columns if c != "Step"]]

    return df
