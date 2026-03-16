def validate_sequence(df):

    warnings = []

    for i, row in df.iterrows():

        step = row.get("Step")

        try:
            primary = float(row["Primary seal Gas Pressure (barg)"])
        except:
            continue

        # read all possible secondary pressures
        try:
            inter = float(row.get("Interspace_Pressure_bar",0))
        except:
            inter = 0

        try:
            bp_de = float(row.get("BackPressure_Drive_End_bar",0))
        except:
            bp_de = 0

        try:
            bp_nde = float(row.get("BackPressure_Non_Drive_End_bar",0))
        except:
            bp_nde = 0

        # find the active secondary pressure
        secondary = max(inter, bp_de, bp_nde)

        # --------------------------------
        # Rule 1: secondary must be lower
        # --------------------------------

        if secondary > primary:

            warnings.append(
                f"Step {step}: Secondary pressure greater than primary"
            )

        # --------------------------------
        # Rule 2: ΔP minimum requirement
        # --------------------------------

        if secondary > 0:

            if primary - secondary < 0.2:

                warnings.append(
                    f"Step {step}: ΔP < 0.2 bar"
                )

    return warnings
