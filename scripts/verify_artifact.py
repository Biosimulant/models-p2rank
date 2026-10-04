"""Download one managed-run artifact through its short-lived owner link and verify size/SHA-256.

Usage: verify_artifact.py DEST DECLARED_SIZE DECLARED_SHA256 ARTIFACT_ID < link.txt
The link is read from stdin so it never appears in shell history or retained files.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

dest, size, sha256, artifact_id = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
link = sys.stdin.read().strip()
request = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0 (biosimulant-verification)'})
with urllib.request.urlopen(request, timeout=120) as response:
    raw = response.read(size + 1024 * 1024)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_bytes(raw)
record = {'artifact_id': artifact_id, 'declared_size_bytes': size, 'actual_size_bytes': len(raw),
          'declared_sha256': sha256, 'actual_sha256': hashlib.sha256(raw).hexdigest()}
record['verified'] = record['actual_size_bytes'] == size and record['actual_sha256'] == sha256
dest.with_name(dest.name + '.verification.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
