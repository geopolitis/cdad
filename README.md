# CDAD Tools

Lightweight automation for Context-Disciplined Agent Development.

The CLI helps teams turn durable goals and designs into compact, verifiable task packets for AI coding agents. It focuses on packetization, validation, context budgeting, verification routing, progress compression, and traceability.

```bash
python -m cdad_tools.cli init
python -m cdad_tools.cli goal new AUTH-ML --objective "Add passwordless email login" --scope-in "magic link backend" --scope-out "social login" --constraint "reuse email provider" --risk "token leakage" --quality-bar "expired links rejected" --verify "npm test -- auth"
python -m cdad_tools.cli packet new AUTH-ML-02 --objective "Implement backend endpoint" --why-now "Frontend flow needs link issuance" --context src/auth/routes.ts --verify "npm test -- tests/auth/magicLink.request.test.ts"
python -m cdad_tools.cli validate
python -m cdad_tools.cli design validate docs/specs/passwordless-login.md --report
python -m cdad_tools.cli next --heuristic risk-first
python -m cdad_tools.cli next --heuristic risk-first --json
python -m cdad_tools.cli context AUTH-ML-02 --budget 6000
python -m cdad_tools.cli verify AUTH-ML-02
python -m cdad_tools.cli progress add AUTH-ML-02 --result Passed --verification "npm test passed" --next "Create frontend packet"
python -m cdad_tools.cli trace
python -m cdad_tools.cli trace --json --output agent/reports/trace.json
python -m cdad_tools.cli coverage --report
python -m cdad_tools.cli benchmark --output agent/benchmarks/metrics.json
python -m cdad_tools.cli toon agent/packets/AUTH-ML-02.json --output agent/packets/AUTH-ML-02.toon --stats
python -m cdad_tools.cli ci
```

Install locally while developing:

```bash
python -m pip install -e .
cdad --help
```

Implemented command groups:

- `goal`: create and validate durable goal records.
- `packet`: create and render agent runtime packets linked to goals.
- `validate`: validate packet schema and optionally write JSON reports.
- `design validate`: check prompt/design files for objective, scope, constraints, risks, verification, and approval boundaries.
- `next`: select the next packet by dependency-first, risk-first, or value-first heuristics, with optional JSON output.
- `context`: build ranked context bundles from explicit packet paths plus related tests/docs.
- `verification`: detect likely project verification commands.
- `verify`: run packet commands and classify evidence.
- `integration generate`: write thin commands for Codex, Claude Code, Cursor, and GitHub Copilot; use `--all` to generate all supported templates.
- `trace`: map goal -> packet -> evidence -> progress.
- `coverage`: check goal-to-packet linkage and thin coverage.
- `benchmark`: report workflow metrics.
- `toon`: convert JSON or Markdown artifacts to compact TOON for lower context footprint.
- `ci`: run CDAD validation, coverage, and benchmark gates from `cdad.config.json`.
- `packet status` / `packet link-goal`: update lifecycle state and goal links.

Release and CI notes are in `docs/release.md`. The GitHub Actions workflow is `.github/workflows/cdad.yml`.

Documentation:

- [User Guide](https://www.opsatscale.com/opsatscale-framework/cdad-user-guide/)
- [Quickstart](docs/quickstart.md)
- [Start Now Guide](docs/start-now-guide.md)
- [Command Reference](docs/command-reference.md)
- [First Project Guide](docs/first-project-guide.md)
- [Release Guide](docs/release.md)
- [Command Snapshots](docs/snapshots/)
