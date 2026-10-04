"""Acquire pinned public assets once: P2Rank 2.5.1 runtime chunks, 3Dmol.js 2.5.5 and RCSB reference structures."""
import hashlib
import io
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from biosim import BioModule, ExecutionPolicy, SignalSpec

SOURCE_URL = 'https://github.com/rdk/p2rank/releases/download/2.5.1/p2rank_2.5.1.tar.gz'
SOURCE_SHA256 = 'd243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274'
SOURCE_SIZE = 275625956
PREFIX = 'p2rank_2.5.1/'
CHUNK_LIMIT = 48 * 1024 * 1024
# Frozen runtime-lock.json assets; the chunks are reproduced exactly as scripts/inventory_assets.py builds them.
FROZEN = [('p2rank-runtime-0.zip', 50248580, '9b84a3f3eb77d8f0ba6491ca5acfaadd2fb4c57de5d5b58a8bc9022a81a606db'),
          ('p2rank-runtime-1.zip', 47064322, '150fd24cb75ded613b2c1795ce520d40bd52af94099be091c3b8191a8b33fd57')]


VIEWER_URL = 'https://registry.npmjs.org/3dmol/-/3dmol-2.5.5.tgz'
VIEWER_SHA256 = '26d91c5036d4efe78fc032c22cb692fea92bbb3cb1e65d20bf3869673fb3d8f5'
VIEWER_SIZE = 4231158
VIEWER_MEMBERS = {'package/build/3Dmol-min.js': ('3Dmol-min.js', 537792, 'f7cc78921ae72e7623e89cdd111434f58c2efddd2ffda1cd212644b406fb8016'),
                  'package/LICENSE': ('3Dmol-LICENSE', 4283, '4c6eaaed856f3f28a3b1a98e74f4a8a71618de7d51ea4155c29f6f793bcef861')}
# RCSB PDB entries (CC0, wwPDB usage policy); bytes pinned as served on 2026-10-03/04.
STRUCTURES = {'1CRN': (69506, '23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba'),
              '1STP': (148195, '36be77b9722ebb9f603b27bf16cbc30057f87ab9923a2d2adab0eadbdb30c30f'),
              '7L13': (575073, 'fb17b4cd4030ab92d5add0ab34603946e0fd74a0e8ed5b3e46f0c23b037e1023')}


def fetch(url, size, sha256):
    request = urllib.request.Request(url, headers={'User-Agent': 'biosimulant-p2rank-runtime-preparation'})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(size + 1)
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError(f'Integrity mismatch for {url}')
    return raw


def small_assets(root):
    records = []
    archive = fetch(VIEWER_URL, VIEWER_SIZE, VIEWER_SHA256)
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        for member, (name, size, sha256) in VIEWER_MEMBERS.items():
            raw = tar.extractfile(member).read()
            if len(raw) != size or hashlib.sha256(raw).hexdigest() != sha256:
                raise ValueError(f'3Dmol member mismatch: {member}')
            (root / name).write_bytes(raw)
            records.append({'path': name, 'source': f'{VIEWER_URL}#{member}', 'size_bytes': size, 'sha256': sha256})
    for entry, (size, sha256) in STRUCTURES.items():
        url = f'https://files.rcsb.org/download/{entry}.cif'
        (root / f'{entry}.cif').write_bytes(fetch(url, size, sha256))
        records.append({'path': f'{entry}.cif', 'source': url, 'size_bytes': size, 'sha256': sha256})
    return records


def selected(rel):
    parts = PurePosixPath(rel).parts
    return parts[0] in ('bin', 'config') or rel.startswith(('models/default/', 'models/_score_transform/')) \
        or parts[-1] == 'LICENSE.txt'


def download(destination):
    digest = hashlib.sha256()
    size = 0
    request = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'biosimulant-p2rank-runtime-preparation'})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open('wb') as out:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > SOURCE_SIZE:
                raise ValueError('Distribution larger than pinned size')
            digest.update(chunk)
            out.write(chunk)
    if size != SOURCE_SIZE or digest.hexdigest() != SOURCE_SHA256:
        raise ValueError('P2Rank distribution integrity mismatch')


def build(root):
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
    if len(groups) != len(FROZEN):
        raise ValueError('Unexpected runtime chunk layout')
    outputs = []
    for members, (name, expected_size, expected_sha) in zip(groups, FROZEN):
        target = root / name
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as z:
            for rel in members:
                info = zipfile.ZipInfo(rel, date_time=(2025, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = 0o644 << 16
                z.writestr(info, contents[rel])
        raw = target.read_bytes()
        record = {'path': name, 'members': len(members), 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                  'expected_size_bytes': expected_size, 'expected_sha256': expected_sha}
        record['matches_frozen_lock'] = record['size_bytes'] == expected_size and record['sha256'] == expected_sha
        outputs.append(record)
    return {'source_url': SOURCE_URL, 'source_sha256': SOURCE_SHA256, 'source_size_bytes': SOURCE_SIZE,
            'members_verified': len(contents), 'chunks': outputs,
            'all_chunks_match': all(o['matches_frozen_lock'] for o in outputs), 'assets': small_assets(root)}


SMALL_PORTS = {'viewer_js': ('3Dmol-min.js', 'js'), 'viewer_license': ('3Dmol-LICENSE', 'txt'),
               'structure_1crn': ('1CRN.cif', 'cif'), 'structure_1stp': ('1STP.cif', 'cif'), 'structure_7l13': ('7L13.cif', 'cif')}


class AcquireRuntime(BioModule):
    execution_policy = ExecutionPolicy.ONCE_BEFORE_RUN

    def __init__(self):
        self.receipt = None

    def outputs(self):
        return {'runtime_0': SignalSpec.scalar(dtype='str', value_type='file', format='zip'),
                'runtime_1': SignalSpec.scalar(dtype='str', value_type='file', format='zip'),
                'receipt': SignalSpec.record(schema={'source_url': 'str', 'source_sha256': 'str', 'source_size_bytes': 'int',
                                                     'members_verified': 'int', 'chunks': 'json', 'all_chunks_match': 'bool',
                                                     'assets': 'json'},
                                             emitted_unit='1'),
                **{port: SignalSpec.scalar(dtype='str', value_type='file', format=fmt) for port, (_, fmt) in SMALL_PORTS.items()}}

    def execute(self, inputs, *, context):
        root = Path.cwd() / 'outputs'
        root.mkdir(exist_ok=True)
        self.receipt = build(root)
        return {'runtime_0': str((root / FROZEN[0][0]).resolve()),
                'runtime_1': str((root / FROZEN[1][0]).resolve()), 'receipt': self.receipt,
                **{port: str((root / name).resolve()) for port, (name, _) in SMALL_PORTS.items()}}

    def visualize(self):
        if not self.receipt:
            return []
        state = 'match' if self.receipt['all_chunks_match'] else 'DO NOT match'
        return {'schema_version': '1', 'render': 'text', 'data': {
            'text': f"Extracted {self.receipt['members_verified']} members from the checksum-pinned P2Rank 2.5.1 release "
                    f"archive; rebuilt runtime chunks {state} the frozen lock. Retained {len(self.receipt['assets'])} "
                    'checksum-pinned 3Dmol.js and RCSB files. Infrastructure artifacts only; no protein or pocket result.'}}
