"""Acquire the pinned P2Rank 2.5.1 distribution once and rebuild byte-identical stored runtime chunks."""
import hashlib
import json
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from biosim import BioModule, ExecutionPolicy, SignalSpec

PLAN = json.loads(Path(__file__).with_name('chunk-plan.json').read_text())


def download(destination):
    digest = hashlib.sha256()
    size = 0
    request = urllib.request.Request(PLAN['source_url'], headers={'User-Agent': 'biosimulant-p2rank-runtime-preparation'})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open('wb') as out:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > PLAN['source_size_bytes']:
                raise ValueError('Distribution larger than pinned size')
            digest.update(chunk)
            out.write(chunk)
    if size != PLAN['source_size_bytes'] or digest.hexdigest() != PLAN['source_sha256']:
        raise ValueError('P2Rank distribution integrity mismatch')


def build(root):
    work = Path(tempfile.mkdtemp(prefix='p2rank-acquire-'))
    archive = work / 'p2rank_2.5.1.tar.gz'
    download(archive)
    wanted = {m['path']: m for c in PLAN['chunks'] for m in c['members']}
    contents = {}
    with tarfile.open(archive, 'r:gz') as tar:
        for info in tar:
            if not info.isfile() or not info.name.startswith(PLAN['tar_prefix']):
                continue
            rel = info.name[len(PLAN['tar_prefix']):]
            if rel in wanted:
                raw = tar.extractfile(info).read()
                if len(raw) != wanted[rel]['size_bytes'] or hashlib.sha256(raw).hexdigest() != wanted[rel]['sha256']:
                    raise ValueError(f'Distribution member mismatch: {rel}')
                contents[rel] = raw
    if set(contents) != set(wanted):
        raise ValueError('Distribution members missing')
    archive.unlink()
    outputs = []
    for chunk in PLAN['chunks']:
        target = root / chunk['path']
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as z:
            for member in chunk['members']:
                info = zipfile.ZipInfo(member['path'], date_time=tuple(PLAN['zip_date_time']))
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = PLAN['external_attr']
                z.writestr(info, contents[member['path']])
        raw = target.read_bytes()
        record = {'path': chunk['path'], 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                  'expected_size_bytes': chunk['size_bytes'], 'expected_sha256': chunk['sha256']}
        record['matches_frozen_lock'] = record['size_bytes'] == chunk['size_bytes'] and record['sha256'] == chunk['sha256']
        outputs.append(record)
    return {'source_url': PLAN['source_url'], 'source_sha256': PLAN['source_sha256'], 'source_size_bytes': PLAN['source_size_bytes'],
            'members_verified': len(contents), 'chunks': outputs,
            'all_chunks_match': all(o['matches_frozen_lock'] for o in outputs)}


class AcquireRuntime(BioModule):
    execution_policy = ExecutionPolicy.ONCE_BEFORE_RUN

    def __init__(self):
        self.receipt = None

    def outputs(self):
        return {'runtime_0': SignalSpec.scalar(dtype='str', value_type='file', format='zip'),
                'runtime_1': SignalSpec.scalar(dtype='str', value_type='file', format='zip'),
                'receipt': SignalSpec.record(schema={'source_url': 'str', 'source_sha256': 'str', 'source_size_bytes': 'int',
                                                     'members_verified': 'int', 'chunks': 'json', 'all_chunks_match': 'bool'},
                                             emitted_unit='1')}

    def execute(self, inputs, *, context):
        root = Path.cwd() / 'outputs'
        root.mkdir(exist_ok=True)
        self.receipt = build(root)
        return {'runtime_0': str((root / PLAN['chunks'][0]['path']).resolve()),
                'runtime_1': str((root / PLAN['chunks'][1]['path']).resolve()), 'receipt': self.receipt}

    def visualize(self):
        if not self.receipt:
            return []
        state = 'match' if self.receipt['all_chunks_match'] else 'DO NOT match'
        return {'schema_version': '1', 'render': 'text', 'data': {
            'text': f"Verified {self.receipt['members_verified']} P2Rank 2.5.1 distribution members against the pinned "
                    f"archive checksum; rebuilt runtime chunks {state} the frozen lock. Infrastructure artifact only; "
                    'no protein or pocket result.'}}
