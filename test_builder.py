import pandas as pd


class TestBuilder:

    def __init__(self):
        self.tests = []

    def add_test(self, df, name="Test"):

        if df is None or df.empty:
            return

        df = df.copy()

        df = df.drop(columns=["Step"], errors="ignore")

        df["Test_Name"] = name

        self.tests.append(df)

    def build(self):

        if not self.tests:
            return pd.DataFrame()

        combined = pd.concat(self.tests, ignore_index=True)

        combined["Step"] = range(1, len(combined) + 1)

        cols = ["Step"] + [c for c in combined.columns if c != "Step"]

        return combined[cols]
