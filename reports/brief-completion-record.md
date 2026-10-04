# Item 03 completion record — BLOCKED, not DONE

Updated 2026-10-04. Gate-by-gate evidence: [acceptance.md](acceptance.md).

- **Status:** BLOCKED. A1–A5, H1–H3 and H6 pass, H4 and H7 are partial, and H5 is blocked by platform hosting and file-type support.
- **MRS/MTS:** P2R-MRS-001 v1.0 (brief criteria verbatim) and P2R-MTS-001 v1.2. Both are in `specifications/p2rank-binding-pockets/`, with summaries in workspace revision 6.
- **Source, model and runtime:**
  - P2Rank 2.5.1: source commit 9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e; release archive SHA-256 d243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274; default model trained on CHEN11.
  - Runtime: Java 21.0.8 via jdk4py 21.0.8.1; gemmi 0.7.3; biosimulant 0.0.34; Python 3.12.
  - Runtime chunks are stored ZIPs: runtime-0 SHA-256 9b84a3f3…606db, runtime-1 960ef240…02d96. vecmath-1.3.1 and openchart-1.4.2 are omitted.
  - 3Dmol.js 2.5.5.
- **Licenses and notices:** NOTICE.md, THIRD_PARTY_NOTICES.md, the per-jar license-audit.json and corresponding-sources.zip (36 files, 31.9 MB). Fixtures are RCSB CC0.
- **Staging (dedicated public repo [Biosimulant/models-p2rank](https://github.com/Biosimulant/models-p2rank/tree/staging)):**
  - Implementation commits: 84dbd94, 1d3e492, 1c48c38, 3d4389b, 7e739f8, aa89d24 (workspace revision 6), 32a6439.
  - The evidence commit follows this record.
  - The new repo has no main baseline, so no core platform repository was modified or deployed.
  - Local evidence: 22 tests, 5 composed CLI cases, browser checks on macOS arm64. These are local checks, separate from the managed (Modal) and public evidence.
- **Workspace and preparation runs:**
  - Workspace 016506d0-086a-41d5-85fe-8e8316719810. Revisions 2–4 are the private preparation step and are never published. Revision 6 is 1e5821dc-8a6b-4a41-b59d-27ed1cb5f828 (SHA-256 420ae2b0…197ce).
  - Preparation runs: 8bc54725, 6ee4c080, 589cbc6b.
  - Owned bundle files: 03485424, 7cef413b, eab13586, a83f6d15, 54c9df9f, fe2aa8d7.
- **Public release:** demi/p2rank-binding-pockets@0.1.0. Package artifact b139f676-0571-4669-88b6-cac8049056b6, SHA-256 779527ea7d48d20bfacb73d5b3799d5885542406618647cad0e90c5bc6b0cc2e, 122,715,583 bytes. Lab 88648162-e30d-49a1-9b07-de5fa0a11d36 is Hub-listed. URL: https://hub.biosimulant.com/labs/88648162-e30d-49a1-9b07-de5fa0a11d36
- **Hosting identity:** none. The preflight was rejected (`Unsupported hosted file format for structure_file`) and nothing was executed.
- **Public runs, study and Passports:** study 47fc0e0d-34b6-4c2d-b689-d5383c9c3e06, public on the Lab.

  | Arm | Run | Status | Passport |
  | --- | --- | --- | --- |
  | 7L13 top-3 | d174ea14-0366-48f1-ae59-1833278aa503 | ok, 3 pockets | b027cbd9 |
  | 7L13 top-1 | f98d3a40-5283-413b-96c8-94faaa1a8414 | ok, 1 pocket | 0d1a24db |
  | 1STP pilot | 779beba6-8679-4a61-8a6f-c6db3169f2a2 | ok, 1 pocket (17.47) | 61bb89b8 |
  | 1CRN pilot | e0eab1ea-a7a4-4340-93b4-c2132c51eed3 | no_pockets | d95cce5f |

  Release Passport: 2d35444c. All Passports are REVIEW. The superseded private study 7c40c4db (revision 5) is retained as a record of the artifact-retention issue.
- **Latency, resources and spend:**
  - 11 Modal Pro runs, 140.3 s total platform time.
  - Managed inference took 4.1–8.8 s per invocation.
  - Estimated provider cost: $0.79 at the timeout caps, about $0.015 pro-rated by duration. User charge $0.
  - Hosted cold/warm latency: not measurable.
- **Caveats and blockers:**
  - Hosted inputs support only JPEG/PNG images.
  - Files storage rejects PDB and mmCIF, so users can't yet run their own structures through platform uploads.
  - Agent-gateway HTML downloads receive Cloudflare beacon injection.
  - Scientific scope: parity is software verification; 7L13 is a single-structure demonstration in which top-1 missed and top-3 found the ligand pocket.
- **Rollback / disable:** there's no hosting and no deployment to roll back, and production is untouched (Modal). To withdraw: use Lab `hub_listed=false` or visibility private; unlist the study with `experiment_update unpublish`; set runs private in Studio; set the GitHub repo private if wanted. The immutable release and evidence remain.

**Next steps:**

1. The platform team adds hosted PDB/mmCIF (or large-string) inputs and Files allowlist entries for `.pdb`/`.cif`, verified on staging.
2. Fresh approval for any production deployment.
3. An exact hosting approval, then cold and subsequent hosted invocations with real uploads, and measurement of limits, cancellation, isolation and idle behavior.

Optionally, a Lab 0.1.1 could accept zipped or `.txt` structure uploads, which the current allowlist accepts, to enable user structures in managed runs. That change needs approval.
