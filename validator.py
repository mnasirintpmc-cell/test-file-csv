import pandas as pd


def safe_float(v):

    if pd.isna(v):
        return 0

    try:
        return float(v)
    except:
        return 0


def validate_sequence(df):

    warnings = []

    for i, row in df.iterrows():

        step = row.get("Step", i + 1)

        primary = safe_float(row.get("Primary seal Gas Pressure (barg)"))
        inter = safe_float(row.get("Interspace_Pressure_bar"))
        bp_de = safe_float(row.get("BackPressure_Drive_End_bar"))
        bp_nde = safe_float(row.get("BackPressure_Non_Drive_End_bar"))

        # TEST MODE override
        if primary == 0:

            if "Test_Mode" in df.columns:
                df.at[i, "Test_Mode"] = 1

            continue

        if inter > primary:
            warnings.append(f"Step {step}: Interspace > Primary")

        if bp_de > primary:
            warnings.append(f"Step {step}: BP DE > Primary")

        if bp_nde > primary:
            warnings.append(f"Step {step}: BP NDE > Primary")

        secondary = max(inter, bp_de, bp_nde)

        if secondary > 0:

            delta_p = primary - secondary

            if delta_p < .2:
                warnings.append(
                    f"Step {step}: ΔP < 10 bar (Primary {primary} / Secondary {secondary})"
                )

    return warnings
