# CDAD Quickstart

Use this when you want the shortest path from a normal project to a verified agent-ready task packet.

## 1. Install

From this repository:

```bash
python3 -m pip install -e .
cdad --help
```

Or run directly during development:

```bash
PYTHONPATH=/path/to/cdad-tools/src python3 -m cdad_tools.cli --help
```

## 2. Initialize

Inside your project:

```bash
cdad init
cdad doctor
```

Expected result:

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
cdad layout: ok
```

## 3. Create A Goal

```bash
cdad goal new AUTH-MAGIC-LINK \
  --objective "Add passwordless magic-link login request handling." \
  --scope-in "backend service for requesting and verifying a magic link request" \
  --scope-out "frontend login screen" \
  --scope-out "social login" \
  --constraint "reuse existing email sender abstraction" \
  --constraint "token expiry must remain 15 minutes" \
  --risk "token leakage or replay" \
  --quality-bar "A valid email request queues exactly one login email, rejects invalid email input, and never returns a token to the caller." \
  --verify "PYTHONPATH=. python3 -m unittest discover -s tests -v"
```

Then:

```bash
cdad goal validate --report
```

## 4. Write And Validate Design

Create `docs/specs/magic-link-design.md` with sections for objective, scope in, scope out, constraints, risks, verification, and approval boundaries.

Then:

```bash
cdad design validate docs/specs/magic-link-design.md --report
```

## 5. Create A Packet

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

Then:

```bash
cdad validate --strict-paths --report
```

## 6. Run The CDAD Loop

```bash
cdad next --heuristic dependency-first
cdad context AUTH-ML-01 --budget 12000
cdad verification
cdad verify AUTH-ML-01
cdad progress add AUTH-ML-01 \
  --goal "Magic link request handling" \
  --file src/auth/magic_link.py \
  --file tests/test_magic_link.py \
  --verification "PYTHONPATH=. python3 -m unittest discover -s tests -v passed" \
  --result Passed \
  --next "Create AUTH-ML-02 for HTTP endpoint routing."
```

## 7. Check Results

```bash
cdad trace
cdad trace --json --output agent/reports/trace.json
cdad coverage --report
cdad benchmark --output agent/benchmarks/metrics.json
cdad toon agent/packets/AUTH-ML-01.json --output agent/packets/AUTH-ML-01.toon --stats
cdad ci
```

Success looks like:

```text
goal coverage: ok
cdad ci: ok
```
