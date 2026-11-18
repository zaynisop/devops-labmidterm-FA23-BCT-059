"""Produce the roll-specific initial training CSV. No external data downloads."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def make_rows(config: dict, n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(int(seed))
    features = config['features']
    weights = np.asarray(config['weights'], dtype=float)
    # Every student receives a distinct, reproducible statistical problem.
    X = rng.normal(size=(n, len(features)))
    X[:, 0] += float(config.get('offset', 0.0))
    if config['variant'] in ['outliers', 'mixed']:
        idx = rng.choice(n, max(1, n // 20), replace=False)
        X[idx, 1] *= 3.5
    logits = X @ weights + float(config.get('bias', 0)) + rng.normal(0, .75, n)
    y = (logits > 0).astype(int)
    data = pd.DataFrame(X.round(5), columns=features)
    if config['variant'] in ['missing', 'mixed']:
        mask = rng.random(size=data.shape) < .035
        data = data.mask(mask)
    if config['variant'] == 'rounded':
        data = data.round(2)
    data['label'] = y
    return data


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--config', default='config.json')
    a.add_argument('--output', default='dataset/train.csv')
    a.add_argument('--rows', default=300, type=int)
    args = a.parse_args()
    config = json.loads(Path(args.config).read_text())
    if args.rows < 80:
        raise SystemExit('At least 80 training records are required')
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    make_rows(config, args.rows, config['seed']).to_csv(output, index=False)
    print(f'Generated {args.rows} rows for {config["student_id"]}: {output}')


if __name__ == '__main__':
    main()
