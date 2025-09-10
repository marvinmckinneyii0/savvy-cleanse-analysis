"""
Enhanced FastAPI backend for SavvyCleanse with comprehensive analytics,
authentication, and multi-tenancy support
"""

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pandas as pd
from io import BytesIO
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
from supabase import create_client, Client
from pydantic import BaseModel
import logging

# Import our custom modules
from cleaner import clean_dataframe
from comprehensive_analytics import ComprehensiveAnalytics
from nlp_processor import NLPProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="SavvyCleanse Enhanced Backend",
    description="Comprehensive data analytics platform with NLP querying",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kahiypfloievcktkyzps.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImthaGl5cGZsb2lldmNrdGt5enBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0NTAzMDUsImV4cCI6MjA2ODAyNjMwNX0.DdMD_rsrbX1FkD_Qxv9jPzBeMzQJZtssfbYxKdJKsjQ")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Security
security = HTTPBearer()

# Initialize analytics and NLP
analytics = ComprehensiveAnalytics()
nlp_processors = {}  # Will store NLP processors per user/API key

# In-memory storage (in production, use Redis or database)
DATA_STORAGE = {}

# Pydantic models
class AnalysisRequest(BaseModel):
    analysis_type: str
    target_column: Optional[str] = None
    feature_columns: Optional[List[str]] = None
    objective: Optional[str] = "maximize"

class NLPQueryRequest(BaseModel):
    query: str
    llm_provider: str = "openai"
    dataset_id: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    id_token: str

class UserProfile(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = "user"

# Authentication middleware
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate user from JWT token"""
    try:
        # Verify JWT token with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        return user.user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_admin_user(current_user = Depends(get_current_user)):
    """Verify user has admin role"""
    try:
        # Check if user is admin
        result = supabase.table('user_profiles').select('role').eq('id', current_user.id).execute()
        if not result.data or result.data[0]['role'] != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    except Exception as e:
        logger.error(f"Admin check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access verification failed"
        )

async def log_activity(user_id: str, action: str, status: str = "success", 
                      metadata: Dict = None, error_message: str = None):
    """Log user activity to database"""
    try:
        log_data = {
            'user_id': user_id,
            'action': action,
            'status': status,
            'metadata': metadata or {},
            'error_message': error_message,
            'created_at': datetime.utcnow().isoformat()
        }
        supabase.table('activity_logs').insert(log_data).execute()
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")

# Authentication endpoints
@app.post("/auth/google/login")
async def google_login(auth_request: GoogleAuthRequest):
    """Handle Google OAuth login"""
    try:
        # In a real implementation, verify the Google ID token
        # For now, we'll simulate the process
        
        # This would typically involve:
        # 1. Verify Google ID token
        # 2. Extract user info
        # 3. Create or update user in Supabase
        # 4. Return JWT token
        
        return JSONResponse({
            "message": "Google OAuth integration needs to be implemented with actual Google credentials",
            "status": "pending_implementation"
        })
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/profile")
async def get_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    try:
        result = supabase.table('user_profiles').select('*').eq('id', current_user.id).execute()
        if result.data:
            return result.data[0]
        else:
            # Create profile if doesn't exist
            profile_data = {
                'id': current_user.id,
                'email': current_user.email,
                'full_name': current_user.email,
                'role': 'user'
            }
            supabase.table('user_profiles').insert(profile_data).execute()
            return profile_data
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/auth/profile")
async def update_profile(profile: UserProfile, current_user = Depends(get_current_user)):
    """Update user profile"""
    try:
        update_data = profile.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = supabase.table('user_profiles').update(update_data).eq('id', current_user.id).execute()
        
        await log_activity(current_user.id, "profile_update")
        
        return {"message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        await log_activity(current_user.id, "profile_update", "error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# Data upload and management endpoints
@app.post("/upload")
async def upload(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """Upload and preview dataset"""
    try:
        content = await file.read()
        
        # Parse file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(content))
        elif file.filename.endswith('.txt'):
            df = pd.read_csv(BytesIO(content), delimiter='\t')
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Generate dataset ID
        dataset_id = str(uuid.uuid4())
        
        # Store in memory (in production, use proper storage)
        DATA_STORAGE[f"{current_user.id}_{dataset_id}"] = df
        
        # Save dataset metadata to database
        dataset_data = {
            'id': dataset_id,
            'user_id': current_user.id,
            'filename': dataset_id + '_' + file.filename,
            'original_filename': file.filename,
            'file_size': len(content),
            'status': 'uploaded',
            'metadata': {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns)
            }
        }
        supabase.table('datasets').insert(dataset_data).execute()
        
        await log_activity(current_user.id, "file_upload", metadata={'filename': file.filename, 'dataset_id': dataset_id})
        
        # Return preview
        preview = df.head().to_dict(orient='records')
        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "preview": preview,
            "columns": list(df.columns),
            "rows": len(df),
            "file_size": len(content)
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        await log_activity(current_user.id, "file_upload", "error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/clean/{dataset_id}")
async def clean_dataset(dataset_id: str, current_user = Depends(get_current_user)):
    """Clean dataset"""
    try:
        # Get dataset from storage
        storage_key = f"{current_user.id}_{dataset_id}"
        df = DATA_STORAGE.get(storage_key)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Clean the dataset
        cleaned_df = clean_dataframe(df)
        
        # Update storage
        DATA_STORAGE[storage_key + "_clean"] = cleaned_df
        
        # Update database status
        supabase.table('datasets').update({
            'status': 'cleaned',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', dataset_id).eq('user_id', current_user.id).execute()
        
        await log_activity(current_user.id, "data_cleaning", metadata={'dataset_id': dataset_id})
        
        return {
            "dataset_id": dataset_id,
            "rows": len(cleaned_df),
            "columns": list(cleaned_df.columns),
            "status": "cleaned"
        }
        
    except Exception as e:
        logger.error(f"Cleaning error: {str(e)}")
        await log_activity(current_user.id, "data_cleaning", "error", metadata={'dataset_id': dataset_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# Analytics endpoints
@app.post("/analyze/descriptive/{dataset_id}")
async def descriptive_analysis(dataset_id: str, current_user = Depends(get_current_user)):
    """Perform descriptive analytics"""
    try:
        # Get cleaned dataset
        storage_key = f"{current_user.id}_{dataset_id}_clean"
        df = DATA_STORAGE.get(storage_key)
        
        if df is None:
            # Try original dataset
            storage_key = f"{current_user.id}_{dataset_id}"
            df = DATA_STORAGE.get(storage_key)
            
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Perform analysis
        results = analytics.analyze_by_type(df, 'descriptive')
        
        # Save results to database
        result_data = {
            'user_id': current_user.id,
            'dataset_id': dataset_id,
            'analysis_type': 'descriptive',
            'results': results
        }
        supabase.table('analytics_results').insert(result_data).execute()
        
        await log_activity(current_user.id, "descriptive_analysis", metadata={'dataset_id': dataset_id})
        
        return results
        
    except Exception as e:
        logger.error(f"Descriptive analysis error: {str(e)}")
        await log_activity(current_user.id, "descriptive_analysis", "error", metadata={'dataset_id': dataset_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze/diagnostic/{dataset_id}")
async def diagnostic_analysis(dataset_id: str, request: AnalysisRequest, current_user = Depends(get_current_user)):
    """Perform diagnostic analytics"""
    try:
        # Get dataset
        storage_key = f"{current_user.id}_{dataset_id}_clean"
        df = DATA_STORAGE.get(storage_key) or DATA_STORAGE.get(f"{current_user.id}_{dataset_id}")
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Perform analysis
        kwargs = {}
        if request.target_column:
            kwargs['target_col'] = request.target_column
        if request.feature_columns:
            kwargs['feature_col'] = request.feature_columns[0]  # For hypothesis testing
        
        results = analytics.analyze_by_type(df, 'diagnostic', **kwargs)
        
        # Save results
        result_data = {
            'user_id': current_user.id,
            'dataset_id': dataset_id,
            'analysis_type': 'diagnostic',
            'results': results
        }
        supabase.table('analytics_results').insert(result_data).execute()
        
        await log_activity(current_user.id, "diagnostic_analysis", metadata={'dataset_id': dataset_id})
        
        return results
        
    except Exception as e:
        logger.error(f"Diagnostic analysis error: {str(e)}")
        await log_activity(current_user.id, "diagnostic_analysis", "error", metadata={'dataset_id': dataset_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze/predictive/{dataset_id}")
async def predictive_analysis(dataset_id: str, request: AnalysisRequest, current_user = Depends(get_current_user)):
    """Perform predictive analytics"""
    try:
        # Get dataset
        storage_key = f"{current_user.id}_{dataset_id}_clean"
        df = DATA_STORAGE.get(storage_key) or DATA_STORAGE.get(f"{current_user.id}_{dataset_id}")
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        if not request.target_column:
            raise HTTPException(status_code=400, detail="Target column required for predictive analysis")
        
        # Perform analysis
        results = analytics.analyze_by_type(df, 'predictive', target_col=request.target_column)
        
        # Save model metadata
        if 'regression' in results or 'classification' in results:
            model_type = 'regression' if 'regression' in results else 'classification'
            accuracy = None
            
            if model_type == 'regression' and 'best_model' in results['regression']:
                accuracy = results['regression']['model_comparison'].get('linear_regression_r2', 0)
            elif model_type == 'classification' and 'best_model' in results['classification']:
                accuracy = results['classification']['model_comparison'].get('logistic_regression_accuracy', 0)
            
            model_data = {
                'user_id': current_user.id,
                'dataset_id': dataset_id,
                'model_type': model_type,
                'algorithm': results.get('regression', results.get('classification', {})).get('best_model', 'unknown'),
                'accuracy': accuracy,
                'parameters': {'target_column': request.target_column}
            }
            supabase.table('ml_models').insert(model_data).execute()
        
        # Save results
        result_data = {
            'user_id': current_user.id,
            'dataset_id': dataset_id,
            'analysis_type': 'predictive',
            'results': results
        }
        supabase.table('analytics_results').insert(result_data).execute()
        
        await log_activity(current_user.id, "predictive_analysis", metadata={'dataset_id': dataset_id})
        
        return results
        
    except Exception as e:
        logger.error(f"Predictive analysis error: {str(e)}")
        await log_activity(current_user.id, "predictive_analysis", "error", metadata={'dataset_id': dataset_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze/prescriptive/{dataset_id}")
async def prescriptive_analysis(dataset_id: str, request: AnalysisRequest, current_user = Depends(get_current_user)):
    """Perform prescriptive analytics"""
    try:
        # Get dataset
        storage_key = f"{current_user.id}_{dataset_id}_clean"
        df = DATA_STORAGE.get(storage_key) or DATA_STORAGE.get(f"{current_user.id}_{dataset_id}")
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        if not request.target_column:
            raise HTTPException(status_code=400, detail="Target column required for prescriptive analysis")
        
        # Perform analysis
        results = analytics.analyze_by_type(df, 'prescriptive', 
                                          target_col=request.target_column, 
                                          objective=request.objective)
        
        # Save results
        result_data = {
            'user_id': current_user.id,
            'dataset_id': dataset_id,
            'analysis_type': 'prescriptive',
            'results': results
        }
        supabase.table('analytics_results').insert(result_data).execute()
        
        await log_activity(current_user.id, "prescriptive_analysis", metadata={'dataset_id': dataset_id})
        
        return results
        
    except Exception as e:
        logger.error(f"Prescriptive analysis error: {str(e)}")
        await log_activity(current_user.id, "prescriptive_analysis", "error", metadata={'dataset_id': dataset_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# Natural Language Processing endpoint
@app.post("/analyze/nlp/{dataset_id}")
async def nlp_query(dataset_id: str, request: NLPQueryRequest, current_user = Depends(get_current_user)):
    """Process natural language query"""
    try:
        # Get dataset
        storage_key = f"{current_user.id}_{dataset_id}_clean"
        df = DATA_STORAGE.get(storage_key) or DATA_STORAGE.get(f"{current_user.id}_{dataset_id}")
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get or create NLP processor for this user
        processor_key = f"{current_user.id}_{request.llm_provider}"
        if processor_key not in nlp_processors:
            # In production, get API key from user settings
            api_key = os.getenv(f"{request.llm_provider.upper()}_API_KEY")
            nlp_processors[processor_key] = NLPProcessor(request.llm_provider, api_key)
        
        processor = nlp_processors[processor_key]
        
        # Process query
        results = processor.process_query(request.query, df)
        
        # Save query to database
        query_data = {
            'user_id': current_user.id,
            'dataset_id': dataset_id,
            'query_text': request.query,
            'interpreted_intent': results.get('intent', {}).get('analysis_type'),
            'analysis_type': results.get('intent', {}).get('analysis_type'),
            'results': results,
            'llm_model': request.llm_provider
        }
        supabase.table('nlp_queries').insert(query_data).execute()
        
        await log_activity(current_user.id, "nlp_query", metadata={'dataset_id': dataset_id, 'query': request.query})
        
        return results
        
    except Exception as e:
        logger.error(f"NLP query error: {str(e)}")
        await log_activity(current_user.id, "nlp_query", "error", metadata={'dataset_id': dataset_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# Dashboard endpoints
@app.get("/dashboard/user")
async def user_dashboard(current_user = Depends(get_current_user)):
    """Get user dashboard data"""
    try:
        # Get user datasets
        datasets = supabase.table('datasets').select('*').eq('user_id', current_user.id).order('created_at', desc=True).execute()
        
        # Get recent analytics results
        analytics_results = supabase.table('analytics_results').select('*').eq('user_id', current_user.id).order('created_at', desc=True).limit(10).execute()
        
        # Get recent NLP queries
        nlp_queries = supabase.table('nlp_queries').select('*').eq('user_id', current_user.id).order('created_at', desc=True).limit(5).execute()
        
        # Get user activity summary
        activity_logs = supabase.table('activity_logs').select('action').eq('user_id', current_user.id).execute()
        
        # Calculate statistics
        total_datasets = len(datasets.data) if datasets.data else 0
        total_analyses = len(analytics_results.data) if analytics_results.data else 0
        total_queries = len(nlp_queries.data) if nlp_queries.data else 0
        
        return {
            'user_stats': {
                'total_datasets': total_datasets,
                'total_analyses': total_analyses,
                'total_nlp_queries': total_queries
            },
            'recent_datasets': datasets.data[:5] if datasets.data else [],
            'recent_analyses': analytics_results.data[:5] if analytics_results.data else [],
            'recent_queries': nlp_queries.data if nlp_queries.data else [],
            'activity_summary': {}  # Could add more detailed activity analysis
        }
        
    except Exception as e:
        logger.error(f"User dashboard error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/dashboard/admin")
async def admin_dashboard(current_user = Depends(get_admin_user)):
    """Get admin dashboard data"""
    try:
        # Get all users
        users = supabase.table('user_profiles').select('*').execute()
        
        # Get all datasets
        datasets = supabase.table('datasets').select('*').execute()
        
        # Get system-wide analytics
        analytics_results = supabase.table('analytics_results').select('*').execute()
        
        # Get recent activity logs
        activity_logs = supabase.table('activity_logs').select('*').order('created_at', desc=True).limit(50).execute()
        
        # Calculate system statistics
        total_users = len(users.data) if users.data else 0
        total_datasets = len(datasets.data) if datasets.data else 0
        total_analyses = len(analytics_results.data) if analytics_results.data else 0
        
        # User activity summary
        user_activity = {}
        if activity_logs.data:
            for log in activity_logs.data:
                user_id = log['user_id']
                if user_id not in user_activity:
                    user_activity[user_id] = 0
                user_activity[user_id] += 1
        
        return {
            'system_stats': {
                'total_users': total_users,
                'total_datasets': total_datasets,
                'total_analyses': total_analyses
            },
            'users': users.data if users.data else [],
            'recent_activity': activity_logs.data if activity_logs.data else [],
            'user_activity_summary': user_activity,
            'dataset_status_summary': {}  # Could add dataset status breakdown
        }
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Legacy endpoints (maintain compatibility)
@app.post("/goal")
async def set_goal(goal: dict, current_user = Depends(get_current_user)):
    """Legacy goal endpoint - redirects to NLP"""
    return {"message": "Use /analyze/nlp/{dataset_id} endpoint for natural language queries"}

@app.post("/analyze")
async def analyze(current_user = Depends(get_current_user)):
    """Legacy analyze endpoint"""
    return {"message": "Use specific analysis endpoints: /analyze/descriptive, /analyze/diagnostic, etc."}

@app.get("/report/summary")
async def report_summary(current_user = Depends(get_current_user)):
    """Get latest analysis summary for user"""
    try:
        result = supabase.table('analytics_results').select('*').eq('user_id', current_user.id).order('created_at', desc=True).limit(1).execute()
        
        if result.data:
            return result.data[0]['results']
        else:
            return {"summary": "No analysis available"}
            
    except Exception as e:
        logger.error(f"Report summary error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/export/{dataset_id}")
async def export_dataset(dataset_id: str, current_user = Depends(get_current_user)):
    """Export cleaned dataset"""
    try:
        # Get cleaned dataset
        storage_key = f"{current_user.id}_{dataset_id}_clean"
        df = DATA_STORAGE.get(storage_key)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Cleaned dataset not found")
        
        # Convert to CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        await log_activity(current_user.id, "data_export", metadata={'dataset_id': dataset_id})
        
        return StreamingResponse(
            output, 
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="cleaned_{dataset_id}.csv"'}
        )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        await log_activity(current_user.id, "data_export", "error", metadata={'dataset_id': dataset_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# Admin endpoints
@app.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: dict, current_user = Depends(get_admin_user)):
    """Update user role (admin only)"""
    try:
        new_role = role_data.get('role')
        if new_role not in ['user', 'admin']:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # Update user role
        result = supabase.table('user_profiles').update({
            'role': new_role,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        await log_activity(current_user.id, "user_role_update", metadata={'target_user_id': user_id, 'new_role': new_role})
        
        return {"message": "User role updated successfully", "user_id": user_id, "new_role": new_role}
        
    except Exception as e:
        logger.error(f"User role update error: {str(e)}")
        await log_activity(current_user.id, "user_role_update", "error", metadata={'target_user_id': user_id}, error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "features": ["analytics", "nlp", "auth", "multi-tenant"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)