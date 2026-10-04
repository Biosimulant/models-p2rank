# P2Rank Binding Pockets — Model Requirements Specification

## 1. Document Control

| Field | Value |
| --- | --- |
| MRS identifier | P2R-MRS-001 |
| Version | 1.0 |
| Status | Approved |
| Last revised | 2026-10-04 |
| Selected type or types | Predictive / ML |

Approval receipt: user's 2026-10-04 goal explicitly authorizes implementing the complete item03 brief and its unchanged acceptance criteria. Approval covers requirements and staging implementation, not a compute grant, public plan digest or production deployment. Agent is implementation/evidence custodian; user owns intended use and release decisions.

Revision History: 1.0, 2026-10-04: exact brief transcribed with explicit preprocessing and verification procedures; no acceptance threshold weakened.

## 2. Executive Summary

Rank candidate binding pockets from uploaded protein coordinates with frozen P2Rank. The goal is a hosted, public, downloadable research Lab; every gate must pass before DONE.

## 3. Biological Objective and Intended Use

One finite prediction per invocation. Support exploratory localization of candidate ligand-binding pockets. Scores and probabilities are upstream model estimates, not experimental binding evidence. No affinity, safety, clinical, or universal accuracy claims. Sequence-only inputs are insufficient.

## 4. Model Definition and Scope

CPU Java P2Rank 2.5.1 default pretrained model; no training, model tuning, implicit structure prediction or external inference service. Initial pilot is three small reference structures, maximum300seconds per invocation. Provisional protective input limits:2MiB,10000protein heavy atoms,2000residues,62chains; measured support remains a gate, not a claim.

## 5. Inputs

MRS-IN-001: Upload one UTF-8 .pdb/.cif/.mmcif atomic-coordinate structure and select author chains (empty selection means all); top_n integer1–10. Reject empty/nonprotein, unsupported extensions, malformed coordinates, missing selected chains or bounds violations explicitly. Binary CIF and compressed uploads are outside this release.

MRS-IN-002: Select first coordinate model; remove waters, ligands, hydrogen atoms and non-amino-acid entities; choose highest occupancy alternate per atom (ties prefer blank then A then lexical). Preserve author/label chain IDs, author residue number, insertion code and label sequence ID through a downloadable reversible mapping. Separate chains with equal author numbers must never collide.

## 6. Outputs

MRS-OUT-001: Return ordered pocket rank, unchanged upstream score and probability if present, x/y/z centers in Å, surface points and exact original residue identities. Retain raw prediction/residue CSVs, processed structure, mapped residues/pockets JSON/CSV, receipt and source identities. Empty pocket list is a successful no_pockets result, never an invented site.

MRS-OUT-002: Show a reusable interactive3D protein view and a reopenable offline pocket view with colored centers/surface points and individually selectable residue highlights, using the computed outputs. Include author identity labels and Å units. Native platform3D may be a protein preview; overlay support must be verified separately. Exact ranks/scores accompany3D; no ad hoc chat visual substitutes.

## 7. Data, Assay, and Evidence Specification

MRS-DQ-001: Retain three legally usable RCSB/upstream structures and their independently verified bytes/licenses. Preserve any reference ligand separately and remove it before inference. Choose a post-training held-out holo structure before reading outcomes. Freeze source/model/runtime/fixtures,4Å metric and no tuning protocol before final verification. Software mapping fixtures may transform coordinates/IDs with documented provenance; these are not biological accuracy cases.

## 8. Ground Truth or Estimand

Closest Euclidean distance from each predicted center to any retained reference-ligand heavy atom; recovery if minimum distance<=4Å. top1 and top3 use first1/3 ranked centers, respectively. Reference ligand is absent from predictor input. This is a small demonstration, not a broad accuracy estimate.

## 9. Generalization Domain

Uploaded small protein-coordinate structures within measured limits. X-ray default uses B-factors; non-X-ray/AlphaFold confidence conventions limit interpretation. No accuracy claims for all proteins, membranes, ensembles or biological function.

## 10. Performance Requirements

MRS-OPS-001: Pilot three small structures on approved CPU Java runtime, each invocation<=300seconds. Record cold/warm latency, available peak memory and provider spend; cap concurrency and scale idle resources to zero. No unbounded jobs. Separate local adapter tests, managed runs, end-to-end staging and hosting evidence.

## 11. Validation Plan

MRS-001: Execute all exact A1–A5 and H1–H8 gates below unchanged. Parity uses separate pinned standalone commands, centers tolerance1e-3Å and scores within emitted precision. No reference-result literals may self-certify acceptance. Managed/hosted result bytes must independently match immutable size/SHA-256. Model/fixtures/protocol lock precedes evaluation.

## 12. Acceptance and Traceability



- [ ] A1: On three legally usable upstream/reference structures, pocket ordering and residue mapping match the standalone pinned P2Rank output exactly; centers agree within 1e-3 Å and scores within the upstream output precision.
- [ ] A2: A chain with insertion codes or residue-number gaps preserves the correct residue identities in CSV and 3D highlights; two chains with the same author residue numbers do not collide.
- [ ] A3: Use at least one held-out holo structure to report nearest predicted-center to ligand-heavy-atom distance and top-1/top-3 recovery at a frozen 4 Å center-distance definition. Report these as a small demonstration, not a broad accuracy estimate.
- [ ] A4: Empty/nonprotein input, unsupported formats and no-pocket results have explicit outcomes. No-pocket is not a runtime exception or fabricated pocket.
- [ ] A5: A public comparison shows top-1 versus top-3 predictions on the same example, with a downloadable receipt and an actual reopenable 3D result.

### Public hosting completion criteria

- [ ] H1: The exact release records code, model/parameter files, ancillary data, sample fixtures, dependency versions/digests and applicable license/attribution obligations; there are no unresolved rights for assets actually shipped or used in the public service.
- [ ] H2: Every item-specific check below has linked evidence. Parity and small demonstrations are labelled accurately; neither is presented as broad biological validation.
- [ ] H3: A completed managed run has non-empty typed results and required visuals; retrieved artifact byte sizes and SHA-256 digests are independently verified. A matching Passport is retained with its limitations.
- [ ] H4: The Lab has a public immutable release, is listed and discoverable on the public Hub, and its page opens as a non-owner. Invocation authentication/payment requirements, if any, are explicit; users need no private owner API key or local software installation.
- [ ] H5: Hosting is active for that exact release on the approved Modal setup. A cold invocation and a subsequent invocation of the declared example accept the real user input, produce the declared outputs and meet frozen limits. Baseline example inference requires no undeclared online service.
- [ ] H6: The Results page contains at least one deliberately public, legally shareable example run with visuals and downloadable artifacts. The item-specific comparison is retained as an actual experiment/study and visible in Experiments when supported. If the platform cannot expose this, record a blocker instead of calling an empty page done.
- [ ] H7: Record measured cold/warm latency, peak memory/VRAM where available, provider compute spend, upload/request bounds, timeout/cancellation behavior and idle resource policy. Release inputs are isolated between users; no private user data or signed asset URLs appear in public examples.
- [ ] H8: Deliver exact staging commit(s), release reference, public URL, hosting identity, run/experiment/Passport references, evidence summary, outstanding limitations and rollback/disable instructions. Update this file and the index only after verifying completion.



## 13. Constraints, Risks, and Governance

MRS-002: Development/tests/commits/push on staging only, synchronized from main preserving staging-only work. Dedicated repository. Production stays Modal. Concrete staging review and fresh explicit user permission required before production deployment. Obtain item-specific bounded managed-compute approval and exact public/hosting approval. License/rights gaps are blockers.

## 14. Reproducibility, Deliverables, and Handoff

MRS-003: Retain exact code, model/config/runtime/digests/licenses, immutable workspace/release, matching Passport, public URL/results/study/downloads, input/cost/latency limits and disable instructions. Record every gate; brief/index DONE only after all pass. Never retain signed URLs or private uploads in deliberate public examples.

## 15. Milestones and Responsibilities

Agent: discovery, assets, code/tests, frozen evidence, concrete approval plans, byte verification and gate records. User: bounded compute/public/production approvals. Platform: exact release hosting and public study/result capabilities. No deployment assumed.

## 16. Open Questions and Decisions

Public generic protein-upload hosting,3D overlays, public studies and artifact-metadata integrity are unverified platform capabilities. Java and shipped third-party license closure are required. These are release gates with agent/platform owners; no acceptance waiver.

## 17. References and Glossary

Source brief item03; https://github.com/rdk/p2rank/tree/2.5.1 ; https://www.rcsb.org/pages/policies ; live Biosimulant authoring contract scientific-authoring-14/runtime0.0.34. Å=angstrom; author IDs identify deposited residues; internal IDs are reversible predictor identifiers.

## 18. Predictive / ML Module

Frozen existing pretrained predictor, no training/calibration/feature selection. Verify parity to native output and report held-out holo distances under frozen4Å definition. Upstream probability is a model estimate, not certainty. Hold-out eligibility requires exclusion from frozen training sources; otherwise A3 remains blocked.
