# P2Rank Binding Pockets — Modeling Technical Specification

## 1. Document Control

| Field | Value |
| --- | --- |
| MTS identifier | P2R-MTS-001 |
| Version | 1.1 |
| Status | Frozen for release verification |
| Last revised | 2026-10-04 |
| MRS | P2R-MRS-001 version 1.0 (approved by the user's exact-brief implementation request) |
| Biosimulant fit | Adapter fit |

Revision history:

- 1.0, 2026-10-04: predictor, preprocessing and metric design frozen.
- 1.1, 2026-10-04: implementation as built. Stored (uncompressed) runtime chunks so managed acquisition reproduces them byte for byte; explicit `execution_failed` outcome; retained results written under the run's `outputs/`; compact runtime lock with per-member digests kept in the repository; fixtures pinned by SHA-256 and the default example switched to the deposited 7L13 mmCIF. No acceptance criterion changed.

## 2. Technical Decision Summary

MTS-001: Run unmodified P2Rank 2.5.1 native Java inference behind a finite typed Biosimulant adapter. The adapter converts the upload to a canonical protein-only PDB with single-character internal chain IDs and sequential internal residue numbers, and keeps a reversible map back to author/label identities. This avoids ambiguous upstream parsing of multi-character chains, insertion codes and duplicate author numbers.

MTS-002: Public assets that are too large to embed in a workspace change (runtime chunks, 3Dmol.js, RCSB fixtures) are retained by a separate private infrastructure revision (`labs/runtime-preparation`) that downloads checksum-pinned public files once. The scientific revision references the resulting owned stored files. The preparation revision is never published and produces no scientific result.

## 3. Scope, Boundaries, and Assumptions

All MRS gates apply unchanged. Default pretrained model only; no training, calibration or rescoring. The first coordinate model is used; alternate locations are resolved per atom by highest occupancy (ties: blank, then `A`, then lexical); hydrogens, waters, ligands and non-amino-acid residues are removed by residue chemistry even when a file declares them inside a polymer entity. The default model uses B-factor features; inputs from non-X-ray methods or predicted structures carry an interpretation caveat.

## 4. MRS Traceability

| MRS item | Implementation | Verification |
| --- | --- | --- |
| MRS-IN-001 | `structure.load`, `PocketPredictor.execute` | `test_a4_invalid_inputs_are_explicit`, `test_a4_module_outcomes` |
| MRS-IN-002 | `structure.preprocess` | `test_frozen_preprocessing_fixtures`, `test_a2_*` |
| MRS-OUT-001 | `predictor.parse_outputs`, `predict` | `test_a1_*`, `test_a4_no_pocket_result_is_valid_empty`, managed byte verification |
| MRS-OUT-002 | `visualize()`, `pocket_html` | composed CLI cases, browser verification, managed visuals |
| MRS-DQ-001 | `fixtures/fixture-lock.json`, `7L13-reference-ligand.json` | `test_a3_held_out_holo_demonstration` |
| MRS-OPS-001 | `TIMEOUT_SECONDS`, input limits, receipt timing | timeout test, managed and hosted timing records |
| MRS-001/002/003 | Repository, workspace revisions, release | `reports/acceptance.md` gate matrix (A1–A5, H1–H8 individually) |

## 5. Architecture and Data Flow

Upload → gemmi parser → first model / chain selection / altloc / protein-only canonical PDB + reversible map → pinned Java predictor (one thread, 2048 MiB heap, unique scratch directory) → strict CSV parser → ranked pockets, residue assignments, surface points → typed report, retained files and visuals. The held-out reference ligand coordinates are read only by the evaluation test, never by the predictor path.

## 6. Data Implementation

Reference structures 1CRN, 1STP and 7L13 from RCSB (CC0 under the wwPDB usage policy), pinned by size and SHA-256 in `fixtures/fixture-lock.json` together with digests of the processed PDB and mapping each produces. 7L13 (SARS-CoV-2 main protease with compound 21, released 2021-03-03) is the held-out holo case: the default model was trained on CHEN11 (published 2011), which predates the entry. Its ligand XF7 A/401 heavy atoms are stored separately in `7L13-reference-ligand.json`. The A2 software fixture is built deterministically from 1STP by `tests/mapping_fixture.py`: two copies with chain IDs `AUTH_A`/`AUTH_B` (label `LABEL_0`/`LABEL_1`) share author numbers, author numbers are doubled to create gaps, label_seq 24 becomes insertion residue 30A inside the biotin pocket, and copy B is shifted +40 Å in x. It is software verification only.

## 7. Input, Output, and Error Contracts

Inputs: exactly one of `structure_file` (PDB, `.pdb`) or `mmcif_file` (text mmCIF, `.cif`/`.mmcif`), each ≤ 2 MiB; `chains_json` JSON list of unique author chain IDs (≤ 1024 characters; `[]` = all protein chains); `top_n` integer 1–10. Content limits: 10000 protein heavy atoms, 2000 residues, 62 chains; coordinates, occupancies and B-factors finite with |x| < 10000 Å.

Outcomes (`report.status`): `ok`; `no_pockets` (valid empty upstream result, raw CSVs and 3D view still retained); `invalid_input` with `receipt.error_code` in {`structure_input`, `structure_file`, `unsupported_format`, `input_size`, `parse_error`, `no_protein`, `chain_selection`, `missing_chain`, `invalid_coordinate`, `ambiguous_residue`, `chain_limit`, `structure_limit`, `top_n`}; `timeout`; `execution_failed`. Failures never produce pockets.

Outputs: `report` record (status, pockets, residues, surface_points, receipt; mixed record, unit `1`, each field documents its unit: centers and surface points in Å, score and probability dimensionless); `pocket_count` (count); files `processed_structure` (PDB), `raw_predictions` and `raw_residues` (unchanged upstream CSV), `mapped_residues` (CSV with original identities and upstream residue scores), `residue_map` (JSON), `report_file`, `receipt_file` (JSON), `pocket_view` (self-contained HTML).

## 8. Model Method and Uncertainty

Unmodified pinned default random forest and configuration, `-threads 1`, seed recorded as 42 (upstream default). No recalibration or re-sorting. Scores and probabilities are preserved at emitted precision; centers within 1e-3 Å. The upstream probability is a calibrated model estimate, not certainty. The frozen held-out metric is the minimum Euclidean distance from a predicted center to any reference ligand heavy atom, recovered when ≤ 4.0 Å, evaluated for top-1 and top-3.

## 9. Biosimulant Fit Assessment

Adapter fit: the authoritative native Java predictor is preserved; the adapter adds upload validation, typed ports, immutable assets, reproducible results and retained views.

## 10. Biosimulant Realization

`PocketPredictor(BioModule)` with `ExecutionPolicy.ONCE_BEFORE_RUN`, declared identically in `model.yaml`. Typed `inputs()`/`outputs()` use `SignalSpec`. Results are written to a unique `mkdtemp` directory under the run's `outputs/`; the runtime is extracted to a separate scratch directory that is deleted after each invocation. `visualize()` reads computed state only and emits: `text` (status and caveat, always), `structure3d` (processed protein PDB, same path as the typed `processed_structure` output) and `table` (rank, score, probability, center x/y/z in Å, residue count) when pockets exist. `lab.yaml` requires `structure3d` and `text`. The native 3D view is a protein preview; the retained `pocket-view.html` (3Dmol.js 2.5.5 embedded, no network) renders colored centers, surface point clouds, per-residue highlight toggles labelled with author chain, author number, insertion code and label IDs, a top-1/top-3/all selector and a receipt download.

## 11. Verification and Test Design

`labs/binding-pockets/tests` (22 tests): runtime archive integrity; frozen fixture digests; reproducible A2 fixture; A1 parity per reference structure against the unpacked original distribution's own `prank` launcher, both on the identical processed PDB (exact rows) and on the original deposited mmCIF (ordering, author residue sets, scores, centers); A2 mapping, gaps, insertion codes, chain selection; A3 held-out distances; A4 invalid inputs, no-pocket, timeout and upstream failure; A5 top-1 vs top-3 consistency, visuals and receipt. `scripts/verify_runtime.py` runs five composed CLI cases (PDB upload, mmCIF upload, chain selection, no pockets, invalid input). The A2 3D highlight check is executed in a browser against the generated `pocket-view.html`. Managed runs are verified by retrieving every artifact and recomputing size and SHA-256.

## 12. Reproducibility, Security, Performance, and Cost

Python 3.12; biosimulant 0.0.34, gemmi 0.7.3, jdk4py 21.0.8.1 (bundled Java 21.0.8). P2Rank source commit 9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e; release archive SHA-256 d243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274. Runtime chunks are uncompressed ZIPs with fixed timestamps and permissions, pinned in `assets/runtime-lock.json`; the archive digest pins every member and `sources/runtime-members.json` lists member digests. Extraction rejects absolute paths, `..` and members > 64 MiB. Inference is offline: a missing or mismatched asset fails closed. Each invocation uses its own mode-700 directories. The predictor subprocess runs in its own process group and is killed at the remaining share of the 300 s limit. Pilot profile: Modal CPU, 2 cores / 4096 MiB. Costs are recorded from preflight estimates and measured durations only.

## 13. Model Lock, Release, and Operations

Code, runtime archives, fixtures, notices and this protocol are frozen before managed verification. Commits and pushes go to `staging` only; no core production deployment. Public publication and hosting each require approval of an exact plan digest. Proposed hosting: max 1 container, scale to zero, 300 s timeout, real upload bounds; these must pass preflight before any claim. Publication, Hub listing, managed runs, hosted runs and public studies are separate evidence. Disable by pausing or withdrawing hosting through the current hosting revision and unlisting the Lab; Modal production remains unchanged.

## 14. Risks, Decisions, and Open Questions

Open release risks: third-party Java license closure for all 113 bundled JARs (see `THIRD_PARTY_NOTICES.md` and `sources/license-audit.json`); platform support for generic protein-file uploads in hosting; public display of a retained study; artifact metadata integrity for generated HTML. These remain gates, not waivers.

## 15. References and Glossary

MRS P2R-MRS-001 v1.0; item-03 brief; P2Rank 2.5.1 README, `config/default.groovy`, `models/readme.md`; Krivák R., Hoksza D. (2018) J. Cheminform. 10:39; wwPDB usage policy; Biosimulant authoring contract scientific-authoring-14. Å = ångström; author IDs identify deposited residues; internal IDs are reversible predictor identifiers.

## 16. Predictive / ML Technical Module

No fitted parameters change. The default model and score transformers are authoritative. All residue assignments, surface points and scalar precision are preserved. Per-invocation elapsed time is recorded in the receipt; the single held-out recovery result is a demonstration, not a population accuracy estimate.
