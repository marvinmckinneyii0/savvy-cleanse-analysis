from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - helper for local dev
    raise SystemExit(
        "pandas is required. Install dependencies with 'pip install -r backend/requirements.txt'"
    )
from io import BytesIO

from cleaner import clean_dataframe
from analytics import analyze_goal

app = FastAPI(title="SavvyClean Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for uploaded and cleaned data
DATA_STORAGE = {}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(BytesIO(content))
    elif file.filename.endswith('.xlsx'):
        df = pd.read_excel(BytesIO(content))
    elif file.filename.endswith('.txt'):
        df = pd.read_csv(BytesIO(content), delimiter='\t')
    else:
        return JSONResponse({"error": "Unsupported file type"}, status_code=400)
    DATA_STORAGE['raw'] = df
    preview = df.head().to_dict(orient='records')
    return {"filename": file.filename, "preview": preview, "columns": list(df.columns)}

@app.post("/clean")
async def clean():
    df = DATA_STORAGE.get('raw')
    if df is None:
        return JSONResponse({"error": "No dataset uploaded"}, status_code=400)
    cleaned = clean_dataframe(df)
    DATA_STORAGE['clean'] = cleaned
    return {"rows": len(cleaned), "columns": list(cleaned.columns)}

@app.post("/goal")
async def set_goal(goal: dict):
    DATA_STORAGE['goal'] = goal.get('goal')
    return {"message": "Goal received"}

@app.post("/analyze")
async def analyze():
    df = DATA_STORAGE.get('clean')
    goal = DATA_STORAGE.get('goal')
    if df is None or goal is None:
        return JSONResponse({"error": "Missing cleaned data or goal"}, status_code=400)
    result = analyze_goal(df, goal)
    DATA_STORAGE['analysis'] = result
    return result

@app.get("/report/summary")
async def report_summary():
    return DATA_STORAGE.get('analysis', {"summary": "No analysis available"})

@app.post("/export")
async def export():
    df = DATA_STORAGE.get('clean')
    if df is None:
        return JSONResponse({"error": "No cleaned data"}, status_code=400)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="cleaned.csv"'})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
