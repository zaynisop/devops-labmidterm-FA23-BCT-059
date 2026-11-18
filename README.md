# CSC418 Lab Midterm — Automated ML Retraining Pipeline (FA23-BCT-059)

A push to `dataset/train.csv` on GitHub triggers the Jenkins job **MIDTERM-FA23-BCT-059** via webhook. Jenkins:

1. fetches the latest commit/data
2. retrains the model (`train.py`) and runs the tests (`tests/`)
3. builds the Docker image (`Dockerfile`)
4. redeploys the FastAPI container on AWS EC2 (port 8000)
5. emails the result to the instructor

## Endpoints
- `GET /metrics` → `student_id`, `accuracy`, `training_rows`, `model_version`, `git_sha`
- `POST /predict` → body `{"records": [{"cpu_usage": 0.1, "memory_pressure": -0.3, "disk_io": 0.5, "request_rate": 1.2}]}`
- `GET /health`

## Local run
```bash
pip install -r requirements-dev.txt
python generate_dataset.py      # dataset/train.csv from config.json
python train.py && pytest -q
uvicorn app:app --port 8000
```
