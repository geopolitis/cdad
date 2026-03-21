# CDAD Tools Release Guide

This project is currently a lightweight Python CLI with no runtime dependencies. The release process should preserve that property unless a dependency has a clear adoption benefit.

## Versioning

Use semantic versioning:

- patch: bug fixes and validation-rule clarifications;
- minor: new CLI commands, report fields, or backward-compatible schema additions;
- major: breaking schema or command contract changes.

Update the version in:

- `pyproject.toml`
- `src/cdad_tools/__init__.py`

## Local Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m cdad_tools.cli --root . validate --strict-paths --report
PYTHONPATH=src python3 -m cdad_tools.cli --root . goal validate --report
PYTHONPATH=src python3 -m cdad_tools.cli --root . coverage --report
PYTHONPATH=src python3 -m cdad_tools.cli --root . trace --json --output agent/reports/trace.json
PYTHONPATH=src python3 -m cdad_tools.cli --root . benchmark --output agent/benchmarks/metrics.json
PYTHONPATH=src python3 -m cdad_tools.cli --root . ci
```

## Build Check

When packaging tools are available:

```bash
python3 -m pip install --upgrade build
python3 -m build
```

Inspect the wheel contents before publishing.

## Release Checklist

- Tests pass.
- `cdad ci` passes.
- `docs/first-project-guide.md` matches current commands.
- `README.md` includes newly added command groups.
- Packet schemas remain backward compatible or the version is bumped appropriately.
- Generated reports are refreshed if examples changed.

## Install From Source

```bash
python3 -m pip install -e .
cdad --help
```

## CI

The repository includes `.github/workflows/cdad.yml`, which runs unit tests and `cdad ci`.

