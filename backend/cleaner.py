import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Simple cleaning logic: fill missing values and drop duplicates."""
    cleaned = df.copy()
    for col in cleaned.columns:
        if cleaned[col].dtype == 'O':
            cleaned[col].fillna('', inplace=True)
        else:
            cleaned[col].fillna(cleaned[col].mean(numeric_only=True), inplace=True)
    cleaned.drop_duplicates(inplace=True)
    return cleaned
