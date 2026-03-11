import pandas as pd


def validate_sequence(df):

    warnings = []

    for i, row in df.iterrows():

        primary = row.get("Primary seal Gas Pressure (barg)")
        inter = row.get("Interspace_Pressure_bar")

        try:
            primary = float(primary)
            inter = float(inter)
        except:
            continue

        step = row.get("Step", i + 1)

        if primary < inter:

            warnings.append(
                f"Step {step}: Primary pressure lower than interspace"
            )

        if primary - inter < 0.2 and inter > 0:

            warnings.append(
                f"Step {step}: ΔP < 0.2 bar"
            )

    return warnings
