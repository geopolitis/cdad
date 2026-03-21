from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

from .benchmark import collect_benchmark_metrics, render_benchmark_report
from .config import load_config
from .context import collect_context, render_context_bundle
from .coverage import analyze_goal_coverage, render_coverage_report
from .design_validation import render_validation_report, validate_design_file
from .integrations import SUPPORTED_AGENTS, generate_all_integrations, generate_integration
from .next import blocked_packets, load_packets, next_packet, packet_to_summary
from .project import evidence_path, goal_markdown_path, goal_path, init_project, packet_markdown_path, packet_path, report_path
from .schema import (
    GoalRecord,
    PacketStatus,
    TaskPacket,
    Verification,
    VerificationKind,
    load_goal,
    load_packet,
    render_goal_markdown,
    render_packet_markdown,
    save_goal,
    save_packet,
    validate_goal,
    validate_packet,
)
from .verification import detect_verification_commands, run_packet_verification
from .trace import render_trace_json, render_trace_markdown
from .toon import file_to_toon, toon_stats


def project_root(args: argparse.Namespace) -> Path:
    return Path(args.root).resolve()


def clean_list(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cdad", description="Context-Disciplined Agent Development CLI")
    parser.add_argument("--root", default=".", help="Project root")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create the default CDAD project layout")

    goal = sub.add_parser("goal", help="Manage durable CDAD goal records")
    goal_sub = goal.add_subparsers(dest="goal_command", required=True)
    new_goal = goal_sub.add_parser("new", help="Create a canonical goal record and Markdown rendering")
    new_goal.add_argument("goal_id")
    new_goal.add_argument("--objective", required=True)
    new_goal.add_argument("--scope-in", action="append", default=[])
    new_goal.add_argument("--scope-out", action="append", default=[])
    new_goal.add_argument("--constraint", action="append", default=[])
    new_goal.add_argument("--risk", action="append", default=[])
    new_goal.add_argument("--approval", action="append", default=[])
    new_goal.add_argument("--quality-bar", default="")
    new_goal.add_argument("--verify", action="append", default=[])
    new_goal.add_argument("--scenario", action="append", default=[])
    new_goal.add_argument("--force", action="store_true")
    validate_goal_cmd = goal_sub.add_parser("validate", help="Validate goal records")
    validate_goal_cmd.add_argument("paths", nargs="*")
    validate_goal_cmd.add_argument("--report", action="store_true", help="Write JSON validation report")

    packet = sub.add_parser("packet", help="Manage task packets")
    packet_sub = packet.add_subparsers(dest="packet_command", required=True)
    new_packet = packet_sub.add_parser("new", help="Create a canonical packet JSON and Markdown rendering")
    new_packet.add_argument("task_id")
    new_packet.add_argument("--objective", required=True)
    new_packet.add_argument("--why-now", required=True)
    new_packet.add_argument("--goal-id", default="")
    new_packet.add_argument("--context", action="append", default=[])
    new_packet.add_argument("--interface", action="append", default=[])
    new_packet.add_argument("--constraint", action="append", default=[])
    new_packet.add_argument("--verify", action="append", default=[], help="Runnable verification command")
    new_packet.add_argument("--scenario", action="append", default=[], help="Manual or BDD-style scenario")
    new_packet.add_argument("--escalate", action="append", default=[])
    new_packet.add_argument("--reference", action="append", default=[])
    new_packet.add_argument("--depends-on", action="append", default=[])
    new_packet.add_argument("--priority", type=int, default=3)
    new_packet.add_argument("--risk", type=int, default=3)
    new_packet.add_argument("--value", type=int, default=3)
    new_packet.add_argument("--status", choices=[x.value for x in PacketStatus], default=PacketStatus.DRAFT.value)
    new_packet.add_argument("--force", action="store_true")

    render_packet = packet_sub.add_parser("render", help="Render packet Markdown from canonical JSON")
    render_packet.add_argument("task_id")
    packet_status = packet_sub.add_parser("status", help="Update packet lifecycle status")
    packet_status.add_argument("task_id")
    packet_status.add_argument("--status", choices=[x.value for x in PacketStatus], required=True)
    packet_link_goal = packet_sub.add_parser("link-goal", help="Link a packet to a goal")
    packet_link_goal.add_argument("task_id")
    packet_link_goal.add_argument("goal_id")

    validate = sub.add_parser("validate", help="Validate packet schemas and CDAD layout")
    validate.add_argument("paths", nargs="*", help="Specific packet JSON files to validate")
    validate.add_argument("--strict-paths", action="store_true", help="Require relevant_context paths to exist")
    validate.add_argument("--report", action="store_true", help="Write JSON validation report")

    design = sub.add_parser("design", help="Validate prompt/design artifacts")
    design_sub = design.add_subparsers(dest="design_command", required=True)
    design_validate = design_sub.add_parser("validate", help="Validate Markdown prompt/design files")
    design_validate.add_argument("paths", nargs="+")
    design_validate.add_argument("--report", action="store_true", help="Write machine-readable reports")

    context = sub.add_parser("context", help="Create a compact context bundle for a packet")
    context.add_argument("task_id")
    context.add_argument("--budget", type=int, default=8000, help="Estimated token budget")
    context.add_argument("--no-discovery", action="store_true", help="Only include explicit packet paths")
    context.add_argument("--stdout", action="store_true", help="Print instead of writing evidence file")

    verify = sub.add_parser("verify", help="Run packet verification commands and save evidence")
    verify.add_argument("task_id")
    verify.add_argument("--timeout", type=int, default=600)

    sub.add_parser("verification", help="Detect project verification commands")

    next_cmd = sub.add_parser("next", help="Choose the next packet")
    next_cmd.add_argument("--heuristic", choices=["dependency-first", "risk-first", "value-first"], default="dependency-first")
    next_cmd.add_argument("--show-blocked", action="store_true")
    next_cmd.add_argument("--json", action="store_true", help="Emit structured selection output")

    integration = sub.add_parser("integration", help="Generate thin agent integration commands")
    integration_sub = integration.add_subparsers(dest="integration_command", required=True)
    integration_generate = integration_sub.add_parser("generate")
    integration_generate.add_argument("--agent", choices=SUPPORTED_AGENTS, required=False)
    integration_generate.add_argument("--all", action="store_true", help="Generate all supported integrations")
    integration_generate.add_argument("--force", action="store_true")

    progress = sub.add_parser("progress", help="Append resumable progress entries")
    progress_sub = progress.add_subparsers(dest="progress_command", required=True)
    progress_add = progress_sub.add_parser("add")
    progress_add.add_argument("task_id")
    progress_add.add_argument("--result", required=True)
    progress_add.add_argument("--goal", default="")
    progress_add.add_argument("--file", action="append", default=[])
    progress_add.add_argument("--verification", action="append", default=[])
    progress_add.add_argument("--open-issue", action="append", default=[])
    progress_add.add_argument("--next", required=True)

    trace = sub.add_parser("trace", help="Print requirement to packet to evidence traceability")
    trace.add_argument("--json", action="store_true", help="Emit structured JSON")
    trace.add_argument("--output", default="", help="Optional output path")
    coverage = sub.add_parser("coverage", help="Analyze goal-to-packet coverage")
    coverage.add_argument("--report", action="store_true", help="Write JSON coverage report")
    benchmark = sub.add_parser("benchmark", help="Emit CDAD workflow metrics")
    benchmark.add_argument("--output", default="", help="Optional JSON output path")
    toon = sub.add_parser("toon", help="Convert JSON or Markdown to token-oriented object notation")
    toon.add_argument("path", help="Input JSON or Markdown file")
    toon.add_argument("--format", choices=["auto", "json", "md", "markdown"], default="auto")
    toon.add_argument("--output", default="", help="Optional TOON output path")
    toon.add_argument("--stats", action="store_true", help="Print estimated token savings to stderr")
    sub.add_parser("ci", help="Run CDAD quality gates for CI")
    sub.add_parser("doctor", help="Check for expected CDAD folders")
    return parser


def command_init(args: argparse.Namespace) -> int:
    root = project_root(args)
    created = init_project(root)
    for path in created:
        print(f"created {path.relative_to(root)}")
    return 0


def command_packet_new(args: argparse.Namespace) -> int:
    root = project_root(args)
    init_project(root)
    target = packet_path(root, args.task_id)
    if target.exists() and not args.force:
        print(f"packet exists: {target}", file=sys.stderr)
        return 2
    verification = [Verification(VerificationKind.UNIT, command=cmd) for cmd in args.verify]
    verification.extend(Verification(VerificationKind.MANUAL, scenario=scenario) for scenario in args.scenario)
    packet = TaskPacket(
        task_id=args.task_id,
        objective=args.objective,
        why_now=args.why_now,
        goal_id=args.goal_id,
        relevant_context=clean_list(args.context),
        interfaces_touched=clean_list(args.interface),
        constraints=clean_list(args.constraint) or ["Stay inside packet scope."],
        verification=verification,
        escalation_conditions=args.escalate
        or ["Escalate dependency, schema, contract, security boundary, destructive, or scope-widening changes."],
        references=clean_list(args.reference),
        depends_on=clean_list(args.depends_on),
        priority=args.priority,
        risk=args.risk,
        value=args.value,
        status=PacketStatus(args.status),
    )
    save_packet(packet, target)
    packet_markdown_path(root, args.task_id).write_text(render_packet_markdown(packet), encoding="utf-8")
    print(f"created {target.relative_to(root)}")
    return 0


def command_goal_new(args: argparse.Namespace) -> int:
    root = project_root(args)
    init_project(root)
    target = goal_path(root, args.goal_id)
    if target.exists() and not args.force:
        print(f"goal exists: {target}", file=sys.stderr)
        return 2
    verification = [Verification(VerificationKind.UNIT, command=cmd) for cmd in args.verify]
    verification.extend(Verification(VerificationKind.MANUAL, scenario=scenario) for scenario in args.scenario)
    goal = GoalRecord(
        goal_id=args.goal_id,
        objective=args.objective,
        scope_in=clean_list(args.scope_in),
        scope_out=clean_list(args.scope_out),
        constraints=clean_list(args.constraint),
        verification=verification,
        risks=clean_list(args.risk),
        approval_boundaries=clean_list(args.approval)
        or ["Approve dependency, schema, contract, security boundary, destructive, or scope-widening changes."],
        quality_bar=args.quality_bar,
    )
    save_goal(goal, target)
    goal_markdown_path(root, args.goal_id).write_text(render_goal_markdown(goal), encoding="utf-8")
    print(f"created {target.relative_to(root)}")
    return 0


def command_goal_validate(args: argparse.Namespace) -> int:
    root = project_root(args)
    paths = [Path(p) for p in args.paths]
    if not paths:
        paths = sorted((root / "docs/specs").glob("*.goal.json"))
    ok = True
    if not paths:
        print("no goals found")
    for path in paths:
        actual = path if path.is_absolute() else root / path
        goal = load_goal(actual)
        issues = validate_goal(goal)
        if args.report:
            report = {
                "schema": "cdad.goal_validation_report.v1",
                "path": str(actual.relative_to(root)),
                "status": "failed" if issues else "passed",
                "findings": [{"severity": "error", "message": issue} for issue in issues],
            }
            target = report_path(root, f"{goal.goal_id}-goal-validation.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            import json

            target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {target.relative_to(root)}")
        if issues:
            ok = False
            print(f"{actual.relative_to(root)}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"{actual.relative_to(root)}: ok")
    return 0 if ok else 1


def command_packet_render(args: argparse.Namespace) -> int:
    root = project_root(args)
    packet = load_packet(packet_path(root, args.task_id))
    rendered = render_packet_markdown(packet)
    packet_markdown_path(root, args.task_id).write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


def command_packet_status(args: argparse.Namespace) -> int:
    root = project_root(args)
    packet = load_packet(packet_path(root, args.task_id))
    packet.status = PacketStatus(args.status)
    save_packet(packet, packet_path(root, args.task_id))
    packet_markdown_path(root, args.task_id).write_text(render_packet_markdown(packet), encoding="utf-8")
    print(f"updated {packet_path(root, args.task_id).relative_to(root)}")
    return 0


def command_packet_link_goal(args: argparse.Namespace) -> int:
    root = project_root(args)
    if not goal_path(root, args.goal_id).exists():
        print(f"goal not found: {args.goal_id}", file=sys.stderr)
        return 1
    packet = load_packet(packet_path(root, args.task_id))
    packet.goal_id = args.goal_id
    save_packet(packet, packet_path(root, args.task_id))
    packet_markdown_path(root, args.task_id).write_text(render_packet_markdown(packet), encoding="utf-8")
    print(f"linked {args.task_id} -> {args.goal_id}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    root = project_root(args)
    paths = [Path(p) for p in args.paths]
    if not paths:
        paths = sorted((root / "agent/packets").glob("*.json"))
    ok = True
    if not paths:
        print("no packets found")
    for path in paths:
        actual = path if path.is_absolute() else root / path
        packet = load_packet(actual)
        issues = validate_packet(packet, root if args.strict_paths else None)
        if args.report:
            report = {
                "schema": "cdad.packet_validation_report.v1",
                "path": str(actual.relative_to(root)),
                "status": "failed" if issues else "passed",
                "findings": [{"severity": "error", "message": issue} for issue in issues],
            }
            target = report_path(root, f"{packet.task_id}-packet-validation.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            import json

            target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {target.relative_to(root)}")
        if issues:
            ok = False
            print(f"{actual.relative_to(root)}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"{actual.relative_to(root)}: ok")
    return 0 if ok else 1


def command_design_validate(args: argparse.Namespace) -> int:
    root = project_root(args)
    ok = True
    for raw in args.paths:
        path = Path(raw)
        actual = path if path.is_absolute() else root / path
        findings = validate_design_file(actual)
        if args.report:
            target = report_path(root, f"{actual.stem}-design-validation.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_validation_report(actual.relative_to(root), findings), encoding="utf-8")
            print(f"wrote {target.relative_to(root)}")
        if findings:
            print(f"{actual.relative_to(root)}:")
            for finding in findings:
                print(f"  - [{finding.severity.value}] {finding.message}")
        else:
            print(f"{actual.relative_to(root)}: ok")
        if any(finding.severity.value == "error" for finding in findings):
            ok = False
    return 0 if ok else 1


def command_context(args: argparse.Namespace) -> int:
    root = project_root(args)
    config = load_config(root)
    packet = load_packet(packet_path(root, args.task_id))
    budget = args.budget if args.budget != 8000 else config.context_token_budget
    items, warnings = collect_context(root, packet, budget, include_discovered=not args.no_discovery)
    bundle = render_context_bundle(packet, items, warnings)
    if args.stdout:
        print(bundle, end="")
    else:
        target = evidence_path(root, args.task_id, "context.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(bundle, encoding="utf-8")
        print(f"wrote {target.relative_to(root)}")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    root = project_root(args)
    packet = load_packet(packet_path(root, args.task_id))
    runs, log = run_packet_verification(root, packet, args.timeout)
    target = evidence_path(root, args.task_id, "verification.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(log, encoding="utf-8")
    if runs and all(run.returncode == 0 for run in runs):
        for item in packet.verification:
            if item.command:
                item.evidence_path = str(target.relative_to(root))
        packet.status = PacketStatus.PASSED
        save_packet(packet, packet_path(root, args.task_id))
        packet_markdown_path(root, args.task_id).write_text(render_packet_markdown(packet), encoding="utf-8")
    print(f"wrote {target.relative_to(root)}")
    return 0 if all(run.returncode == 0 for run in runs) else 1


def command_progress_add(args: argparse.Namespace) -> int:
    root = project_root(args)
    init_project(root)
    target = root / "agent/progress/progress.md"
    timestamp = datetime.now(timezone.utc).isoformat()
    files = ", ".join(args.file) if args.file else "None recorded"
    verification = "; ".join(args.verification) if args.verification else "None recorded"
    issues = "; ".join(args.open_issue) if args.open_issue else "None"
    entry = f"""## {timestamp} {args.task_id}
- Goal worked on: {args.goal or args.task_id}
- Files changed: {files}
- Verification run: {verification}
- Result: {args.result}
- Open issues: {issues}
- Next recommended step: {args.next}

"""
    with target.open("a", encoding="utf-8") as handle:
        handle.write(entry)
    packet_file = packet_path(root, args.task_id)
    if packet_file.exists():
        packet = load_packet(packet_file)
        packet.progress_snapshot = (
            f"{args.result}. Verification: {verification}. Next recommended step: {args.next}"
        )
        if args.result in {status.value for status in PacketStatus}:
            packet.status = PacketStatus(args.result)
        save_packet(packet, packet_file)
        packet_markdown_path(root, args.task_id).write_text(render_packet_markdown(packet), encoding="utf-8")
    print(f"updated {target.relative_to(root)}")
    return 0


def command_trace(args: argparse.Namespace) -> int:
    root = project_root(args)
    rendered = render_trace_json(root) if args.json else render_trace_markdown(root)
    if args.output:
        target = Path(args.output)
        actual = target if target.is_absolute() else root / target
        actual.parent.mkdir(parents=True, exist_ok=True)
        actual.write_text(rendered, encoding="utf-8")
        print(f"wrote {actual.relative_to(root)}")
    else:
        print(rendered, end="")
    return 0


def command_coverage(args: argparse.Namespace) -> int:
    root = project_root(args)
    findings = analyze_goal_coverage(root)
    if args.report:
        target = report_path(root, "goal-coverage.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_coverage_report(root), encoding="utf-8")
        print(f"wrote {target.relative_to(root)}")
    if findings:
        for finding in findings:
            print(f"[{finding.severity}] {finding.message}")
    else:
        print("goal coverage: ok")
    return 0 if not any(finding.severity == "error" for finding in findings) else 1


def command_verification(args: argparse.Namespace) -> int:
    root = project_root(args)
    commands = detect_verification_commands(root)
    if not commands:
        print("no verification commands detected")
        return 1
    for kind, command in commands:
        print(f"[{kind.value}] {command}")
    return 0


def command_next(args: argparse.Namespace) -> int:
    root = project_root(args)
    packets = load_packets(root)
    selected = next_packet(packets, args.heuristic)
    blocked = blocked_packets(packets)
    if args.json:
        payload = {
            "schema": "cdad.next_selection.v1",
            "heuristic": args.heuristic,
            "selected": packet_to_summary(selected, args.heuristic) if selected else None,
            "blocked": [packet_to_summary(packet, args.heuristic) for packet in blocked],
        }
        print(json.dumps(payload, indent=2))
        return 0 if selected else 1
    if selected is None:
        print("no unblocked open packets")
    else:
        summary = packet_to_summary(selected, args.heuristic)
        print(
            f"{selected.task_id} ({selected.status.value}) goal={selected.goal_id or 'None'} "
            f"priority={selected.priority} risk={selected.risk} value={selected.value} reason={summary['rank_reason']}"
        )
    if args.show_blocked:
        for packet in blocked:
            print(f"blocked {packet.task_id}: waiting on {', '.join(packet.depends_on)}")
    return 0 if selected else 1


def command_integration_generate(args: argparse.Namespace) -> int:
    root = project_root(args)
    try:
        if args.all:
            targets = generate_all_integrations(root, args.force)
            for target in targets:
                print(f"wrote {target.relative_to(root)}")
            return 0
        if not args.agent:
            print("choose --agent or --all", file=sys.stderr)
            return 2
        target = generate_integration(root, args.agent, args.force)
    except FileExistsError as exc:
        print(f"integration exists: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {target.relative_to(root)}")
    return 0


def command_benchmark(args: argparse.Namespace) -> int:
    root = project_root(args)
    report = render_benchmark_report(root)
    if args.output:
        target = Path(args.output)
        actual = target if target.is_absolute() else root / target
        actual.parent.mkdir(parents=True, exist_ok=True)
        actual.write_text(report, encoding="utf-8")
        print(f"wrote {actual.relative_to(root)}")
    else:
        print(report, end="")
    return 0


def command_toon(args: argparse.Namespace) -> int:
    root = project_root(args)
    path = Path(args.path)
    actual = path if path.is_absolute() else root / path
    original = actual.read_text(encoding="utf-8", errors="replace")
    rendered = file_to_toon(actual, args.format)
    if args.output:
        target = Path(args.output)
        output = target if target.is_absolute() else root / target
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"wrote {output.relative_to(root)}")
    else:
        print(rendered, end="")
    if args.stats:
        print(json.dumps(toon_stats(original, rendered), indent=2), file=sys.stderr)
    return 0


def command_ci(args: argparse.Namespace) -> int:
    root = project_root(args)
    config = load_config(root)
    ok = True
    for path in sorted((root / "docs/specs").glob("*.goal.json")):
        issues = validate_goal(load_goal(path))
        for issue in issues:
            print(f"[goal] {path.relative_to(root)}: {issue}")
        ok = ok and not issues
    for path in sorted((root / "agent/packets").glob("*.json")):
        issues = validate_packet(load_packet(path), root)
        for issue in issues:
            print(f"[packet] {path.relative_to(root)}: {issue}")
        ok = ok and not issues
    if config.require_goal_coverage:
        findings = analyze_goal_coverage(root)
        for finding in findings:
            print(f"[coverage:{finding.severity}] {finding.message}")
        ok = ok and not any(finding.severity == "error" for finding in findings)
    if config.require_design_reports:
        reports = list((root / "agent/reports").glob("*design-validation.json"))
        if not reports:
            print("[design] no design validation reports found")
            ok = False
    metrics = collect_benchmark_metrics(root)
    if metrics.verification_pass_rate < config.min_verification_pass_rate:
        print(f"[benchmark] verification pass rate {metrics.verification_pass_rate} below {config.min_verification_pass_rate}")
        ok = False
    if metrics.rework_mentions > config.max_rework_mentions:
        print(f"[benchmark] rework mentions {metrics.rework_mentions} above {config.max_rework_mentions}")
        ok = False
    if ok:
        print("cdad ci: ok")
    return 0 if ok else 1


def command_doctor(args: argparse.Namespace) -> int:
    root = project_root(args)
    expected = [
        "docs/architecture",
        "docs/decisions",
        "docs/specs",
        "agent/memory",
        "agent/packets",
        "agent/progress",
        "agent/verification",
        "agent/reports",
        "agent/integrations",
        "agent/benchmarks",
    ]
    missing = [path for path in expected if not (root / path).is_dir()]
    if missing:
        for path in missing:
            print(f"missing {path}")
        return 1
    print("cdad layout: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        return command_init(args)
    if args.command == "goal" and args.goal_command == "new":
        return command_goal_new(args)
    if args.command == "goal" and args.goal_command == "validate":
        return command_goal_validate(args)
    if args.command == "packet" and args.packet_command == "new":
        return command_packet_new(args)
    if args.command == "packet" and args.packet_command == "render":
        return command_packet_render(args)
    if args.command == "packet" and args.packet_command == "status":
        return command_packet_status(args)
    if args.command == "packet" and args.packet_command == "link-goal":
        return command_packet_link_goal(args)
    if args.command == "validate":
        return command_validate(args)
    if args.command == "design" and args.design_command == "validate":
        return command_design_validate(args)
    if args.command == "context":
        return command_context(args)
    if args.command == "verify":
        return command_verify(args)
    if args.command == "verification":
        return command_verification(args)
    if args.command == "next":
        return command_next(args)
    if args.command == "integration" and args.integration_command == "generate":
        return command_integration_generate(args)
    if args.command == "progress" and args.progress_command == "add":
        return command_progress_add(args)
    if args.command == "trace":
        return command_trace(args)
    if args.command == "coverage":
        return command_coverage(args)
    if args.command == "benchmark":
        return command_benchmark(args)
    if args.command == "toon":
        return command_toon(args)
    if args.command == "ci":
        return command_ci(args)
    if args.command == "doctor":
        return command_doctor(args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
