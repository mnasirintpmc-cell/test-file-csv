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
            engine_kwargs={"data_only": True},
        )
    else:
        sheets = pd.read_excel(
            file,
            engine=engine,
            sheet_name=None,
            header=None,
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

                for k in range(i + 1, len(df)):

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

                    primary_cell = safe_get(row, step_col + 1)
                    secondary = to_float(safe_get(row, step_col + 2))
                    speed = to_float(safe_get(row, step_col + 3))
                    temp = safe_get(row, step_col + 4)
                    hold = to_float(safe_get(row, step_col + 5))
                    remarks = safe_get(row, step_col + 8)

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

                    # -------------------------------
                    # PRIMARY
                    # -------------------------------
                    if (
                        isinstance(primary_cell, str)
                        and "secondary" in primary_cell.lower()
                    ):
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
                        (speed is None or speed == 0)
                        and (primary is None or primary == 0)
                        and (secondary is None or secondary == 0)
                        and (hold is None or hold == 0)
                        and (
                            not isinstance(remarks, str)
                            or remarks.strip() == ""
                        )
                    )

                    if is_empty_row:
                        continue

                    rows.append(
                        {
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
                            "Notes": remarks if remarks else "",
                        }
                    )

    df = pd.DataFrame(rows)

    # =====================================================
    # 🔥 SURGICAL FIX: STEP DEDUPLICATION (NO LOGIC REMOVED)
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
            df.sort_values("Step")
            .groupby("Step", as_index=False)
            .apply(merge_rows)
            .reset_index(drop=True)
        )

    # =====================================================
    # ✅ Extract Maximum Leakage Limits (Inboard & Outboard)
    # =====================================================
    max_inboard = None
    max_outboard = None

    for sheet_name, df_sheet in sheets.items():
        if df_sheet is None or df_sheet.empty:
            continue

        for i in range(len(df_sheet)):
            for j in range(len(df_sheet.columns)):
                cell_val = str(df_sheet.iloc[i, j]).strip().lower()
                if "max leakage" in cell_val:
                    next_val = (
                        str(df_sheet.iloc[i, j + 1])
                        if j + 1 < len(df_sheet.columns)
                        else ""
                    )
                    num_val = pd.to_numeric(next_val, errors="coerce")
                    if pd.isna(num_val):
                        import re
                        match = re.search(r"([\d\.]+)", str(next_val))
                        if match:
                            num_val = float(match.group(1))
                    if "inboard" in cell_val:
                        max_inboard = num_val
                    elif "outboard" in cell_val:
                        max_outboard = num_val

    df["ISFlowLimits"] = (
        [max_inboard] * len(df) if max_inboard is not None else [None] * len(df)
    )
    df["OBFlowLimits"] = (
        [max_outboard] * len(df) if max_outboard is not None else [None] * len(df)
    )

    return df
