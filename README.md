# P2Rank Binding-Pocket Prediction

Biosimulant finite CPU Lab: upload one protein structure (PDB or text mmCIF, at most 2 MiB) and get ranked candidate ligand-binding pockets from the pinned P2Rank 2.5.1 default model. Outputs include upstream score and probability, pocket centers and surface points in Å, residue assignments with original author/label chain and residue IDs (insertion codes kept), retained upstream CSVs, the processed structure, and an offline 3D pocket view (`pocket-view.html`). Scores are model estimates, not experimentally confirmed binding sites.

Status: **IN PROGRESS on staging**. All acceptance gates are tracked in [reports/acceptance.md](reports/acceptance.md).

Inputs: exactly one of `structure_file` (PDB) or `mmcif_file` (mmCIF); `chains_json` (JSON list of author chain IDs, `[]` = all protein chains in model 1); `top_n` integer 1–10. Preprocessing keeps protein heavy atoms from the first model, picks the highest-occupancy alternate location (blank, then A, then lexical order on ties), and drops waters and ligands. Limits: 10000 protein heavy atoms, 2000 residues, 62 chains, 300 s per invocation. Invalid input, timeout, upstream failure and no-pocket results each return an explicit status.

Layout:

- `labs/binding-pockets` — the public Lab (adapter, fixtures, tests, frozen runtime lock, 3Dmol.js 2.5.5).
- `labs/runtime-preparation` — private one-time Lab that downloads the pinned P2Rank release archive and rebuilds byte-identical stored runtime chunks for the workspace. No scientific result.
- `scripts/inventory_assets.py` — rebuilds `assets/p2rank-runtime-{0,1}.zip` and `runtime-lock.json` from `sources/p2rank_2.5.1.tar.gz` (sha256 `d243f2d9…b274`). The zips are not committed; they are reproduced byte-for-byte locally or by the runtime-preparation Lab.
- `specifications/p2rank-binding-pockets` — MRS/MTS.

Local verification (Python 3.12, `requirements-test.txt`): download and unpack the release archive into `sources/`, run `python scripts/inventory_assets.py`, then `python -m pytest labs/binding-pockets/tests -q` and `python scripts/verify_runtime.py`. Local CLI runs create no managed Run or Passport.

Code and tests live on `staging`. Production stays on Modal; nothing in this repository authorizes a production deployment or provider switch.
