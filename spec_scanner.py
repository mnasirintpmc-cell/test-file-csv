"""
spec_scanner.py
---------------
Reads a .xlsb test specification file and returns a DataFrame in the
standard technician format expected by app.py.

Spec column names  →  Technician column names
─────────────────────────────────────────────
Step               →  Step
Speed_RPM          →  Speed_RPM
Primary seal Gas   →  Primary seal Gas Pressure (barg)
  Pressure (barg)
Interspace_Pressure→  Interspace_Pressure_bar   (primary seal test)
                   →  BackPressure_Drive_End_bar (secondary seal test)
                   →  BackPressure_Non_Drive_End_bar (secondary seal test)
Duration_s         →  Duration_s
Gas_Type           →  Gas_Type
Temperature_C      →  Temperature_C
Acceptance point   →  Acceptance point
measurment         →  Measurement
[auto]             →  Test_Mode  (1 = primary, 2 = secondary)
[empty]            →  Notes

Test mode logic
───────────────
If the row's test label (in column "Test_Mode" or inferred from context)
contains "primary" or "main" (case-insensitive):
    • Interspace_Pressure_bar  = spec interspace value
    • BackPressure_Drive_End_bar      = 0
    • BackPressure_Non_Drive_End_bar  = 0
    • Test_Mode = 1

If the row's test label contains "secondary" or "sep":
    • Interspace_Pressure_bar         = 0
    • BackPressure_Drive_End_bar      = spec interspace value
    • BackPressure_Non_Drive_End_bar  = spec interspace value
    • Test_Mode = 2

If no test mode column exists the whole sheet is treated as primary seal.
"""

import pandas as pd
from pyxlsb import open_workbook
import io
import re


# ──────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ──────────────────────────────────────────────────────────────────────────────

# Map of possible spec header names → canonical internal key
_HEADER_ALIASES: dict[str, str] = {
    # Step
    "step":                              "step",
    "step number":                       "step",
    "step_number":                       "step",
    "step no":                           "step",
    "step no.":                          "step",

    # Speed
    "speed_rpm":                         "speed_rpm",
    "speed (rpm)":                       "speed_rpm",
    "speed":                             "speed_rpm",

    # Primary seal pressure
    "primary seal gas pressure (barg)":  "primary_pressure",
    "primary seal pressure":             "primary_pressure",
    "primary pressure":                  "primary_pressure",
    "cell pressure":                     "primary_pressure",
    "primary_pressure":                  "primary_pressure",

    # Interspace / back-pressure (all variants point to same key)
    "interspace_pressure_bar":           "interspace",
    "interspace pressure":               "interspace",
    "interspace":                        "interspace",
    "backpressure_drive_end_bar":        "interspace",
    "backpressure_non_drive_end_bar":    "interspace",
    "bp":                                "interspace",
    "back pressure":                     "interspace",

    # Duration
    "duration_s":                        "duration",
    "duration":                          "duration",
    "step duration":                     "duration",
    "step_duration":                     "duration",

    # Gas type
    "gas_type":                          "gas_type",
    "gas type":                          "gas_type",
    "gas":                               "gas_type",

    # Temperature
    "temperature_c":                     "temperature",
    "temperature":                       "temperature",
    "temp":                              "temperature",
    "temp_c":                            "temperature",

    # Acceptance point
    "acceptance point":                  "acceptance_point",
    "acceptance_point":                  "acceptance_point",
    "ap":                                "acceptance_point",
    "ap flag":                           "acceptance_point",
    "ap_flag":                           "acceptance_point",

    # Measurement
    "measurment":                        "measurement",   # common typo in spec
    "measurement":                       "measurement",
    "measurement req":                   "measurement",
    "measurement_req":                   "measurement",
    "meas":                              "measurement",

    # Test mode (optional column in the spec)
    "test_mode":                         "test_mode_label",
    "test mode":                         "test_mode_label",
    "test type":                         "test_mode_label",
    "test_type":                         "test_mode_label",
    "mode":                              "test_mode_label",
}


def _normalise_header(raw: str) -> str:
    """Lower-case, strip whitespace for robust matching."""
    return str(raw).strip().lower()


def _find_header_row(sheet_rows: list[list]) -> int:
    """
    Return the index of the row that contains the step/speed header.
    Scans the first 20 rows.  Returns 0 if nothing found (assume row 0).
    """
    for i, row in enumerate(sheet_rows[:20]):
        values = [_normalise_header(c) for c in row if c is not None]
        # Must contain at least 'step' or 'speed' to be the header row
        if any(v in ("step", "step number", "step_number") for v in values):
            return i
        if any(v in ("speed_rpm", "speed (rpm)", "speed") for v in values):
            return i
    return 0


def _read_xlsb(file) -> pd.DataFrame:
    """
    Read the first sheet of a .xlsb file into a raw DataFrame.
    `file` can be a file path (str) or a file-like object.
    """
    rows: list[list] = []

    # pyxlsb needs a real file-like with a .read(); wrap bytes buffer if needed
    if hasattr(file, "read"):
        data = file.read()
        buf = io.BytesIO(data)
    else:
        buf = file

    with open_workbook(buf) as wb:
        sheet_name = wb.sheets[0]
        with wb.get_sheet(sheet_name) as ws:
            for row in ws.rows():
                rows.append([c.v for c in row])

    if not rows:
        return pd.DataFrame()

    header_idx = _find_header_row(rows)
    headers    = [str(c) if c is not None else f"col_{i}"
                  for i, c in enumerate(rows[header_idx])]
    data_rows  = rows[header_idx + 1:]

    # Pad short rows so every row has the same width as the header
    n_cols = len(headers)
    padded = [r + [None] * (n_cols - len(r)) if len(r) < n_cols else r[:n_cols]
              for r in data_rows]

    df = pd.DataFrame(padded, columns=headers)
    return df


def _map_columns(df: pd.DataFrame) -> dict[str, str]:
    """
    Return a dict  {original_column_name: canonical_key}
    for every column in df that matches a known alias.
    """
    mapping: dict[str, str] = {}
    for col in df.columns:
        key = _HEADER_ALIASES.get(_normalise_header(col))
        if key and key not in mapping.values():
            mapping[col] = key
    return mapping


def _is_primary(label: str) -> bool:
    """Return True when test mode label indicates a primary / main seal test."""
    l = str(label).lower()
    return bool(re.search(r"\bprimary\b|\bmain\b", l))


def _is_secondary(label: str) -> bool:
    """Return True when test mode label indicates a secondary / sep seal test."""
    l = str(label).lower()
    return bool(re.search(r"\bsecondary\b|\bsep\b", l))


def _to_float(val) -> float:
    """Safely convert a cell value to float; return 0.0 on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _flag(val) -> str:
    """
    Convert boolean-ish spec values (1/0/True/False/Yes/No) to 'Yes'/'No'
    for the technician format.
    """
    if val is None:
        return "No"
    s = str(val).strip().lower()
    if s in ("1", "yes", "true", "y"):
        return "Yes"
    return "No"


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def scan_spec(file) -> pd.DataFrame:
    """
    Read a .xlsb spec file and return a DataFrame in technician format,
    ready to be passed directly to editable_dataframe() in app.py.

    Parameters
    ----------
    file : str | file-like
        Path to the .xlsb file, or an uploaded file object (e.g. from
        st.file_uploader).

    Returns
    -------
    pd.DataFrame  with columns:
        Step, Speed_RPM, Primary seal Gas Pressure (barg),
        Interspace_Pressure_bar, BackPressure_Drive_End_bar,
        BackPressure_Non_Drive_End_bar, Duration_s, Gas_Type,
        Temperature_C, Acceptance point, Measurement, Test_Mode, Notes
    """

    # 1. Read raw data from the .xlsb
    raw_df = _read_xlsb(file)

    if raw_df.empty:
        raise ValueError(
            "The spec file appears to be empty or could not be read. "
            "Please check the file and try again."
        )

    # 2. Build column mapping  {original → canonical_key}
    col_map = _map_columns(raw_df)

    if not col_map:
        raise ValueError(
            "No recognisable column headers found in the spec file. "
            f"Headers detected: {list(raw_df.columns)}"
        )

    # 3. Rename to canonical keys for easy access
    canonical = raw_df.rename(columns=col_map)

    # Drop rows where every mapped column is null (blank separator rows)
    mapped_keys = list(col_map.values())
    canonical = canonical.dropna(
        subset=[k for k in mapped_keys if k in canonical.columns],
        how="all"
    ).reset_index(drop=True)

    if canonical.empty:
        raise ValueError(
            "The spec file has headers but no data rows. "
            "Please check the sheet content."
        )

    # 4. Determine whole-sheet default test mode (used if no test_mode column)
    has_mode_col = "test_mode_label" in canonical.columns

    output_rows: list[dict] = []

    for idx, row in canonical.iterrows():

        # ── test mode determination ──────────────────────────────────────────
        if has_mode_col:
            label = str(row.get("test_mode_label", "primary"))
        else:
            label = "primary"   # default: treat entire sheet as primary seal

        if _is_secondary(label):
            test_mode_int  = 2
            interspace_val = _to_float(row.get("interspace", 0))
            interspace_bar = 0.0
            bp_de          = interspace_val
            bp_nde         = interspace_val
        else:
            # Primary / main seal (also catches rows with no recognisable label)
            test_mode_int  = 1
            interspace_val = _to_float(row.get("interspace", 0))
            interspace_bar = interspace_val
            bp_de          = 0.0
            bp_nde         = 0.0

        # ── step number ──────────────────────────────────────────────────────
        step_raw = row.get("step", None)
        if step_raw is not None and str(step_raw).strip() not in ("", "None"):
            step = step_raw
        else:
            step = idx + 1      # fall back to 1-based row index

        output_rows.append({
            "Step":                              step,
            "Speed_RPM":                         _to_float(row.get("speed_rpm", 0)),
            "Primary seal Gas Pressure (barg)":  _to_float(row.get("primary_pressure", 0)),
            "Interspace_Pressure_bar":           interspace_bar,
            "BackPressure_Drive_End_bar":        bp_de,
            "BackPressure_Non_Drive_End_bar":    bp_nde,
            "Duration_s":                        _to_float(row.get("duration", 0)),
            "Gas_Type":                          str(row.get("gas_type", "")).strip(),
            "Temperature_C":                     _to_float(row.get("temperature", 0)),
            "Acceptance point":                  _flag(row.get("acceptance_point", 0)),
            "Measurement":                       _flag(row.get("measurement", 0)),
            "Test_Mode":                         test_mode_int,
            "Notes":                             "",
        })

    result = pd.DataFrame(output_rows)

    # 5. Coerce numeric columns — anything that slipped through as string
    numeric_cols = [
        "Speed_RPM",
        "Primary seal Gas Pressure (barg)",
        "Interspace_Pressure_bar",
        "BackPressure_Drive_End_bar",
        "BackPressure_Non_Drive_End_bar",
        "Duration_s",
        "Temperature_C",
    ]
    for col in numeric_cols:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0.0)

    return result
