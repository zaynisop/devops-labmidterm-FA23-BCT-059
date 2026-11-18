"""Reference classification workload. CI/CD implementation is the student's task."""
import hashlib
import json
import os
from pathlib import Path
import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def fit_reference(data: pd.DataFrame, config: dict):
    fields = config['features']
    needed = fields + ['label']
    if len(data) < 100 or data['label'].nunique() != 2:
        raise ValueError('Training dataset must contain >=100 rows and both classes')
    if not set(needed).issubset(data.columns):
        raise ValueError('Dataset is missing one or more required columns')
    X = data[fields].apply(pd.to_numeric, errors='coerce')
    y = data['label'].astype(int)
    if X.isna().all(axis=0).any():
        raise ValueError('A feature column contains no numeric training data')
    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=.25, random_state=int(config['seed']), stratify=y
    )
    def model():
        return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                             LogisticRegression(max_iter=700, random_state=int(config['seed'])))
    evaluation_model = model()
    evaluation_model.fit(x_train, y_train)
    accuracy = float(accuracy_score(y_test, evaluation_model.predict(x_test)))
    production_model = model()
    production_model.fit(X, y)
    return production_model, accuracy


def main():
    config = json.loads(Path('config.json').read_text())
    dataset = Path('dataset/train.csv')
    raw = dataset.read_bytes()
    df = pd.read_csv(dataset)
    model, accuracy = fit_reference(df, config)
    digest = hashlib.sha256(raw).hexdigest()
    build_sha = os.environ.get('GIT_COMMIT', os.environ.get('BUILD_COMMIT', 'local'))
    metrics = {
        'student_id': config['student_id'], 'accuracy': round(accuracy, 6),
        'training_rows': int(len(df)), 'model_version': digest[:12],
        'dataset_sha256': digest, 'git_sha': build_sha,
    }
    Path('artifacts').mkdir(exist_ok=True)
    joblib.dump({'model': model, 'features': config['features']}, 'artifacts/model.joblib')
    Path('artifacts/metrics.json').write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics))


if __name__ == '__main__':
    main()
