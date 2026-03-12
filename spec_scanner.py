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

                col_primary = str(df.iloc[i, j+1]).lower() if j+1 < len(df.columns) else ""
                col_secondary = str(df.iloc[i, j+2]).lower() if j+2 < len(df.columns) else ""

                if (
                    "primary seal gas pressure" not in col_primary
                    or "secondary seal gas pressure" not in col_secondary
                ):
                    continue

                step_col = j

                for k in range(i + 1, len(df)):

                    row = df.iloc[k].tolist()

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

                    # pressure rule
                    primary = None

                    try:
                        primary = float(primary_cell)
                    except:
                        try:
                            primary = float(secondary) + 5
                        except:
                            primary = 0

                    try:
                        secondary = float(secondary)
                    except:
                        secondary = 0

                    # pressure routing
                    interspace = 0
                    bp_de = 0
                    bp_nde = 0

                    if test_mode == 1:
                        bp_de = secondary
                        bp_nde = secondary
                    else:
                        interspace = secondary

                    rows.append({

                        "Step": step,
                        "Speed_RPM": speed,
                        "Primary seal Gas Pressure (barg)": primary,
                        "Interspace_Pressure_bar": interspace,
                        "BackPressure_Drive_End_bar": bp_de,
                        "BackPressure_Non_Drive_End_bar": bp_nde,
                        "Gas_Injection_bar": 0,
                        "Duration_s": hold * 60 if hold else 0,
                        "Acceptance point": 1 if isinstance(remarks,str) else 0,
                        "Temperature_C": temp,
                        "Gas_Type": "Air",
                        "Test_Mode": test_mode,
                        "Measurement": 1,
                        "Torque_Check": 0,
                        "Notes": remarks if remarks else ""

                    })

    df = pd.DataFrame(rows)

    return df
