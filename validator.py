import pandas as pd


def validate_test_sequence(df):

    warnings = []

    for i, row in df.iterrows():

        cell = float(row.get("Primary seal Gas Pressure (barg)",0))
        inter = float(row.get("Interspace_Pressure_bar",0))
        bp_de = float(row.get("BackPressure_Drive_End_bar",0))
        bp_nde = float(row.get("BackPressure_Non_Drive_End_bar",0))

        # rule 1
        if cell <= inter:
            warnings.append(
                f"Row {i+1}: Cell pressure must be greater than Interspace"
            )

        # rule 2
        if (cell - inter) < 0.2:
            warnings.append(
                f"Row {i+1}: Cell − Interspace < 0.2 bar safety margin"
            )

        # rule 3
        if inter < 0:
            warnings.append(
                f"Row {i+1}: Interspace pressure cannot be negative"
            )

        # rule 4
        if bp_de != bp_nde:
            warnings.append(
                f"Row {i+1}: BP_DE and BP_NDE mismatch"
            )

    return warnings
