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
    return row[idx] if idx is not None and idx < len(row) else None


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

        # --------------------------------------------------------------
        # FIND ALL HEADER ROWS (multi-section support)
        # --------------------------------------------------------------
        header_indices = [
            i for i in range(len(df))
            if any("test step" in str(x).lower() for x in df.iloc[i].tolist())
        ]

        for h_idx in header_indices:

            header_labels = [str(x).strip().lower() for x in df.iloc[h_idx]]

            col_step = next((i for i, c in enumerate(header_labels) if "test step" in c), None)
            col_primary = next((i for i, c in enumerate(header_labels) if "primary" in c and "pressure" in c), None)
            col_secondary = next((i for i, c in enumerate(header_labels) if "secondary" in c and "pressure" in c), None)
            col_speed = next((i for i, c in enumerate(header_labels) if "speed" in c), None)
            col_temp = next((i for i, c in enumerate(header_labels) if "temp" in c), None)
            col_hold = next((i for i, c in enumerate(header_labels) if "hold" in c), None)
            col_remarks = next((i for i, c in enumerate(header_labels) if "remark" in c), None)

            # leak columns
            leak_cols = {}
            for idx, txt in enumerate(header_labels):
                if "leak" in txt and "max" in txt:
                    txt_clean = txt.replace(" ", " ")
                    if any(k in txt_clean for k in ["p/s", "ps", "primary", "inb", "inboard"]):
                        leak_cols["in"] = idx
                    elif any(k in txt_clean for k in ["s/s", "ss", "secondary", "outb", "outboard"]):
                        leak_cols["out"] = idx

            # --------------------------------------------------------------
            # PROCESS SECTION UNTIL "END OF TEST"
            # --------------------------------------------------------------
            for k in range(h_idx + 1, len(df)):
                row = df.iloc[k].tolist()
                step_val = safe_get(row, col_step)

                if step_val is None:
                    continue

                step_str = str(step_val).lower().strip()

                # stop this section only
                if "end of test" in step_str:
                    break

                if step_str == "":
                    continue

                # ----------------------------------------------------------
                # robust step parsing
                # ----------------------------------------------------------
                step_match = re.search(r"\d+", str(step_val))
                if not step_match:
                    continue

                step = int(step_match.group())

                primary_cell = safe_get(row, col_primary)
                secondary = to_float(safe_get(row, col_secondary))
                speed = to_float(safe_get(row, col_speed))
                temp = safe_get(row, col_temp)
                hold = to_float(safe_get(row, col_hold))
                remarks = safe_get(row, col_remarks) or ""

                # leaks
                in_leak = to_float(safe_get(row, leak_cols.get("in")))
                out_leak = to_float(safe_get(row, leak_cols.get("out")))

                # ----------------------------------------------------------
                # FIX: reject non-test garbage rows (like 321991)
                # REQUIRE: at least one meaningful field besides step
                # ----------------------------------------------------------
                has_data = any(
                    v not in [None, 0, ""]
                    for v in [speed, primary_cell, secondary, hold, in_leak, out_leak]
                )
                has_text = isinstance(remarks, str) and remarks.strip() != ""

                if not has_data and not has_text:
                    continue

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
                # PRIMARY
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
                        "Notes": remarks,
                        "ISFlowLimits": in_leak,
                        "OBFlowLimits": out_leak,
                    }
                )

    df = pd.DataFrame(rows)

    # --------------------------------------------------------------
    # MERGE / DEDUP
    # --------------------------------------------------------------
    if not df.empty:

        def merge_rows(group):
            base = group.iloc[0].copy()

            for _, r in group.iterrows():
                for c in group.columns:
                    vb, vn = base[c], r[c]

                    if (vb in [None, 0, ""] or pd.isna(vb)) and (
                        vn not in [None, 0, ""] and not pd.isna(vn)
                    ):
                        base[c] = vn

            return base

        df = (
            df.sort_values("Step")
            .groupby("Step", as_index=False)
            .apply(merge_rows)
            .reset_index(drop=True)
        )

    return df
