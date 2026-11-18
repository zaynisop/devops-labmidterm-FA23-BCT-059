"""FastAPI server for the deployed model. Train first to create artifacts."""
import json
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title='CSC418 Auto-Retraining Service')

class PredictionRequest(BaseModel):
    records: list[dict]


def artifacts():
    try:
        metrics = json.loads(Path('artifacts/metrics.json').read_text())
        bundle = joblib.load('artifacts/model.joblib')
        return metrics, bundle
    except (FileNotFoundError, ValueError) as err:
        raise HTTPException(status_code=503, detail='Model not ready') from err


@app.get('/health')
def health():
    return {'status': 'ok' if Path('artifacts/model.joblib').exists() else 'not-ready'}


@app.get('/metrics')
def metrics():
    return artifacts()[0]


@app.post('/predict')
def predict(request: PredictionRequest):
    if not 1 <= len(request.records) <= 100:
        raise HTTPException(status_code=422, detail='Provide 1-100 records')
    _, bundle = artifacts()
    features = bundle['features']
    df = pd.DataFrame(request.records).reindex(columns=features)
    for field in features:
        df[field] = pd.to_numeric(df[field], errors='coerce')
    probabilities = bundle['model'].predict_proba(df)[:, 1]
    predictions = (probabilities >= .5).astype(int)
    return {'predictions': predictions.tolist(), 'probabilities': probabilities.round(6).tolist()}
