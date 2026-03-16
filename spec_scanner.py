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
    if idx is None:
        return None
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


def find_col(header, keywords):

    for i, col in enumerate(header):
        text = str(col).lower()

        for k in keywords:
            if k in text:
                return i

    return None


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

            header_cell = str(df.iloc[i,0]).lower()

            if "test step" not in header_cell and "test point" not in header_cell:
                continue

            header = [str(x).lower() for x in df.iloc[i].tolist()]

            step_idx = find_col(header, ["test step","test point"])
            primary_idx = find_col(header, ["primary seal","inboard seal"])
            secondary_idx = find_col(header, ["secondary seal","outboard seal","process side"])
            speed_idx = find_col(header, ["speed"])
            temp_idx = find_col(header, ["temp"])
            hold_idx = find_col(header, ["hold"])
            remarks_idx = find_col(header, ["remark","comment"])

            if step_idx is None or primary_idx is None or secondary_idx is None:
                continue

            for k in range(i+1, len(df)):

                row = df.iloc[k].tolist()

                step_val = safe_get(row, step_idx)

                if step_val is None:
                    continue

                if "end of" in str(step_val).lower():
                    break

                try:
                    step = int(float(step_val))
                except:
                    continue

                primary_cell = safe_get(row, primary_idx)
                secondary = to_float(safe_get(row, secondary_idx))
                speed = to_float(safe_get(row, speed_idx))
                temp = safe_get(row, temp_idx)
                hold = to_float(safe_get(row, hold_idx))
                remarks = safe_get(row, remarks_idx)

                primary = None

                if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                    if secondary is not None:
                        primary = secondary + 5
                else:
                    primary = to_float(primary_cell)

                if primary is None and secondary is not None:
                    primary = secondary + 5

                if isinstance(temp, str) and temp.upper() == "AMB":
                    temp = 60

                try:
                    duration = int(float(hold) * 60)
                except:
                    duration = 0

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
