def validate_sequence(df):

    warnings = []

    for i, row in df.iterrows():

        step = row.get("Step")

        try:
            primary = float(row["Primary seal Gas Pressure (barg)"])
        except:
            continue

        try:
            inter = float(row["Interspace_Pressure_bar"])
        except:
            inter = 0

        if primary < inter:

            warnings.append(
                f"Step {step}: Primary pressure lower than interspace"
            )

        if inter > 0:

            if primary - inter < 0.2:

                warnings.append(
                    f"Step {step}: ΔP < 0.2 bar"
                )

    return warnings
