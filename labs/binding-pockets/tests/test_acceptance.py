"""Frozen item-03 acceptance checks; results are derived from executed predictions."""
import hashlib
import json
import math
import subprocess
from pathlib import Path

import gemmi
import pytest

from conftest import LAB, example_path, read_csv, standalone
from src import predictor
from src.predictor import PocketPredictor, predict
from src.structure import InputError, preprocess

REFERENCES = ['1CRN', '1STP', '7L13']
CENTER_TOLERANCE = 1e-3
RECOVERY_DISTANCE = 4.0


def ids(row):
    return row['residue_ids'].split()


def mapped_author_tokens(pocket):
    return sorted(f"{r['author_chain']}_{r['author_residue_number']}{r['insertion_code']}" for r in pocket['residues'])


def assert_same_predictions(adapter_rows, upstream_rows, translate=lambda t: t):
    assert [int(r['rank']) for r in adapter_rows] == [int(r['rank']) for r in upstream_rows]
    for a, u in zip(adapter_rows, upstream_rows):
        assert a['score'] == u['score'] and a['probability'] == u['probability']
        assert a['sas_points'] == u['sas_points'] and a['surf_atoms'] == u['surf_atoms']
        for axis in 'xyz':
            assert abs(float(a[f'center_{axis}']) - float(u[f'center_{axis}'])) <= CENTER_TOLERANCE
        assert sorted(translate(t) for t in ids(a)) == sorted(ids(u))


def test_runtime_assets_match_frozen_distribution(tmp_path):
    lock = predictor.runtime(tmp_path)
    assert lock['distribution_sha256'] == 'd243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274'
    assert (tmp_path / 'models/default').is_dir() and (tmp_path / 'bin/p2rank.jar').is_file()


LOCK = json.loads((LAB / 'fixtures/fixture-lock.json').read_text())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('name', REFERENCES)
def test_frozen_preprocessing_fixtures(name):
    raw = example_path(f'{name}.cif').read_bytes()
    assert digest(raw) == LOCK[name]['source_sha256']
    prep = preprocess(raw, 'cif', [])
    assert digest(prep['pdb'].encode()) == LOCK[name]['processed_pdb_sha256']
    assert digest(json.dumps(prep['mapping'], sort_keys=True).encode()) == LOCK[name]['mapping_sha256']
    assert 'HETATM' not in prep['pdb']


def test_mapping_fixture_is_reproducible():
    from mapping_fixture import build
    assert digest(build().encode()) == LOCK['mapping-edge']['sha256']


@pytest.mark.parametrize('name', REFERENCES)
def test_a1_parity_with_standalone_distribution(name, adapter_runs, tmp_path, evidence):
    report, files = adapter_runs(name)
    adapter_rows = read_csv(files['raw_predictions'])
    adapter_residues = read_csv(files['raw_residues'])
    # Exact native parity on the identical processed coordinates.
    up_rows, up_residues = standalone(Path(files['processed_structure']), tmp_path / 'processed')
    assert_same_predictions(adapter_rows, up_rows)
    assert [r['name'] for r in adapter_rows] == [r['name'] for r in up_rows]
    assert adapter_residues == up_residues
    # Standalone run on the original deposited mmCIF; reversible map must restore author identities.
    orig_rows, orig_residues = standalone(example_path(f'{name}.cif'), tmp_path / 'original')
    lookup = {f"{r['internal_chain']}_{r['internal_residue']}": f"{r['author_chain']}_{r['author_residue_number']}{r['insertion_code']}"
              for r in json.loads(Path(files['residue_map']).read_text())}
    assert_same_predictions(adapter_rows, orig_rows, translate=lambda t: lookup[t])
    assert [p['rank'] for p in report['pockets']] == [int(r['rank']) for r in orig_rows][:10]
    for pocket, row in zip(report['pockets'], orig_rows):
        assert mapped_author_tokens(pocket) == sorted(ids(row))
        assert pocket['upstream_score'] == float(row['score'])
        assert all(abs(c - float(row[f'center_{a}'])) <= CENTER_TOLERANCE for c, a in zip(pocket['center_angstrom'], 'xyz'))
    assert report['status'] == ('ok' if orig_rows else 'no_pockets')
    evidence.setdefault('A1', {})[name] = {
        'pockets': len(orig_rows), 'ranks': [int(r['rank']) for r in orig_rows],
        'scores': [r['score'] for r in orig_rows], 'probabilities': [r['probability'] for r in orig_rows],
        'max_center_delta_angstrom_vs_original': max([abs(float(a[f'center_{x}']) - float(u[f'center_{x}']))
                                                       for a, u in zip(adapter_rows, orig_rows) for x in 'xyz'] or [0.0]),
        'residue_rows_processed_parity': len(adapter_residues),
        'comparisons': ['adapter vs standalone on identical processed PDB: exact rows',
                        'adapter mapped author IDs vs standalone on original mmCIF: ordering, residues, scores, centers'],
    }


def view_payload(html):
    """Decode the gzip+base64 data embedded in pocket-view.html."""
    import base64, gzip, re
    packed = json.loads(re.search(r"const packed=(\"[^\"]*\");", html).group(1))
    return json.loads(gzip.decompress(base64.b64decode(packed)))


def atoms_by_residue(structure, chain_name, key):
    for chain in structure[0]:
        if chain.name != chain_name:
            continue
        for res in chain:
            if key(res):
                return {a.name: (round(a.pos.x, 3), round(a.pos.y, 3), round(a.pos.z, 3)) for a in res if not a.is_hydrogen()}
    raise KeyError(chain_name)


def test_a2_insertion_codes_gaps_and_duplicate_author_numbers(tmp_path, evidence):
    from mapping_fixture import build
    raw = build().encode()
    report, files = predict(raw, 'cif', [], 10, root=tmp_path)
    mapping = json.loads(Path(files['residue_map']).read_text())
    original = gemmi.make_structure_from_block(gemmi.cif.read_string(raw.decode()).sole_block())
    processed = gemmi.read_pdb_string(Path(files['processed_structure']).read_text())
    identities = {(r['author_chain'], r['author_residue_number'], r['insertion_code']) for r in mapping}
    assert len(identities) == len(mapping)
    assert ('AUTH_A', 30, '') in identities and ('AUTH_A', 30, 'A') in identities
    assert ('AUTH_B', 30, '') in identities and ('AUTH_B', 30, 'A') in identities
    gaps = [b['author_residue_number'] - a['author_residue_number'] for a, b in zip(mapping, mapping[1:])
            if a['author_chain'] == b['author_chain']]
    assert max(gaps) >= 2
    for row in mapping:
        source = atoms_by_residue(original, row['author_chain'], lambda r: r.seqid.num == row['author_residue_number']
                                  and r.seqid.icode.strip() == row['insertion_code'])
        target = atoms_by_residue(processed, row['internal_chain'], lambda r: r.seqid.num == row['internal_residue'])
        assert target.items() <= source.items()
    mapped = read_csv(files['mapped_residues'])
    assert mapped and {(m['author_chain'], m['author_residue_number'], m['insertion_code']) for m in mapped} <= \
        {(a, str(n), i) for a, n, i in identities}
    pocket_residues = [r for p in report['pockets'] for r in p['residues']]
    chains = {r['author_chain'] for r in pocket_residues}
    assert any(r['insertion_code'] == 'A' for r in pocket_residues), 'insertion-code residue must be highlighted in a pocket'
    assert chains == {'AUTH_A', 'AUTH_B'}
    browser = LAB.parents[1] / 'outputs'
    if browser.is_dir():
        (browser / 'a2').mkdir(exist_ok=True)
        (browser / 'a2/pocket-view.html').write_text(Path(files['pocket_view']).read_text())
    only_b, _ = predict(raw, 'cif', ['AUTH_B'], 10, root=tmp_path / 'b')
    assert {r['author_chain'] for p in only_b['pockets'] for r in p['residues']} <= {'AUTH_B'}
    embedded = view_payload(Path(files['pocket_view']).read_text())
    assert embedded['pockets'] == report['pockets'] and embedded['points'] == report['surface_points']
    assert any(r['insertion_code'] == 'A' for p in embedded['pockets'] for r in p['residues'])
    evidence['A2'] = {'mapped_residues': len(mapping), 'pockets': len(report['pockets']), 'pocket_author_chains': sorted(chains),
                      'insertion_code_residues_in_pockets': sorted({f"{r['author_chain']}:{r['author_residue_number']}{r['insertion_code']}"
                                                                    for r in pocket_residues if r['insertion_code']}),
                      'chain_selection_AUTH_B_pockets': len(only_b['pockets'])}


def test_a3_held_out_holo_demonstration(adapter_runs, evidence):
    ligand = json.loads((LAB / 'fixtures/7L13-reference-ligand.json').read_text())
    report, files = adapter_runs('7L13', top_n=3)
    processed = Path(files['processed_structure']).read_text()
    assert 'HETATM' not in processed and ligand['name'] not in processed
    atoms = ligand['heavy_atoms_angstrom']
    distances = [min(math.dist(p['center_angstrom'], a) for a in atoms) for p in report['pockets']]
    nearest = min(range(len(distances)), key=distances.__getitem__)
    top1 = distances[0] <= RECOVERY_DISTANCE
    top3 = any(d <= RECOVERY_DISTANCE for d in distances[:3])
    evidence['A3'] = {'structure': '7L13 (released 2021-03-03; P2Rank default model trained on CHEN11)',
                      'reference_ligand': f"{ligand['name']} {ligand['author_chain']}/{ligand['author_residue_number']}",
                      'definition': 'minimum distance from predicted pocket center to any reference ligand heavy atom <= 4.0 Angstrom',
                      'distances_angstrom_by_rank': distances, 'nearest_rank': nearest + 1,
                      'nearest_distance_angstrom': distances[nearest], 'top1_recovered': top1, 'top3_recovered': top3,
                      'scope': 'Single-structure demonstration; not an accuracy estimate'}
    assert len(distances) == 3


PROTEIN_FREE = ('HETATM    1  O   HOH A   1       0.000   0.000   0.000  1.00 10.00           O\n'
                'HETATM    2  C1  LIG A   2       1.000   0.000   0.000  1.00 10.00           C\nEND\n')


@pytest.mark.parametrize('raw,fmt,chains,top_n,code', [
    (b'', 'pdb', [], 3, 'input_size'),
    (PROTEIN_FREE.encode(), 'pdb', [], 3, 'no_protein'),
    (b'\x00\x01\x02binary', 'cif', [], 3, 'parse_error'),
    (b'ATOM', 'sdf', [], 3, 'unsupported_format'),
    (None, 'cif', [], 0, 'top_n'),
    (None, 'cif', [], 11, 'top_n'),
    (None, 'cif', ['Z'], 3, 'missing_chain'),
    (None, 'cif', ['A', 'A'], 3, 'chain_selection'),
    (b'x' * (2 * 1024 * 1024 + 1), 'pdb', [], 3, 'input_size'),
])
def test_a4_invalid_inputs_are_explicit(raw, fmt, chains, top_n, code, tmp_path):
    raw = raw if raw is not None else example_path('1STP.cif').read_bytes()
    with pytest.raises(InputError) as error:
        predict(raw, fmt, chains, top_n, root=tmp_path)
    assert error.value.code == code
    assert not (tmp_path / 'predictions.csv').exists()


def test_a4_no_pocket_result_is_valid_empty(adapter_runs, evidence):
    report, files = adapter_runs('1CRN', top_n=3)
    assert report['status'] == 'no_pockets' and report['pockets'] == [] and report['receipt']['returned_pockets'] == 0
    assert read_csv(files['raw_predictions']) == []
    assert 'No pockets predicted' in Path(files['pocket_view']).read_text()
    evidence.setdefault('A4', {})['1CRN_no_pockets'] = {'status': report['status'], 'files': sorted(files)}


class Signal:
    def __init__(self, value):
        self.value = value


def execute(tmp_path, monkeypatch, **values):
    monkeypatch.chdir(tmp_path)
    module = PocketPredictor()
    out = module.execute({k: Signal(v) for k, v in values.items()}, context=None)
    return module, out


def test_a4_module_outcomes(tmp_path, monkeypatch, evidence):
    module, out = execute(tmp_path, monkeypatch, structure_file='fixtures/1CRN.cif',
                          mmcif_file='fixtures/1CRN.cif', chains_json='[]', top_n=3)
    assert out['report']['status'] == 'invalid_input' and out['report']['receipt']['error_code'] == 'structure_input'
    bad = tmp_path / 'protein.txt'
    bad.write_text('ATOM')
    module, out = execute(tmp_path, monkeypatch, structure_file=str(bad), chains_json='[]', top_n=3)
    assert out['report']['receipt']['error_code'] == 'unsupported_format'
    assert [v['render'] for v in module.visualize()] == ['text']
    packed = tmp_path / 'packed.cif'
    packed.write_bytes(b'\x1f\x8b' + b'0' * 64)
    module, out = execute(tmp_path, monkeypatch, mmcif_file=str(packed), chains_json='[]', top_n=3)
    assert out['report']['receipt']['error_code'] == 'unsupported_format'
    monkeypatch.setattr(predictor, 'TIMEOUT_SECONDS', 0.5)
    module, out = execute(tmp_path, monkeypatch, mmcif_file='fixtures/7L13.cif', chains_json='[]', top_n=3)
    assert out['report']['status'] == 'timeout' and out['pocket_count'] == 0
    monkeypatch.setattr(predictor, 'TIMEOUT_SECONDS', 300)
    original = predictor.invoke

    def failing(install, pdb, out, timeout):
        (install / 'bin/p2rank.jar').write_bytes(b'not a jar')
        return original(install, pdb, out, timeout)
    monkeypatch.setattr(predictor, 'invoke', failing)
    module, out = execute(tmp_path, monkeypatch, mmcif_file='fixtures/7L13.cif', chains_json='[]', top_n=3)
    assert out['report']['status'] == 'execution_failed' and out['report']['pockets'] == []
    evidence.setdefault('A4', {})['module_outcomes'] = ['structure_input', 'unsupported_format', 'compressed_upload', 'timeout', 'execution_failed']


def test_a5_top1_versus_top3_and_view(tmp_path, monkeypatch, adapter_runs, evidence):
    module, out = execute(tmp_path, monkeypatch, mmcif_file='fixtures/7L13.cif', chains_json='[]', top_n=1)
    three, files = adapter_runs('7L13', top_n=3)
    one = out['report']
    assert one['status'] == 'ok' and len(one['pockets']) == 1 and len(three['pockets']) == 3
    assert one['pockets'][0]['upstream_score'] == three['pockets'][0]['upstream_score']
    assert one['pockets'][0]['center_angstrom'] == three['pockets'][0]['center_angstrom']
    renders = [v['render'] for v in module.visualize()]
    assert renders == ['text', 'structure3d', 'table']
    for key in predictor.FILES:
        assert Path(out[key]).is_file() and str(tmp_path / 'outputs') in out[key]
    receipt = json.loads(Path(out['receipt_file']).read_text())
    assert receipt['top_n'] == 1 and receipt['input_sha256'] == LOCK['7L13']['source_sha256']
    html = Path(out['pocket_view']).read_text()
    assert '$3Dmol' in html and 'window.verification' in html and 'Download receipt' in html
    embedded = view_payload(html)
    assert embedded['pockets'] == one['pockets'] and embedded['receipt']['top_n'] == 1
    assert all(p['pocket_rank'] == 1 for p in one['surface_points']) and len(one['surface_points']) == one['pockets'][0]['surface_point_count']
    sizes = {key: Path(files[key]).stat().st_size for key in predictor.FILES}
    assert max(sizes.values()) < 1_000_000, sizes  # managed artifact upload is verified up to ~1.08 MB per file
    evidence['output_sizes_7L13_top3'] = sizes
    evidence['A5'] = {'top1_rank_scores': [p['upstream_score'] for p in one['pockets']],
                      'top3_rank_scores': [p['upstream_score'] for p in three['pockets']]}
