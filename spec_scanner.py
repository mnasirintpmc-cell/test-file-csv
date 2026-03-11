import pandas as pd
import re

# --------------------------------------------------
# Ensure pyxlsb is installed
# --------------------------------------------------

try:
    import pyxlsb
except ImportError:
    raise ImportError(
        "Missing dependency 'pyxlsb'. Install with: pip install pyxlsb"
    )


# --------------------------------------------------
# SPEC SCANNER
# --------------------------------------------------

def scan_spec(file):

    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    # --------------------------------------------------
    # Scan all sheets (each sheet = one test)
    # --------------------------------------------------

    for sheet_name, df in sheets.items():

        mode = 1

        for _, r in df.iterrows():

            value = str(r[0]).strip()
            text = value.lower()

            # Detect mode
            if "primary" in text:
                mode = 1
                continue

            if "secondary" in text:
                mode = 2
                continue

            # --------------------------------------------------
            # Detect step number
            # --------------------------------------------------

            match = re.search(r"\d+", value)

            if not match:
                continue

            spec_step = int(match.group())

            # --------------------------------------------------
            # Safe column reading
            # --------------------------------------------------

            primary_spec = r[1] if len(r) > 1 else None
            secondary = r[2] if len(r) > 2 else None
            speed = r[3] if len(r) > 3 else 0
            temp = r[4] if len(r) > 4 else 60
            hold = r[5] if len(r) > 5 else 0

            remarks = str(r[8]) if len(r) > 8 else ""

            # --------------------------------------------------
            # Skip rows without valid secondary pressure
            # --------------------------------------------------

            if pd.isna(secondary):
                continue

            try:
                secondary = float(secondary)
            except:
                continue

            # --------------------------------------------------
            # Primary pressure rule
            # --------------------------------------------------

            if "secondary seal gas pressure" in str(primary_spec).lower():
                primary = secondary + 5
            else:
                try:
                    primary = float(primary_spec)
                except:
                    primary = secondary + 5

            # --------------------------------------------------
            # Temperature handling
            # --------------------------------------------------

            if str(temp).upper() == "AMB":
                temp = 60

            # --------------------------------------------------
            # Speed safety
            # --------------------------------------------------

            try:
                speed = float(speed)
            except:
                speed = 0

            # --------------------------------------------------
            # Duration
            # --------------------------------------------------

            hold = 0 if pd.isna(hold) else hold
            duration = int(hold * 60)

            # --------------------------------------------------
            # Pressure routing
            # --------------------------------------------------

            if mode == 1:

                interspace = 0
                bp_de = secondary
                bp_nde = secondary

            else:

                interspace = secondary
                bp_de = 0
                bp_nde = 0

            # --------------------------------------------------
            # Acceptance detection
            # --------------------------------------------------

            ap = 1 if "acceptance" in remarks.lower() else 0

            # --------------------------------------------------
            # Append row
            # --------------------------------------------------

            rows.append({

                "spec_step": spec_step,
                "Speed_RPM": speed,
                "Primary seal Gas Pressure (barg)": primary,
                "Interspace_Pressure_bar": interspace,
                "BackPressure_Drive_End_bar": bp_de,
                "BackPressure_Non_Drive_End_bar": bp_nde,
                "Gas_Injection_bar": 0,
                "Duration_s": duration,
                "Acceptance point": ap,
                "Temperature_C": temp,
                "Gas_Type": "Air",
                "Test_Mode": mode,
                "Measurement": ap,
                "Torque_Check": 0,
                "Notes": remarks,
                "Test_Name": sheet_name

            })

    # --------------------------------------------------
    # Check results
    # --------------------------------------------------

    if not rows:
        raise ValueError(
            "No numeric test steps found in any sheet"
        )

    df = pd.DataFrame(rows)

    df = df.sort_values("spec_step")

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["spec_step"])

    return df
