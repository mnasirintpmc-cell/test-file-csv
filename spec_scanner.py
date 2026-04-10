import pandas as pd
import re

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
    """Parse specification → dataframe of steps, with flow limits and accurate test‑mode detection."""

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
        sheets = pd.read_excel(file, engine=engine, sheet_name=None, header=None)

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

                    # =====================================================
                    # 🔍 TEST MODE DETECTION (refined & safe)
                    # =====================================================
                    row_test_mode = 1

                    prim_str = str(primary_cell).lower() if isinstance(primary_cell, str) else ""
                    sec_colname = ""

                    # look up header row (above “Test Step”) for context keywords
                    if i > 0:
                        header_row = list(df.iloc[i - 1])
                        if step_col + 2 < len(header_row):
                            sec_colname = str(header_row[step_col + 2]).lower()

                    # case 1 – explicit textual indicators
                    if any(k in prim_str for k in ["sec", "secondary", "inboard", "outboard"]):
                        row_test_mode = 2
                    elif any(k in sec_colname for k in ["sec", "secondary"]):
                        row_test_mode = 2
                    # case 2 – numeric heuristic: only when primary blank/zero and secondary > 0
                    elif (to_float(primary_cell) in [None, 0]) and (secondary not in [None, 0]) and str(primary_cell).strip() == "":
                        row_test_mode = 2

                    # =====================================================
                    # PRIMARY VALUE
                    # =====================================================
                    if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                        primary = secondary + 10 if secondary is not None else None
                    else:
                        primary = to_float(primary_cell)
                    if primary is None and secondary is not None:
                        primary = secondary + 10

                    # =====================================================
                    # TEMPERATURE NORMALIZATION
                    # =====================================================
                    if isinstance(temp, str) and temp.strip().upper() == "AMB":
                        temp = 60

                    # =====================================================
                    # DURATION / HOLD
                    # =====================================================
                    duration = float(hold) if hold not in [None, ""] else 0

                    # =====================================================
                    # ACCEPTANCE FLAG
                    # =====================================================
                    acceptance = (
                        1
                        if isinstance(remarks, str)
                        and "acceptance" in remarks.lower()
                        else 0
                    )

                    # =====================================================
                    # PRESSURE MAPPING
                    # =====================================================
                    interspace = 0
                    bp_de = 0
                    bp_nde = 0
                    if row_test_mode == 1:
                        bp_de = secondary
                        bp_nde = secondary
                    else:
                        interspace = secondary

                    # =====================================================
                    # FILTER EMPTY ROWS
                    # =====================================================
                    is_empty_row = (
                        (speed in [None, 0])
                        and (primary in [None, 0])
                        and (secondary in [None, 0])
                        and (hold in [None, 0])
                        and (not isinstance(remarks, str) or remarks.strip() == "")
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
    # MERGE DUPLICATE STEPS (existing logic)
    # =====================================================
    if not df.empty:

        def merge_rows(group):
            base = group.iloc[0].copy()
            for _, row in group.iterrows():
                for col in group.columns:
                    vb, vn = base[col], row[col]
                    if pd.notna(vb) and vb not in [0, "", None]:
                        continue
                    if pd.notna(vn) and vn not in [0, "", None]:
                        base[col] = vn
            return base

        df = (
            df.sort_values("Step")
            .groupby("Step", as_index=False)
            .apply(merge_rows)
            .reset_index(drop=True)
        )

    # =====================================================
    # 🔍 PARSE MAX LEAKAGE INBOARD / OUTBOARD
    # =====================================================
    max_inboard = None
    max_outboard = None
    for sheet_name, df_sheet in sheets.items():
        if df_sheet is None or df_sheet.empty:
            continue
        for i in range(len(df_sheet)):
            for j in range(len(df_sheet.columns)):
                text = str(df_sheet.iloc[i, j]).strip().lower()
                if not text:
                    continue
                if "max" in text and "leakage" in text:
                    # check same and next cell for numeric
                    candidates = [text]
                    if j + 1 < len(df_sheet.columns):
                        candidates.append(str(df_sheet.iloc[i, j + 1]))
                    for cand in candidates:
                        m = re.search(r"([-+]?\d*\.?\d+)", cand)
                        if m:
                            val = float(m.group(1))
                            if "inboard" in text:
                                max_inboard = val
                            elif "outboard" in text:
                                max_outboard = val

    # replicate across rows so Excel/CSV show the values
    df["ISFlowLimits"] = (
        [max_inboard] * len(df) if max_inboard is not None else [None] * len(df)
    )
    df["OBFlowLimits"] = (
        [max_outboard] * len(df) if max_outboard is not None else [None] * len(df)
    )

    return df
