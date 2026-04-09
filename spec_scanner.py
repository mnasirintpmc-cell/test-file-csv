import pandas as pd
import sqlite3
from sqlalchemy import create_engine

# =========================
# DB CONFIG (PostgreSQL)
# =========================
DB_URL = "postgresql+psycopg2://user:password@localhost:5432/testdb"
engine = create_engine(DB_URL)

# =========================
# SAFE HELPERS
# =========================
def safe_get(row, idx):
    if idx is None or idx < 0 or idx >= len(row):
        return None
    return row[idx]

def to_float(v):
    try:
        if v is None:
            return None
        v = str(v).replace(",", "").strip()
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
    return "openpyxl"

# =========================
# HEADER DETECTION
# =========================
def find_header_row(df):
    for i in range(len(df)):
        row = df.iloc[i].astype(str).str.lower()
        if any("step" in c for c in row):
            return i
    return None

def build_column_map(header_row):
    col_map = {}

    for idx, col in enumerate(header_row.astype(str).str.lower()):

        if "step" in col:
            col_map["step"] = idx
        elif "primary" in col:
            col_map["primary"] = idx
        elif "secondary" in col:
            col_map["secondary"] = idx
        elif "speed" in col:
            col_map["speed"] = idx
        elif "temp" in col:
            col_map["temp"] = idx
        elif "hold" in col or "duration" in col:
            col_map["hold"] = idx
        elif "remark" in col:
            col_map["remarks"] = idx

    return col_map

# =========================
# ORIGINAL SCANNER (KEEP)
# =========================
def scan_spec(file):

    engine_type = _detect_engine(file)

    sheets = pd.read_excel(file, engine=engine_type, sheet_name=None, header=None)

    rows = []

    for sheet_name, df in sheets.items():

        if df is None or df.empty:
            continue

        for i in range(len(df)):
            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                if cell != "test step":
                    continue

                step_col = j

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

                    primary_cell = safe_get(row, step_col+1)
                    secondary = to_float(safe_get(row, step_col+2))
                    speed = to_float(safe_get(row, step_col+3))
                    temp = safe_get(row, step_col+4)
                    hold = to_float(safe_get(row, step_col+5))
                    remarks = safe_get(row, step_col+8)

                    # TEST MODE
                    row_test_mode = 1
                    if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                        row_test_mode = 2

                    # PRIMARY
                    primary = to_float(primary_cell)
                    if primary is None and secondary is not None:
                        primary = secondary + 10

                    # TEMP
                    if isinstance(temp, str) and temp.upper() == "AMB":
                        temp = 60

                    duration = hold if hold else 0

                    acceptance = 1 if isinstance(remarks, str) and "acceptance" in remarks.lower() else 0

                    interspace = 0
                    bp_de = 0
                    bp_nde = 0

                    if row_test_mode == 1:
                        bp_de = secondary
                        bp_nde = secondary
                    else:
                        interspace = secondary

                    rows.append({
                        "Step": step,
                        "Row_Type": "PROCESS",
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
                        "Test_Mode": row_test_mode,
                        "Measurement": 1,
                        "Torque_Check": 0,
                        "Notes": remarks if remarks else ""
                    })

    return pd.DataFrame(rows)

# =========================
# FALLBACK SCANNER (ROBUST)
# =========================
def scan_spec_fallback(file):

    engine_type = _detect_engine(file)

    sheets = pd.read_excel(file, engine=engine_type, sheet_name=None, header=None)

    rows = []

    for sheet_name, df in sheets.items():

        if df is None or df.empty:
            continue

        df = df.fillna(method="ffill")

        header_idx = find_header_row(df)
        if header_idx is None:
            continue

        header = df.iloc[header_idx]
        col_map = build_column_map(header)

        for i in range(header_idx + 1, len(df)):

            row = df.iloc[i].tolist()
            step = to_float(safe_get(row, col_map.get("step")))

            if step is None:
                continue

            rows.append({
                "Step": int(step),
                "Row_Type": "PROCESS",
                "Speed_RPM": to_float(safe_get(row, col_map.get("speed"))),
                "Primary seal Gas Pressure (barg)": to_float(safe_get(row, col_map.get("primary"))),
                "Interspace_Pressure_bar": to_float(safe_get(row, col_map.get("secondary"))),
                "BackPressure_Drive_End_bar": 0,
                "BackPressure_Non_Drive_End_bar": 0,
                "Gas_Injection_bar": 0,
                "Duration_s": to_float(safe_get(row, col_map.get("hold"))) or 0,
                "Acceptance point": 0,
                "Temperature_C": to_float(safe_get(row, col_map.get("temp"))) or 60,
                "Gas_Type": "Air",
                "Test_Mode": 1,
                "Measurement": 1,
                "Torque_Check": 0,
                "Notes": str(safe_get(row, col_map.get("remarks")) or "")
            })

    return pd.DataFrame(rows)

# =========================
# SAFE ENTRY POINT
# =========================
def scan_spec_safe(file):
    try:
        return scan_spec(file)
    except Exception as e:
        print(f"[WARN] Primary scan failed: {e}")
        return scan_spec_fallback(file)

# =========================
# SAVE TO POSTGRES
# =========================
def save_raw(df, test_id):

    df = df.copy()
    df["test_id"] = test_id

    df = df.rename(columns={
        "Step": "step",
        "Row_Type": "row_type",
        "Speed_RPM": "speed_rpm",
        "Primary seal Gas Pressure (barg)": "primary_pressure",
        "Interspace_Pressure_bar": "interspace_pressure",
        "BackPressure_Drive_End_bar": "bp_de",
        "BackPressure_Non_Drive_End_bar": "bp_nde",
        "Gas_Injection_bar": "gas_injection",
        "Duration_s": "duration",
        "Acceptance point": "acceptance",
        "Temperature_C": "temperature",
        "Gas_Type": "gas_type",
        "Test_Mode": "test_mode",
        "Measurement": "measurement",
        "Torque_Check": "torque_check",
        "Notes": "notes"
    })

    df.to_sql("raw_spec", engine, if_exists="append", index=False)

# =========================
# EXPORT NORMALIZED CSV
# =========================
def export_tst(test_id):

    query = f"""
    SELECT
        test_id,
        step,
        COALESCE(primary_pressure,0) AS primary_pressure,
        COALESCE(interspace_pressure,0) AS interspace_pressure,
        COALESCE(bp_de,0) AS bp_de,
        COALESCE(bp_nde,0) AS bp_nde,
        COALESCE(speed_rpm,0) AS speed_rpm,
        COALESCE(duration,0) AS duration,
        acceptance,
        COALESCE(temperature,60) AS temperature,
        test_mode
    FROM raw_spec
    WHERE test_id = '{test_id}'
    ORDER BY step
    """

    df = pd.read_sql(query, engine)

    df.to_csv(f"TST_{test_id}.csv", index=False)

    return df

# =========================
# MAIN PIPELINE
# =========================
if __name__ == "__main__":

    file = "your_spec.xlsx"
    test_id = "001"

    df = scan_spec_safe(file)

    save_raw(df, test_id)

    export_tst(test_id)

    print("✅ Done: TST CSV generated")
