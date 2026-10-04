import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import jdk4py
import pytest

LAB = Path(__file__).resolve().parents[1]
REPO = LAB.parents[1]
DISTRIBUTION = REPO / 'sources/p2rank_2.5.1'
sys.path.insert(0, str(LAB / 'models/predict'))


def read_csv(path):
    with Path(path).open(newline='') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [x.strip() for x in reader.fieldnames]
        return [{k: v.strip() for k, v in row.items()} for row in reader]


def standalone(structure, out):
    """Run the original unpacked 2.5.1 distribution through its own launcher."""
    if not (DISTRIBUTION / 'prank').is_file():
        pytest.skip('Original P2Rank 2.5.1 distribution is not unpacked under sources/')
    env = {**os.environ, 'JAVA_HOME': str(jdk4py.JAVA_HOME)}
    subprocess.run(['bash', str(DISTRIBUTION / 'prank'), 'predict', '-f', str(structure), '-o', str(out),
                    '-threads', '1'], check=True, env=env, cwd=DISTRIBUTION,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    name = Path(structure).name
    return read_csv(out / f'{name}_predictions.csv'), read_csv(out / f'{name}_residues.csv')


@pytest.fixture(scope='session')
def evidence():
    path = REPO / 'reports/local-acceptance-evidence.json'
    record = json.loads(path.read_text()) if path.exists() else {}
    yield record
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')


@pytest.fixture(scope='session')
def adapter_runs(tmp_path_factory):
    """One adapter invocation per frozen reference structure, reused across checks."""
    from src.predictor import predict
    cache = {}

    def run(name, top_n=10, chains=None, fmt='cif', suffix='.cif'):
        key = (name, top_n, tuple(chains or []), fmt)
        if key not in cache:
            root = tmp_path_factory.mktemp(f'{name}-{top_n}')
            raw = (LAB / 'fixtures' / f'{name}{suffix}').read_bytes()
            cache[key] = predict(raw, fmt, chains or [], top_n, root=root)
        return cache[key]
    return run
