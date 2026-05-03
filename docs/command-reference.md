# CDAD Command Reference

All commands accept `--root <path>`. If omitted, CDAD uses the current directory.

## `cdad init`

Creates the CDAD folder layout and `cdad.config.json`.

```bash
cdad init
```

## `cdad doctor`

Checks that required CDAD folders exist.

```bash
cdad doctor
```

## `cdad goal new`

Creates a durable goal record as JSON and Markdown.

```bash
cdad goal new GOAL-ID \
  --objective "..." \
  --scope-in "..." \
  --scope-out "..." \
  --constraint "..." \
  --risk "..." \
  --quality-bar "..." \
  --verify "..."
```

Output:

- `docs/specs/<GOAL-ID>.goal.json`
- `docs/specs/<GOAL-ID>.goal.md`

## `cdad goal validate`

Validates goal records.

```bash
cdad goal validate --report
```

Output:

- `agent/reports/<GOAL-ID>-goal-validation.json`

## `cdad design validate`

Validates Markdown prompt/design/spec files for required CDAD sections and basic consistency.

```bash
cdad design validate docs/specs/my-design.md --report
```

Checks:

- objective
- scope in
- scope out
- constraints
- risks
- verification
- approval boundaries
- objective/scope-out conflicts
- token/security risk coverage in verification
- constraint/approval-boundary alignment

## `cdad packet new`

Creates a task packet as canonical JSON and reviewable Markdown.

```bash
cdad packet new TASK-ID \
  --goal-id GOAL-ID \
  --objective "..." \
  --why-now "..." \
  --context path/to/file \
  --constraint "..." \
  --verify "..." \
  --reference docs/specs/GOAL-ID.goal.json \
  --priority 1 \
  --risk 4 \
  --value 5
```

Output:

- `agent/packets/<TASK-ID>.json`
- `agent/packets/<TASK-ID>.md`

## `cdad packet render`

Regenerates packet Markdown from JSON.

```bash
cdad packet render TASK-ID
```

## `cdad packet status`

Updates packet lifecycle state.

```bash
cdad packet status TASK-ID --status NeedsApproval
cdad packet status TASK-ID --status Blocked
cdad packet status TASK-ID --status Ready
```

Statuses:

- `Draft`
- `Ready`
- `InProgress`
- `Passed`
- `Blocked`
- `NeedsApproval`
- `Ambiguous`

## `cdad packet link-goal`

Links or repairs packet-to-goal traceability.

```bash
cdad packet link-goal TASK-ID GOAL-ID
```

## `cdad validate`

Validates packet schemas.

```bash
cdad validate --strict-paths --report
```

`--strict-paths` checks local `relevant_context` paths exist.

## `cdad next`

Selects the next unblocked open packet.

```bash
cdad next --heuristic dependency-first
cdad next --heuristic risk-first
cdad next --heuristic value-first
cdad next --heuristic dependency-first --json
```

## `cdad context`

Builds a ranked context bundle for one packet.

```bash
cdad context TASK-ID --budget 12000
```

Output:

- `agent/verification/<TASK-ID>-context.md`

The bundle includes explicit packet context, references, related source files, tests, decisions, architecture notes, and specs.

## `cdad verification`

Detects likely verification commands without running them.

```bash
cdad verification
```

## `cdad verify`

Runs packet verification commands and writes evidence.

```bash
cdad verify TASK-ID
```

If runnable verification passes, CDAD updates:

- packet status to `Passed`
- verification evidence paths
- packet Markdown rendering

## `cdad progress add`

Appends a resumable progress entry and updates the packet progress snapshot.

```bash
cdad progress add TASK-ID \
  --result Passed \
  --file src/example.py \
  --verification "tests passed" \
  --next "Create next packet."
```

## `cdad trace`

Shows goal -> packet -> evidence -> progress.

```bash
cdad trace
cdad trace --json --output agent/reports/trace.json
```

## `cdad coverage`

Checks goal-to-packet coverage.

```bash
cdad coverage --report
```

Output:

- `agent/reports/goal-coverage.json`

## `cdad benchmark`

Emits workflow metrics.

```bash
cdad benchmark --output agent/benchmarks/metrics.json
```

Metrics:

- packet count
- passed packet count
- verification pass rate
- context bundle token estimate
- verification evidence count
- progress entry count
- rework mentions
- average time to verified packet

## `cdad toon`

Converts JSON or Markdown artifacts to TOON-style compact notation for lower context footprint.

```bash
cdad toon agent/packets/AUTH-ML-01.json --output agent/packets/AUTH-ML-01.toon --stats
cdad toon docs/specs/magic-link-design.md --format md --output docs/specs/magic-link-design.toon
```

Efficiency guidance:

- JSON -> TOON is the preferred path because CDAD JSON is already typed and structured.
- Markdown -> TOON is best-effort: headings and bullets are preserved, but the converter must infer structure.
- Use `--stats` before adopting a TOON export in an integration. Structured packet JSON should shrink; prose-heavy Markdown can grow.
- Keep canonical artifacts as JSON/Markdown; use TOON as a runtime context export.

## `cdad integration generate`

Generates thin agent integration templates.

```bash
cdad integration generate --agent codex --force
cdad integration generate --agent claude-code --force
cdad integration generate --agent cursor --force
cdad integration generate --agent github-copilot --force
cdad integration generate --all --force
```

## `cdad ci`

Runs CDAD quality gates for CI.

```bash
cdad ci
```

Configured by `cdad.config.json`.
