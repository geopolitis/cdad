# CDAD Automation Plan

## Purpose

Build a lightweight automation layer that helps engineers and architects turn CDAD artifacts into agent-ready task packets, validate prompt/design quality, assemble compact context, route verification, and preserve resumable progress.

## Product Direction

CDAD differs from SPDD-style design-contract tooling by treating prompts and designs as source material, not as the main runtime object. The core runtime artifact is a compact, typed task packet with retrieval pointers, constraints, verification, escalation boundaries, and progress state.

## MVP Features

1. `cdad init`
   - Creates the default CDAD layout from the user guide.
   - Adds concise project memory and progress log starter files.

2. Canonical packet schema
   - Uses JSON as the machine-readable source of truth.
   - Renders Markdown for human review.
   - Defines packet states: `Draft`, `Ready`, `InProgress`, `Passed`, `Blocked`, `NeedsApproval`, `Ambiguous`.
   - Defines verification taxonomy: `unit`, `integration`, `e2e`, `visual`, `security`, `policy`, `evidence`, `manual`, `lint`, `typecheck`, `build`.

3. `cdad packet new`
   - Creates a task packet from command-line inputs.
   - Generates both canonical JSON and human Markdown rendering.

4. `cdad validate`
   - Checks required packet fields.
   - Flags verification-free packets.
   - Flags missing escalation boundaries.
   - Optionally checks that referenced local context paths exist.

5. `cdad context`
   - Builds a compact context bundle from packet `relevant_context` and `references`.
   - Estimates token cost.
   - Writes evidence under `agent/verification`.

6. `cdad verify`
   - Runs packet verification commands.
   - Captures stdout, stderr, return codes, and timestamped evidence.

7. `cdad progress add`
   - Appends CDAD-compatible progress entries.
   - Keeps resumed sessions from reconstructing intent from chat.

8. `cdad trace`
   - Maps packet status to references and evidence artifacts.
   - Provides the first traceability view from intent to execution evidence.

9. `cdad doctor`
   - Checks whether the expected CDAD folders exist.

10. `cdad goal new` / `cdad goal validate`
    - Creates durable goal records.
    - Validates objective, scope, constraints, risks, verification, approval boundaries, and quality bar.

11. `cdad design validate`
    - Validates Markdown prompt/design artifacts.
    - Emits machine-readable JSON validation reports.

12. `cdad next`
    - Selects next packet with dependency-first, risk-first, or value-first heuristics.

13. Improved `cdad context`
    - Includes explicit packet paths.
    - Searches related tests, decisions, architecture notes, and specs.
    - Scores included files in the context bundle.

14. `cdad integration generate`
    - Generates thin agent commands for Codex, Claude Code, Cursor, and GitHub Copilot.

15. `cdad verification`
    - Detects likely project verification commands from common project files.
    - Classifies runnable evidence as unit, lint, typecheck, build, e2e, or manual.

16. `cdad benchmark`
    - Emits metrics for packet pass rate, context bundle size, verification evidence count, progress entries, and rework mentions.

17. `cdad trace --json`
    - Emits machine-readable trace data for automation and CI.

18. `cdad coverage --report`
    - Checks packet-to-goal links and thin goal coverage.

19. Packet lifecycle commands
    - `cdad packet status` updates lifecycle state.
    - `cdad packet link-goal` repairs explicit goal links.

20. `cdad ci`
    - Runs goal validation, packet validation, coverage, and benchmark gates.
    - Reads thresholds and policy from `cdad.config.json`.

## Suggested Structure

```text
project/
  docs/
    architecture/
    decisions/
    specs/
  agent/
    memory/
      project.md
    packets/
      TASK-ID.json
      TASK-ID.md
    progress/
      progress.md
    verification/
      TASK-ID-context.md
      TASK-ID-verification.md
  src/
    cdad_tools/
  tests/
```

## Near-Term Roadmap

1. Stronger design analysis
   - Add consistency checks between scope, risks, constraints, and verification.
   - Add severity override/configuration.

2. Richer context ranking
   - Add symbol/name extraction and changed-file history when a git repository is available.
   - Add configurable token budgets per model or agent.

3. Traceability map
   - Parse changed files from progress entries into structured records.

4. Benchmarking
   - Add explicit reopen/rework event recording instead of keyword inference.
   - Improve time-to-verified-change by using verification evidence timestamps rather than packet update time.

5. Release operations
   - Add publishing automation once the package name and distribution target are decided.

## Test Plan

- Unit-test packet validation for complete and incomplete packets.
- Unit-test token estimation and context bundling.
- CLI-test `init`, `packet new`, `validate`, `context`, `progress add`, `verify`, and `trace` in temporary directories.
- Add regression tests whenever packet schema fields or command output contracts change.
