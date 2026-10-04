"""Build the deterministic asset bundles and record them in assets/runtime-lock.json.

Bundles are stored (uncompressed) ZIPs with fixed timestamps and permissions so the
private runtime-preparation Lab reproduces them byte for byte from public sources:
- viewer-3dmol-2.5.5.zip: 3Dmol-min.js and LICENSE from the npm 3dmol 2.5.5 tarball
- reference-structures.zip: RCSB 1CRN/1STP/7L13 mmCIF (CC0)
- license-records.zip: notices and provenance records from this repository
- corresponding-sources.zip: exact source for the copyleft runtime jars (license-audit.json)
"""
import hashlib
import json
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/binding-pockets'
ASSETS = LAB / 'assets'
RECORD_FILES = ['labs/binding-pockets/THIRD_PARTY_NOTICES.md', 'sources/P2RANK-LICENSE.txt',
                'labs/binding-pockets/sources/license-audit.json', 'labs/binding-pockets/sources/jar-inventory.json',
                'labs/binding-pockets/sources/runtime-members.json', 'labs/binding-pockets/sources/corresponding-sources-manifest.json',
                'reports/runtime-trim-verification.json']
FRF_MIRROR = 'https://raw.githubusercontent.com/rdk/p2rank/9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e/lib/FastRandomForest_0.99_src.jar'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_zip(target, members):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as z:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            z.writestr(info, members[name])
    raw = target.read_bytes()
    return {'path': target.name, 'size_bytes': len(raw), 'sha256': digest(raw), 'members': len(members)}


def record_members():
    paths = list(RECORD_FILES) + sorted(str(p.relative_to(ROOT)) for p in (LAB / 'sources/jar-notices').rglob('*') if p.is_file())
    entries = []
    for rel in paths:
        raw = (ROOT / rel).read_bytes()
        name = rel.removeprefix('labs/binding-pockets/')
        entries.append({'member': name, 'repo_path': rel, 'size_bytes': len(raw), 'sha256': digest(raw)})
    return entries


def main():
    bundles = []
    with tarfile.open(ROOT / 'sources/3dmol-2.5.5.tgz', 'r:gz') as tar:
        viewer = {'3Dmol-min.js': tar.extractfile('package/build/3Dmol-min.js').read(),
                  'LICENSE': tar.extractfile('package/LICENSE').read()}
    bundles.append(write_zip(ASSETS / 'viewer-3dmol-2.5.5.zip', viewer))
    bundles.append(write_zip(ASSETS / 'reference-structures.zip',
                             {f'{n}.cif': (LAB / f'fixtures/{n}.cif').read_bytes() for n in ['1CRN', '1STP', '7L13']}))
    audit = json.loads((LAB / 'sources/license-audit.json').read_text())
    sources, listing = {}, {}
    for jar in audit['jars']:
        cs = jar.get('corresponding_source') or {}
        if cs.get('url'):
            raw = (ROOT / cs['local_path']).read_bytes()
            assert len(raw) == cs['size_bytes'] and digest(raw) == cs['sha256'], cs['local_path']
            name = Path(cs['local_path']).name
            sources[name] = raw
            url = FRF_MIRROR if cs['kind'] == 'shipped-source-jar' else cs['url']
            listing[name] = {'member': name, 'url': url, 'size_bytes': len(raw), 'sha256': cs['sha256'],
                             'for_jars': sorted(set(listing.get(name, {}).get('for_jars', [])) | {jar['jar']})}
    (LAB / 'sources/corresponding-sources-manifest.json').write_text(json.dumps(sorted(listing.values(), key=lambda e: e['member']), indent=2) + '\n')
    entries = record_members()
    manifest = LAB / 'sources/license-records-manifest.json'
    manifest.write_text(json.dumps(entries, indent=2) + '\n')
    bundles.append(write_zip(ASSETS / 'license-records.zip', {e['member']: (ROOT / e['repo_path']).read_bytes() for e in entries}))
    bundles.append(write_zip(ASSETS / 'corresponding-sources.zip', sources))
    lock_path = ASSETS / 'runtime-lock.json'
    lock = json.loads(lock_path.read_text())
    lock['bundles'] = bundles
    lock_path.write_text(json.dumps(lock, indent=2) + '\n')
    print(json.dumps(bundles, indent=1))


if __name__ == '__main__':
    main()
