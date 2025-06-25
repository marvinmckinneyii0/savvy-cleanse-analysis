import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from typing import Any, Dict


def analyze_goal(df: pd.DataFrame, goal: str) -> Dict[str, Any]:
    """Very basic analytics based on goal type."""
    if goal == 'descriptive':
        summary = df.describe(include='all').to_dict()
        return {"type": "descriptive", "summary": summary}
    elif goal == 'predictive':
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) < 2:
            return {"error": "Not enough numeric data for prediction"}
        X = df[numeric_cols[:-1]]
        y = df[numeric_cols[-1]]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = LinearRegression().fit(X_train, y_train)
        preds = model.predict(X_test)
        mse = mean_squared_error(y_test, preds)
        return {"type": "predictive", "mse": mse}
    else:
        return {"message": f"Goal '{goal}' not implemented"}
