# STATUS: LEGACY — deprecate. Scheduled for removal alongside advanced_pipeline.py
# in Phase 3 when backend/api/ takes over request handling. Do NOT import from
# new code — this module is a thin adapter over the legacy reference pipeline.

import pandas as pd
from typing import Any, Dict

from advanced_pipeline import DataCleaner, AnalyticsClassifier, LLMDataInterface

_cleaner = DataCleaner()
_classifier = AnalyticsClassifier()
_interface = LLMDataInterface(_cleaner, _classifier)


def analyze_goal(df: pd.DataFrame, goal: str) -> Dict[str, Any]:
    """Analyze a user question with the advanced analytics pipeline."""
    _interface.load_data(df)
    return _interface.process_user_question(goal)
