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


def find_column(header, keyword):

    keyword = keyword.lower()

    for idx, col in enumerate(header):
        if keyword in str(col).lower():
            return idx

    return None


def scan_spec(file):

    engine = _detect_engine(file)

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

            cell = str(df.iloc[i, 0]).lower()

            if "test step" not in cell:
                continue

            header = df.iloc[i].astype(str).tolist()

            step_col = find_column(header, "test step")
            primary_col = find_column(header, "primary seal gas pressure")
            secondary_col = find_column(header, "secondary seal gas pressure")
            speed_col = find_column(header, "speed")
            temp_col = find_column(header, "temp")
            hold_col = find_column(header, "hold")
            remarks_col = find_column(header, "remark")

            for k in range(i + 1, len(df)):

                row = df.iloc[k].tolist()

                step_val = safe_get(row, step_col)

                if step_val is None:
                    continue

                step_text = str(step_val).strip()

                if step_text == "":
                    continue

                if "end of" in step_text.lower():
                    break

                step_num = to_float(step_text)

                if step_num is None or pd.isna(step_num):
                    continue

                try:
                    step = int(step_num)
                except:
                    continue

                primary_cell = safe_get(row, primary_col)
                secondary_cell = safe_get(row, secondary_col)

                secondary = to_float(secondary_cell)

                if secondary is None:
                    secondary = 0

                if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                    primary = secondary + 5
                else:
                    primary = to_float(primary_cell)

                if primary is None:
                    primary = 0

                speed = to_float(safe_get(row, speed_col))

                if speed is None:
                    speed = 0

                temp = safe_get(row, temp_col)

                if isinstance(temp, str) and temp.upper() == "AMB":
                    temp = 60

                hold_val = to_float(safe_get(row, hold_col))

                if hold_val is None or pd.isna(hold_val):
                    duration = 0
                else:
                    duration = int(hold_val * 60)

                remarks = safe_get(row, remarks_col)

                acceptance = 1 if isinstance(remarks, str) and remarks.strip() != "" else 0

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

        df = df.sort_values("Step")

        df = df.drop_duplicates(subset=["Step"], keep="first")

        df = df.reset_index(drop=True)

    return df
