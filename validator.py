def validate_sequence(df):

    warnings = []

    for i, r in df.iterrows():

        cell = r["Primary seal Gas Pressure (barg)"]
        inter = r["Interspace_Pressure_bar"]

        if cell <= inter:

            warnings.append(
                f"Row {i+1}: Cell pressure must be greater than Interspace"
            )

        if (cell - inter) < 0.2:

            warnings.append(
                f"Row {i+1}: Cell − Interspace < 0.2 bar"
            )

    return warnings
