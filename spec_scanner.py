import pandas as pd
import re

# --------------------------------------------------
# Ensure pyxlsb is installed
# --------------------------------------------------
try:
    import pyxlsb  # noqa: F401
except ImportError:
    raise ImportError("Missing dependency 'pyxlsb'. Install with: pip install pyxlsb")


def _norm(s):
    """Normalize header text for matching."""
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def _to_float(v, default=None):
    """Safe float conversion."""
    try:
        if pd.isna(v):
            return default
        return float(str(v).replace(",", "").strip())
    except Exception:
        return default


def _to_int(v, default=None):
    """Extract first integer from a value like '42', '42.0', 'Step 42'."""
    if pd.isna(v):
        return default
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else default


def scan_spec(file):
    # Read ALL sheets
    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    # --------------------------------------------------
    # Scan each sheet
    # --------------------------------------------------
    for sheet_name, df in sheets.items():
        if df is None or df.empty:
            continue

        header_row = None

        # --------------------------------------------------
        # Locate header row that contains "Test Step"
        # (any column in the row)
        # --------------------------------------------------
        for i in range(len(df)):
            row_texts = [_norm(x) for x in df.iloc[i].tolist()]
            if any("test step" in t for t in row_texts):
                header_row = i
                break

        if header_row is None:
            # No table in this sheet
            continue

        # --------------------------------------------------
        # Build column index map from header names
        # --------------------------------------------------
        headers = [_norm(x) for x in df.iloc[header_row].tolist()]

        def find_col(*names):
            for idx, h in enumerate(headers):
                for n in names:
                    if n in h:
                        return idx
            return None

        col_step = find_col("test step", "step")
        col_primary = find_col("primary seal gas pressure", "primary")
        col_secondary = find_col("secondary seal gas pressure", "secondary")
        col_speed = find_col("speed")
        col_temp = find_col("temp")
        col_hold = find_col("hold")
        col_remarks = find_col("remarks")

        if col_step is None:
            # Can't parse without step column
            continue

        # --------------------------------------------------
        # Read rows under header
        # --------------------------------------------------
        for i in range(header_row + 1, len(df)):
            r = df.iloc[i]

            step_cell = r[col_step] if col_step < len(r) else None

            # Stop conditions
            if pd.isna(step_cell):
                break

            if "end of" in str(step_cell).lower():
                break

            spec_step = _to_int(step_cell)
            if spec_step is None:
                continue

            primary = _to_float(r[col_primary]) if col_primary is not None else None
            secondary = _to_float(r[col_secondary]) if col_secondary is not None else None
            speed = _to_float(r[col_speed], 0) if col_speed is not None else 0
            temp = r[col_temp] if col_temp is not None else None
            hold = _to_float(r[col_hold], 0) if col_hold is not None else 0
            remarks = r[col_remarks] if (col_remarks is not None and col_remarks < len(r)) else ""

            if secondary is None:
                continue

            if primary is None:
                primary = secondary + 5

            # Temperature handling
            if isinstance(temp, str) and "amb" in temp.lower():
                temp = 60
            temp = _to_float(temp, 60)

            duration = int((hold or 0) * 60)

            rows.append({
                "spec_step": spec_step,
                "Speed_RPM": speed,
                "Primary seal Gas Pressure (barg)": primary,
                "Interspace_Pressure_bar": 0,
                "BackPressure_Drive_End_bar": secondary,
                "BackPressure_Non_Drive_End_bar": secondary,
                "Gas_Injection_bar": 0,
                "Duration_s": duration,
                "Acceptance point": 1 if "acceptance" in str(remarks).lower() else 0,
                "Temperature_C": temp,
                "Gas_Type": "Air",
                "Test_Mode": 1,
                "Measurement": 1,
                "Torque_Check": 0,
                "Notes": remarks,
                "Test_Name": sheet_name
            })

    if not rows:
        raise ValueError("No test procedure tables found in any sheet")

    df_out = pd.DataFrame(rows)

    df_out = df_out.sort_values("spec_step")
    df_out.insert(0, "Step", range(1, len(df_out) + 1))
    df_out = df_out.drop(columns=["spec_step"])

    return df_out
