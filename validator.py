def validate_sequence(df):

    warnings = []

    for i, row in df.iterrows():

        cell = row["Primary seal Gas Pressure (barg)"]
        inter = row["Interspace_Pressure_bar"]

        if cell < inter:
            warnings.append(
                f"Step {i+1}: Primary pressure lower than interspace"
            )

        if cell - inter < 0.2 and inter > 0:
            warnings.append(
                f"Step {i+1}: Primary-interspace < 0.2 bar"
            )

    return warnings
