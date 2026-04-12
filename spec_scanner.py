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
    return row[idx] if idx < len(row) else None


def to_float(v):
    try:
        return float(v)
    except Exception:
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
    """Parse specification → dataframe with pressures, leaks, and metadata."""

    engine = _detect_engine(file)

    if engine == "openpyxl":
        sheets = pd.read_excel(
            file, engine=engine, sheet_name=None, header=None, engine_kwargs={"data_only": True}
        )
    else:
        sheets = pd.read_excel(file, engine=engine, sheet_name=None, header=None)

    rows = []

    for sheet_name, df in sheets.items():
        if df is None or df.empty:
            continue

        # --------------------------------------------------------------
        # find the row where "Test Step" header lives (true header row)
        # --------------------------------------------------------------
        header_row_index = None
        for i in range(len(df)):
            if any("test step" in str(x).lower() for x in df.iloc[i].tolist()):
                header_row_index = i
                break
        if header_row_index is None:
            continue

        # lowercase header names
        header_labels = [str(x).strip().lower() for x in df.iloc[header_row_index]]

        # --------------------------------------------------------------
        # locate known column indices
        # --------------------------------------------------------------
        col_step = next((idx for idx, c in enumerate(header_labels) if "test step" in c), None)
        col_primary = next((idx for idx, c in enumerate(header_labels) if "primary" in c and "pressure" in c), None)
        col_secondary = next((idx for idx, c in enumerate(header_labels) if "secondary" in c and "pressure" in c), None)
        col_speed = next((idx for idx, c in enumerate(header_labels) if "speed" in c), None)
        col_temp = next((idx for idx, c in enumerate(header_labels) if "temp" in c), None)
        col_hold = next((idx for idx, c in enumerate(header_labels) if "hold" in c), None)
        col_remarks = next((idx for idx, c in enumerate(header_labels) if "remark" in c), None)

        # --- detect leak columns (handles Max P/S Leak., Max S/S Leak.) ---
        leak_cols = {}
        for idx, txt in enumerate(header_labels):
            if "leak" in txt and "max" in txt:
                txt_clean = txt.replace(" ", " ")  # normalize nbsp
                if any(k in txt_clean for k in ["p/s", "ps", "primary", "inb", "inboard"]):
                    leak_cols["in"] = idx
                elif any(k in txt_clean for k in ["s/s", "ss", "secondary", "outb", "outboard"]):
                    leak_cols["out"] = idx

        # --------------------------------------------------------------
        # iterate step rows below header until blank or "end of"
        # --------------------------------------------------------------
        for k in range(header_row_index + 1, len(df)):
            row = df.iloc[k].tolist()
            step_val = safe_get(row, col_step)
            if step_val is None or str(step_val).strip() == "":
                continue
            if "end of" in str(step_val).lower():
                break

            try:
                step = int(float(step_val))
            except Exception:
                continue

            primary_cell = safe_get(row, col_primary) if col_primary is not None else None
            secondary = to_float(safe_get(row, col_secondary)) if col_secondary is not None else None
            speed = to_float(safe_get(row, col_speed)) if col_speed is not None else None
            temp = safe_get(row, col_temp) if col_temp is not None else None
            hold = to_float(safe_get(row, col_hold)) if col_hold is not None else None
            remarks = safe_get(row, col_remarks) if col_remarks is not None else ""

            # -------------------------------
            # TEST MODE
            # -------------------------------
            row_test_mode = 1
            prim_str = str(primary_cell).lower() if isinstance(primary_cell, str) else ""
            if any(k in prim_str for k in ["sec", "secondary", "inboard", "outboard"]):
                row_test_mode = 2
            elif (to_float(primary_cell) in [None, 0]) and (secondary not in [None, 0]) and str(primary_cell).strip() == "":
                row_test_mode = 2

            # -------------------------------
            # PRIMARY VALUE
            # -------------------------------
            if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
                primary = secondary + 10 if secondary is not None else None
            else:
                primary = to_float(primary_cell)
            if primary is None and secondary is not None:
                primary = secondary + 10

            if isinstance(temp, str) and temp.strip().upper() == "AMB":
                temp = 60

            duration = float(hold) if hold not in [None, ""] else 0
            acceptance = 1 if isinstance(remarks, str) and "acceptance" in remarks.lower() else 0

            interspace = 0
            bp_de = 0
            bp_nde = 0
            if row_test_mode == 1:
                bp_de = secondary
                bp_nde = secondary
            else:
                interspace = secondary

            # -------------------------------
            # Leak numbers per step
            # -------------------------------
            in_leak = None
            out_leak = None
            if "in" in leak_cols:
                in_leak = to_float(safe_get(row, leak_cols["in"]))
            if "out" in leak_cols:
                out_leak = to_float(safe_get(row, leak_cols["out"]))

            # skip ghost rows
            if all(
                v in [None, 0, ""]
                for v in [speed, primary, secondary, hold]
            ) and (not isinstance(remarks, str) or remarks.strip() == ""):
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
                    "ISFlowLimits": in_leak,
                    "OBFlowLimits": out_leak,
                }
            )

    df = pd.DataFrame(rows)

    # --------------------------------------------------------------
    # STEP MERGE / DEDUP
    # --------------------------------------------------------------
    if not df.empty:

        def merge_rows(group):
            base = group.iloc[0].copy()
            for _, r in group.iterrows():
                for c in group.columns:
                    vb, vn = base[c], r[c]
                    if pd.notna(vb) and vb not in [0, "", None]:
                        continue
                    if pd.notna(vn) and vn not in [0, "", None]:
                        base[c] = vn
            return base

        df = (
            df.sort_values("Step")
            .groupby("Step", as_index=False)
            .apply(merge_rows)
            .reset_index(drop=True)
        )

    return df
