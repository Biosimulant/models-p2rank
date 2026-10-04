"""Anonymous verification of the public release, listing, example runs and downloads (no owner credentials)."""
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB_DIR = ROOT / 'labs/binding-pockets'
API = 'https://api.biosimulant.com/api'
LAB = '88648162-e30d-49a1-9b07-de5fa0a11d36'
RUNS = {'7L13 top-3': 'd174ea14-0366-48f1-ae59-1833278aa503', '7L13 top-1': 'f98d3a40-5283-413b-96c8-94faaa1a8414',
        '1STP top-3 pilot': '779beba6-8679-4a61-8a6f-c6db3169f2a2', '1CRN no-pocket pilot': 'e0eab1ea-a7a4-4340-93b4-c2132c51eed3'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (anonymous verification)'}


def get(route, raw=False):
    url = route if route.startswith('http') else API + route
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as f:
            body = f.read()
            return f.status, body if raw else json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def package_check(lab):
    artifact = lab['download_package_artifact_id']
    status, info = get(f'/packages/{artifact}/download-url')
    record = {'artifact_id': artifact, 'download_url_status': status}
    if status != 200:
        status, data = get(f'/packages/{artifact}/download', raw=True)
    else:
        url = info.get('url') or info.get('download_url')
        status, data = get(url, raw=True)
    record['download_status'] = status
    if status != 200:
        return record
    record.update({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                   'matches_declared_artifact_sha256': hashlib.sha256(data).hexdigest() == lab['latest_package_artifact_sha256']})
    archive = zipfile.ZipFile(io.BytesIO(data))
    names = archive.namelist()
    root = next((n.split('/')[0] + '/' for n in names if n.endswith('lab.yaml') and n.count('/') == 1), '')
    lock = json.loads((LAB_DIR / 'assets/runtime-lock.json').read_text())
    bundles = {}
    for entry in lock['assets'] + lock['bundles']:
        member = next((n for n in names if n.endswith('assets/' + entry['path'])), None)
        body = archive.read(member) if member else b''
        bundles[entry['path']] = member is not None and len(body) == entry['size_bytes'] and hashlib.sha256(body).hexdigest() == entry['sha256']
    exact = {}
    for rel in ['models/predict/src/predictor.py', 'models/predict/src/structure.py', 'tests/test_acceptance.py',
                'fixtures/fixture-lock.json', 'fixtures/7L13-reference-ligand.json', 'assets/runtime-lock.json', 'NOTICE.md', 'LICENSE']:
        member = next((n for n in names if n.endswith(rel)), None)
        exact[rel] = member is not None and archive.read(member) == (LAB_DIR / rel).read_bytes()
    record.update({'members': len(names), 'package_root': root, 'bundles_match_lock': bundles, 'source_files_match_staging': exact})
    return record


def main():
    checks = {}
    status, lab = get(f'/labs/{LAB}')
    checks['lab'] = {'status': status, 'is_public': lab['is_public'], 'is_hub_listed': lab['is_hub_listed'], 'is_mine': lab['is_mine'],
                     'latest_package_version': lab['latest_package_version'], 'qualified_package_name': lab['qualified_package_name']}
    status, page = get(f'https://hub.biosimulant.com/labs/{LAB}', raw=True)
    checks['hub_page'] = {'status': status, 'title_present': b'P2Rank Binding-Pocket Prediction' in page if status == 200 else False}
    status, listing = get(f'/labs/{LAB}/runs')
    checks['public_lab_runs'] = {'status': status, 'total': listing.get('total'), 'ids': sorted(i['id'] for i in listing.get('items', []))}
    checks['package'] = package_check(lab)
    checks['runs'] = {}
    for label, run in RUNS.items():
        status, data = get(f'/runs/{run}')
        meta = json.loads((ROOT / 'reports/managed/run-artifacts.json').read_text())[run]
        artifacts = []
        for a in meta:
            code, body = get(f'/runs/{run}/artifacts/{a["artifact_id"]}', raw=True)
            item = {'role': a['role'], 'status': code, 'declared_size': a['size_bytes']}
            if code == 200:
                item['bytes'] = len(body)
                item['verified'] = len(body) == a['size_bytes'] and hashlib.sha256(body).hexdigest() == a['sha256']
                if not item['verified'] and a['file_name'].endswith('.html'):
                    stripped = re.sub(rb'<script[^>]*cloudflareinsights[^>]*>\s*</script>\n', b'', body, count=1)
                    item['verified_after_removing_injected_beacon'] = hashlib.sha256(stripped).hexdigest() == a['sha256']
            artifacts.append(item)
        checks['runs'][label] = {'run_id': run, 'status': status, 'is_public': data.get('is_public') if isinstance(data, dict) else None,
                                 'artifacts': artifacts}
    out = ROOT / 'reports/public-verification.json'
    out.write_text(json.dumps({'scope': 'Anonymous HTTPS requests from macOS; no owner credentials or signed URLs retained',
                               'checks': checks}, indent=2) + '\n')
    summary = {label: (r['is_public'], sum(a.get('verified', False) for a in r['artifacts']), len(r['artifacts'])) for label, r in checks['runs'].items()}
    print(json.dumps({'lab': checks['lab'], 'hub_page': checks['hub_page'], 'public_runs': checks['public_lab_runs']['total'],
                      'package': {k: checks['package'].get(k) for k in ('download_status', 'bytes', 'matches_declared_artifact_sha256')},
                      'bundles': checks['package'].get('bundles_match_lock'), 'sources': checks['package'].get('source_files_match_staging'),
                      'runs': summary}, indent=1))


if __name__ == '__main__':
    main()
