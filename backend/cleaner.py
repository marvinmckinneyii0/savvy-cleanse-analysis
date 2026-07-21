# STATUS: LEGACY — do not import from new code. Delegates to the unfactored
# `advanced_pipeline.DataCleaner` (on the project-context legacy list) and has no
# tests. It is NOT the deterministic Cleaning Engine. The Tier-based cleaning
# introduced in Epic 3 lives in `backend/pipeline/cleaning_engine.py` +
# `cleaning_primitives.py` (Story 3.2); this file is left untouched and unwired,
# pending the factory refactor noted in project-context.md. New cleaning work
# must target the pipeline modules, never this one.
import pandas as pd
from advanced_pipeline import DataCleaner

_cleaner = DataCleaner()


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean dataframe using the advanced DataCleaner."""
    return _cleaner.clean_data(df, method="auto")
