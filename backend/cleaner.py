import pandas as pd
from advanced_pipeline import DataCleaner

_cleaner = DataCleaner()


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean dataframe using the advanced DataCleaner."""
    return _cleaner.clean_data(df, method="auto")
