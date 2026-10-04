"""Compare byte-verified managed-run artifacts with a fresh local adapter run on the same input.

Usage: verify_managed.py RUN_DIR FIXTURE TOP_N
RUN_DIR holds artifacts downloaded by verify_artifact.py (each with a .verification.json).
Writes RUN_DIR/managed-parity.json. Local evidence only; managed bytes come from the platform.
"""
import csv
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/binding-pockets'
sys.path.insert(0, str(LAB / 'models/predict'))
from src.predictor import bundled_example, predict  # noqa: E402

UPSTREAM = ['predictions.csv', 'residues.csv', 'processed.pdb', 'mapped_residues.csv']


def main():
    run_dir, fixture, top_n = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    checks = {p.name.removesuffix('.verification.json'): json.loads(p.read_text())['verified']
              for p in run_dir.glob('*.verification.json')}
    raw = bundled_example(Path('fixtures') / fixture).read_bytes()
    with tempfile.TemporaryDirectory() as temp:
        report, files = predict(raw, 'cif', [], top_n, root=Path(temp))
        local = {Path(v).name: Path(v).read_bytes() for v in files.values()}
    record = {'fixture': fixture, 'top_n': top_n, 'artifact_byte_checks': checks, 'all_artifacts_verified': all(checks.values()),
              'byte_identical_to_local': {}, 'report': {}}
    for name in UPSTREAM:
        managed = run_dir / name
        record['byte_identical_to_local'][name] = managed.exists() and managed.read_bytes() == local[name]
    results = json.loads((run_dir / 'results.json').read_text())
    managed_report = results['outputs']['predict']['report']['value']
    record['report'] = {
        'status': managed_report['status'], 'local_status': report['status'],
        'pockets_equal': managed_report['pockets'] == report['pockets'],
        'residues_equal': managed_report['residues'] == report['residues'],
        'surface_points_equal': managed_report['surface_points'] == report['surface_points'],
        'scores': [p['upstream_score'] for p in managed_report['pockets']],
        'probabilities': [p['upstream_probability'] for p in managed_report['pockets']],
        'centers_angstrom': [p['center_angstrom'] for p in managed_report['pockets']],
        'managed_elapsed_seconds': managed_report['receipt'].get('elapsed_seconds'),
        'managed_java_version': managed_report['receipt'].get('java_version', '').splitlines()[:1],
    }
    visuals = results['visuals'][0]['visuals']
    record['visual_renders'] = [v['render'] for v in visuals]
    table = next((v for v in visuals if v['render'] == 'table'), None)
    if table:
        record['table_matches_report'] = [r[1] for r in table['data']['rows']] == record['report']['scores']
    if (run_dir / 'receipt_file.json').exists():
        receipt = json.loads((run_dir / 'receipt_file.json').read_text())
        record['receipt_input_sha256'] = receipt['input_sha256']
    if (run_dir / 'mapped_residues.csv').exists():
        with (run_dir / 'mapped_residues.csv').open(newline='') as f:
            record['mapped_residue_rows'] = sum(1 for _ in csv.DictReader(f))
    (run_dir / 'managed-parity.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ('fixture', 'top_n', 'all_artifacts_verified', 'byte_identical_to_local')}
                     | {'pockets_equal': record['report']['pockets_equal'], 'status': record['report']['status']}))


if __name__ == '__main__':
    main()
