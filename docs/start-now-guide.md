# Start Now With CDAD

This guide is the complete first-run path for a team that wants to use Context-Disciplined Agent Development today.

It is based on a clean demo run captured in `docs/snapshots/`. Every command shown here was executed against a sample project and produced the listed artifacts.

## The CDAD Loop

```text
Goal -> Design -> Packet -> Context -> Verify -> Progress -> Trace -> Benchmark
```

The key rule: durable intent lives in `docs/`; agent runtime work lives in `agent/packets/`; evidence lives in `agent/verification/`.

## Demo Project

The demo task is small enough for a first run:

> Add passwordless magic-link login request handling for the backend service.

Initial project files:

```text
src/auth/magic_link.py
tests/test_magic_link.py
docs/architecture/auth.md
docs/decisions/auth-magic-link.md
pyproject.toml
```

## Step 1: Initialize CDAD

```bash
cdad init
cdad doctor
```

Snapshot: `docs/snapshots/02-init.txt`

```text
created docs/architecture
created docs/decisions
created docs/specs
created agent/memory
created agent/packets
created agent/progress
created agent/verification
created agent/reports
created agent/integrations
created agent/benchmarks
created cdad.config.json
```

## Step 2: Create A Goal

```bash
cdad goal new AUTH-MAGIC-LINK \
  --objective "Add passwordless magic-link login request handling." \
  --scope-in "backend service for requesting and verifying a magic link request" \
  --scope-out "frontend login screen" \
  --scope-out "social login" \
  --constraint "reuse existing email sender abstraction" \
  --constraint "token expiry must remain 15 minutes" \
  --risk "token leakage or replay" \
  --risk "schema change may be needed for token metadata" \
  --quality-bar "A valid email request queues exactly one login email, rejects invalid email input, and never returns a token to the caller." \
  --verify "PYTHONPATH=. python3 -m unittest discover -s tests -v"
```

Then:

```bash
cdad goal validate --report
```

Snapshot: `docs/snapshots/05-goal-validate.txt`

```text
wrote agent/reports/AUTH-MAGIC-LINK-goal-validation.json
docs/specs/AUTH-MAGIC-LINK.goal.json: ok
```

## Step 3: Write A Design

Create `docs/specs/magic-link-design.md`:

```markdown
# Magic Link Design

## Objective
Add passwordless magic-link login request handling for the auth backend.

## Scope In
- backend request service for valid and invalid email input
- token safety check that request responses do not expose auth tokens

## Scope Out
- frontend login screen
- social login
- production email provider migration

## Constraints
- reuse the existing email sender abstraction
- token expiry stays 15 minutes
- no schema change without approval

## Risks
- token leakage or replay
- invalid email handling could become inconsistent

## Verification
- run `PYTHONPATH=. python3 -m unittest discover -s tests -v`
- scenario: valid email request returns queued status
- scenario: invalid email request returns rejected status
- scenario: auth token is not returned in the request response

## Approval Boundaries
- dependency changes require approval
- schema or contract changes require approval
- security boundary changes require approval
```

Validate:

```bash
cdad design validate docs/specs/magic-link-design.md --report
```

Snapshot: `docs/snapshots/06-design-validate.txt`

```text
wrote agent/reports/magic-link-design-design-validation.json
docs/specs/magic-link-design.md: ok
```

## Step 4: Create A Packet

```bash
cdad packet new AUTH-ML-01 \
  --goal-id AUTH-MAGIC-LINK \
  --objective "Implement and verify magic-link request behavior in the auth service." \
  --why-now "This is the backend increment needed before endpoint and UI packets." \
  --context src/auth/magic_link.py \
  --interface "auth magic-link request service" \
  --constraint "Do not change frontend behavior." \
  --constraint "Do not introduce a new dependency." \
  --verify "PYTHONPATH=. python3 -m unittest discover -s tests -v" \
  --scenario "valid email request returns queued status" \
  --scenario "invalid email request returns rejected status" \
  --scenario "auth token is not returned in the request response" \
  --escalate "Escalate dependency, schema, contract, security boundary, destructive, or scope-widening changes." \
  --reference docs/specs/AUTH-MAGIC-LINK.goal.json \
  --reference docs/specs/magic-link-design.md \
  --priority 1 \
  --risk 4 \
  --value 5
```

Validate:

```bash
cdad validate --strict-paths --report
```

Snapshot: `docs/snapshots/08-packet-validate.txt`

```text
wrote agent/reports/AUTH-ML-01-packet-validation.json
agent/packets/AUTH-ML-01.json: ok
```

## Step 5: Select The Packet

```bash
cdad next --heuristic dependency-first
cdad next --heuristic dependency-first --json
```

The JSON form is useful in scripts and CI.

## Step 6: Build Context

```bash
cdad context AUTH-ML-01 --budget 12000
```

Snapshot: `docs/snapshots/11-context.txt`

```text
wrote agent/verification/AUTH-ML-01-context.md
```

The context bundle includes scored files such as source, tests, goal, design, architecture, and decision notes.

## Step 7: Verify

```bash
cdad verification
cdad verify AUTH-ML-01
```

Snapshot: `docs/snapshots/13-verify.txt`

```text
wrote agent/verification/AUTH-ML-01-verification.md
```

After verification passes, the packet becomes `Passed`.

## Step 8: Record Progress

```bash
cdad progress add AUTH-ML-01 \
  --goal "Magic link request handling" \
  --file src/auth/magic_link.py \
  --file tests/test_magic_link.py \
  --verification "PYTHONPATH=. python3 -m unittest discover -s tests -v passed" \
  --result Passed \
  --next "Create AUTH-ML-02 for HTTP endpoint routing."
```

This updates:

- `agent/progress/progress.md`
- the packet progress snapshot

## Step 9: Trace, Coverage, Benchmark, CI

```bash
cdad trace
cdad trace --json --output agent/reports/trace.json
cdad coverage --report
cdad benchmark --output agent/benchmarks/metrics.json
cdad toon agent/packets/AUTH-ML-01.json --output agent/packets/AUTH-ML-01.toon --stats
cdad ci
```

Snapshots:

```text
goal coverage: ok
cdad ci: ok
```

Benchmark result from the demo:

```json
{
  "packets_total": 1,
  "packets_passed": 1,
  "verification_pass_rate": 1.0,
  "context_bundle_tokens": 745,
  "verification_records": 1,
  "progress_entries": 1,
  "rework_mentions": 0
}
```

## Step 10: Generate Agent Integrations

```bash
cdad integration generate --all --force
```

This creates:

```text
agent/integrations/codex-cdad.md
.claude/commands/cdad.md
.cursor/commands/cdad.md
.github/prompts/cdad.prompt.md
```

## Step 11: Export TOON For Runtime Context

TOON is useful when you want to hand compact structured artifacts to an agent.

```bash
cdad toon agent/packets/AUTH-ML-01.json \
  --output agent/packets/AUTH-ML-01.toon \
  --stats
```

Use JSON as the source when possible. JSON-to-TOON is more efficient than Markdown-to-TOON because field names, arrays, and repeated objects are already typed. Markdown conversion is supported, but it has to infer structure from headings and bullets.

In the current CDAD sample, a packet JSON export reduced the estimated footprint by 12.74%. A prose-heavy Markdown guide was still 4.02% larger after conversion, so Markdown-to-TOON should be treated as a fallback for unstructured inputs, not the primary compression path.

## Resulting Artifact Tree

Snapshot: `docs/snapshots/25-artifact-tree.txt`

```text
agent/benchmarks/metrics.json
agent/memory/project.md
agent/packets/AUTH-ML-01.json
agent/packets/AUTH-ML-01.md
agent/packets/AUTH-ML-01.toon
agent/progress/progress.md
agent/reports/AUTH-MAGIC-LINK-goal-validation.json
agent/reports/AUTH-ML-01-packet-validation.json
agent/reports/goal-coverage.json
agent/reports/magic-link-design-design-validation.json
agent/reports/trace.json
agent/verification/AUTH-ML-01-context.md
agent/verification/AUTH-ML-01-verification.md
cdad.config.json
docs/specs/AUTH-MAGIC-LINK.goal.json
docs/specs/AUTH-MAGIC-LINK.goal.md
docs/specs/magic-link-design.md
```

## What To Hand To An Agent

For the first implementation turn, give the agent:

- `agent/packets/AUTH-ML-01.md`
- `agent/verification/AUTH-ML-01-context.md`
- the rule that it must run `cdad verify AUTH-ML-01`
- the rule that it must call `cdad progress add ...` before stopping

## Quality Gate

Before merging a CDAD-governed change:

```bash
cdad ci
```

If this passes, the minimum artifact discipline is intact.
