# P2Rank Binding-Pocket Prediction

Biosimulant finite CPU Lab: upload one protein structure (PDB or text mmCIF, at most 2 MiB) and get ranked candidate ligand-binding pockets from the pinned P2Rank 2.5.1 default model. Outputs include upstream score and probability, pocket centers and surface points in Å, residue assignments with original author/label chain and residue IDs (insertion codes kept), retained upstream CSVs, the processed structure, and an offline 3D pocket view (`pocket-view.html`). Scores are model estimates, not experimentally confirmed binding sites.

Status: **BLOCKED for active hosting**. Public [Lab](https://hub.biosimulant.com/labs/88648162-e30d-49a1-9b07-de5fa0a11d36) release `demi/p2rank-binding-pockets@0.1.0` is Hub-listed with four public example runs, a public top-1 vs top-3 study and verified anonymous downloads. Hosting is blocked: the hosting preflight rejects PDB/mmCIF structure-file inputs, and Files storage rejects PDB/mmCIF uploads. All gates: [reports/acceptance.md](reports/acceptance.md).

Inputs: exactly one of `structure_file` (PDB) or `mmcif_file` (mmCIF); `chains_json` (JSON list of author chain IDs, `[]` = all protein chains in model 1); `top_n` integer 1–10. Preprocessing keeps protein heavy atoms from the first model, picks the highest-occupancy alternate location (blank, then A, then lexical order on ties), and drops waters and ligands. Limits: 10000 protein heavy atoms, 2000 residues, 62 chains, 300 s per invocation. Invalid input, timeout, upstream failure and no-pocket results each return an explicit status.

Layout:

- `labs/binding-pockets` — the public Lab (adapter, fixtures, tests, frozen runtime lock, 3Dmol.js 2.5.5).
- `labs/runtime-preparation` — private one-time Lab that downloads the pinned P2Rank release archive and rebuilds byte-identical stored runtime chunks for the workspace. No scientific result.
- `scripts/inventory_assets.py` — rebuilds `assets/p2rank-runtime-{0,1}.zip` and `runtime-lock.json` from `sources/p2rank_2.5.1.tar.gz` (sha256 `d243f2d9…b274`). The zips are not committed; they are reproduced byte-for-byte locally or by the runtime-preparation Lab.
- `specifications/p2rank-binding-pockets` — MRS/MTS.
- `scripts/build_bundles.py` — rebuilds the pinned viewer, reference-structure, license-record and corresponding-source bundles after `inventory_assets.py`.
- `labs/binding-pockets/THIRD_PARTY_NOTICES.md` — per-jar licenses, the two jars omitted from the shipped runtime (`vecmath-1.3.1`, `openchart-1.4.2`) and corresponding-source locations.

Local verification (Python 3.12, `requirements-test.txt`): download and unpack the release archive into `sources/`, run `python scripts/inventory_assets.py`, then `python -m pytest labs/binding-pockets/tests -q` and `python scripts/verify_runtime.py`. Local CLI runs create no managed Run or Passport.

Code and tests live on `staging`. Production stays on Modal; nothing in this repository authorizes a production deployment or provider switch.
