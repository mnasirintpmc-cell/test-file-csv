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

    filename = ""

    if isinstance(file, str):
        filename = file.lower()
    elif hasattr(file, "name"):
        filename = file.name.lower()

    if filename.endswith(".xlsb"):
        return "pyxlsb"

    if filename.endswith(".xlsx") or filename.endswith(".xlsm"):
        return "openpyxl"

    return "openpyxl"


def find_column(header, keywords):

    for idx, col in enumerate(header):
        text = str(col).lower()
        for k in keywords:
            if k in text:
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

        header_row = None

        # find first header row only
        for i in range(len(df)):
            row_text = str(df.iloc[i,0]).lower()

            if "test step" in row_text or "test point" in row_text:
                header_row = i
                break

        if header_row is None:
            continue

        header = [str(x).lower() for x in df.iloc[header_row].tolist()]

        step_col = find_column(header, ["test step","test point"])

        primary_col = find_column(header, [
            "primary seal",
            "inboard seal"
        ])

        secondary_col = find_column(header, [
            "secondary seal",
            "outboard seal",
            "process side"
        ])

        speed_col = find_column(header, ["speed"])
        temp_col = find_column(header, ["temp"])
        hold_col = find_column(header, ["hold"])
        remarks_col = find_column(header, ["remark","comment"])

        if step_col is None:
            continue

        # read table rows
        for k in range(header_row+1, len(df)):

            row = df.iloc[k].tolist()

            step_val = safe_get(row, step_col)

            # stop table when step column becomes empty
            if step_val is None or str(step_val).strip() == "":
                break

            if "end of" in str(step_val).lower():
                break

            try:
                step = int(float(step_val))
            except:
                continue

            primary_cell = safe_get(row, primary_col)
            secondary = to_float(safe_get(row, secondary_col))
            speed = to_float(safe_get(row, speed_col))
            temp = safe_get(row, temp_col)
            hold = to_float(safe_get(row, hold_col))
            remarks = safe_get(row, remarks_col)

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
