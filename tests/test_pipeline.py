"""Quality gate run by Jenkins after train.py and before the Docker image is built."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config.json').read_text())
DATASET = ROOT / 'dataset' / 'train.csv'
METRICS = ROOT / 'artifacts' / 'metrics.json'
MODEL = ROOT / 'artifacts' / 'model.joblib'


@pytest.fixture(scope='module')
def client(monkeypatch_module):
    monkeypatch_module.chdir(ROOT)
    import app
    return TestClient(app.app)


@pytest.fixture(scope='module')
def monkeypatch_module():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


def test_dataset_schema():
    df = pd.read_csv(DATASET)
    assert list(df.columns) == CONFIG['features'] + ['label']
    assert len(df) >= 100
    assert set(df['label'].unique()) == {0, 1}


def test_artifacts_exist():
    assert MODEL.exists(), 'run train.py first'
    assert METRICS.exists(), 'run train.py first'


def test_metrics_match_current_dataset():
    metrics = json.loads(METRICS.read_text())
    raw = DATASET.read_bytes()
    assert metrics['student_id'] == CONFIG['student_id']
    assert metrics['training_rows'] == len(pd.read_csv(DATASET))
    assert metrics['dataset_sha256'] == hashlib.sha256(raw).hexdigest()
    assert metrics['model_version'] == metrics['dataset_sha256'][:12]


def test_model_accuracy_threshold():
    metrics = json.loads(METRICS.read_text())
    assert 0.0 <= metrics['accuracy'] <= 1.0
    assert metrics['accuracy'] >= 0.70, f"accuracy too low: {metrics['accuracy']}"


def test_health_and_metrics_endpoint(client):
    assert client.get('/health').json() == {'status': 'ok'}
    body = client.get('/metrics').json()
    for key in ('student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha'):
        assert key in body
    assert body['student_id'] == CONFIG['student_id']


def test_predict_endpoint(client):
    df = pd.read_csv(DATASET).dropna().head(5)
    records = df[CONFIG['features']].to_dict(orient='records')
    res = client.post('/predict', json={'records': records})
    assert res.status_code == 200
    body = res.json()
    assert len(body['predictions']) == 5
    assert all(p in (0, 1) for p in body['predictions'])
    assert all(0.0 <= p <= 1.0 for p in body['probabilities'])


def test_predict_rejects_empty(client):
    assert client.post('/predict', json={'records': []}).status_code == 422
