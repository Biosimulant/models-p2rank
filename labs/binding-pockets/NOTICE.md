# Notices

Adapter code in this Lab: MIT, Copyright (c) 2026 Biosimulant (see LICENSE).

P2Rank 2.5.1 (MIT, Copyright (c) 2017-2025 Radoslav Krivák, David Hoksza, Lukáš Jendele, Petr Škoda and other contributors), from https://github.com/rdk/p2rank commit 9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e, release archive sha256 d243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274. Cite: Krivák R., Hoksza D. (2018) P2Rank: machine learning based tool for rapid and accurate prediction of ligand binding sites from protein structure. J. Cheminform. 10:39.

`assets/p2rank-runtime-0.zip` and `assets/p2rank-runtime-1.zip` contain the P2Rank binary, default model, configuration and 111 of the 113 bundled third-party jars, unmodified. Several are GPL-2.0, GPL-3.0 or LGPL licensed (Weka 3.9.6, FastRandomForest 0.99, FasterForest 2.5.2, CDK 2.11, BioJava 7.2.2, forester, jgrapht, mtj, xom and others). `vecmath-1.3.1.jar` (restrictive Sun notice) and `openchart-1.4.2.jar` (no retained LGPL source) are omitted; prediction outputs on all reference structures are byte-identical without them.

- `assets/license-records.zip`: THIRD_PARTY_NOTICES.md (per-jar license table), license-audit.json, jar inventory and member digests, every license/notice file bundled in the jars, the P2Rank license and the runtime-omission verification.
- `assets/corresponding-sources.zip`: exact corresponding source for every copyleft jar (Maven Central source jars and upstream commit tarballs), listed with URLs and digests in corresponding-sources-manifest.json inside license-records.zip.
- `assets/viewer-3dmol-2.5.5.zip`: 3Dmol.js 2.5.5 and its BSD-3-Clause license (embedded in each pocket-view.html with the license text).
- `assets/reference-structures.zip`: RCSB PDB entries 1CRN, 1STP and 7L13 (CC0, wwPDB usage policy).
- Runtime Python packages: gemmi 0.7.3 (MPL-2.0), jdk4py 21.0.8.1 (bundled OpenJDK 21.0.8, GPL-2.0 with Classpath Exception), biosimulant 0.0.34.

This is an engineering provenance record, not legal advice. Source repository: https://github.com/Biosimulant/models-p2rank (staging).
