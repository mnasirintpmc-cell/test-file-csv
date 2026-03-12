import pandas as pd

TECH_COLUMNS = [
"Step",
"Speed_RPM",
"Primary seal Gas Pressure (barg)",
"Interspace_Pressure_bar",
"BackPressure_Drive_End_bar",
"BackPressure_Non_Drive_End_bar",
"Gas_Injection_bar",
"Duration_s",
"Acceptance point",
"Temperature_C",
"Gas_Type",
"Test_Mode",
"Measurement",
"Torque_Check",
"Notes"
]


def scan_spec(file):

    sheets = pd.read_excel(
        file,
        engine="pyxlsb",
        sheet_name=None,
        header=None
    )

    rows = []

    for sheet_name, df in sheets.items():

        if df is None or df.empty:
            continue

        sheet_lower = sheet_name.lower()

        mode = 1
        if "secondary" in sheet_lower:
            mode = 2

        for r in range(len(df)):

            if str(df.iloc[r,0]).strip().lower() != "test step":
                continue

            header_row = r

            for i in range(header_row+1,len(df)):

                row = df.iloc[i]

                step_val = row[0]

                if step_val is None:
                    continue

                if "end of" in str(step_val).lower():
                    break

                try:
                    step = int(float(step_val))
                except:
                    continue

                primary_spec = row[1]
                secondary = row[2]
                speed = row[3]
                temp = row[4]
                hold = row[5]
                remarks = row[8]

                try:
                    secondary = float(secondary)
                except:
                    secondary = 0

                if mode == 1:

                    try:
                        primary = float(primary_spec)
                    except:
                        primary = secondary + 5

                    inter = 0
                    bp_de = secondary
                    bp_nde = secondary

                else:

                    primary = secondary + 5
                    inter = secondary
                    bp_de = 0
                    bp_nde = 0

                ap = 1 if isinstance(remarks,str) and remarks.strip() != "" else 0

                rows.append({

                    "Step":step,
                    "Speed_RPM":speed,
                    "Primary seal Gas Pressure (barg)":primary,
                    "Interspace_Pressure_bar":inter,
                    "BackPressure_Drive_End_bar":bp_de,
                    "BackPressure_Non_Drive_End_bar":bp_nde,
                    "Gas_Injection_bar":0,
                    "Duration_s":hold*60 if hold else 0,
                    "Acceptance point":ap,
                    "Temperature_C":temp,
                    "Gas_Type":"Air",
                    "Test_Mode":mode,
                    "Measurement":1,
                    "Torque_Check":0,
                    "Notes":remarks if remarks else ""

                })

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.sort_values("Step").reset_index(drop=True)

    return df
