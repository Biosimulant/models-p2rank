"""Acquire pinned public assets once and rebuild the binding-pocket Lab's byte-identical stored bundles."""
import hashlib
import io
import json
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from biosim import BioModule, ExecutionPolicy, SignalSpec

AGENT = {'User-Agent': 'biosimulant-p2rank-runtime-preparation'}
SOURCE_URL = 'https://github.com/rdk/p2rank/releases/download/2.5.1/p2rank_2.5.1.tar.gz'
SOURCE_SHA256 = 'd243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274'
SOURCE_SIZE = 275625956
PREFIX = 'p2rank_2.5.1/'
CHUNK_LIMIT = 48 * 1024 * 1024
# Omitted: restrictive Sun notice (classes duplicated by vecmath-1.5.2) and LGPL GUI charting without retained source.
EXCLUDED = {'bin/lib/vecmath-1.3.1.jar', 'bin/lib/openchart-1.4.2.jar'}
VIEWER_URL = 'https://registry.npmjs.org/3dmol/-/3dmol-2.5.5.tgz'
VIEWER_SHA256 = '26d91c5036d4efe78fc032c22cb692fea92bbb3cb1e65d20bf3869673fb3d8f5'
VIEWER_SIZE = 4231158
# RCSB PDB entries (CC0, wwPDB usage policy); bytes pinned as served on 2026-10-03/04.
STRUCTURES = {'1CRN': (69506, '23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba'),
              '1STP': (148195, '36be77b9722ebb9f603b27bf16cbc30057f87ab9923a2d2adab0eadbdb30c30f'),
              '7L13': (575073, 'fb17b4cd4030ab92d5add0ab34603946e0fd74a0e8ed5b3e46f0c23b037e1023')}
# Public dedicated repository commit holding the notice records and the corresponding-source manifest.
REPO_RAW = 'https://raw.githubusercontent.com/Biosimulant/models-p2rank/1d3e49225d491f6f81cdea61b8ef0198903565d5/'
RECORDS_MANIFEST = ('labs/binding-pockets/sources/license-records-manifest.json', 26155,
                    'a7d8e0a04960039fe35aecba6305ceeeaabf2a83675290b828208ecdddfa3069')
SOURCES_MANIFEST = ('labs/binding-pockets/sources/corresponding-sources-manifest.json', 12261,
                    '1b9f218d366715ebaf6544afa6e88ad16e730a635197c1d575f490c0989ddcf8')
# Frozen assets/runtime-lock.json entries reproduced by scripts/inventory_assets.py and scripts/build_bundles.py.
FROZEN = {'p2rank-runtime-0.zip': (50248580, '9b84a3f3eb77d8f0ba6491ca5acfaadd2fb4c57de5d5b58a8bc9022a81a606db'),
          'p2rank-runtime-1.zip': (46645586, '960ef240086f91e1a8dd12fadd59f106b53966585232847be99bb21e95e02d96'),
          'viewer-3dmol-2.5.5.zip': (542287, '7f2b3a16b60b3ce0a7b835e105c792e86db6192fd172fdca2bd7566ea843c1f8'),
          'reference-structures.zip': (793072, 'a8397f7e28fb1fb7254104c6aa6db9263d51c4ae6a842ae00ba1a1e848356a19'),
          'license-records.zip': (951602, '85827901f6ae5be738c0f72d407e7c027fb7486d7f3a8519be65fc39f545035f'),
          'corresponding-sources.zip': (31891277, 'a5f466f0895ff9f95b1622094d17f8781de6bdd17d72c95e53feb0eaae13bfc9')}
PORTS = {'runtime_0': 'p2rank-runtime-0.zip', 'runtime_1': 'p2rank-runtime-1.zip', 'viewer': 'viewer-3dmol-2.5.5.zip',
         'reference_structures': 'reference-structures.zip', 'license_records': 'license-records.zip',
         'corresponding_sources': 'corresponding-sources.zip'}


def fetch(url, size, sha256):
    parts, total = [], 0
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=120) as response:
        while (chunk := response.read(1024 * 1024)) and total <= size:
            parts.append(chunk)
            total += len(chunk)
    raw = b''.join(parts)
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError(f'Integrity mismatch for {url}')
    return raw


def write_zip(target, members):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as z:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            z.writestr(info, members[name])
    raw = target.read_bytes()
    size, sha256 = FROZEN[target.name]
    return {'path': target.name, 'members': len(members), 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'expected_sha256': sha256, 'matches_frozen_lock': len(raw) == size and hashlib.sha256(raw).hexdigest() == sha256}


def selected(rel):
    parts = PurePosixPath(rel).parts
    return rel not in EXCLUDED and (parts[0] in ('bin', 'config') or rel.startswith(('models/default/', 'models/_score_transform/'))
                                    or parts[-1] == 'LICENSE.txt')


def download(destination):
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(urllib.request.Request(SOURCE_URL, headers=AGENT), timeout=60) as response, \
            destination.open('wb') as out:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > SOURCE_SIZE:
                raise ValueError('Distribution larger than pinned size')
            digest.update(chunk)
            out.write(chunk)
    if size != SOURCE_SIZE or digest.hexdigest() != SOURCE_SHA256:
        raise ValueError('P2Rank distribution integrity mismatch')


def runtime_chunks(root):
    work = Path(tempfile.mkdtemp(prefix='p2rank-acquire-'))
    archive = work / 'p2rank_2.5.1.tar.gz'
    download(archive)
    contents = {}
    with tarfile.open(archive, 'r:gz') as tar:
        for info in tar:
            if info.isfile() and info.name.startswith(PREFIX) and selected(info.name[len(PREFIX):]):
                contents[info.name[len(PREFIX):]] = tar.extractfile(info).read()
    archive.unlink()
    groups, group, size = [], [], 0
    for rel in sorted(contents, key=PurePosixPath):
        if size + len(contents[rel]) > CHUNK_LIMIT:
            groups.append(group)
            group, size = [], 0
        group.append(rel)
        size += len(contents[rel])
    groups.append(group)
    if len(groups) != 2:
        raise ValueError('Unexpected runtime chunk layout')
    return len(contents), [write_zip(root / f'p2rank-runtime-{i}.zip', {rel: contents[rel] for rel in members})
                           for i, members in enumerate(groups)]


def bundles(root):
    records = []
    with tarfile.open(fileobj=io.BytesIO(fetch(VIEWER_URL, VIEWER_SIZE, VIEWER_SHA256)), mode='r:gz') as tar:
        viewer = {'3Dmol-min.js': tar.extractfile('package/build/3Dmol-min.js').read(),
                  'LICENSE': tar.extractfile('package/LICENSE').read()}
    records.append(write_zip(root / 'viewer-3dmol-2.5.5.zip', viewer))
    records.append(write_zip(root / 'reference-structures.zip',
                             {f'{entry}.cif': fetch(f'https://files.rcsb.org/download/{entry}.cif', size, sha256)
                              for entry, (size, sha256) in STRUCTURES.items()}))
    path, size, sha256 = RECORDS_MANIFEST
    notices = {e['member']: fetch(REPO_RAW + e['repo_path'], e['size_bytes'], e['sha256'])
               for e in json.loads(fetch(REPO_RAW + path, size, sha256))}
    records.append(write_zip(root / 'license-records.zip', notices))
    path, size, sha256 = SOURCES_MANIFEST
    sources = {e['member']: fetch(e['url'], e['size_bytes'], e['sha256']) for e in json.loads(fetch(REPO_RAW + path, size, sha256))}
    records.append(write_zip(root / 'corresponding-sources.zip', sources))
    return records


def build(root):
    members, chunks = runtime_chunks(root)
    records = chunks + bundles(root)
    return {'source_url': SOURCE_URL, 'source_sha256': SOURCE_SHA256, 'source_size_bytes': SOURCE_SIZE,
            'runtime_members': members, 'excluded_members': sorted(EXCLUDED), 'repository_raw_base': REPO_RAW,
            'bundles': records, 'all_match': all(r['matches_frozen_lock'] for r in records)}


class AcquireRuntime(BioModule):
    execution_policy = ExecutionPolicy.ONCE_BEFORE_RUN

    def __init__(self):
        self.receipt = None

    def outputs(self):
        return {**{port: SignalSpec.scalar(dtype='str', value_type='file', format='zip') for port in PORTS},
                'receipt': SignalSpec.record(schema={'source_url': 'str', 'source_sha256': 'str', 'source_size_bytes': 'int',
                                                     'runtime_members': 'int', 'excluded_members': 'json',
                                                     'repository_raw_base': 'str', 'bundles': 'json', 'all_match': 'bool'},
                                             emitted_unit='1')}

    def execute(self, inputs, *, context):
        root = Path.cwd() / 'outputs'
        root.mkdir(exist_ok=True)
        self.receipt = build(root)
        return {**{port: str((root / name).resolve()) for port, name in PORTS.items()}, 'receipt': self.receipt}

    def visualize(self):
        if not self.receipt:
            return []
        state = 'all match' if self.receipt['all_match'] else 'DO NOT all match'
        return {'schema_version': '1', 'render': 'text', 'data': {
            'text': f"Rebuilt {len(self.receipt['bundles'])} stored bundles from checksum-pinned public sources "
                    f"(P2Rank 2.5.1 release, npm 3Dmol.js 2.5.5, RCSB, Maven Central/GitHub sources); they {state} "
                    'the frozen lock. Infrastructure artifacts only; no protein or pocket result.'}}
