"""Command line interface for dso."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from .grader import apply_patch, copy_repo, run_grade, run_reference
from .report import load_records, render
from .runner import run_one
from .slop import analyze, format_report
from .spec import (
    DEFAULT_TASKS_DIR,
    TaskError,
    discover_tasks,
    load_harnesses,
    load_models,
    select_tasks,
)


def _models(value: str) -> dict[str, str]:
    registry = load_models()
    resolved: dict[str, str] = {}
    for key in [part.strip() for part in value.split(",") if part.strip()]:
        resolved[key] = registry[key].id if key in registry else key
    return resolved


def cmd_list(args: argparse.Namespace) -> int:
    tasks = discover_tasks(Path(args.tasks_dir))
    models = load_models()
    harnesses = load_harnesses()

    print(f"tasks ({len(tasks)}):")
    for task in tasks:
        print(f"  {task.id:<40} {task.category:<14} {task.language:<10} d{task.difficulty}")
    print(f"\nmodels ({len(models)}):")
    for entry in models.values():
        print(f"  {entry.key:<14} {entry.id}")
    print(f"\nharnesses ({len(harnesses)}):")
    for key, meta in harnesses.items():
        print(f"  {key:<4} {meta.get('label', '')}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    tasks = select_tasks(discover_tasks(Path(args.tasks_dir)), args.tasks)
    failures = 0
    print(f"validating {len(tasks)} task(s)\n")
    for task in tasks:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            broken = root / "broken"
            copy_repo(task, broken)

            fixed = root / "fixed"
            copy_repo(task, fixed)
            try:
                apply_patch(fixed, task.solution_patch)
            except RuntimeError as exc:
                print(f"FAIL {task.id:<40} {exc}")
                failures += 1
                continue

            if task.grade_type == "mutation":
                assert task.reference_test is not None
                broken_result = run_reference(task, broken, task.reference_test)
                fixed_result = run_reference(task, fixed, task.reference_test)
                ok = (not broken_result.passed) and fixed_result.passed
                no_patch_label = "fail" if not broken_result.passed else "pass"
                with_patch_label = "pass" if fixed_result.passed else "fail"
                no_patch_detail = broken_result.detail
                with_patch_detail = fixed_result.detail
            else:
                no_patch = run_grade(task, broken, test_override=task.reference_test)
                with_patch = run_grade(task, fixed, test_override=task.reference_test)
                ok = (not no_patch.passed) and with_patch.passed
                no_patch_label = "pass" if no_patch.passed else "fail"
                with_patch_label = "pass" if with_patch.passed else "fail"
                no_patch_detail = no_patch.detail
                with_patch_detail = with_patch.detail

        status = "ok  " if ok else "FAIL"
        print(
            f"{status} {task.id:<40} "
            f"without patch: {no_patch_label} | with patch: {with_patch_label}"
        )
        if not ok:
            failures += 1
            print(f"     without: {no_patch_detail.splitlines()[0][:160]}")
            print(f"     with:    {with_patch_detail.splitlines()[0][:160]}")
    print(f"\n{len(tasks) - failures}/{len(tasks)} tasks valid")
    return 0 if failures == 0 else 1


def cmd_eval(args: argparse.Namespace) -> int:
    tasks = select_tasks(discover_tasks(Path(args.tasks_dir)), args.tasks)
    models = _models(args.models)
    harnesses = [part.strip() for part in args.harnesses.split(",") if part.strip()]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run_root = Path(args.run_root)
    run_root.mkdir(parents=True, exist_ok=True)

    total = len(tasks) * len(models) * len(harnesses) * args.repeats
    done = 0
    solved = 0

    for model_key, model_id in models.items():
        for harness in harnesses:
            for task in tasks:
                for repeat in range(1, args.repeats + 1):
                    done += 1
                    print(f"[{done}/{total}] {task.id} {model_key} {harness} r{repeat}", flush=True)
                    try:
                        record = run_one(
                            task,
                            model_key=model_key,
                            model_id=model_id,
                            harness=harness,
                            repeat=repeat,
                            run_root=run_root,
                            timeout_scale=args.timeout_scale,
                            keep=args.keep,
                        )
                    except Exception as exc:  # noqa: BLE001 - keep the suite running
                        record = {
                            "schema": 1,
                            "task": task.id,
                            "category": task.category,
                            "language": task.language,
                            "difficulty": task.difficulty,
                            "model_key": model_key,
                            "model_id": model_id,
                            "harness": harness,
                            "repeat": repeat,
                            "passed": False,
                            "grade_detail": f"runner error: {exc}",
                            "grade_s": 0.0,
                            "duration_s": 0.0,
                            "cost_usd": 0.0,
                            "tokens": {
                                "input": 0,
                                "output": 0,
                                "reasoning": 0,
                                "cache_read": 0,
                                "cache_write": 0,
                            },
                            "steps": 0,
                            "files_changed": 0,
                            "diff_lines": 0,
                            "timed_out": False,
                            "stderr": "",
                            "opencode_version": "unknown",
                            "run_dir": "",
                        }
                    solved += int(record["passed"])
                    with out_path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(record) + "\n")
                    print(
                        f"    {'PASS' if record['passed'] else 'fail'} "
                        f"{record['duration_s']:.1f}s ${record['cost_usd']:.4f}",
                        flush=True,
                    )

    print(f"\n{solved}/{total} runs passed -> {out_path}")
    if args.report:
        records = load_records([out_path])
        Path(args.report).write_text(render(records), encoding="utf-8")
        print(f"report -> {args.report}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    paths = [Path(p) for p in args.inputs]
    records = load_records(paths)
    if not records:
        print("no records found", file=sys.stderr)
        return 1
    text = render(records)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"report -> {args.out}")
    else:
        print(text)
    return 0


def cmd_slop(args: argparse.Namespace) -> int:
    path = Path(args.transcript)
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        return 2

    texts: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text":
            text = (event.get("part") or {}).get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text)

    print(format_report(analyze(texts)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dso", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tasks-dir", default=str(DEFAULT_TASKS_DIR))

    p_list = sub.add_parser("list", parents=[common], help="list tasks, models, harnesses")
    p_list.set_defaults(func=cmd_list)

    p_validate = sub.add_parser("validate", parents=[common], help="check task solvability")
    p_validate.add_argument("--tasks", default="all")
    p_validate.set_defaults(func=cmd_validate)

    p_eval = sub.add_parser("eval", parents=[common], help="run the evaluation matrix")
    p_eval.add_argument("--models", default="flash-high")
    p_eval.add_argument("--harnesses", default="v0")
    p_eval.add_argument("--tasks", default="all")
    p_eval.add_argument("--repeats", type=int, default=1)
    p_eval.add_argument("--out", default="results/raw/run.jsonl")
    p_eval.add_argument("--run-root", default="runs")
    p_eval.add_argument("--timeout-scale", type=float, default=1.0)
    p_eval.add_argument("--keep", action="store_true", help="keep agent workspaces")
    p_eval.add_argument("--report", default=None, help="write a markdown report after the run")
    p_eval.set_defaults(func=cmd_eval)

    p_report = sub.add_parser("report", help="render markdown from raw jsonl")
    p_report.add_argument("inputs", nargs="+")
    p_report.add_argument("--out", default="results/summary.md")
    p_report.set_defaults(func=cmd_report)

    p_slop = sub.add_parser("slop", help="count low-value patterns in a transcript")
    p_slop.add_argument("transcript")
    p_slop.set_defaults(func=cmd_slop)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TaskError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
