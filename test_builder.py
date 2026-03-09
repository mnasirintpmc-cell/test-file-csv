import pandas as pd


class TestBuilder:

    def __init__(self):
        self.tests = []

    def add_test(self, df):
        """
        Add a test dataframe to the sequence
        """
        if df is None or df.empty:
            return

        self.tests.append(df)

    def build(self):
        """
        Combine all loaded tests and rebuild step numbers
        """
        if not self.tests:
            return pd.DataFrame()

        combined = pd.concat(self.tests, ignore_index=True)

        combined["Step"] = range(1, len(combined) + 1)

        cols = ["Step"] + [c for c in combined.columns if c != "Step"]

        return combined[cols]
