import pandas as pd


# ---------------------------------------------------
# SPEC TABLE DETECTION
# ---------------------------------------------------

def _find_test_tables(df):

    tables = []

    for r in range(len(df)):
        for c in range(len(df.columns)):

            val = str(df.iloc[r, c]).strip().lower()

            if val != "test step":
                continue

            primary = str(df.iloc[r, c+1]).lower() if c+1 < len(df.columns) else ""
            secondary = str(df.iloc[r, c+2]).lower() if c+2 < len(df.columns) else ""

            if (
                "primary seal gas pressure" in primary and
                "secondary seal gas pressure" in secondary
            ):
                tables.append((r, c))

    return tables


# ---------------------------------------------------
# PRESSURE ROUTING
# ---------------------------------------------------

def _route_pressures(test_mode, secondary):

    inter = 0
    bp_de = 0
    bp_nde = 0

    if test_mode == 1:
        bp_de = secondary
        bp_nde = secondary
    else:
        inter = secondary

    return inter, bp_de, bp_nde


# ---------------------------------------------------
# PRIMARY PRESSURE RULE
# ---------------------------------------------------

def _resolve_primary(primary_cell, secondary):

    try:
        return float(primary_cell)
    except:

        try:
            return float(secondary) + 5
        except:
            return 0


# ---------------------------------------------------
# MAIN SCANNER
# ---------------------------------------------------

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

        name = sheet_name.lower()

        test_mode = 1
        if "secondary" in name:
            test_mode = 2

        tables = _find_test_tables(df)

        for (header_row, step_col) in tables:

            for r in range(header_row + 1, len(df)):

                row = df.iloc[r].tolist()

                step_val = row[step_col]

                if step_val is None:
                    continue

                if "end of" in str(step_val).lower():
                    break

                try:
                    step = int(float(step_val))
                except:
                    continue

                primary_cell = row[step_col + 1]
                secondary = row[step_col + 2]
                speed = row[step_col + 3]
                temp = row[step_col + 4]
                hold = row[step_col + 5]
                remarks = row[step_col + 8]

                try:
                    secondary = float(secondary)
                except:
                    secondary = 0

                primary = _resolve_primary(primary_cell, secondary)

                inter, bp_de, bp_nde = _route_pressures(test_mode, secondary)

                rows.append({

                    "Step": step,
                    "Speed_RPM": speed,
                    "Primary seal Gas Pressure (barg)": primary,
                    "Interspace_Pressure_bar": inter,
                    "BackPressure_Drive_End_bar": bp_de,
                    "BackPressure_Non_Drive_End_bar": bp_nde,
                    "Gas_Injection_bar": 0,
                    "Duration_s": hold * 60 if hold else 0,
                    "Acceptance point": 1 if isinstance(remarks, str) else 0,
                    "Temperature_C": temp,
                    "Gas_Type": "Air",
                    "Test_Mode": test_mode,
                    "Measurement": 1,
                    "Torque_Check": 0,
                    "Notes": remarks if remarks else ""

                })

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.sort_values("Step").reset_index(drop=True)

    return df
