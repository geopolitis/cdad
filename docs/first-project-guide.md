# Starting Your First CDAD Project

This guide walks through a first Context-Disciplined Agent Development project using a small passwordless login example. The goal is not to add process for its own sake. The goal is to give an AI agent a compact, verified task packet instead of a vague prompt or a full-repository dump.

## What You Will Create

By the end, your project will have:

- a durable goal record under `docs/specs/`;
- a design note that can be validated;
- one agent-ready task packet under `agent/packets/`;
- a ranked context bundle under `agent/verification/`;
- verification evidence from your test command;
- a progress note for the next session;
- trace and benchmark outputs.

## 1. Install Or Run The CLI

From the CDAD tools repository:

```bash
python3 -m pip install -e .
cdad --help
```

During local development, you can also run without installing:

```bash
PYTHONPATH=/path/to/cdad-tools/src python3 -m cdad_tools.cli --help
```

In the examples below, replace `cdad` with the `PYTHONPATH=... python3 -m cdad_tools.cli` form if you have not installed the package.

## 2. Start From A Real Project

Move into the project you want to govern with CDAD:

```bash
cd /path/to/your-project
```

For a first trial, choose a small but non-trivial task. Good candidates:

- add one backend endpoint;
- update one workflow;
- add one integration point;
- repair one bug with a clear test.

Avoid starting with a whole product rewrite. CDAD works best when the first packet is a bounded verified increment.

## 3. Initialize CDAD

```bash
cdad init
cdad doctor
```

This creates:

```text
docs/
  architecture/
  decisions/
  specs/
agent/
  memory/
  packets/
  progress/
  verification/
  reports/
  integrations/
  benchmarks/
```

The split matters:

- `docs/` stores durable human-reviewed intent.
- `agent/packets/` stores compact runtime units for agents.
- `agent/verification/` stores evidence.
- `agent/progress/` stores resumable state.

## 4. Create A Goal Record

A goal record is the source of truth. It should define scope, non-goals, constraints, verification, risks, and approval boundaries.

Example:

```bash
cdad goal new AUTH-MAGIC-LINK \
  --objective "Add passwordless magic-link login request handling." \
  --scope-in "backend service for requesting a magic link" \
  --scope-in "unit verification for queued email behavior" \
  --scope-out "frontend login screen" \
  --scope-out "social login" \
  --constraint "reuse existing email sender abstraction" \
  --constraint "token expiry must remain 15 minutes" \
  --risk "token leakage or replay" \
  --risk "schema change may be needed for token metadata" \
  --quality-bar "A valid email request queues exactly one login email and existing auth behavior remains unchanged." \
  --verify "PYTHONPATH=. python3 -m unittest discover -s tests -v"
```

Validate it:

```bash
cdad goal validate --report
```

Expected outputs:

- `docs/specs/AUTH-MAGIC-LINK.goal.json`
- `docs/specs/AUTH-MAGIC-LINK.goal.md`
- `agent/reports/AUTH-MAGIC-LINK-goal-validation.json`

The Markdown rendering should be readable by humans. The JSON file is the canonical machine-readable record.

## 5. Write A Design Note

Create a design note in `docs/specs/`. Keep it short and operational:

```markdown
# Magic Link Design

## Objective
Add passwordless magic-link login request handling for the auth backend.

## Scope In
- backend request service
- unit test coverage for queued email behavior

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
- rate limiting may need infrastructure support

## Verification
- run `PYTHONPATH=. python3 -m unittest discover -s tests -v`
- scenario: valid email request returns queued status

## Approval Boundaries
- dependency changes require approval
- schema or contract changes require approval
- security boundary changes require approval
```

Validate the design:

```bash
cdad design validate docs/specs/magic-link-design.md --report
```

The validator checks for:

- objective;
- scope in;
- scope out;
- constraints;
- risks;
- verification;
- approval boundaries.

## 6. Create The First Task Packet

A packet is what the agent should actually consume. It is smaller than the full goal or design.

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
  --escalate "Escalate dependency, schema, contract, security boundary, destructive, or scope-widening changes." \
  --reference docs/specs/AUTH-MAGIC-LINK.goal.json \
  --reference docs/specs/magic-link-design.md \
  --priority 1 \
  --risk 4 \
  --value 5
```

Validate packets:

```bash
cdad validate --strict-paths --report
```

Expected outputs:

- `agent/packets/AUTH-ML-01.json`
- `agent/packets/AUTH-ML-01.md`
- `agent/reports/AUTH-ML-01-packet-validation.json`

The packet should answer:

- What is the one concrete objective?
- Why is this the next step?
- Which files should be loaded first?
- What must not change?
- How will the agent verify success?
- When should the agent stop and escalate?

## 7. Select The Next Packet

```bash
cdad next --heuristic dependency-first
cdad next --heuristic dependency-first --json
```

Other options:

```bash
cdad next --heuristic risk-first
cdad next --heuristic value-first
```

Use:

- `dependency-first` when packet order matters;
- `risk-first` when unknowns or approval boundaries dominate;
- `value-first` when several packets are independent.

## 8. Build A Context Bundle

```bash
cdad context AUTH-ML-01 --budget 12000
```

The context bundle includes:

- explicit packet files first;
- referenced goal/design docs;
- related tests;
- related architecture and decision notes;
- estimated token count and file scores.

Expected output:

```text
agent/verification/AUTH-ML-01-context.md
```

This is the bundle you can hand to an agent with the packet. It is intentionally smaller than the full repo.

## 9. Detect And Run Verification

Check what CDAD detects:

```bash
cdad verification
```

Run the packet verification:

```bash
cdad verify AUTH-ML-01
```

If runnable verification passes, CDAD updates:

- packet status to `Passed`;
- packet verification evidence path;
- packet Markdown rendering;
- `agent/verification/AUTH-ML-01-verification.md`.

## 10. Record Progress

```bash
cdad progress add AUTH-ML-01 \
  --goal "Magic link request handling" \
  --file src/auth/magic_link.py \
  --file tests/test_magic_link.py \
  --verification "PYTHONPATH=. python3 -m unittest discover -s tests -v passed" \
  --result Passed \
  --next "Create AUTH-ML-02 for HTTP endpoint routing."
```

Progress records are what let the next agent or next session resume without reconstructing intent from chat.

## 11. Review Traceability

```bash
cdad trace
cdad trace --json --output agent/reports/trace.json
```

You should see a row like:

```text
Goal             Packet      Status  Evidence                                  Progress
AUTH-MAGIC-LINK  AUTH-ML-01  Passed  AUTH-ML-01-context.md, verification.md   yes
```

The important point is that the packet is linked back to a goal and forward to evidence.

## 11a. Check Goal Coverage

```bash
cdad coverage --report
```

Coverage checks whether:

- packets are linked to goals;
- packet links point to existing goals;
- goals have at least some packet coverage.

Warnings usually mean “add more packets soon.” Errors mean the workflow is not traceable enough for CI.

## 12. Generate Benchmark Metrics

```bash
cdad benchmark --output agent/benchmarks/metrics.json
```

The report includes:

- total packets;
- passed packets;
- verification pass rate;
- context bundle token estimate;
- verification evidence count;
- progress entry count;
- rework mentions.
- average time to verified packet, based on packet timestamps.

This gives you a baseline for whether CDAD is helping or just adding ceremony.

## 13. Optional Agent Integrations

Generate thin command templates:

```bash
cdad integration generate --agent codex --force
cdad integration generate --agent claude-code --force
cdad integration generate --agent cursor --force
cdad integration generate --agent github-copilot --force
cdad integration generate --all --force
```

These templates tell agents to use CDAD artifacts. They do not embed a giant prompt.

## 14. Run CDAD In CI

```bash
cdad ci
```

CI runs the main quality gates:

- goal validation;
- packet validation with strict path checks;
- goal coverage, if enabled;
- benchmark thresholds.

Defaults live in `cdad.config.json`:

```json
{
  "context_token_budget": 8000,
  "ci": {
    "min_verification_pass_rate": 0.0,
    "max_rework_mentions": 0,
    "require_goal_coverage": true
  }
}
```

Use the config to tune token budgets and quality thresholds for your team.

## 15. Update Packet Lifecycle Manually

Most packets become `Passed` when `cdad verify` succeeds. For other states:

```bash
cdad packet status AUTH-ML-01 --status NeedsApproval
cdad packet status AUTH-ML-01 --status Blocked
cdad packet link-goal AUTH-ML-01 AUTH-MAGIC-LINK
```

Use manual status changes when the right answer is to pause, ask for approval, or repair traceability rather than keep coding.

## What Good Output Looks Like

A useful goal record is specific:

```markdown
## Objective
Add passwordless magic-link login request handling.

## Scope Out
- frontend login screen
- social login

## Verification
- [unit] PYTHONPATH=. python3 -m unittest discover -s tests -v
```

A useful task packet is narrower:

```markdown
## Objective
Implement and verify magic-link request behavior in the auth service.

## Relevant context
- src/auth/magic_link.py

## Verification
- [unit] PYTHONPATH=. python3 -m unittest discover -s tests -v
- [manual] valid email request returns queued status
```

A useful progress snapshot says what happened and what comes next:

```markdown
Passed. Verification: PYTHONPATH=. python3 -m unittest discover -s tests -v passed. Next recommended step: Create AUTH-ML-02 for HTTP endpoint routing.
```

## First-Project Checklist

- `cdad doctor` passes.
- Goal validation report is `passed`.
- Design validation report is `passed`.
- Packet validation report is `passed`.
- `cdad context` creates a bundle with relevant source, tests, and docs.
- `cdad verify <TASK_ID>` passes.
- Packet status becomes `Passed`.
- `cdad progress add` updates the progress log and packet snapshot.
- `cdad trace` shows goal -> packet -> evidence -> progress.
- `cdad trace --json` writes a machine-readable trace.
- `cdad coverage --report` has no errors.
- `cdad benchmark` writes metrics.
- `cdad ci` passes.

## Common Mistakes

- Starting with a task that is too large.
- Creating a goal without scope-out.
- Creating a packet without verification.
- Referencing files that do not exist.
- Letting the agent widen scope instead of creating a new packet.
- Treating the context bundle as permanent memory instead of a per-packet runtime input.

## Recommended Next Packet

After the first packet passes, create the next narrow increment:

```bash
cdad packet new AUTH-ML-02 \
  --goal-id AUTH-MAGIC-LINK \
  --objective "Expose the magic-link request behavior through an HTTP endpoint." \
  --why-now "The service is verified and now needs a route for clients." \
  --context src/auth/routes.py \
  --context src/auth/magic_link.py \
  --constraint "Do not change token expiry." \
  --verify "PYTHONPATH=. python3 -m unittest discover -s tests -v" \
  --reference docs/specs/AUTH-MAGIC-LINK.goal.json \
  --depends-on AUTH-ML-01 \
  --priority 2 \
  --risk 3 \
  --value 5
```

That is the CDAD loop: goal, design, packet, context, verify, progress, repeat.
