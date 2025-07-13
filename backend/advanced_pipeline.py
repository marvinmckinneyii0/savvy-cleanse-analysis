import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from scipy import stats
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import warnings

warnings.filterwarnings('ignore')


class AnalyticsType(Enum):
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"


@dataclass
class DataProfile:
    """Data profiling results"""
    shape: Tuple[int, int]
    missing_percentage: float
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    outlier_percentage: float
    duplicates: int
    data_quality_score: float


@dataclass
class CleaningRecommendation:
    """Cleaning method recommendation"""
    method: str
    confidence: float
    reasons: List[str]
    parameters: Dict[str, Any]


class DataCleaner:
    """Advanced data cleaning with multiple algorithms"""

    def __init__(self):
        self.cleaning_methods = {
            'basic': self._basic_cleaning,
            'statistical': self._statistical_cleaning,
            'ml_based': self._ml_based_cleaning,
            'domain_specific': self._domain_specific_cleaning
        }

    def profile_data(self, df: pd.DataFrame) -> DataProfile:
        """Profile dataset to understand its characteristics"""
        shape = df.shape
        missing_pct = (df.isnull().sum().sum() / (shape[0] * shape[1])) * 100
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = []
        for col in categorical_cols:
            if df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col].dropna().head(100))
                    datetime_cols.append(col)
                except Exception:
                    pass
        categorical_cols = [col for col in categorical_cols if col not in datetime_cols]
        outlier_count = 0
        total_numeric_values = 0
        for col in numeric_cols:
            if df[col].dtype in [np.number]:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
                outlier_count += outliers
                total_numeric_values += len(df[col].dropna())
        outlier_pct = (outlier_count / max(total_numeric_values, 1)) * 100
        duplicates = df.duplicated().sum()
        quality_score = max(0, 100 - missing_pct - (outlier_pct * 0.5) - (duplicates / len(df) * 20))
        return DataProfile(
            shape=shape,
            missing_percentage=missing_pct,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            datetime_columns=datetime_cols,
            outlier_percentage=outlier_pct,
            duplicates=duplicates,
            data_quality_score=quality_score
        )

    def recommend_cleaning_method(self, profile: DataProfile) -> CleaningRecommendation:
        """Recommend optimal cleaning method based on data profile"""
        reasons: List[str] = []
        confidence = 0.0
        if profile.missing_percentage > 30:
            method = 'ml_based'
            confidence = 0.9
            reasons.append(f"High missing data percentage ({profile.missing_percentage:.1f}%)")
            reasons.append("ML-based imputation recommended for complex patterns")
        elif profile.outlier_percentage > 20:
            method = 'statistical'
            confidence = 0.8
            reasons.append(f"High outlier percentage ({profile.outlier_percentage:.1f}%)")
            reasons.append("Statistical methods best for outlier handling")
        elif len(profile.datetime_columns) > 0 or profile.data_quality_score < 60:
            method = 'domain_specific'
            confidence = 0.85
            reasons.append("Domain-specific cleaning needed")
            if len(profile.datetime_columns) > 0:
                reasons.append("Datetime columns detected")
        else:
            method = 'basic'
            confidence = 0.7
            reasons.append("Data quality is acceptable for basic cleaning")
        return CleaningRecommendation(
            method=method,
            confidence=confidence,
            reasons=reasons,
            parameters=self._get_method_parameters(method, profile)
        )

    def _get_method_parameters(self, method: str, profile: DataProfile) -> Dict[str, Any]:
        params = {
            'basic': {
                'drop_threshold': 0.5,
                'fill_numeric': 'median',
                'fill_categorical': 'mode'
            },
            'statistical': {
                'outlier_method': 'iqr',
                'outlier_threshold': 1.5,
                'imputation': 'iterative'
            },
            'ml_based': {
                'imputer': 'knn',
                'n_neighbors': 5,
                'outlier_detector': 'isolation_forest'
            },
            'domain_specific': {
                'datetime_format': 'infer',
                'business_rules': True,
                'custom_validation': True
            }
        }
        return params.get(method, {})

    def clean_data(self, df: pd.DataFrame, method: str = 'auto') -> pd.DataFrame:
        if method == 'auto':
            profile = self.profile_data(df)
            recommendation = self.recommend_cleaning_method(profile)
            method = recommendation.method
        return self.cleaning_methods[method](df)

    def _basic_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        df_clean = df_clean.drop_duplicates()
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        categorical_cols = df_clean.select_dtypes(include=['object']).columns
        for col in numeric_cols:
            df_clean[col].fillna(df_clean[col].median(), inplace=True)
        for col in categorical_cols:
            mode_val = df_clean[col].mode()
            if len(mode_val) > 0:
                df_clean[col].fillna(mode_val[0], inplace=True)
        return df_clean

    def _statistical_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        df_clean = df_clean.drop_duplicates()
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df_clean[col] = np.clip(df_clean[col], lower_bound, upper_bound)
        imputer = SimpleImputer(strategy='median')
        df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
        return df_clean

    def _ml_based_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        df_clean = df_clean.drop_duplicates()
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            knn_imputer = KNNImputer(n_neighbors=5)
            df_clean[numeric_cols] = knn_imputer.fit_transform(df_clean[numeric_cols])
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            outliers = iso_forest.fit_predict(df_clean[numeric_cols])
            df_clean = df_clean[outliers == 1]
        return df_clean

    def _domain_specific_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        df_clean = df_clean.drop_duplicates()
        for col in df_clean.select_dtypes(include=['object']).columns:
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='ignore')
            except Exception:
                pass
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if 'age' in col.lower() or 'price' in col.lower():
                df_clean = df_clean[df_clean[col] >= 0]
        return df_clean


class AnalyticsClassifier:
    """Classify the type of analytics needed based on user request and data"""

    def __init__(self):
        self.keywords = {
            AnalyticsType.DESCRIPTIVE: [
                'summary', 'describe', 'statistics', 'mean', 'median', 'distribution',
                'frequency', 'count', 'average', 'overview', 'profile', 'explore'
            ],
            AnalyticsType.DIAGNOSTIC: [
                'why', 'cause', 'reason', 'correlation', 'relationship', 'impact',
                'influence', 'factor', 'explain', 'analyze', 'drill down'
            ],
            AnalyticsType.PREDICTIVE: [
                'predict', 'forecast', 'future', 'trend', 'model', 'regression',
                'classification', 'machine learning', 'estimate', 'project'
            ],
            AnalyticsType.PRESCRIPTIVE: [
                'recommend', 'optimize', 'suggest', 'should', 'best', 'improve',
                'decision', 'action', 'strategy', 'solution', 'maximize', 'minimize'
            ]
        }

    def classify_analytics_type(self, user_request: str, data_profile: DataProfile) -> Tuple[AnalyticsType, float]:
        user_request_lower = user_request.lower()
        scores: Dict[AnalyticsType, int] = {}
        for analytics_type, keywords in self.keywords.items():
            score = sum(1 for keyword in keywords if keyword in user_request_lower)
            scores[analytics_type] = score
        if data_profile.shape[0] < 100:
            scores[AnalyticsType.DESCRIPTIVE] += 2
        elif data_profile.shape[0] > 1000:
            scores[AnalyticsType.PREDICTIVE] += 1
        if len(data_profile.datetime_columns) > 0:
            scores[AnalyticsType.PREDICTIVE] += 1
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        total_score = sum(scores.values())
        confidence = max_score / max(total_score, 1)
        return best_type, confidence

    def get_analytics_recommendations(self, analytics_type: AnalyticsType, data_profile: DataProfile) -> Dict[str, Any]:
        recommendations = {
            AnalyticsType.DESCRIPTIVE: {
                'methods': ['summary_statistics', 'distributions', 'correlations'],
                'visualizations': ['histograms', 'box_plots', 'scatter_plots'],
                'focus': 'Understanding current state of data'
            },
            AnalyticsType.DIAGNOSTIC: {
                'methods': ['correlation_analysis', 'regression_analysis', 'hypothesis_testing'],
                'visualizations': ['heatmaps', 'regression_plots', 'feature_importance'],
                'focus': 'Understanding why things happened'
            },
            AnalyticsType.PREDICTIVE: {
                'methods': ['time_series_analysis', 'machine_learning', 'forecasting'],
                'visualizations': ['trend_lines', 'prediction_intervals', 'model_performance'],
                'focus': 'Predicting future outcomes'
            },
            AnalyticsType.PRESCRIPTIVE: {
                'methods': ['optimization', 'simulation', 'decision_trees'],
                'visualizations': ['decision_trees', 'optimization_plots', 'scenario_analysis'],
                'focus': 'Recommending best actions'
            }
        }
        return recommendations.get(analytics_type, {})


class LLMDataInterface:
    """Interface for handling LLM interactions with data"""

    def __init__(self, data_cleaner: DataCleaner, analytics_classifier: AnalyticsClassifier):
        self.data_cleaner = data_cleaner
        self.analytics_classifier = analytics_classifier
        self.current_data: Optional[pd.DataFrame] = None
        self.current_profile: Optional[DataProfile] = None

    def load_data(self, df: pd.DataFrame) -> str:
        self.current_data = df
        self.current_profile = self.data_cleaner.profile_data(df)
        return f"""
Data loaded successfully!
- Shape: {self.current_profile.shape}
- Missing data: {self.current_profile.missing_percentage:.1f}%
- Data quality score: {self.current_profile.data_quality_score:.1f}/100
- Numeric columns: {len(self.current_profile.numeric_columns)}
- Categorical columns: {len(self.current_profile.categorical_columns)}
"""

    def process_user_question(self, question: str) -> Dict[str, Any]:
        if self.current_data is None:
            return {"error": "No data loaded. Please load data first."}
        analytics_type, confidence = self.analytics_classifier.classify_analytics_type(
            question, self.current_profile
        )
        recommendations = self.analytics_classifier.get_analytics_recommendations(
            analytics_type, self.current_profile
        )
        response = {
            "analytics_type": analytics_type.value,
            "confidence": confidence,
            "recommendations": recommendations,
            "data_summary": {
                "shape": self.current_profile.shape,
                "quality_score": self.current_profile.data_quality_score,
                "missing_percentage": self.current_profile.missing_percentage
            },
            "suggested_next_steps": self._get_next_steps(analytics_type, self.current_profile)
        }
        return response

    def _get_next_steps(self, analytics_type: AnalyticsType, profile: DataProfile) -> List[str]:
        steps: List[str] = []
        if profile.data_quality_score < 70:
            steps.append("Clean and preprocess the data")
        if analytics_type == AnalyticsType.DESCRIPTIVE:
            steps.extend([
                "Generate summary statistics",
                "Create data visualizations",
                "Identify patterns and trends"
            ])
        elif analytics_type == AnalyticsType.DIAGNOSTIC:
            steps.extend([
                "Perform correlation analysis",
                "Conduct hypothesis testing",
                "Analyze relationships between variables"
            ])
        elif analytics_type == AnalyticsType.PREDICTIVE:
            steps.extend([
                "Prepare features for modeling",
                "Split data into training/testing sets",
                "Build and validate predictive models"
            ])
        elif analytics_type == AnalyticsType.PRESCRIPTIVE:
            steps.extend([
                "Define optimization objectives",
                "Identify decision variables",
                "Build recommendation engine"
            ])
        return steps


if __name__ == "__main__":
    # Example usage and quick sanity check
    np.random.seed(42)
    sample_data = pd.DataFrame({
        "age": np.random.randint(18, 80, 1000),
        "income": np.random.normal(50000, 15000, 1000),
        "spending": np.random.normal(30000, 10000, 1000),
        "category": np.random.choice(["A", "B", "C"], 1000),
        "date": pd.date_range("2023-01-01", periods=1000, freq="D"),
    })

    sample_data.loc[0:50, "income"] = np.nan
    sample_data.loc[100:110, "spending"] = sample_data.loc[100:110, "spending"] * 10

    cleaner = DataCleaner()
    classifier = AnalyticsClassifier()
    llm_interface = LLMDataInterface(cleaner, classifier)

    print("=== Data Profiling ===")
    profile = cleaner.profile_data(sample_data)
    print(f"Data quality score: {profile.data_quality_score:.1f}")
    print(f"Missing percentage: {profile.missing_percentage:.1f}%")

    print("\n=== Cleaning Recommendation ===")
    recommendation = cleaner.recommend_cleaning_method(profile)
    print(f"Recommended method: {recommendation.method}")
    print(f"Confidence: {recommendation.confidence:.1f}")
    print(f"Reasons: {recommendation.reasons}")

    print("\n=== Clean Data ===")
    clean_data = cleaner.clean_data(sample_data)
    print(f"Original shape: {sample_data.shape}")
    print(f"Cleaned shape: {clean_data.shape}")

    print("\n=== Analytics Classification ===")
    test_questions = [
        "Show me the average income by category",
        "Why did spending increase in Q2?",
        "Can you predict next month's sales?",
        "What's the best strategy to increase revenue?",
    ]

    llm_interface.load_data(clean_data)
    for question in test_questions:
        response = llm_interface.process_user_question(question)
        print(f"\nQuestion: {question}")
        print(f"Analytics type: {response['analytics_type']}")
        print(f"Confidence: {response['confidence']:.2f}")
        print(f"Focus: {response['recommendations']['focus']}")
