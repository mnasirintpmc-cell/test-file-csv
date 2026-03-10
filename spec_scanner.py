import pandas as pd

# --------------------------------------------------
# Ensure pyxlsb is installed
# --------------------------------------------------

try:
    import pyxlsb
except ImportError:
    raise ImportError(
        "Missing dependency 'pyxlsb'. Install it with: pip install pyxlsb"
    )


# --------------------------------------------------
# SPEC SCANNER
# --------------------------------------------------

def scan_spec(file):

    # Read all sheets from the spec
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

        mode = 1
        header_found = False

        for _, r in df.iterrows():

            text = str(r[0]).lower()

            # Detect primary / secondary section
            if "primary" in text:
                mode = 1
                continue

            if "secondary" in text:
                mode = 2
                continue

            # Detect table start
            if "test step" in text:
                header_found = True
                continue

            if not header_found:
                continue

            # ------------------------------------------
            # Try reading row values
            # ------------------------------------------

            try:

                spec_step = int(r[0])
                primary_spec = r[1]
                secondary = r[2]
                speed = r[3]
                temp = r[4]
                hold = r[5]

                remarks = ""

                if len(r) > 8:
                    remarks = str(r[8])

            except Exception:
                continue

            # Skip rows without secondary pressure
            if pd.isna(secondary):
                continue

            secondary = float(secondary)

            # ------------------------------------------
            # Primary pressure logic
            # ------------------------------------------

            if "secondary seal gas pressure" in str(primary_spec).lower():
                primary = secondary + 5
            else:
                try:
                    primary = float(primary_spec)
                except:
                    primary = secondary + 5

            # ------------------------------------------
            # Temperature logic
            # ------------------------------------------

            if str(temp).upper() == "AMB":
                temp = 60

            # ------------------------------------------
            # Speed safety
            # ------------------------------------------

            try:
                speed = float(speed)
            except:
                speed = 0

            # ------------------------------------------
            # Hold time safety
            # ------------------------------------------

            hold = 0 if pd.isna(hold) else hold

            duration = int(hold * 60)

            # ------------------------------------------
            # Pressure routing
            # ------------------------------------------

            if mode == 1:

                interspace = 0
                bp_de = secondary
                bp_nde = secondary

            else:

                interspace = secondary
                bp_de = 0
                bp_nde = 0

            # ------------------------------------------
            # Acceptance point
            # ------------------------------------------

            ap = 1 if "acceptance" in remarks.lower() else 0

            # ------------------------------------------
            # Build row
            # ------------------------------------------

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

                "Spec_Sheet": sheet_name

            })

    # --------------------------------------------------
    # Convert to dataframe
    # --------------------------------------------------

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("No test steps detected in the spec file")

    # --------------------------------------------------
    # Sort by spec step
    # --------------------------------------------------

    df = df.sort_values("spec_step")

    # --------------------------------------------------
    # Generate step numbers
    # --------------------------------------------------

    df.insert(0, "Step", range(1, len(df) + 1))

    df = df.drop(columns=["spec_step"])

    return df
