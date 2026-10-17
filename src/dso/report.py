"""Aggregate raw run records into a markdown report."""

from __future__ import annotations

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path


def load_records(paths: list[Path]) -> list[dict]:
    records: dict[tuple, dict] = {}
    order: list[tuple] = []
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            key = (
                record.get("task"),
                record.get("model_key"),
                record.get("harness"),
                record.get("repeat"),
            )
            if key not in records:
                order.append(key)
            records[key] = record
    return [records[key] for key in order]


def bootstrap_ci(values: list[float], iterations: int = 2000, seed: int = 7) -> tuple[float, float]:
    if len(values) <= 1:
        value = values[0] if values else 0.0
        return value, value
    rng = random.Random(seed)
    means = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[int(0.025 * iterations)], means[int(0.975 * iterations) - 1]


def aggregate(records: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        groups[(record["model_key"], record["harness"])].append(record)

    rows = []
    for (model_key, harness), items in sorted(groups.items()):
        passes = [1.0 if item["passed"] else 0.0 for item in items]
        solved = sum(1 for item in items if item["passed"])
        total_cost = sum(item["cost_usd"] for item in items)
        low, high = bootstrap_ci(passes)
        rows.append(
            {
                "model": model_key,
                "harness": harness,
                "runs": len(items),
                "pass_rate": sum(passes) / len(passes),
                "ci_low": low,
                "ci_high": high,
                "solved": solved,
                "cost_total": total_cost,
                "cost_per_solved": (total_cost / solved) if solved else None,
                "input_tokens_per_solved": (
                    sum(item["tokens"]["input"] for item in items) / solved if solved else None
                ),
                "median_duration_s": statistics.median(item["duration_s"] for item in items),
                "mean_input_tokens": statistics.fmean(
                    item["tokens"]["input"] for item in items
                ),
                "mean_files_changed": statistics.fmean(item["files_changed"] for item in items),
                "mean_slop_per_1k": statistics.fmean(
                    item.get("slop_per_1k_words", 0.0) for item in items
                ),
                "mean_tool_calls": statistics.fmean(item.get("tool_calls", 0) for item in items),
                "mean_cache_ratio": statistics.fmean(
                    item.get("cache_ratio", 0.0) for item in items
                ),
                "mean_tool_output_chars": statistics.fmean(
                    item.get("tool_output_chars", 0) for item in items
                ),
                "mean_response_words": statistics.fmean(
                    item.get("response_words", 0) for item in items
                ),
            }
        )
    return rows


def _money(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value < 0.01:
        return f"${value:.6f}"
    return f"${value:.4f}"


def render(records: list[dict]) -> str:
    rows = aggregate(records)
    lines = ["# dso results", "", f"Runs: {len(records)}", ""]

    lines += [
        "## Model x harness",
        "",
        "| Model | Harness | Runs | pass@1 | 95% CI | Cost total | Cost / solved "
        "| Tok / solved | Median s | Input tok | Files | Slop /1k | Tools | Cache |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        tps = row["input_tokens_per_solved"]
        lines.append(
            "| {model} | {harness} | {runs} | {rate:.1%} | {lo:.0%}-{hi:.0%} | {cost} | {cps} | "
            "{tps} | {dur:.1f} | {tok:.0f} | {files:.1f} | {slop:.2f} | {tools:.1f} | {cache:.0%} |"
            .format(
                model=row["model"],
                harness=row["harness"],
                runs=row["runs"],
                rate=row["pass_rate"],
                lo=row["ci_low"],
                hi=row["ci_high"],
                cost=_money(row["cost_total"]),
                cps=_money(row["cost_per_solved"]),
                tps=f"{tps:.0f}" if tps is not None else "n/a",
                dur=row["median_duration_s"],
                tok=row["mean_input_tokens"],
                files=row["mean_files_changed"],
                slop=row["mean_slop_per_1k"],
                tools=row["mean_tool_calls"],
                cache=row["mean_cache_ratio"],
            )
        )

    baselines = {(row["model"]): row for row in rows if row["harness"] == "v0"}
    deltas = [row for row in rows if row["harness"] != "v0" and row["model"] in baselines]
    if deltas:
        lines += [
            "",
            "## Delta vs v0",
            "",
            "| Model | Harness | pass@1 delta | Cost / solved delta |",
            "|---|---|---:|---:|",
        ]
        for row in deltas:
            base = baselines[row["model"]]
            delta = row["pass_rate"] - base["pass_rate"]
            if row["cost_per_solved"] and base["cost_per_solved"]:
                cost_delta = row["cost_per_solved"] - base["cost_per_solved"]
                cost_text = _money(cost_delta)
            else:
                cost_text = "n/a"
            lines.append(
                f"| {row['model']} | {row['harness']} | {delta:+.1%} | {cost_text} |"
            )

    cats: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        cats[(record["harness"], record["category"])].append(record)
    if cats:
        categories = sorted({key[1] for key in cats})
        harnesses = sorted({key[0] for key in cats})
        lines += [
            "",
            "## pass@1 by category",
            "",
            "| Harness | " + " | ".join(categories) + " |",
            "|---|" + "---:|" * len(categories),
        ]
        for harness in harnesses:
            cells = []
            for category in categories:
                items = cats.get((harness, category), [])
                if items:
                    rate = sum(1 for i in items if i["passed"]) / len(items)
                    cells.append(f"{rate:.0%}")
                else:
                    cells.append("-")
            lines.append(f"| {harness} | " + " | ".join(cells) + " |")

    marker_totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for record in records:
        for name, count in (record.get("slop_markers") or {}).items():
            marker_totals[record["harness"]][name] += int(count)
    if marker_totals:
        lines += [
            "",
            "## Style markers",
            "",
            "Total occurrences per harness. Code blocks are excluded.",
            "",
            "| Harness | Markers |",
            "|---|---|",
        ]
        for harness, counts in sorted(marker_totals.items()):
            top = sorted(counts.items(), key=lambda item: -item[1])[:8]
            detail = ", ".join(f"{name}={count}" for name, count in top)
            lines.append(f"| {harness} | {detail} |")

    failures = [record for record in records if not record["passed"]]
    if failures:
        lines += [
            "",
            "## Failing runs",
            "",
            "| Task | Model | Harness | Detail |",
            "|---|---|---|---|",
        ]
        for record in failures[:60]:
            detail = str(record["grade_detail"]).replace("|", "\\|").replace("\n", " ")[:120]
            lines.append(
                f"| {record['task']} | {record['model_key']} | {record['harness']} | {detail} |"
            )

    return "\n".join(lines) + "\n"
