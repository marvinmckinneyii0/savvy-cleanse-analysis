"""
Natural Language Processing module for SavvyCleanse
Handles natural language queries and maps them to appropriate analytics
"""

import pandas as pd
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import openai
import anthropic
import google.generativeai as genai
from comprehensive_analytics import ComprehensiveAnalytics


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class NLPProcessor:
    """Natural Language Processing for analytics queries"""
    
    def __init__(self, llm_provider: str = "openai", api_key: str = None):
        self.llm_provider = LLMProvider(llm_provider.lower())
        self.api_key = api_key
        self.analytics = ComprehensiveAnalytics()
        
        # Initialize the selected LLM client
        if self.llm_provider == LLMProvider.OPENAI and api_key:
            openai.api_key = api_key
        elif self.llm_provider == LLMProvider.ANTHROPIC and api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        elif self.llm_provider == LLMProvider.GEMINI and api_key:
            genai.configure(api_key=api_key)
    
    def process_query(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Process natural language query and return analysis results"""
        try:
            # Parse the query to understand intent and extract parameters
            intent_analysis = self._analyze_query_intent(query, df)
            
            if 'error' in intent_analysis:
                return intent_analysis
            
            # Execute the appropriate analysis based on intent
            analysis_result = self._execute_analysis(intent_analysis, df)
            
            # Generate natural language response
            nl_response = self._generate_response(query, analysis_result, intent_analysis)
            
            return {
                'query': query,
                'intent': intent_analysis,
                'analysis_results': analysis_result,
                'natural_language_response': nl_response,
                'llm_provider': self.llm_provider.value
            }
            
        except Exception as e:
            return {'error': f'Error processing query: {str(e)}'}
    
    def _analyze_query_intent(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze query intent using LLM"""
        # Prepare dataset context
        dataset_context = self._prepare_dataset_context(df)
        
        # Create prompt for intent analysis
        system_prompt = """You are an expert data analyst AI. Analyze the user's natural language query and determine:
1. The type of analysis needed (descriptive, diagnostic, predictive, prescriptive)
2. The target column (if any)
3. Feature columns to focus on (if any)
4. Specific parameters or objectives

Available analysis types:
- descriptive: Statistical summaries, distributions, basic data exploration
- diagnostic: Correlation analysis, hypothesis testing, why something happened
- predictive: Regression or classification models, forecasting
- prescriptive: Optimization, recommendations, what actions to take

Respond ONLY with a JSON object in this exact format:
{
    "analysis_type": "descriptive|diagnostic|predictive|prescriptive",
    "target_column": "column_name or null",
    "feature_columns": ["col1", "col2"] or null,
    "objective": "maximize|minimize|analyze|null",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}"""

        user_prompt = f"""Dataset Context:
{dataset_context}

User Query: "{query}"

Analyze this query and provide the JSON response."""

        try:
            llm_response = self._call_llm(system_prompt, user_prompt)
            intent = self._parse_json_response(llm_response)
            
            # Validate the response
            if not self._validate_intent_response(intent, df):
                return {'error': 'Invalid intent analysis from LLM'}
            
            return intent
            
        except Exception as e:
            # Fallback to rule-based intent detection
            return self._fallback_intent_analysis(query, df)
    
    def _prepare_dataset_context(self, df: pd.DataFrame) -> str:
        """Prepare dataset context for LLM"""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        context = f"""Dataset Information:
- Total rows: {len(df)}
- Total columns: {len(df.columns)}
- Numeric columns: {numeric_cols}
- Categorical columns: {categorical_cols}
- Missing values: {df.isnull().sum().sum()}

Sample data (first 3 rows):
{df.head(3).to_string()}"""
        
        return context
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the selected LLM provider"""
        if self.llm_provider == LLMProvider.OPENAI:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            return response.choices[0].message.content
            
        elif self.llm_provider == LLMProvider.ANTHROPIC:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.1,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
            
        elif self.llm_provider == LLMProvider.GEMINI:
            model = genai.GenerativeModel('gemini-pro')
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = model.generate_content(full_prompt)
            return response.text
            
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            return json.loads(response)
    
    def _validate_intent_response(self, intent: Dict[str, Any], df: pd.DataFrame) -> bool:
        """Validate intent response from LLM"""
        required_fields = ['analysis_type', 'target_column', 'confidence']
        
        # Check required fields
        if not all(field in intent for field in required_fields):
            return False
        
        # Check analysis type
        valid_types = ['descriptive', 'diagnostic', 'predictive', 'prescriptive']
        if intent['analysis_type'] not in valid_types:
            return False
        
        # Check target column exists (if specified)
        if intent['target_column'] and intent['target_column'] not in df.columns:
            return False
        
        # Check feature columns exist (if specified)
        if intent.get('feature_columns'):
            if not all(col in df.columns for col in intent['feature_columns']):
                return False
        
        return True
    
    def _fallback_intent_analysis(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Fallback rule-based intent analysis"""
        query_lower = query.lower()
        
        # Define keywords for each analysis type
        descriptive_keywords = ['summary', 'describe', 'statistics', 'mean', 'average', 'count', 'distribution', 'overview']
        diagnostic_keywords = ['correlation', 'relationship', 'why', 'cause', 'impact', 'influence', 'affect', 'related']
        predictive_keywords = ['predict', 'forecast', 'future', 'will', 'model', 'estimate', 'trend']
        prescriptive_keywords = ['optimize', 'recommend', 'should', 'best', 'improve', 'action', 'strategy']
        
        # Score each analysis type
        scores = {
            'descriptive': sum(1 for keyword in descriptive_keywords if keyword in query_lower),
            'diagnostic': sum(1 for keyword in diagnostic_keywords if keyword in query_lower),
            'predictive': sum(1 for keyword in predictive_keywords if keyword in query_lower),
            'prescriptive': sum(1 for keyword in prescriptive_keywords if keyword in query_lower)
        }
        
        # Determine analysis type
        analysis_type = max(scores, key=scores.get)
        confidence = scores[analysis_type] / len(query_lower.split()) if scores[analysis_type] > 0 else 0.3
        
        # Try to extract column names from query
        target_column = None
        feature_columns = None
        
        for col in df.columns:
            if col.lower() in query_lower:
                if target_column is None:
                    target_column = col
                else:
                    if feature_columns is None:
                        feature_columns = [col]
                    else:
                        feature_columns.append(col)
        
        return {
            'analysis_type': analysis_type,
            'target_column': target_column,
            'feature_columns': feature_columns,
            'objective': 'maximize' if 'maximize' in query_lower or 'increase' in query_lower else 'minimize' if 'minimize' in query_lower else None,
            'confidence': confidence,
            'reasoning': f'Rule-based analysis detected {analysis_type} intent based on keywords'
        }
    
    def _execute_analysis(self, intent: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Execute analysis based on intent"""
        analysis_type = intent['analysis_type']
        target_col = intent.get('target_column')
        feature_cols = intent.get('feature_columns')
        objective = intent.get('objective', 'maximize')
        
        kwargs = {}
        if target_col:
            kwargs['target_col'] = target_col
        if feature_cols:
            kwargs['feature_cols'] = feature_cols
        if objective:
            kwargs['objective'] = objective
        
        return self.analytics.analyze_by_type(df, analysis_type, **kwargs)
    
    def _generate_response(self, original_query: str, analysis_result: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Generate natural language response"""
        try:
            # Create prompt for response generation
            system_prompt = """You are a data analyst AI. Generate a clear, concise, and actionable response to the user's question based on the analysis results. 

Guidelines:
- Be conversational and easy to understand
- Highlight key findings and insights
- Provide actionable recommendations when relevant
- Use specific numbers and statistics
- Keep response under 200 words
- Don't mention technical details about the analysis methods"""

            user_prompt = f"""Original Question: "{original_query}"

Analysis Intent: {intent['analysis_type']} analysis
Target Column: {intent.get('target_column', 'N/A')}

Analysis Results:
{json.dumps(analysis_result, indent=2)}

Generate a natural language response that directly answers the user's question."""

            return self._call_llm(system_prompt, user_prompt)
            
        except Exception as e:
            # Fallback to structured response
            return self._generate_fallback_response(analysis_result, intent)
    
    def _generate_fallback_response(self, analysis_result: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Generate fallback response without LLM"""
        analysis_type = intent['analysis_type']
        
        if analysis_type == 'descriptive':
            if 'dataset_info' in analysis_result:
                info = analysis_result['dataset_info']
                return f"Your dataset has {info['total_rows']} rows and {info['total_columns']} columns. It contains {info['numeric_columns']} numeric and {info['categorical_columns']} categorical features with {info['missing_values_total']} missing values."
        
        elif analysis_type == 'diagnostic':
            if 'correlation_analysis' in analysis_result and 'strong_correlations' in analysis_result['correlation_analysis']:
                strong_corrs = analysis_result['correlation_analysis']['strong_correlations']
                if strong_corrs:
                    top_corr = strong_corrs[0]
                    return f"Found strong correlation between {top_corr['feature1']} and {top_corr['feature2']} (correlation: {top_corr['correlation']:.3f}). This suggests these variables are closely related."
        
        elif analysis_type == 'predictive':
            if 'regression' in analysis_result and 'best_model' in analysis_result['regression']:
                best_model = analysis_result['regression']['best_model']
                return f"Built predictive model using {best_model.replace('_', ' ')}. {analysis_result['regression']['model_comparison']['recommendation']}"
        
        elif analysis_type == 'prescriptive':
            if 'actionable_insights' in analysis_result:
                insights = analysis_result['actionable_insights'][:3]
                return "Based on the analysis, here are the top recommendations: " + " ".join(insights)
        
        return "Analysis completed. Please check the detailed results for specific insights."


# Example usage and testing functions
def test_nlp_processor():
    """Test function for NLP processor"""
    # Create sample data
    data = {
        'sales': [100, 150, 200, 180, 220, 250, 300],
        'marketing_spend': [10, 15, 25, 20, 30, 35, 40],
        'temperature': [20, 25, 30, 28, 32, 35, 38],
        'season': ['winter', 'spring', 'summer', 'summer', 'summer', 'fall', 'fall']
    }
    df = pd.DataFrame(data)
    
    # Test queries
    test_queries = [
        "What's the average sales?",
        "How does marketing spend relate to sales?",
        "Can you predict future sales?",
        "What should I do to maximize sales?"
    ]
    
    processor = NLPProcessor(llm_provider="openai")  # Would need API key
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = processor._fallback_intent_analysis(query, df)  # Using fallback for testing
        print(f"Intent: {result}")


if __name__ == "__main__":
    test_nlp_processor()