import pandas as pd

try:
    import pyxlsb
except ImportError:
    raise ImportError("Install pyxlsb: pip install pyxlsb")

try:
    import openpyxl
except ImportError:
    raise ImportError("Install openpyxl: pip install openpyxl")


def safe_get(row, idx):
    if idx < len(row):
        return row[idx]
    return None


def to_float(v):
    try:
        return float(v)
    except:
        return None


def _detect_engine(file):

    name = ""

    if hasattr(file, "name"):
        name = file.name.lower()
    elif isinstance(file, str):
        name = file.lower()

    if name.endswith(".xlsb"):
        return "pyxlsb"

    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        return "openpyxl"

    return "openpyxl"


def scan_spec(file):

    engine = _detect_engine(file)

    if engine == "openpyxl":
        sheets = pd.read_excel(
            file,
            engine=engine,
            sheet_name=None,
            header=None,
            engine_kwargs={"data_only": True}
        )
    else:
        sheets = pd.read_excel(
            file,
            engine=engine,
            sheet_name=None,
            header=None
        )

    rows = []

    for sheet_name, df in sheets.items():

        if df is None or df.empty:
            continue

        name_lower = sheet_name.lower()

        test_mode = 1
        if "secondary" in name_lower:
            test_mode = 2

        for i in range(len(df)):

            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                # accept both step labels
                if cell not in ["test step", "test point"]:
                    continue

                col1 = str(df.iloc[i, j+1]).lower() if j+1 < len(df.columns) else ""
                col2 = str(df.iloc[i, j+2]).lower() if j+2 < len(df.columns) else ""
                col3 = str(df.iloc[i, j+3]).lower() if j+3 < len(df.columns) else ""
                col4 = str(df.iloc[i, j+4]).lower() if j+4 < len(df.columns) else ""

                primary_names = [
                    "primary seal gas pressure",
                    "inboard seal pressure"
                ]

                secondary_names = [
                    "secondary seal gas pressure",
                    "process side gas pressure",
                    "outboard seal pressure"
                ]

                if not any(name in col1 for name in primary_names):
                    continue

                if not any(name in col3 for name in secondary_names):
                    continue

                step_col = j

                # detect API format (two pressure columns)
                api_format = "inboard seal pressure" in col1

                if api_format:
                    primary_offset = 2
                    secondary_offset = 4
                else:
                    primary_offset = 1
                    secondary_offset = 2

                for k in range(i+1, len(df)):

                    row = df.iloc[k].tolist()

                    step_val = safe_get(row, step_col)

                    if step_val is None:
                        continue

                    if "end of" in str(step_val).lower():
                        break

                    try:
                        step = int(float(step_val))
                    except:
                        continue

                    primary_cell = safe_get(row, step_col + primary_offset)
                    secondary = to_float(safe_get(row, step_col + secondary_offset))

                    speed = to_float(safe_get(row, step_col + 3))
                    temp = safe_get(row, step_col + 4)
                    hold = to_float(safe_get(row, step_col + 5))
                    remarks = safe_get(row, step_col + 8)

                    primary = None

                    if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                        if secondary is not None:
                            primary = secondary + 5
                    else:
                        primary = to_float(primary_cell)

                    if primary is None and secondary is not None:
                        primary = secondary + 5

                    if isinstance(temp, str) and str(temp).upper() == "AMB":
                        temp = 60

                    duration = int(hold * 60) if hold is not None else 0

                    acceptance = 1 if isinstance(remarks, str) and remarks.strip() != "" else 0

                    interspace = 0
                    bp_de = 0
                    bp_nde = 0

                    if test_mode == 1:
                        interspace = 0
                        bp_de = secondary
                        bp_nde = secondary
                    else:
                        interspace = secondary
                        bp_de = 0
                        bp_nde = 0

                    rows.append({

                        "Step": step,
                        "Speed_RPM": speed,
                        "Primary seal Gas Pressure (barg)": primary,
                        "Interspace_Pressure_bar": interspace,
                        "BackPressure_Drive_End_bar": bp_de,
                        "BackPressure_Non_Drive_End_bar": bp_nde,
                        "Gas_Injection_bar": 0,
                        "Duration_s": duration,
                        "Acceptance point": acceptance,
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
