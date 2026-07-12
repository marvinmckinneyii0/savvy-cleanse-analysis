# STATUS: Legacy reference implementation
# This module is NOT part of the SAINT pipeline.
# Reusable logic has been extracted into pipeline/ and models/.
# Retained for web API compatibility until Phase 3 integration.

"""
Comprehensive Analytics Module for SAINT
Implements descriptive, diagnostic, predictive, and prescriptive analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union
from scipy import stats
from scipy.optimize import minimize
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings  # retained for downstream warning emission; global suppression removed in Story 1.1


class DescriptiveAnalytics:
    """Implements descriptive analytics - What happened?"""
    
    @staticmethod
    def statistical_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive statistical summaries"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        results = {
            'dataset_info': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(numeric_cols),
                'categorical_columns': len(categorical_cols),
                'missing_values_total': df.isnull().sum().sum(),
                'duplicate_rows': df.duplicated().sum()
            },
            'numeric_summary': {},
            'categorical_summary': {},
            'missing_values': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
        # Numeric column analysis
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) > 0:
                results['numeric_summary'][col] = {
                    'count': len(series),
                    'mean': float(series.mean()),
                    'median': float(series.median()),
                    'mode': float(series.mode().iloc[0]) if not series.mode().empty else None,
                    'std': float(series.std()),
                    'variance': float(series.var()),
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'q25': float(series.quantile(0.25)),
                    'q75': float(series.quantile(0.75)),
                    'iqr': float(series.quantile(0.75) - series.quantile(0.25)),
                    'skewness': float(stats.skew(series)),
                    'kurtosis': float(stats.kurtosis(series)),
                    'outliers_count': DescriptiveAnalytics._count_outliers(series)
                }
        
        # Categorical column analysis
        for col in categorical_cols:
            series = df[col].dropna()
            if len(series) > 0:
                value_counts = series.value_counts()
                results['categorical_summary'][col] = {
                    'count': len(series),
                    'unique_values': len(value_counts),
                    'most_frequent': str(value_counts.index[0]),
                    'most_frequent_count': int(value_counts.iloc[0]),
                    'least_frequent': str(value_counts.index[-1]),
                    'least_frequent_count': int(value_counts.iloc[-1]),
                    'distribution': value_counts.head(10).to_dict()
                }
        
        return results
    
    @staticmethod
    def _count_outliers(series: pd.Series) -> int:
        """Count outliers using IQR method"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return len(series[(series < lower_bound) | (series > upper_bound)])


class DiagnosticAnalytics:
    """Implements diagnostic analytics - Why did it happen?"""
    
    @staticmethod
    def correlation_analysis(df: pd.DataFrame) -> Dict[str, Any]:
        """Perform correlation analysis"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return {'error': 'Need at least 2 numeric columns for correlation analysis'}
        
        # Pearson correlation
        pearson_corr = numeric_df.corr(method='pearson')
        
        # Spearman correlation (for non-linear relationships)
        spearman_corr = numeric_df.corr(method='spearman')
        
        # Find strongest correlations
        def get_strong_correlations(corr_matrix, threshold=0.5):
            strong_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) >= threshold:
                        strong_corr.append({
                            'feature1': corr_matrix.columns[i],
                            'feature2': corr_matrix.columns[j],
                            'correlation': float(corr_val),
                            'strength': 'strong' if abs(corr_val) >= 0.7 else 'moderate'
                        })
            return sorted(strong_corr, key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'pearson_correlation': pearson_corr.to_dict(),
            'spearman_correlation': spearman_corr.to_dict(),
            'strong_correlations': get_strong_correlations(pearson_corr),
            'correlation_insights': DiagnosticAnalytics._generate_correlation_insights(pearson_corr)
        }
    
    @staticmethod
    def hypothesis_testing(df: pd.DataFrame, target_col: str, feature_col: str) -> Dict[str, Any]:
        """Perform hypothesis testing"""
        if target_col not in df.columns or feature_col not in df.columns:
            return {'error': 'Specified columns not found'}
        
        target_data = df[target_col].dropna()
        feature_data = df[feature_col].dropna()
        
        # Determine test type based on data types
        target_is_numeric = pd.api.types.is_numeric_dtype(target_data)
        feature_is_numeric = pd.api.types.is_numeric_dtype(feature_data)
        
        results = {}
        
        if target_is_numeric and feature_is_numeric:
            # Pearson correlation test
            corr_coeff, p_value = stats.pearsonr(
                df[[target_col, feature_col]].dropna()[target_col],
                df[[target_col, feature_col]].dropna()[feature_col]
            )
            results['test_type'] = 'Pearson Correlation Test'
            results['correlation_coefficient'] = float(corr_coeff)
            results['p_value'] = float(p_value)
            results['is_significant'] = p_value < 0.05
            
        elif target_is_numeric and not feature_is_numeric:
            # T-test or ANOVA for numeric target vs categorical feature
            groups = [group[target_col].dropna() for name, group in df.groupby(feature_col)]
            if len(groups) == 2:
                # Two-sample t-test
                stat, p_value = stats.ttest_ind(groups[0], groups[1])
                results['test_type'] = 'Two-sample T-test'
            else:
                # One-way ANOVA
                stat, p_value = stats.f_oneway(*groups)
                results['test_type'] = 'One-way ANOVA'
            
            results['test_statistic'] = float(stat)
            results['p_value'] = float(p_value)
            results['is_significant'] = p_value < 0.05
            
        elif not target_is_numeric and not feature_is_numeric:
            # Chi-square test for independence
            contingency_table = pd.crosstab(df[target_col], df[feature_col])
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            
            results['test_type'] = 'Chi-square Test of Independence'
            results['chi2_statistic'] = float(chi2)
            results['p_value'] = float(p_value)
            results['degrees_of_freedom'] = int(dof)
            results['is_significant'] = p_value < 0.05
            results['contingency_table'] = contingency_table.to_dict()
        
        return results
    
    @staticmethod
    def _generate_correlation_insights(corr_matrix: pd.DataFrame) -> List[str]:
        """Generate insights from correlation matrix"""
        insights = []
        
        # Find highest correlations
        max_corr = 0
        max_pair = None
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = abs(corr_matrix.iloc[i, j])
                if corr_val > max_corr:
                    max_corr = corr_val
                    max_pair = (corr_matrix.columns[i], corr_matrix.columns[j])
        
        if max_pair:
            insights.append(f"Strongest correlation is between {max_pair[0]} and {max_pair[1]} ({max_corr:.3f})")
        
        # Count strong correlations
        strong_count = 0
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) >= 0.7:
                    strong_count += 1
        
        insights.append(f"Found {strong_count} strong correlations (>0.7)")
        
        return insights


class PredictiveAnalytics:
    """Implements predictive analytics - What will happen?"""
    
    @staticmethod
    def build_regression_model(df: pd.DataFrame, target_col: str, feature_cols: List[str] = None) -> Dict[str, Any]:
        """Build regression model for numeric prediction"""
        if target_col not in df.columns:
            return {'error': f'Target column {target_col} not found'}
        
        # Prepare data
        if feature_cols is None:
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in feature_cols:
                feature_cols.remove(target_col)
        
        # Clean data
        model_df = df[feature_cols + [target_col]].dropna()
        if len(model_df) < 10:
            return {'error': 'Insufficient data for modeling (need at least 10 rows)'}
        
        X = model_df[feature_cols]
        y = model_df[target_col]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        results = {}
        
        # Linear Regression
        lr_model = LinearRegression()
        lr_model.fit(X_train_scaled, y_train)
        lr_pred = lr_model.predict(X_test_scaled)
        lr_r2 = r2_score(y_test, lr_pred)
        lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))
        
        results['linear_regression'] = {
            'r2_score': float(lr_r2),
            'rmse': float(lr_rmse),
            'feature_importance': dict(zip(feature_cols, lr_model.coef_.tolist()))
        }
        
        # Random Forest Regression
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)
        rf_r2 = r2_score(y_test, rf_pred)
        rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
        
        results['random_forest'] = {
            'r2_score': float(rf_r2),
            'rmse': float(rf_rmse),
            'feature_importance': dict(zip(feature_cols, rf_model.feature_importances_.tolist()))
        }
        
        # Determine best model
        best_model = 'linear_regression' if lr_r2 > rf_r2 else 'random_forest'
        results['best_model'] = best_model
        results['model_comparison'] = {
            'linear_regression_r2': float(lr_r2),
            'random_forest_r2': float(rf_r2),
            'recommendation': f"Use {best_model.replace('_', ' ')} model (R² = {max(lr_r2, rf_r2):.3f})"
        }
        
        return results
    
    @staticmethod
    def build_classification_model(df: pd.DataFrame, target_col: str, feature_cols: List[str] = None) -> Dict[str, Any]:
        """Build classification model for categorical prediction"""
        if target_col not in df.columns:
            return {'error': f'Target column {target_col} not found'}
        
        # Prepare data
        if feature_cols is None:
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in feature_cols:
                feature_cols.remove(target_col)
        
        # Clean data
        model_df = df[feature_cols + [target_col]].dropna()
        if len(model_df) < 10:
            return {'error': 'Insufficient data for modeling (need at least 10 rows)'}
        
        X = model_df[feature_cols]
        y = model_df[target_col]
        
        # Encode target if necessary
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        results = {}
        
        # Logistic Regression
        lr_model = LogisticRegression(random_state=42, max_iter=1000)
        lr_model.fit(X_train_scaled, y_train)
        lr_pred = lr_model.predict(X_test_scaled)
        lr_accuracy = accuracy_score(y_test, lr_pred)
        
        results['logistic_regression'] = {
            'accuracy': float(lr_accuracy),
            'classification_report': classification_report(y_test, lr_pred, output_dict=True)
        }
        
        # Random Forest Classification
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)
        rf_accuracy = accuracy_score(y_test, rf_pred)
        
        results['random_forest'] = {
            'accuracy': float(rf_accuracy),
            'feature_importance': dict(zip(feature_cols, rf_model.feature_importances_.tolist())),
            'classification_report': classification_report(y_test, rf_pred, output_dict=True)
        }
        
        # Determine best model
        best_model = 'logistic_regression' if lr_accuracy > rf_accuracy else 'random_forest'
        results['best_model'] = best_model
        results['model_comparison'] = {
            'logistic_regression_accuracy': float(lr_accuracy),
            'random_forest_accuracy': float(rf_accuracy),
            'recommendation': f"Use {best_model.replace('_', ' ')} model (Accuracy = {max(lr_accuracy, rf_accuracy):.3f})"
        }
        
        return results


class PrescriptiveAnalytics:
    """Implements prescriptive analytics - What should be done?"""
    
    @staticmethod
    def optimize_feature_values(df: pd.DataFrame, target_col: str, objective: str = 'maximize') -> Dict[str, Any]:
        """Optimize feature values to achieve desired target outcome"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_col in numeric_cols:
            numeric_cols.remove(target_col)
        
        if len(numeric_cols) == 0:
            return {'error': 'No numeric features available for optimization'}
        
        # Build a simple model to understand feature impact
        model_data = df[numeric_cols + [target_col]].dropna()
        if len(model_data) < 5:
            return {'error': 'Insufficient data for optimization'}
        
        X = model_data[numeric_cols]
        y = model_data[target_col]
        
        # Fit linear regression to understand relationships
        model = LinearRegression()
        model.fit(X, y)
        
        # Get feature bounds (min/max from data)
        feature_bounds = []
        for col in numeric_cols:
            min_val = float(X[col].min())
            max_val = float(X[col].max())
            feature_bounds.append((min_val, max_val))
        
        # Define optimization objective
        def objective_function(x):
            prediction = model.predict([x])[0]
            return -prediction if objective == 'maximize' else prediction
        
        # Optimize
        initial_guess = [X[col].mean() for col in numeric_cols]
        result = minimize(objective_function, initial_guess, bounds=feature_bounds, method='L-BFGS-B')
        
        optimized_values = dict(zip(numeric_cols, result.x))
        predicted_outcome = model.predict([result.x])[0]
        
        # Generate recommendations
        current_means = {col: float(X[col].mean()) for col in numeric_cols}
        recommendations = []
        
        for col in numeric_cols:
            current_val = current_means[col]
            optimal_val = optimized_values[col]
            change = optimal_val - current_val
            percent_change = (change / current_val * 100) if current_val != 0 else 0
            
            if abs(percent_change) > 5:  # Only recommend significant changes
                direction = "increase" if change > 0 else "decrease"
                recommendations.append({
                    'feature': col,
                    'current_average': float(current_val),
                    'recommended_value': float(optimal_val),
                    'change': float(change),
                    'percent_change': float(percent_change),
                    'action': f"{direction.capitalize()} {col} by {abs(percent_change):.1f}%"
                })
        
        return {
            'optimization_objective': f"{objective.capitalize()} {target_col}",
            'predicted_outcome': float(predicted_outcome),
            'current_average_outcome': float(y.mean()),
            'improvement': float(predicted_outcome - y.mean()),
            'optimized_values': optimized_values,
            'recommendations': recommendations,
            'feature_importance': dict(zip(numeric_cols, model.coef_.tolist()))
        }
    
    @staticmethod
    def generate_actionable_insights(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights based on analysis results"""
        insights = []
        
        # Data quality insights
        if 'dataset_info' in analysis_results:
            info = analysis_results['dataset_info']
            missing_pct = (info['missing_values_total'] / (info['total_rows'] * info['total_columns'])) * 100
            
            if missing_pct > 10:
                insights.append(f"⚠️ High missing data ({missing_pct:.1f}%) - Consider data imputation or collection improvements")
            
            if info['duplicate_rows'] > 0:
                insights.append(f"🔍 Remove {info['duplicate_rows']} duplicate rows to improve data quality")
        
        # Correlation insights
        if 'strong_correlations' in analysis_results:
            strong_corrs = analysis_results['strong_correlations']
            if len(strong_corrs) > 0:
                top_corr = strong_corrs[0]
                insights.append(f"🔗 Strong relationship found: {top_corr['feature1']} and {top_corr['feature2']} (r={top_corr['correlation']:.3f})")
        
        # Model performance insights
        if 'model_comparison' in analysis_results:
            recommendation = analysis_results['model_comparison'].get('recommendation', '')
            if recommendation:
                insights.append(f"🎯 Model recommendation: {recommendation}")
        
        # Optimization insights
        if 'recommendations' in analysis_results:
            recs = analysis_results['recommendations'][:3]  # Top 3 recommendations
            for rec in recs:
                insights.append(f"📈 {rec['action']} to improve outcomes")
        
        return insights


class ComprehensiveAnalytics:
    """Main class that orchestrates all analytics types"""
    
    def __init__(self):
        self.descriptive = DescriptiveAnalytics()
        self.diagnostic = DiagnosticAnalytics()
        self.predictive = PredictiveAnalytics()
        self.prescriptive = PrescriptiveAnalytics()
    
    def run_full_analysis(self, df: pd.DataFrame, target_col: str = None) -> Dict[str, Any]:
        """Run comprehensive analysis across all four analytics types"""
        results = {
            'descriptive': self.descriptive.statistical_summary(df),
            'diagnostic': {},
            'predictive': {},
            'prescriptive': {}
        }
        
        # Diagnostic analytics
        results['diagnostic']['correlation_analysis'] = self.diagnostic.correlation_analysis(df)
        
        # If target column specified, run additional analysis
        if target_col and target_col in df.columns:
            target_is_numeric = pd.api.types.is_numeric_dtype(df[target_col])
            
            # Predictive analytics
            if target_is_numeric:
                results['predictive']['regression'] = self.predictive.build_regression_model(df, target_col)
                results['prescriptive']['optimization'] = self.prescriptive.optimize_feature_values(df, target_col)
            else:
                results['predictive']['classification'] = self.predictive.build_classification_model(df, target_col)
        
        # Generate actionable insights
        results['actionable_insights'] = self.prescriptive.generate_actionable_insights(df, results)
        
        return results
    
    def analyze_by_type(self, df: pd.DataFrame, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Run specific type of analysis"""
        if analysis_type == 'descriptive':
            return self.descriptive.statistical_summary(df)
        
        elif analysis_type == 'diagnostic':
            target_col = kwargs.get('target_col')
            feature_col = kwargs.get('feature_col')
            
            result = {'correlation_analysis': self.diagnostic.correlation_analysis(df)}
            
            if target_col and feature_col:
                result['hypothesis_testing'] = self.diagnostic.hypothesis_testing(df, target_col, feature_col)
            
            return result
        
        elif analysis_type == 'predictive':
            target_col = kwargs.get('target_col')
            if not target_col:
                return {'error': 'Target column required for predictive analysis'}
            
            target_is_numeric = pd.api.types.is_numeric_dtype(df[target_col])
            
            if target_is_numeric:
                return {'regression': self.predictive.build_regression_model(df, target_col)}
            else:
                return {'classification': self.predictive.build_classification_model(df, target_col)}
        
        elif analysis_type == 'prescriptive':
            target_col = kwargs.get('target_col')
            objective = kwargs.get('objective', 'maximize')
            
            if not target_col:
                return {'error': 'Target column required for prescriptive analysis'}
            
            result = self.prescriptive.optimize_feature_values(df, target_col, objective)
            result['actionable_insights'] = self.prescriptive.generate_actionable_insights(df, {'optimization': result})
            
            return result
        
        else:
            return {'error': f'Unknown analysis type: {analysis_type}'}