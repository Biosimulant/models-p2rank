# Workspace workflow

The user requires all new development, fixes, and tests to use `staging`, not
`main`. Sync staging from the current main baseline before starting new work,
preserving any staging-only commits. Use a staging worktree when another
checkout is in use. Commit and push changes to staging only.

Production is reserved for the upcoming presentation and must remain on Modal.
Do not deploy new changes or switch production providers without a new explicit
user instruction. Read-only health checks are allowed. Test compute-provider
changes in staging or an isolated harness built from staging, restore Modal
after testing, and confirm cleanup of resources created by the test.

Distinguish branch synchronization, deployment, isolated adapter tests, and
end-to-end staging tests in reports. Record exact commits, environment,
results, blockers, and rollback state; do not claim a provider is deployment
ready based only on isolated tests.
