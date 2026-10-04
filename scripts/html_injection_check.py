"""Forensic check: does removing the injected Cloudflare analytics beacon restore the declared HTML digest?"""
import hashlib, json, re, sys
from pathlib import Path


def check(path, size, sha256):
    raw = Path(path).read_bytes()
    match = re.search(rb'<script[^>]*cloudflareinsights[^>]*>\s*</script>\n', raw)
    stripped = raw.replace(match.group(0), b'', 1) if match else raw
    return {'downloaded_size': len(raw), 'declared_size': size, 'injected_bytes': len(match.group(0)) if match else 0,
            'injection': 'Cloudflare Web Analytics beacon script' if match else None,
            'reconstructed_sha256': hashlib.sha256(stripped).hexdigest(),
            'matches_declared_after_removal': len(stripped) == size and hashlib.sha256(stripped).hexdigest() == sha256,
            'scope': 'Forensic reconstruction only; the transformed transfer itself still fails its declared digest'}


if __name__ == '__main__':
    out = Path(sys.argv[1])
    items = json.loads(sys.argv[2])
    record = {name: check(out.parent / name, size, sha) for name, (size, sha) in items.items()}
    out.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: (v['injected_bytes'], v['matches_declared_after_removal']) for k, v in record.items()}))
