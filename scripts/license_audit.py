#!/usr/bin/env python3
"""Per-jar third-party license audit for the P2Rank 2.5.1 binary distribution.

Engineering provenance record only; this is not legal advice or clearance.

For every jar under sources/p2rank_2.5.1/bin (p2rank.jar + bin/lib/*.jar):
  * hash it (sha256, sha1, size),
  * determine Maven coordinates (in-jar pom.properties > Maven Central SHA-1
    search > curated upstream evidence > filename heuristic),
  * verify whether the bytes are identical to the Maven Central artifact,
  * collect licenses from the POM (+ parents, up to 5 levels), the MANIFEST
    Bundle-License header and bundled LICENSE/NOTICE/COPYING files,
  * classify (permissive / weak-copyleft / strong-copyleft / unknown),
  * for copyleft jars, fetch exact corresponding source (Maven Central
    -sources.jar for the identical artifact, or the upstream git commit
    tarball) into sources/corresponding-sources/.

Writes labs/binding-pockets/sources/license-audit.json.

stdlib only. Network: search.maven.org, repo1.maven.org, api.github.com,
raw.githubusercontent.com (and codeload.github.com, the redirect target of
api.github.com tarball downloads). Set GITHUB_TOKEN to raise API limits.
HTTP responses are cached in outputs/license-audit-cache/ (git-ignored).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "sources" / "p2rank_2.5.1" / "bin"
LAB_SOURCES = ROOT / "labs" / "binding-pockets" / "sources"
NOTICES_DIR = LAB_SOURCES / "jar-notices"
OUT_JSON = LAB_SOURCES / "license-audit.json"
CORR_DIR = ROOT / "sources" / "corresponding-sources"
CACHE_DIR = ROOT / "outputs" / "license-audit-cache"

CENTRAL = "https://repo1.maven.org/maven2"
SEARCH = "https://search.maven.org/solrsearch/select"
ALLOWED_HOSTS = {
    "search.maven.org",
    "repo1.maven.org",
    "api.github.com",
    "raw.githubusercontent.com",
    "codeload.github.com",  # redirect target of api.github.com/.../tarball/<sha>
}
MAX_DOWNLOAD = 60 * 1024 * 1024

P2RANK_COMMIT = "9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e"
P2RANK_RAW = f"https://raw.githubusercontent.com/rdk/p2rank/{P2RANK_COMMIT}"

# Jars that are not (identically) on Maven Central. Each entry lists the
# targeted evidence that was located manually (GitHub API) and is re-fetched
# and hashed on every run. `byte_match` URLs are expected to return bytes
# identical to the shipped jar (sha256 compared at runtime).
CURATED = {
    "p2rank.jar": {
        "coordinates": f"github:rdk/p2rank@{P2RANK_COMMIT} (P2Rank 2.5.1 main jar)",
        "license_urls": [f"{P2RANK_RAW}/LICENSE.txt"],
        "source_tarball": None,  # MIT; source location recorded, not retained
        "source_location": f"https://github.com/rdk/p2rank/tree/{P2RANK_COMMIT}",
        "notes": "Built from the P2Rank source commit; no Maven artifact.",
    },
    "FastRandomForest_0.99.jar": {
        "coordinates": "FastRandomForest 0.99 (Fran Supek; code.google.com/archive/p/fast-random-forest), vendored at rdk/p2rank lib/",
        "byte_match": [f"{P2RANK_RAW}/lib/FastRandomForest_0.99.jar"],
        "license_urls": [],
        "source_location": "bin/lib/FastRandomForest_0.99_src.jar (shipped in the same distribution); also "
        f"{P2RANK_RAW}/lib/FastRandomForest_0.99_src.jar",
        "shipped_source": "FastRandomForest_0.99_src.jar",
        "notes": "No Maven artifact. Upstream lib/readme.txt names Fran Supek's Google Code project.",
        "extra_evidence": [f"{P2RANK_RAW}/lib/readme.txt"],
    },
    "FastRandomForest_0.99_src.jar": {
        "coordinates": "FastRandomForest 0.99 source jar, vendored at rdk/p2rank lib/",
        "byte_match": [f"{P2RANK_RAW}/lib/FastRandomForest_0.99_src.jar"],
        "license_urls": [],
        "shipped_source": "FastRandomForest_0.99_src.jar",
        "source_location": "this jar is itself the source archive",
        "notes": "Source archive shipped by P2Rank alongside FastRandomForest_0.99.jar.",
    },
    "FasterForest-2.5.2.jar": {
        "coordinates": "github:rdk/FasterForest@2.5.2 (246546ac8c184c16dc2f432e8d1d5256776e0b7d)",
        "byte_match": [f"{P2RANK_RAW}/lib/FasterForest-2.5.2.jar"],
        "license_urls": [
            "https://raw.githubusercontent.com/rdk/FasterForest/246546ac8c184c16dc2f432e8d1d5256776e0b7d/LICENSE.txt",
        ],
        "extra_evidence": [
            "https://raw.githubusercontent.com/rdk/FasterForest/246546ac8c184c16dc2f432e8d1d5256776e0b7d/README.md",
        ],
        "source_tarball": ("rdk/FasterForest", "246546ac8c184c16dc2f432e8d1d5256776e0b7d", "FasterForest-2.5.2"),
        "notes": "No Maven artifact; README at tag 2.5.2 states GPL v2 or (at your option) any later version. "
        "Tag commit 2024-09-27T19:49Z; jar entries dated 2024-09-27 21:41 (local time). Jar not rebuilt to verify reproducibility.",
    },
    "faster-molecular-surface-1.0.jar": {
        "coordinates": "cz.cuni.cusbg:faster-molecular-surface:1.0 (P2Rank local-mvn-repo; github:rdk/FasterMolecularSurface@1.0 207cc34debc41f50bab1d879d08da88da9309763)",
        "byte_match": [
            f"{P2RANK_RAW}/lib/local-mvn-repo/cz/cuni/cusbg/faster-molecular-surface/1.0/faster-molecular-surface-1.0.jar"
        ],
        "license_urls": [
            "https://raw.githubusercontent.com/rdk/FasterMolecularSurface/207cc34debc41f50bab1d879d08da88da9309763/LICENSE",
        ],
        "extra_evidence": [
            f"{P2RANK_RAW}/lib/local-mvn-repo/cz/cuni/cusbg/faster-molecular-surface/1.0/faster-molecular-surface-1.0.pom",
        ],
        "source_tarball": ("rdk/FasterMolecularSurface", "207cc34debc41f50bab1d879d08da88da9309763", "FasterMolecularSurface-1.0"),
        "notes": "Not on Maven Central (local-mvn-repo POM has no <licenses>). License taken from LICENSE at upstream tag 1.0. "
        "Tag commit 2024-08-02T18:38Z; jar entries dated 2024-08-02 18:52 (local time). Not rebuilt to verify reproducibility.",
    },
    "openchart-1.4.2.jar": {
        "coordinates": "openchart:openchart:1.4.2 (JBoss thirdparty-releases repository, declared as a dependency by org.biojava.thirdparty:forester:1.039)",
        "license_urls": [],
        "method": "dependency declaration in forester-1.039 POM (bytes not hash-verified)",
        "extra_evidence": [f"{CENTRAL}/org/biojava/thirdparty/forester/1.039/forester-1.039.pom"],
        "source_location": "Upstream OpenChart project (approximatrix, SourceForge); artifact hosted at "
        "https://repository.jboss.org/nexus/content/repositories/thirdparty-releases/openchart/openchart/1.4.2/ (host outside the audit allowlist, not fetched)",
        "notes": "Not on Maven Central (SHA-1 and a:openchart searches empty). Coordinates from the forester-1.039 POM, which says the JBoss "
        "repository is needed for openchart; P2Rank build.gradle also declares that repository. Jar bytes NOT verified against the JBoss copy. "
        "License from the LGPL-2.1 text bundled at the jar root.",
    },
    "biojava-structure-7.2.2-rdk.1.jar": {
        "coordinates": "org.biojava:biojava-structure:7.2.2-rdk.1 (fork; P2Rank local-mvn-repo; github:rdk/biojava branch updated-cif-parsing-bug-7.2.2 @ 49c633adae29f9fea58395b4c896e478b677e899)",
        "byte_match": [
            f"{P2RANK_RAW}/lib/local-mvn-repo/org/biojava/biojava-structure/7.2.2-rdk.1/biojava-structure-7.2.2-rdk.1.jar"
        ],
        "pom_url": f"{P2RANK_RAW}/lib/local-mvn-repo/org/biojava/biojava-structure/7.2.2-rdk.1/biojava-structure-7.2.2-rdk.1.pom",
        "license_urls": [
            "https://raw.githubusercontent.com/rdk/biojava/49c633adae29f9fea58395b4c896e478b677e899/LICENSE",
        ],
        "extra_evidence": [
            "https://raw.githubusercontent.com/rdk/biojava/49c633adae29f9fea58395b4c896e478b677e899/biojava-structure/pom.xml",
        ],
        "source_tarball": ("rdk/biojava", "49c633adae29f9fea58395b4c896e478b677e899", "biojava-7.2.2-rdk.1"),
        "notes": "Modified BioJava fork (not on Maven Central). Source = head of rdk/biojava branch updated-cif-parsing-bug-7.2.2 "
        "(commit 49c633a 'update version in pom', 2025-08-07T16:39Z), whose biojava-structure/pom.xml declares 7.2.2-rdk.1; "
        "jar entries dated 2025-08-07 18:37 (local time). No release tag exists; not rebuilt to verify byte reproducibility.",
    },
}

# Upstream LICENSE files at the exact release commit, used when the Central
# POM has no <licenses> or an unversioned one and source headers are silent.
SUPPLEMENTAL_LICENSE = {
    "multiverse-core-0.7.0.jar": {
        "url": "https://raw.githubusercontent.com/pveentjer/Multiverse/4b41a46a627dd7b4a3dcf8fbf4db5d0a4df84bb4/LICENSE",
        "why": "tag multiverse-0.7.0 (commit 4b41a46, '[maven-release-plugin] prepare release multiverse-0.7.0')",
    },
    "jniloader-1.1.jar": {
        "url": "https://raw.githubusercontent.com/fommil/jniloader/d9c4eb7c554138d1f20392b07bd471a7b0c19c77/LICENSE",
        "why": "commit d9c4eb7 '[maven-release-plugin] prepare release jniloader-1.1'",
    },
}

# ----------------------------------------------------------------- helpers

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def file_hashes(p: Path) -> tuple[str, str, int]:
    h256, h1 = hashlib.sha256(), hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h256.update(chunk)
            h1.update(chunk)
    return h256.hexdigest(), h1.hexdigest(), p.stat().st_size


class Net:
    def __init__(self, offline: bool = False):
        self.offline = offline
        self.token = os.environ.get("GITHUB_TOKEN")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _check(self, url: str):
        host = urllib.parse.urlparse(url).hostname
        if host not in ALLOWED_HOSTS:
            raise RuntimeError(f"host not allowed: {host}")

    def _req(self, url: str, method: str = "GET"):
        self._check(url)
        headers = {"User-Agent": "p2rank-license-audit/1.0 (stdlib urllib)"}
        if self.token and urllib.parse.urlparse(url).hostname == "api.github.com":
            headers["Authorization"] = f"Bearer {self.token}"
        return urllib.request.Request(url, headers=headers, method=method)

    def get(self, url: str, max_bytes: int = 8 * 1024 * 1024) -> bytes | None:
        """GET with on-disk cache. Returns None on 404."""
        key = CACHE_DIR / hashlib.sha1(url.encode()).hexdigest()
        if key.exists():
            data = key.read_bytes()
            return None if data == b"__404__" else data
        if self.offline:
            return None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(self._req(url), timeout=60) as r:
                    self._check(r.geturl())
                    data = r.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise RuntimeError(f"response too large: {url}")
                key.write_bytes(data)
                return data
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    key.write_bytes(b"__404__")
                    return None
                if e.code in (403, 429, 500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                if attempt < 3:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        return None

    def download(self, url: str, dest: Path) -> dict:
        """Stream to dest, abort above MAX_DOWNLOAD. Returns record dict."""
        if dest.exists():
            s256, _, size = file_hashes(dest)
            return {"status": "ok", "final_url": url, "sha256": s256, "size_bytes": size, "cached": True}
        if self.offline:
            return {"status": "skipped", "reason": "offline"}
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            with urllib.request.urlopen(self._req(url), timeout=300) as r:
                final = r.geturl()
                self._check(final)
                cl = r.headers.get("Content-Length")
                if cl and int(cl) > MAX_DOWNLOAD:
                    return {"status": "skipped", "reason": f"Content-Length {cl} > 60 MB", "final_url": final,
                            "size_bytes": int(cl)}
                h = hashlib.sha256()
                n = 0
                with open(tmp, "wb") as f:
                    for chunk in iter(lambda: r.read(1 << 20), b""):
                        n += len(chunk)
                        if n > MAX_DOWNLOAD:
                            f.close()
                            tmp.unlink(missing_ok=True)
                            return {"status": "skipped", "reason": "stream exceeded 60 MB; aborted", "final_url": final}
                        h.update(chunk)
                        f.write(chunk)
            tmp.rename(dest)
            return {"status": "ok", "final_url": final, "sha256": h.hexdigest(), "size_bytes": n, "cached": False}
        except urllib.error.HTTPError as e:
            tmp.unlink(missing_ok=True)
            return {"status": "error", "reason": f"HTTP {e.code}"}


# ----------------------------------------------------------- license logic

RANK = {"permissive": 0, "weak-copyleft": 1, "strong-copyleft": 2, "unknown": 3}

SPDX_CLASS = {
    "Apache-2.0": "permissive", "Apache-1.1": "permissive", "MIT": "permissive",
    "BSD-2-Clause": "permissive", "BSD-3-Clause": "permissive", "BSD (variant unspecified)": "permissive",
    "0BSD": "permissive", "EDL-1.0 (BSD-3-Clause)": "permissive", "Public-Domain": "permissive",
    "CC0-1.0": "permissive", "Unlicense": "permissive", "HPND-like (CUP license)": "permissive",
    "LGPL-2.1": "weak-copyleft", "LGPL-2.1-or-later": "weak-copyleft", "LGPL-3.0": "weak-copyleft",
    "LGPL-3.0-or-later": "weak-copyleft", "LGPL (version unspecified)": "weak-copyleft",
    "EPL-1.0": "weak-copyleft", "EPL-2.0": "weak-copyleft", "MPL-1.1": "weak-copyleft", "MPL-2.0": "weak-copyleft",
    "CDDL-1.0": "weak-copyleft", "CDDL-1.1": "weak-copyleft",
    "GPL-2.0": "strong-copyleft", "GPL-2.0-or-later": "strong-copyleft", "GPL-3.0": "strong-copyleft",
    "GPL-3.0-or-later": "strong-copyleft", "GPL-2.0-with-classpath-exception": "strong-copyleft",
    "GPL (version unspecified)": "strong-copyleft", "AGPL-3.0": "strong-copyleft",
}
PROBLEM_PATTERNS = re.compile(r"non-?commercial|affero|agpl|proprietary|evaluation only|binary code license|"
                              r"licenses restricting its use|without prior written authori[sz]ation", re.I)


def normalize(name: str | None, url: str | None) -> str:
    s = f"{name or ''} | {url or ''}".lower()
    if "cup parser generator" in s:
        return "HPND-like (CUP license)"
    if re.search(r"affero|agpl", s):
        return "AGPL-3.0"
    if re.search(r"eclipse distribution|edl-v10|\bedl\b", s):
        return "EDL-1.0 (BSD-3-Clause)"
    if re.search(r"lgpl|lesser general public|library general public", s):
        if re.search(r"2\.1|v2|version 2|lgpl-2|old-licenses", s):
            return "LGPL-2.1"
        if re.search(r"3\.0|v3|version 3|lgpl-3", s):
            return "LGPL-3.0"
        return "LGPL (version unspecified)"
    if re.search(r"classpath", s) and re.search(r"gpl|general public", s):
        return "GPL-2.0-with-classpath-exception"
    if re.search(r"\bgpl|general public licen", s):
        if re.search(r"3\.0|v3|version 3|gpl-3", s):
            return "GPL-3.0"
        if re.search(r"2\.0|v2|version 2|gpl-2", s):
            return "GPL-2.0"
        return "GPL (version unspecified)"
    if re.search(r"common development and distribution|cddl", s):
        return "CDDL-1.1" if "1.1" in s else "CDDL-1.0"
    if re.search(r"eclipse public|\bepl", s):
        return "EPL-2.0" if re.search(r"2\.0|v20|epl-2", s) else "EPL-1.0"
    if re.search(r"mozilla|\bmpl", s):
        return "MPL-1.1" if "1.1" in s else "MPL-2.0"
    if re.search(r"apache", s):
        return "Apache-1.1" if re.search(r"1\.1", s) and "2.0" not in s else "Apache-2.0"
    if re.search(r"\b0bsd|zero-clause|zero clause", s):
        return "0BSD"
    if re.search(r"bsd", s):
        if re.search(r"2-clause|2 clause|simplified|bsd-2", s):
            return "BSD-2-Clause"
        if re.search(r"3-clause|3 clause|new bsd|revised|bsd-3|modified bsd", s):
            return "BSD-3-Clause"
        return "BSD (variant unspecified)"
    if re.search(r"\bmit\b|/mit\b|mit license|license/mit", s):
        return "MIT"
    if re.search(r"cc0|creativecommons.org/publicdomain/zero", s):
        return "CC0-1.0"
    if re.search(r"public domain", s):
        return "Public-Domain"
    if re.search(r"unlicense", s):
        return "Unlicense"
    return "UNKNOWN"


def detect_text(text: str) -> str:
    t = text[:6000]
    tl = t.lower()
    if re.search(r"licenses restricting its use|without prior written authori[sz]ation of sun", tl):
        return "LicenseRef-Sun-restrictive-notice"
    head = re.sub(r"\s+", " ", tl[:400])
    if "gnu general public license" in head and "lesser" not in head and "library" not in head:
        cpe = "classpath" in text.lower()
        if "version 3" in head:
            return "GPL-3.0"
        if "version 2" in head:
            return "GPL-2.0-with-classpath-exception" if cpe else "GPL-2.0"
    if "gnu affero general public license" in tl:
        return "AGPL-3.0"
    if "gnu lesser general public license" in tl or "gnu library general public license" in tl:
        if re.search(r"version 3", tl):
            return "LGPL-3.0"
        if re.search(r"version 2\.1", tl):
            return "LGPL-2.1"
        return "LGPL (version unspecified)"
    if "gnu general public license" in tl:
        cpe = "classpath exception" in text.lower()
        if re.search(r"version 3, 29 june 2007", tl):
            return "GPL-3.0"
        if re.search(r"version 2, june 1991", tl):
            return "GPL-2.0-with-classpath-exception" if cpe else "GPL-2.0"
    if "eclipse distribution license" in tl:
        return "EDL-1.0 (BSD-3-Clause)"
    if "eclipse public license" in tl:
        return "EPL-2.0" if "version 2.0" in tl or "v 2.0" in tl else "EPL-1.0"
    if "mozilla public license" in tl:
        return "MPL-2.0" if "version 2.0" in tl else "MPL-1.1"
    if "common development and distribution license" in tl:
        return "CDDL-1.1" if "1.1" in tl else "CDDL-1.0"
    if "apache license" in tl and "version 2.0" in tl:
        return "Apache-2.0"
    if "permission is hereby granted, free of charge" in tl:
        return "MIT"
    if "redistribution and use in source and binary forms" in tl:
        return "BSD-3-Clause" if ("neither the name" in tl or "may not be used to endorse" in tl) else "BSD-2-Clause"
    if "permission to use, copy, modify, and/or distribute this software for any" in tl:
        return "0BSD"
    if "public domain" in tl:
        return "Public-Domain"
    return "UNKNOWN"


# --------------------------------------------------------------- POM logic

NS = re.compile(r"\{.*?\}")


def strip_ns(root: ET.Element) -> ET.Element:
    for el in root.iter():
        el.tag = NS.sub("", el.tag)
    return root


def parse_pom(data: bytes) -> ET.Element | None:
    try:
        return strip_ns(ET.fromstring(data))
    except ET.ParseError:
        # some old POMs have undeclared entities / junk; strip DOCTYPE and retry
        txt = re.sub(rb"<!DOCTYPE[^>]*>", b"", data)
        try:
            return strip_ns(ET.fromstring(txt))
        except ET.ParseError:
            return None


def pom_url(g: str, a: str, v: str) -> str:
    return f"{CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{a}-{v}.pom"


def licenses_from_pom(net: Net, g: str, a: str, v: str, first_url: str | None = None):
    """Walk POM + parents (max 5 parent levels). Returns (licenses, evidence, trail)."""
    evidence, trail = [], []
    url = first_url or pom_url(g, a, v)
    for depth in range(6):
        data = net.get(url)
        if data is None:
            trail.append(f"404 {url}")
            break
        evidence.append({"url": url, "sha256": sha256_bytes(data), "kind": "pom" if depth == 0 else f"parent-pom-{depth}"})
        root = parse_pom(data)
        if root is None:
            trail.append(f"unparseable {url}")
            break
        lics = []
        for lic in root.findall("./licenses/license"):
            lics.append({"name": (lic.findtext("name") or "").strip(), "url": (lic.findtext("url") or "").strip() or None})
        if lics:
            trail.append(f"licenses found at depth {depth}: {url}")
            return lics, evidence, trail
        par = root.find("./parent")
        if par is None:
            trail.append(f"no <licenses> and no <parent> at {url}")
            break
        pg, pa, pv = (par.findtext(x, "").strip() for x in ("groupId", "artifactId", "version"))
        if not (pg and pa and pv):
            break
        url = pom_url(pg, pa, pv)
    return [], evidence, trail


# ----------------------------------------------------------- jar inspection

# Applied to full in-jar notice texts; deliberately narrower than PROBLEM_PATTERNS
# because e.g. the GPL text itself mentions "proprietary programs".
TEXT_PROBLEM_PATTERNS = re.compile(r"non-?commercial use only|licenses restricting its use|"
                                   r"without prior written authori[sz]ation of sun|evaluation only", re.I)
NOTICE_RE = re.compile(r"(^|/)(LICEN[CS]E|NOTICE|COPYING|LEGAL)[^/]*$", re.I)


def inspect_jar(path: Path, jar_name: str):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    props = []
    for n in names:
        if re.match(r"META-INF/maven/[^/]+/[^/]+/pom\.properties$", n):
            d = {}
            for line in z.read(n).decode("utf-8", "replace").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    d[k.strip()] = v.strip()
            if {"groupId", "artifactId", "version"} <= d.keys():
                props.append((n, d))
    manifest = z.read("META-INF/MANIFEST.MF").decode("utf-8", "replace") if "META-INF/MANIFEST.MF" in names else ""
    manifest = re.sub(r"\r?\n ", "", manifest)
    bl = re.search(r"^Bundle-License:\s*(.+)$", manifest, re.M)
    notices = []
    for n in names:
        if n.endswith("/") or n.endswith(".class"):
            continue
        if NOTICE_RE.search(n):
            data = z.read(n)
            text = data.decode("utf-8", "replace")
            local = NOTICES_DIR / jar_name / n.replace("/", "__")
            notices.append({
                "path": f"{jar_name}!/{n}",
                "sha256": sha256_bytes(data),
                "detected": detect_text(text) if re.search(r"licen[cs]e|copying|legal", n, re.I) else None,
                "restrictive": bool(TEXT_PROBLEM_PATTERNS.search(text[:20000])),
                "extracted_copy": str(local.relative_to(ROOT)) if local.exists() else None,
            })
    return {"names": names, "pom_properties": props, "bundle_license": bl.group(1).strip() if bl else None,
            "notices": notices, "manifest": manifest}


def pick_props(props, jar_name):
    if not props:
        return None
    stem = jar_name[:-4]
    for n, d in props:
        if stem.startswith(f"{d['artifactId']}-{d['version']}") or stem == f"{d['artifactId']}-{d['version']}":
            return n, d
    return props[0] if len(props) == 1 else None


def bundle_license_entries(bl: str):
    out = []
    # e.g. "Apache-2.0";link="..."  or  http://...  or  a, b
    for part in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", bl):
        part = part.strip()
        m = re.match(r'"?([^";]+)"?(?:;.*?link="?([^";]+)"?)?', part)
        if not m:
            continue
        name, link = m.group(1).strip(), m.group(2)
        if name.startswith("http"):
            out.append({"name": None, "url": name})
        else:
            out.append({"name": name, "url": link})
    return out


# ------------------------------------------------------------------- main

def central_sha1_search(net: Net, sha1: str):
    data = net.get(f"{SEARCH}?q=1:{sha1}&wt=json")
    if not data:
        return None, None
    docs = json.loads(data).get("response", {}).get("docs", [])
    return (docs[0] if docs else None), f"{SEARCH}?q=1:{sha1}&wt=json"


def central_sha1_of(net: Net, g, a, v, classifier=None):
    fn = f"{a}-{v}{'-' + classifier if classifier else ''}.jar"
    d = net.get(f"{CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{fn}.sha1")
    return d.decode().strip().split()[0].lower() if d else None


_GRADLE = None


def gradle_coords():
    """jar filename -> (g, a, v) for direct dependencies declared in sources/build.gradle."""
    global _GRADLE
    if _GRADLE is None:
        _GRADLE = {}
        txt = (ROOT / "sources" / "build.gradle").read_text()
        for g, a, v in re.findall(r"^\s*implementation\s+'([^':]+):([^':]+):([^':]+)'", txt, re.M):
            _GRADLE[f"{a}-{v}.jar"] = (g, a, v)
    return _GRADLE


HEADER_PATTERNS = [
    ("LGPL-2.1", r"lesser general public license.{0,200}?version 2\.1|lgpl.{0,10}2\.1"),
    ("LGPL-3.0", r"lesser general public license.{0,200}?version 3"),
    ("LGPL (version unspecified)", r"lesser general public license|library general public license"),
    ("GPL-3.0", r"general public license.{0,200}?version 3"),
    ("GPL-2.0", r"general public license.{0,200}?version 2"),
    ("CC0-1.0", r"creativecommons\.org/publicdomain/zero"),
    ("Public-Domain", r"released to the public domain|placed in the public domain|public domain"),
    ("Apache-2.0", r"apache license,? version 2\.0|www\.apache\.org/licenses/license-2\.0"),
    ("MIT", r"permission is hereby granted, free of charge"),
    ("BSD (variant unspecified)", r"redistribution and use in source and binary forms"),
]


def scan_sources_jar(net: "Net", g, a, v):
    """Scan leading comment blocks of .java files in the Central -sources.jar.
    Returns (result_spdx|None, detail dict) ; detail carries url/sha256/counts/sample."""
    url = f"{CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{a}-{v}-sources.jar"
    data = net.get(url, max_bytes=MAX_DOWNLOAD)
    if data is None:
        return None, {"url": url, "status": "404"}
    z = zipfile.ZipFile(io.BytesIO(data))
    counts, sample, n = {}, {}, 0
    for name in z.namelist():
        if not name.endswith(".java"):
            continue
        n += 1
        head = z.read(name)[:4000].decode("utf-8", "replace")
        m = re.match(r"\s*(/\*.*?\*/)", head, re.S)
        block = (m.group(1) if m else head[:1500]).lower()
        block = re.sub(r"\s+", " ", re.sub(r"(?m)^\s*(//+|/?\*+/?)", " ", block))
        hit = None
        for spdx, pat in HEADER_PATTERNS:
            if re.search(pat, block, re.S):
                hit = spdx
                break
        hit = hit or "no-license-header"
        counts[hit] = counts.get(hit, 0) + 1
        sample.setdefault(hit, name)
    lic = [k for k in counts if k != "no-license-header"]
    best = max(lic, key=lambda k: counts[k]) if lic else None
    return best, {"url": url, "sha256": sha256_bytes(data), "java_files": n, "header_counts": counts, "sample_files": sample}


def filename_guess(jar_name: str):
    m = re.match(r"(.+?)-(\d[\w.\-]*?)(?:-(natives))?\.jar$", jar_name)
    return (m.group(1), m.group(2)) if m else (jar_name[:-4], None)


def audit_jar(net: Net, path: Path, download: bool):
    jar = path.name
    sha256, sha1, size = file_hashes(path)
    info = inspect_jar(path, jar)
    rec = {"jar": str(path.relative_to(BIN.parent)), "sha256": sha256, "sha1": sha1, "size_bytes": size,
           "coordinates": None, "coordinate_method": None, "identical_to_maven_central": None,
           "licenses": [], "license_spdx": [], "license_source": None, "classification": "unknown",
           "evidence": [], "corresponding_source": None, "source_location": None,
           "status": "unresolved", "notes": [], "tried": []}
    g = a = v = classifier = None

    cur = CURATED.get(jar)
    picked = pick_props(info["pom_properties"], jar)
    if picked:
        n, d = picked
        g, a, v = d["groupId"], d["artifactId"], d["version"]
        rec["coordinate_method"] = "in-jar pom.properties"
        rec["evidence"].append({"path": f"{jar}!/{n}", "sha256": None, "kind": "pom.properties"})
        if "-natives" in jar:
            classifier = jar[len(f"{a}-{v}-"):-4] if jar.startswith(f"{a}-{v}-") else None
    else:
        rec["tried"].append("no usable META-INF/maven/*/*/pom.properties in jar")

    # Identity check against Maven Central. When pom.properties gives
    # coordinates, compare with the published .jar.sha1 (fast); otherwise (or
    # on mismatch) fall back to the SHA-1 search API (slow, ~30 s/query).
    if g:
        c_url = f"{CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{a}-{v}{'-' + classifier if classifier else ''}.jar.sha1"
        c_sha1 = central_sha1_of(net, g, a, v, classifier)
        if c_sha1 == sha1:
            rec["identical_to_maven_central"] = True
            rec["evidence"].append({"url": c_url, "sha256": None, "kind": "central-sha1-file-match", "sha1": c_sha1})
        elif c_sha1:
            rec["identical_to_maven_central"] = False
            rec["notes"].append(f"Central artifact {g}:{a}:{v} exists but its SHA-1 ({c_sha1}) differs from the shipped jar.")
        else:
            rec["tried"].append(f"no Central artifact at {c_url}")
    if not rec["identical_to_maven_central"]:
        doc, surl = central_sha1_search(net, sha1)
        if doc:
            if g and (g, a, v) != (doc["g"], doc["a"], doc["v"]):
                rec["notes"].append(f"In-jar pom.properties says {g}:{a}:{v} (not on Central under that name); "
                                    f"the identical bytes are published on Central as {doc['id']}.")
            g, a, v = doc["g"], doc["a"], doc["v"]
            rec["coordinate_method"] = "maven-central-sha1-search"
            rec["identical_to_maven_central"] = True
            rec["evidence"].append({"url": surl, "sha256": None, "kind": "maven-central-sha1-search-hit", "id": doc["id"]})
        else:
            rec["tried"].append(f"Maven Central SHA-1 search: no hit ({surl})")
            if rec["identical_to_maven_central"] is None:
                rec["identical_to_maven_central"] = False

    if cur:
        rec["coordinates"] = cur["coordinates"]
        if not rec["coordinate_method"] or rec["identical_to_maven_central"] is False:
            rec["coordinate_method"] = cur.get("method", "curated upstream evidence (GitHub)")
        for u in cur.get("byte_match", []):
            data = net.get(u, max_bytes=MAX_DOWNLOAD)
            ok = data is not None and sha256_bytes(data) == sha256
            rec["evidence"].append({"url": u, "sha256": sha256_bytes(data) if data else None,
                                    "kind": "upstream-repo-byte-match" if ok else "upstream-repo-byte-MISMATCH"})
            if ok:
                rec["coordinate_method"] = "upstream repo byte-identical copy (" + rec["coordinate_method"] + ")"
            else:
                rec["notes"].append(f"byte comparison against {u} FAILED")
        for u in cur.get("extra_evidence", []):
            data = net.get(u)
            rec["evidence"].append({"url": u, "sha256": sha256_bytes(data) if data else None, "kind": "supporting"})
        rec["notes"].append(cur["notes"])
        if cur.get("source_location"):
            rec["source_location"] = cur["source_location"]
    elif g:
        rec["coordinates"] = f"{g}:{a}:{v}" + (f":{classifier}" if classifier else "")
    elif jar in gradle_coords():
        g, a, v = gradle_coords()[jar]
        c_sha1 = central_sha1_of(net, g, a, v)
        c_url = f"{CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{a}-{v}.jar.sha1"
        rec["coordinates"] = f"{g}:{a}:{v}"
        rec["identical_to_maven_central"] = c_sha1 == sha1
        rec["coordinate_method"] = "P2Rank build.gradle declaration" + (" + Central .jar.sha1 match" if c_sha1 == sha1 else " (Central SHA-1 does NOT match)")
        rec["evidence"].append({"path": "sources/build.gradle", "sha256": sha256_bytes((ROOT / 'sources/build.gradle').read_bytes()), "kind": "dependency declaration"})
        if c_sha1 == sha1:
            rec["evidence"].append({"url": c_url, "sha256": None, "kind": "central-sha1-file-match", "sha1": c_sha1})
    else:
        name, ver = filename_guess(jar)
        rec["tried"].append(f"filename heuristic a={name} v={ver}")
        if ver:
            q = urllib.parse.quote(f'a:"{name}" AND v:"{ver}"')
            data = net.get(f"{SEARCH}?q={q}&wt=json&rows=5")
            docs = json.loads(data).get("response", {}).get("docs", []) if data else []
            if len(docs) == 1:
                g, a, v = docs[0]["g"], docs[0]["a"], docs[0]["v"]
                rec["coordinates"] = f"{g}:{a}:{v}"
                rec["coordinate_method"] = "filename-heuristic (Central a:/v: search, bytes NOT identical)"
                rec["identical_to_maven_central"] = False
            else:
                rec["tried"].append(f"Central a:/v: search returned {len(docs)} docs")

    # ---- licenses
    pom_lics = []
    if cur and cur.get("pom_url"):
        pom_lics, ev, trail = licenses_from_pom(net, g, a, v, first_url=cur["pom_url"])
        rec["evidence"] += ev
        rec["tried"] += trail
    elif g:
        pom_lics, ev, trail = licenses_from_pom(net, g, a, v)
        rec["evidence"] += ev
        rec["tried"] += trail
        if not ev and classifier:
            pass

    curated_lics = []
    if cur:
        for u in cur.get("license_urls", []):
            data = net.get(u)
            if data is None:
                rec["tried"].append(f"404 {u}")
                continue
            det = detect_text(data.decode("utf-8", "replace"))
            rec["evidence"].append({"url": u, "sha256": sha256_bytes(data), "kind": "license-text", "detected": det})
            curated_lics.append({"name": det, "url": u})

    bundle = bundle_license_entries(info["bundle_license"]) if info["bundle_license"] else []
    if info["bundle_license"]:
        rec["evidence"].append({"path": f"{jar}!/META-INF/MANIFEST.MF (Bundle-License)", "sha256": None,
                                "kind": "manifest", "value": info["bundle_license"]})
    for nt in info["notices"]:
        rec["evidence"].append({"path": nt["path"], "sha256": nt["sha256"], "kind": "in-jar notice",
                                "detected": nt["detected"], "extracted_copy": nt["extracted_copy"]})
    root_lic_texts = [nt for nt in info["notices"] if nt["detected"] and nt["detected"] != "UNKNOWN"
                      and (re.match(r"[^!]+!/(META-INF/)?(src/)?(LICEN[CS]E|COPYING)[^/]*$", nt["path"], re.I)
                           or nt["detected"].startswith("LicenseRef"))]

    if pom_lics:
        rec["licenses"], rec["license_source"] = pom_lics, "POM <licenses>"
    elif curated_lics:
        rec["licenses"], rec["license_source"] = curated_lics, "upstream LICENSE file at matching commit/tag"
    elif bundle:
        rec["licenses"], rec["license_source"] = bundle, "MANIFEST Bundle-License"
    elif root_lic_texts:
        rec["licenses"] = [{"name": nt["detected"], "url": None, "in_jar": nt["path"]} for nt in root_lic_texts[:1]]
        rec["license_source"] = "bundled LICENSE text in jar"

    spdx = []
    for lic in rec["licenses"]:
        nm = lic.get("name") or ""
        s = nm if (nm in SPDX_CLASS or nm.startswith("LicenseRef")) else normalize(lic.get("name"), lic.get("url"))
        spdx.append(s)
    # dual-licence strings such as "CDDL + GPLv2 with classpath exception"
    expanded = []
    for lic, sp in zip(rec["licenses"], spdx):
        txt = f"{lic.get('name')} {lic.get('url')}".lower()
        if re.search(r"cddl", txt) and re.search(r"gpl", txt):
            expanded += ["CDDL-1.1" if "1.1" in txt else "CDDL-1.0", "GPL-2.0-with-classpath-exception"]
            rec["notes"].append(f"License string '{lic.get('name')}' denotes a dual licence (CDDL or GPLv2+Classpath Exception).")
        else:
            expanded.append(sp)
    spdx = expanded

    # Source-header scan of the identical Central -sources.jar when the
    # licence is missing or its version is unspecified.
    if g and rec["identical_to_maven_central"] and (not spdx or any(x == "UNKNOWN" or "unspecified" in x for x in spdx)):
        best, detail = scan_sources_jar(net, g, a, v)
        rec["evidence"].append({"url": detail["url"], "sha256": detail.get("sha256"), "kind": "sources-jar header scan",
                                "detail": {k: detail[k] for k in ("java_files", "header_counts", "sample_files") if k in detail}})
        if best and not spdx:
            spdx = [best]
            rec["licenses"] = [{"name": best, "url": None, "evidence": f"source-file headers in {detail['url']}"}]
            rec["license_source"] = "source-file headers in identical Maven Central -sources.jar"
        elif best:
            for i, x in enumerate(spdx):
                if "unspecified" in x and SPDX_CLASS.get(best) == SPDX_CLASS.get(x) and "unspecified" not in best:
                    rec["notes"].append(f"POM licence '{x}' refined to {best} from source headers ({detail['header_counts']}).")
                    spdx[i] = best
        else:
            rec["tried"].append(f"sources-jar header scan found no licence statement ({detail})")
    sup = SUPPLEMENTAL_LICENSE.get(jar)
    if sup and (not spdx or any(x == "UNKNOWN" or "unspecified" in x for x in spdx)):
        data = net.get(sup["url"])
        det = detect_text(data.decode("utf-8", "replace")) if data else "UNKNOWN"
        rec["evidence"].append({"url": sup["url"], "sha256": sha256_bytes(data) if data else None, "kind": "upstream LICENSE at release commit",
                                "detected": det, "why": sup["why"]})
        if det != "UNKNOWN":
            if not spdx:
                spdx = [det]
                rec["licenses"] = [{"name": det, "url": sup["url"]}]
                rec["license_source"] = f"upstream LICENSE at release commit ({sup['why']})"
            else:
                for i, x in enumerate(spdx):
                    if "unspecified" in x and SPDX_CLASS.get(det) == SPDX_CLASS.get(x):
                        rec["notes"].append(f"POM licence '{x}' refined to {det} from upstream LICENSE at {sup['why']}.")
                        spdx[i] = det
    rec["license_spdx"] = spdx

    # cross-check with other sources
    others = set()
    for b in bundle:
        others.add(normalize(b.get("name"), b.get("url")))
    for nt in root_lic_texts:
        others.add(nt["detected"])
    for c in curated_lics:
        others.add(c["name"])
    others.discard("UNKNOWN")
    def fam(x):
        return {"EDL-1.0 (BSD-3-Clause)": "BSD", "BSD-3-Clause": "BSD", "BSD-2-Clause": "BSD", "BSD (variant unspecified)": "BSD"}.get(
            x, re.sub(r"[- ].*", "", x))
    if spdx and others and not {fam(o) for o in others} & {fam(x) for x in spdx}:
        rec["notes"].append(f"License sources disagree: primary={spdx}, other in-jar/manifest/upstream={sorted(others)}")

    # classification: Maven POM semantics -> multiple licenses are alternatives
    # ("If multiple licenses are listed, it is assumed that the user can select
    # any of them"), so take the least restrictive known option.
    classes = [SPDX_CLASS.get(s, "unknown") for s in spdx]
    known = [c for c in classes if c != "unknown"]
    if known:
        rec["classification"] = min(known, key=lambda c: RANK[c])
        if len(set(known)) > 1:
            rec["notes"].append(f"Multiple licenses listed {spdx}; treated as alternatives per Maven POM semantics; "
                                f"most restrictive option is {max(known, key=lambda c: RANK[c])}")
        rec["status"] = "resolved"
        unk = [x for x, c in zip(spdx, classes) if c == "unknown"]
        if unk:
            raw = [l.get("name") for l in rec["licenses"]]
            rec["notes"].append(f"Unrecognised additional licence entry {unk} (raw names {raw}); a recognised alternative exists, "
                                "so classification uses it per Maven POM semantics.")
    if any(PROBLEM_PATTERNS.search(f"{l.get('name')} {l.get('url')}") for l in rec["licenses"]) or \
            any(nt.get("restrictive") for nt in info["notices"]):
        bad = [nt["path"] for nt in info["notices"] if nt.get("restrictive")]
        rec["notes"].append(f"FLAG: restrictive/proprietary licensing language found {bad}; no redistribution grant located.")
        if "LicenseRef-Sun-restrictive-notice" in spdx:
            rec["classification"], rec["status"] = "unknown", "unresolved"

    if not rec["source_location"] and g:
        rec["source_location"] = f"{CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{a}-{v}-sources.jar (if published)"

    # ---- corresponding source for copyleft
    if rec["classification"] in ("weak-copyleft", "strong-copyleft"):
        rec["corresponding_source"] = corresponding_source(net, rec, jar, g, a, v, classifier, cur, download)

    if not rec["tried"]:
        del rec["tried"]
    rec["notes"] = " ".join(rec["notes"]) if rec["notes"] else ""
    return rec


def corresponding_source(net: Net, rec, jar, g, a, v, classifier, cur, download):
    CORR_DIR.mkdir(parents=True, exist_ok=True)
    if cur and cur.get("shipped_source"):
        p = BIN / "lib" / cur["shipped_source"]
        s256, _, size = file_hashes(p)
        return {"url": f"bin/lib/{cur['shipped_source']} (shipped inside the P2Rank 2.5.1 distribution); mirror {P2RANK_RAW}/lib/{cur['shipped_source']}",
                "sha256": s256, "size_bytes": size, "kind": "shipped-source-jar", "local_path": str(p.relative_to(ROOT))}
    if cur and cur.get("source_tarball"):
        repo, sha, stem = cur["source_tarball"]
        url = f"https://api.github.com/repos/{repo}/tarball/{sha}"
        dest = CORR_DIR / f"{stem}-{sha[:12]}.tar.gz"
        if not download:
            return {"url": url, "sha256": None, "size_bytes": None, "kind": "git-commit-tarball", "status": "not downloaded (--no-download)"}
        r = net.download(url, dest)
        out = {"url": url, "final_url": r.get("final_url"), "sha256": r.get("sha256"), "size_bytes": r.get("size_bytes"),
               "kind": "git-commit-tarball", "local_path": str(dest.relative_to(ROOT)) if r["status"] == "ok" else None}
        if r["status"] != "ok":
            out["status"] = f"{r['status']}: {r.get('reason')}"
        return out
    if g and rec["identical_to_maven_central"]:
        if classifier:  # native jars: source lives in the non-classifier sources jar
            pass
        fn = f"{a}-{v}-sources.jar"
        url = f"{CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{fn}"
        if not download:
            return {"url": url, "sha256": None, "size_bytes": None, "kind": "maven-central-sources-jar", "status": "not downloaded"}
        dest = CORR_DIR / fn
        r = net.download(url, dest)
        if r["status"] == "ok":
            return {"url": url, "sha256": r["sha256"], "size_bytes": r["size_bytes"], "kind": "maven-central-sources-jar",
                    "local_path": str(dest.relative_to(ROOT))}
        return {"url": url, "sha256": None, "size_bytes": r.get("size_bytes"), "kind": "maven-central-sources-jar",
                "status": f"{r['status']}: {r.get('reason')}"}
    return {"url": None, "sha256": None, "size_bytes": None, "status": "no exact source located"}


NOTICES_MD = ROOT / "labs" / "binding-pockets" / "THIRD_PARTY_NOTICES.md"

# Non-jar components shipped/used by the lab. Evidence verified manually on
# the audit date (see report); hashes are of the license text relied on.
OTHER_COMPONENTS = [
    {"name": "3Dmol.js", "version": "2.5.5", "license": "BSD-3-Clause",
     "evidence": "labs/binding-pockets/assets/LICENSE (sha256 4c6eaaed856f3f28a3b1a98e74f4a8a71618de7d51ea4155c29f6f793bcef861); "
                 "npm tarball https://registry.npmjs.org/3dmol/-/3dmol-2.5.5.tgz (sources/3dmol-2.5.5.tgz)",
     "source": "https://github.com/3dmol/3Dmol.js (npm 3dmol@2.5.5)",
     "notes": "Incorporates GLmol, Three.js and jQuery code; their notices are reproduced in assets/LICENSE."},
    {"name": "gemmi", "version": "0.7.3", "license": "MPL-2.0",
     "evidence": "https://raw.githubusercontent.com/project-gemmi/gemmi/v0.7.3/LICENSE.txt (sha256 fab3dd6bdab226f1c08630b1dd917e11fcb4ec5e1e020e2c16f83a0a13863e85); "
                 "PyPI gemmi 0.7.3 license=MPL-2.0, classifier 'Mozilla Public License 2.0 (MPL 2.0)'",
     "source": "https://github.com/project-gemmi/gemmi/tree/v0.7.3",
     "notes": "Weak copyleft (file-level). Source for the release is at tag v0.7.3; no copy is retained in this repository."},
    {"name": "jdk4py (bundled OpenJDK runtime)", "version": "21.0.8.1",
     "license": "GPL-2.0 WITH Classpath-exception-2.0",
     "evidence": "PyPI https://pypi.org/pypi/jdk4py/21.0.8.1/json: license and license_expression fields empty; classifier "
                 "'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'. Repository LICENSE "
                 "https://raw.githubusercontent.com/activeviam/jdk4py/main/LICENSE (sha256 4b9abebc4338048a7c2dc184e9f800deb349366bdf28eb23c2677a77b4c87726) "
                 "is byte-identical to https://raw.githubusercontent.com/openjdk/jdk21u/jdk-21.0.8-ga/LICENSE (GPLv2 + \"CLASSPATH\" EXCEPTION).",
     "source": "https://github.com/activeviam/jdk4py (wrapper; runtime built with jlink from Eclipse Temurin per .github/actions/build-java-runtime on main); "
               "OpenJDK 21 source: https://github.com/openjdk/jdk21u (tag jdk-21.0.8+9 / jdk-21.0.8-ga)",
     "notes": "No 21.0.8.1 release tag exists in the jdk4py repo; the build workflow and LICENSE were read from the default branch at audit time. "
              "The PyPI classifier alone says GPLv2; the Classpath Exception is evidenced by the OpenJDK LICENSE text the project ships."},
    {"name": "RCSB PDB fixtures 1CRN, 1STP, 7L13", "version": "mmCIF as downloaded (labs/binding-pockets/fixtures, sources/*.cif)",
     "license": "CC0-1.0",
     "evidence": "wwPDB usage policy https://www.wwpdb.org/about/usage-policies (PDB archive data are available under CC0 1.0)",
     "source": "https://www.rcsb.org/structure/1CRN, /1STP, /7L13",
     "notes": "Derived PDB/mapping files in fixtures/ are generated from these entries."},
]


def render_notices(data: dict) -> str:
    s, recs = data["summary"], data["jars"]
    def lic(r):
        return " OR ".join(r["license_spdx"]) if r["license_spdx"] else "UNRESOLVED"
    def src(r):
        cs = r.get("corresponding_source")
        if cs and cs.get("local_path"):
            return f"`{cs['local_path']}`"
        if cs and cs.get("url"):
            return cs["url"] + (f" ({cs.get('status')})" if cs.get("status") else "")
        return r.get("source_location") or ""
    L = []
    L.append("# Third-party notices: binding-pockets lab\n")
    L.append("This is an engineering provenance record produced by `scripts/license_audit.py` "
             "(machine-readable detail in `sources/license-audit.json`). It is not legal advice or legal clearance.\n")
    L.append("## P2Rank 2.5.1 binary distribution\n")
    L.append("The Java components below are redistributed **unmodified** from the P2Rank 2.5.1 binary distribution "
             "(`p2rank_2.5.1.tar.gz`, sha256 `d243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274`), "
             f"built from https://github.com/rdk/p2rank commit `{P2RANK_COMMIT}`. Every jar's sha256 is listed in "
             "`sources/license-audit.json` and `sources/jar-inventory.json`. Licenses bundled inside the jars "
             "(META-INF/LICENSE*, NOTICE*) remain in place and copies are in `sources/jar-notices/`.\n")
    L.append("### P2Rank license (MIT)\n")
    L.append("```\n" + (ROOT / "sources" / "P2RANK-LICENSE.txt").read_text().strip() + "\n```\n")
    L.append("### Summary\n")
    c = s["counts_by_classification"]
    L.append(f"{s['jar_count']} jars: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + ". "
             f"Unresolved: {', '.join(u['jar'].split('/')[-1] for u in s['unresolved_jars']) or 'none'}.\n")
    strong = [f"`{r['jar'].split('/')[-1]}` ({lic(r)})" for r in recs if r["classification"] == "strong-copyleft"]
    L.append("Strong-copyleft components combined with P2Rank (MIT) in the distributed runtime: " + ", ".join(strong) + ". "
             "Redistributing the runtime carries those licenses' source-availability obligations; see "
             "Corresponding source below.\n")
    open_items = []
    for r in recs:
        n = r["jar"].split("/")[-1]
        if r["status"] != "resolved":
            open_items.append(f"- `{n}`: **unresolved** ({lic(r)}). {r['notes']}")
        cs = r.get("corresponding_source")
        if r["classification"] in ("weak-copyleft", "strong-copyleft") and not (cs or {}).get("sha256"):
            open_items.append(f"- `{n}`: {lic(r)}, **corresponding source not retained**. {r['notes']}")
    if open_items:
        L.append("### Open items flagged for review before public redistribution\n")
        L += open_items
        L.append("")
    if s.get("non_jar_files_in_lib"):
        L.append("Non-jar files also shipped in `bin/lib/`: " + ", ".join(f"`{x}`" for x in s["non_jar_files_in_lib"])
                 + " (Maven POM of netlib-java `com.github.fommil.netlib:all:1.1.2`, BSD-3-Clause like the netlib jars).\n")
    L.append("### Jar table\n")
    L.append("| Jar | Coordinates | License | Class | Source |")
    L.append("|---|---|---|---|---|")
    for r in recs:
        L.append(f"| `{r['jar'].split('/')[-1]}` | {r['coordinates'] or 'unresolved'} | {lic(r)} | {r['classification']} | {src(r)} |")
    L.append("")
    L.append("## Other components\n")
    L.append("| Component | Version | License | Evidence | Source |")
    L.append("|---|---|---|---|---|")
    for o in OTHER_COMPONENTS:
        L.append(f"| {o['name']} | {o['version']} | {o['license']} | {o['evidence']} | {o['source']} |")
    L.append("")
    for o in OTHER_COMPONENTS:
        L.append(f"- **{o['name']}**: {o['notes']}")
    L.append("")
    L.append("## Corresponding source for copyleft components\n")
    L.append("For each GPL/LGPL/EPL/CDDL jar below, the source for the exact distributed version was retained under "
             "`sources/corresponding-sources/` (repository root `models/models-p2rank/`) and is also published at the listed URL. "
             "Maven Central `-sources.jar` files belong to the byte-identical Central artifact (SHA-1 verified). "
             "GitHub tarballs are the commit archives of the matching upstream tag/commit; GitHub does not guarantee "
             "archive byte-stability, so the sha256 identifies the retained copy. "
             "Shipping these files alongside the binaries (or an equivalent offer under each license) is the distributor's responsibility; "
             "this record is not itself a written offer.\n")
    L.append("| Jar | License | Corresponding source | sha256 | Bytes |")
    L.append("|---|---|---|---|---|")
    for r in recs:
        if r["classification"] not in ("weak-copyleft", "strong-copyleft"):
            continue
        cs = r.get("corresponding_source") or {}
        where = cs.get("local_path") and f"`{cs['local_path']}` ← {cs.get('final_url') or cs.get('url')}" or (cs.get("url") or "MISSING")
        if cs.get("status"):
            where += f" ({cs['status']})"
        L.append(f"| `{r['jar'].split('/')[-1]}` | {lic(r)} | {where} | {('`' + cs['sha256'][:16] + '…`') if cs.get('sha256') else '-'} | {cs.get('size_bytes') or '-'} |")
    L.append("")
    L.append(f"Total downloaded corresponding source: {s['corresponding_sources_downloaded_bytes']:,} bytes in "
             f"{s['corresponding_sources_downloaded_files']} files (plus `bin/lib/FastRandomForest_0.99_src.jar`, "
             f"{s['corresponding_sources_shipped_in_distribution_bytes']:,} bytes, shipped inside the P2Rank distribution).\n")
    L.append("Gemmi (MPL-2.0) and the jdk4py OpenJDK runtime (GPL-2.0 with Classpath Exception) source locations are listed in "
             "Other components; no copies are retained under `sources/corresponding-sources/`.\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-download", action="store_true", help="do not download corresponding sources")
    ap.add_argument("--offline", action="store_true", help="use cache only")
    ap.add_argument("--notices-only", action="store_true", help="re-render THIRD_PARTY_NOTICES.md from existing JSON")
    args = ap.parse_args()
    if args.notices_only:
        NOTICES_MD.write_text(render_notices(json.loads(OUT_JSON.read_text())))
        return
    net = Net(offline=args.offline)

    jars = [BIN / "p2rank.jar"] + sorted((BIN / "lib").glob("*.jar"), key=lambda p: p.name.lower())
    records = []
    for p in jars:
        print(f"[audit] {p.name}", file=sys.stderr)
        records.append(audit_jar(net, p, download=not args.no_download))

    # source-jar coverage check for FastRandomForest
    try:
        b = {n[:-6].split("$")[0] for n in zipfile.ZipFile(BIN / "lib/FastRandomForest_0.99.jar").namelist() if n.endswith(".class")}
        s = {re.sub(r"^src/", "", n)[:-5] for n in zipfile.ZipFile(BIN / "lib/FastRandomForest_0.99_src.jar").namelist() if n.endswith(".java")}
        missing = sorted(b - s)
        for r in records:
            if r["jar"].endswith("FastRandomForest_0.99.jar"):
                r["notes"] += (f" Source-jar coverage: {len(b) - len(missing)}/{len(b)} top-level classes have a .java file in FastRandomForest_0.99_src.jar"
                               + (f"; missing: {missing}" if missing else "") + ".")
    except Exception as e:  # pragma: no cover
        print(f"coverage check failed: {e}", file=sys.stderr)

    counts = {}
    for r in records:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    # count each distinct downloaded file once
    seen, total = set(), 0
    for r in records:
        cs = r["corresponding_source"]
        if cs and cs.get("sha256") and cs.get("kind") != "shipped-source-jar" and cs["sha256"] not in seen:
            seen.add(cs["sha256"])
            total += cs["size_bytes"] or 0
    shipped = {r["corresponding_source"]["sha256"]: r["corresponding_source"]["size_bytes"]
               for r in records if r["corresponding_source"] and r["corresponding_source"].get("kind") == "shipped-source-jar"}
    non_jar = sorted(p.name for p in (BIN / "lib").iterdir() if p.is_file() and not p.name.endswith(".jar"))
    summary = {
        "generated_by": "scripts/license_audit.py",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "distribution": "P2Rank 2.5.1 binary distribution (sources/p2rank_2.5.1.tar.gz sha256 d243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274)",
        "p2rank_source_commit": P2RANK_COMMIT,
        "jar_count": len(records),
        "non_jar_files_in_lib": non_jar,
        "counts_by_classification": counts,
        "copyleft_jars": [{"jar": r["jar"], "license_spdx": r["license_spdx"], "classification": r["classification"]}
                          for r in records if r["classification"] in ("weak-copyleft", "strong-copyleft")],
        "unresolved_jars": [{"jar": r["jar"], "tried": r.get("tried"), "notes": r["notes"]} for r in records if r["status"] != "resolved"],
        "copyleft_without_retained_source": [r["jar"] for r in records if r["classification"] in ("weak-copyleft", "strong-copyleft")
                                             and not (r["corresponding_source"] or {}).get("sha256")],
        "flagged_for_redistribution_review": [r["jar"] for r in records if "FLAG" in r["notes"] or r["classification"] == "unknown"],
        "corresponding_sources_downloaded_bytes": total,
        "corresponding_sources_downloaded_files": len(seen),
        "corresponding_sources_shipped_in_distribution_bytes": sum(shipped.values()),
        "classification_rules": {
            "permissive": "Apache, MIT, BSD-*, 0BSD, EDL-1.0 (=BSD-3-Clause), public domain, CC0, CUP (HPND-like)",
            "weak-copyleft": "LGPL-*, EPL-*, MPL-*, CDDL-*",
            "strong-copyleft": "GPL-* (including GPL-2.0 with Classpath Exception), AGPL",
            "multiple_licenses": "Maven POM lists are alternatives; least restrictive known option is used and the most restrictive is noted",
        },
        "disclaimer": "Engineering provenance record; not legal advice or clearance.",
    }
    OUT_JSON.write_text(json.dumps({"summary": summary, "jars": records}, indent=2) + "\n")
    NOTICES_MD.write_text(render_notices({"summary": summary, "jars": records}))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
