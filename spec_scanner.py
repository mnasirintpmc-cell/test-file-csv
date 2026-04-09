import pandas as pd
from sqlalchemy import create_engine, text

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
        return float(str(v).strip())
    except:
        return None

def _detect_engine(file):
    name = file.name.lower() if hasattr(file, "name") else str(file).lower()
    return "pyxlsb" if name.endswith(".xlsb") else "openpyxl"

# =========================
# HEADER DETECTION (FIXED)
# =========================
def find_header_row(df):
    for i in range(len(df)):
        row = df.iloc[i]

        # 🔥 FIX: force string conversion
        if any("step" in str(c).lower() for c in row):
            return i

    return None

def build_column_map(header_row):
    col_map = {}

    for idx, col in enumerate(header_row):
        col = str(col).lower()

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

        # 🔥 FLOW COLUMNS (CRITICAL)
        elif "i/b" in col and "leak" in col:
            col_map["is_flow"] = idx

        elif "o/b" in col and "leak" in col:
            col_map["ob_flow"] = idx

    return col_map

# =========================
# MAIN SCANNER
# =========================
def scan_spec(file):

    engine_type = _detect_engine(file)
    sheets = pd.read_excel(file, engine=engine_type, sheet_name=None, header=None)

    rows = []

    for sheet_name, df in sheets.items():

        if df is None or df.empty:
            continue

        header_idx = find_header_row(df)
        if header_idx is None:
            continue

        header_row = df.iloc[header_idx]
        col_map = build_column_map(header_row)

        if "step" not in col_map:
            continue

        for k in range(header_idx + 1, len(df)):

            row = df.iloc[k].tolist()

            step_val = safe_get(row, col_map.get("step"))

            if step_val is None:
                continue

            if "end of" in str(step_val).lower():
                break

            try:
                step = int(float(step_val))
            except:
                continue

            primary_cell = safe_get(row, col_map.get("primary"))
            secondary = to_float(safe_get(row, col_map.get("secondary")))
            speed = to_float(safe_get(row, col_map.get("speed")))
            temp = safe_get(row, col_map.get("temp"))
            hold = to_float(safe_get(row, col_map.get("hold")))
            remarks = safe_get(row, col_map.get("remarks"))

            # =========================
            # FLOW LIMITS (CORRECT)
            # =========================
            is_flow = to_float(safe_get(row, col_map.get("is_flow")))
            ob_flow = to_float(safe_get(row, col_map.get("ob_flow")))

            # =========================
            # TEST MODE
            # =========================
            row_test_mode = 1

            if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                row_test_mode = 2

            primary_val = to_float(primary_cell)

            if secondary is not None and primary_val in [None, 0]:
                row_test_mode = 2

            if secondary is not None and primary_val is not None:
                if secondary < primary_val:
                    row_test_mode = 2

            # =========================
            # PRIMARY
            # =========================
            primary = primary_val
            if primary is None and secondary is not None:
                primary = secondary + 10

            # =========================
            # TEMP
            # =========================
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
                "Notes": remarks if remarks else "",
                "ISFlowLimit": is_flow,
                "OBFlowLimit": ob_flow
            })

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.sort_values("Step").reset_index(drop=True)

    return df

# =========================
# SAFE ENTRY POINT
# =========================
def scan_spec_safe(file):
    try:
        return scan_spec(file)
    except Exception as e:
        print(f"[WARN] Scan failed: {e}")
        return pd.DataFrame()

# =========================
# SAVE TO POSTGRES
# =========================
def save_raw(df, test_id):

    df = df.copy()
    df["test_id"] = test_id

    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM raw_spec WHERE test_id = '{test_id}'"))

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
        "ISFlowLimit": "isflowlimit",
        "OBFlowLimit": "obflowlimit",
        "Notes": "notes"
    })

    df.to_sql("raw_spec", engine, if_exists="append", index=False)

# =========================
# EXPORT CSV
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
        test_mode,
        COALESCE(isflowlimit,0) AS "TST_ISFlowLimit",
        COALESCE(obflowlimit,0) AS "TST_OBFlowLimit"
    FROM raw_spec
    WHERE test_id = '{test_id}'
    ORDER BY step
    """

    df = pd.read_sql(query, engine)
    df.to_csv(f"TST_{test_id}.csv", index=False)

    return df

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    file = "your_spec.xlsx"
    test_id = "001"

    df = scan_spec_safe(file)

    print("Rows extracted:", len(df))

    save_raw(df, test_id)

    export_tst(test_id)

    print("✅ Done")
