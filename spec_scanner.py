import pandas as pd
from sqlalchemy import create_engine, text
import re

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
# FLOW LIMIT EXTRACTION (TEXT)
# =========================
def extract_flow_limits(remarks):
    is_flow = None
    ob_flow = None

    if isinstance(remarks, str):
        text = remarks.lower()

        ib_match = re.search(r"(i\s*/?\s*b[^0-9]*)(\d+\.?\d*)", text)
        ob_match = re.search(r"(o\s*/?\s*b[^0-9]*)(\d+\.?\d*)", text)

        if ib_match:
            is_flow = to_float(ib_match.group(2))

        if ob_match:
            ob_flow = to_float(ob_match.group(2))

    return is_flow, ob_flow

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

                    # =========================
                    # REMARKS (COLUMN-AWARE FIX)
                    # =========================
                    remarks = safe_get(row, step_col+8)

                    def is_valid_text(x):
                        return isinstance(x, str) and x.strip() != ""

                    if not is_valid_text(remarks):
                        for idx in range(step_col+1, len(row)):
                            cell = row[idx]

                            if not is_valid_text(cell):
                                continue

                            txt = cell.lower()

                            if "leak" in txt or "i/b" in txt or "o/b" in txt:
                                remarks = cell
                                break

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

                    # =========================
                    # FLOW LIMITS
                    # =========================
                    is_flow, ob_flow = extract_flow_limits(remarks)

                    # ---- COLUMN NUMERIC FALLBACK (CRITICAL FIX) ----
                    if is_flow is None or ob_flow is None:

                        numeric_candidates = []

                        for idx in range(step_col+1, len(row)):
                            val = to_float(row[idx])
                            if val is not None and val <= 100:
                                numeric_candidates.append(val)

                        if numeric_candidates:
                            if ob_flow is None:
                                ob_flow = numeric_candidates[-1]  # usually OB is last
                            if is_flow is None and len(numeric_candidates) > 1:
                                is_flow = numeric_candidates[0]

                    # =========================
                    # DEBUG (REMOVE LATER)
                    # =========================
                    if step == 56:
                        print("\n--- DEBUG STEP 56 ---")
                        print("ROW:", row)
                        print("REMARKS:", remarks)
                        print("IS:", is_flow, "OB:", ob_flow)

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
        print(f"[WARN] Primary scan failed: {e}")
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
        "Notes": "notes",
        "ISFlowLimit": "isflowlimit",
        "OBFlowLimit": "obflowlimit"
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

    print("✅ Done: TST CSV generated")
