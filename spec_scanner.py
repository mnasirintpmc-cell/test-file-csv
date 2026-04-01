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

        for i in range(len(df)):

            for j in range(len(df.columns)):

                cell = str(df.iloc[i, j]).strip().lower()

                if cell != "test step":
                    continue

                step_col = j

                # =====================================================
                # 🔥 SURGICAL FIX: HEADER-BASED COLUMN DETECTION
                # =====================================================
                header_row = df.iloc[i].astype(str).str.lower().tolist()

                def find_col(keywords):
                    for idx, val in enumerate(header_row):
                        for k in keywords:
                            if k in val:
                                return idx
                    return None

                col_map = {
                    "step": step_col,
                    "speed": find_col(["speed", "rpm"]),
                    "primary": find_col(["primary"]),
                    "secondary": find_col(["secondary", "interspace"]),
                    "temp": find_col(["temp"]),
                    "hold": find_col(["hold", "duration"]),
                    "remarks": find_col(["remark", "note"])
                }

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

                    # =====================================================
                    # 🔥 USE DETECTED COLUMNS (WITH SAFE FALLBACK)
                    # =====================================================
                    speed = to_float(safe_get(row, col_map["speed"]))
                    primary_cell = safe_get(row, col_map["primary"])
                    secondary = to_float(safe_get(row, col_map["secondary"]))
                    temp = safe_get(row, col_map["temp"])
                    hold = to_float(safe_get(row, col_map["hold"]))
                    remarks = safe_get(row, col_map["remarks"])

                    # Fallback if detection failed
                    if primary_cell is None and secondary is None:
                        speed = to_float(safe_get(row, step_col+1))
                        primary_cell = safe_get(row, step_col+2)
                        secondary = to_float(safe_get(row, step_col+3))
                        temp = safe_get(row, step_col+4)
                        hold = to_float(safe_get(row, step_col+5))
                        remarks = safe_get(row, step_col+8)

                    # -------------------------------
                    # TEST MODE DETECTION
                    # -------------------------------
                    row_test_mode = 1

                    if isinstance(primary_cell, str):
                        if "secondary" in primary_cell.lower():
                            row_test_mode = 2

                    try:
                        if float(primary_cell) == 0:
                            row_test_mode = 1
                    except:
                        pass

                    # =====================================================
                    # 🔥 SURGICAL FIX: FORCE MODE 2 FOR CLEAN NUMERIC ROWS
                    # =====================================================
                    if row_test_mode == 1:
                        if (
                            isinstance(primary_cell, (int, float)) or to_float(primary_cell) is not None
                        ) and secondary is not None:
                            row_test_mode = 2

                    # -------------------------------
                    # PRIMARY
                    # -------------------------------
                    if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                        primary = secondary + 10 if secondary is not None else None
                    else:
                        primary = to_float(primary_cell)

                    if primary is None and secondary is not None:
                        primary = secondary + 10

                    # -------------------------------
                    # TEMP
                    # -------------------------------
                    if isinstance(temp, str) and temp.upper() == "AMB":
                        temp = 60

                    # -------------------------------
                    # DURATION (minutes)
                    # -------------------------------
                    duration = float(hold) if hold not in [None, ""] else 0

                    # -------------------------------
                    # ACCEPTANCE FIX (SURGICAL)
                    # -------------------------------
                    acceptance = 0
                    if isinstance(remarks, str):
                        if "acceptance" in remarks.lower():
                            acceptance = 1

                    # -------------------------------
                    # PRESSURE MAPPING
                    # -------------------------------
                    interspace = 0
                    bp_de = 0
                    bp_nde = 0

                    if row_test_mode == 1:
                        bp_de = secondary
                        bp_nde = secondary
                    else:
                        interspace = secondary

                    # ==========================================
                    # SURGICAL FIX: FILTER GHOST / EMPTY STEPS
                    # ==========================================
                    is_empty_row = (
                        (speed is None or speed == 0) and
                        (primary is None or primary == 0) and
                        (secondary is None or secondary == 0) and
                        (hold is None or hold == 0) and
                        (not isinstance(remarks, str) or remarks.strip() == "")
                    )

                    if is_empty_row:
                        continue

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
                        "Test_Mode": row_test_mode,
                        "Measurement": 1,
                        "Torque_Check": 0,
                        "Notes": remarks if remarks else ""
                    })

    df = pd.DataFrame(rows)

    # =====================================================
    # 🔥 SURGICAL FIX: STEP DEDUPLICATION (UNCHANGED)
    # =====================================================
    if not df.empty:

        def merge_rows(group):

            base = group.iloc[0].copy()

            for _, row in group.iterrows():

                for col in group.columns:

                    val_base = base[col]
                    val_new = row[col]

                    if pd.notna(val_base) and val_base not in [0, "", None]:
                        continue

                    if pd.notna(val_new) and val_new not in [0, "", None]:
                        base[col] = val_new

            return base

        df = (
            df
            .sort_values("Step")
            .groupby("Step", as_index=False)
            .apply(merge_rows)
            .reset_index(drop=True)
        )

    return df
