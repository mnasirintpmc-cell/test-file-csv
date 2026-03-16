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

    for _, row in df.iterrows():

        step = row.get("Step")

        primary = safe_float(row.get("Primary seal Gas Pressure (barg)"))
        inter = safe_float(row.get("Interspace_Pressure_bar"))
        bp_de = safe_float(row.get("BackPressure_Drive_End_bar"))
        bp_nde = safe_float(row.get("BackPressure_Non_Drive_End_bar"))

        # --------------------------------
        # Direct pressure safety checks
        # --------------------------------

        if inter > primary:
            warnings.append(
                f"Step {step}: Interspace pressure ({inter}) greater than primary ({primary})"
            )

        if bp_de > primary:
            warnings.append(
                f"Step {step}: BP Drive End ({bp_de}) greater than primary ({primary})"
            )

        if bp_nde > primary:
            warnings.append(
                f"Step {step}: BP Non-Drive End ({bp_nde}) greater than primary ({primary})"
            )

        # --------------------------------
        # Differential pressure check
        # --------------------------------

        secondary = max(inter, bp_de, bp_nde)

        if secondary > 0:

            delta_p = primary - secondary

            if delta_p < 0.2:

                warnings.append(
                    f"Step {step}: ΔP < 0.2 bar (Primary {primary} / Secondary {secondary})"
                )

    return warnings
