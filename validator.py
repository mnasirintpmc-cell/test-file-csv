import pandas as pd


def safe_float(v):
    """Convert safely to float, returning 0 when blank or non‑numeric."""
    if pd.isna(v) or v in ["", None]:
        return 0.0
    try:
        return float(v)
    except:
        return 0.0


def validate_sequence(df):
    """
    Validate a technician / spec dataframe.
    Produces a list of human‑readable warning strings.
    """

    warnings = []

    # ------------------------------------------------------------------
    # 1️⃣  Duplicate Step detection
    # ------------------------------------------------------------------
    if "Step" in df.columns:
        step_counts = df["Step"].value_counts()
        dup_steps = step_counts[step_counts > 1].index.tolist()
        for s in dup_steps:
            warnings.append(f"Step {s}: duplicated step number detected")

    # ------------------------------------------------------------------
    # 2️⃣  Row‑by‑row safety logic
    # ------------------------------------------------------------------
    for i, row in df.iterrows():

        step = row.get("Step", i + 1)

        primary = safe_float(row.get("Primary seal Gas Pressure (barg)"))
        inter = safe_float(row.get("Interspace_Pressure_bar"))
        bp_de = safe_float(row.get("BackPressure_Drive_End_bar"))
        bp_nde = safe_float(row.get("BackPressure_Non_Drive_End_bar"))
        mode = int(safe_float(row.get("Test_Mode")))

        # -- Skip empty placeholder rows
        if primary == 0 and inter == 0 and bp_de == 0 and bp_nde == 0:
            continue

        # ------------------------------------------------------------------
        # 🔸 Existing interlock checks
        # ------------------------------------------------------------------
        if inter > primary:
            warnings.append(f"Step {step}: Interspace pressure > Primary pressure")
        if bp_de > primary:
            warnings.append(f"Step {step}: Back‑pressure DE > Primary pressure")
        if bp_nde > primary:
            warnings.append(f"Step {step}: Back‑pressure NDE > Primary pressure")

        secondary = max(inter, bp_de, bp_nde)
        if secondary > 0:
            delta_p = primary - secondary
            if delta_p < 0.2:
                warnings.append(
                    f"Step {step}: ΔP < 0.2 bar (Primary {primary} / Secondary {secondary})"
                )

        # ------------------------------------------------------------------
        # 3️⃣  New rule: Mode 2 but Primary = 0
        # ------------------------------------------------------------------
        if mode == 2 and primary == 0:
            warnings.append(f"Step {step}: Test Mode 2 but Primary pressure = 0")

        # ------------------------------------------------------------------
        # 4️⃣  New rule: Mode 2 but BackPressure > Interspace
        # ------------------------------------------------------------------
        if mode == 2 and (bp_de > inter or bp_nde > inter):
            details = []
            if bp_de > inter:
                details.append("DE")
            if bp_nde > inter:
                details.append("NDE")
            side_info = "/".join(details)
            warnings.append(
                f"Step {step}: Test Mode 2 Back‑pressure ({side_info}) > Interspace pressure"
            )

    return warnings
