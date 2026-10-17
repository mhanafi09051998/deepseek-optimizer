"""Spawn the OpenCode CLI and parse its JSON event stream."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def resolve_opencode() -> list[str]:
    """Return an argv prefix that runs the OpenCode CLI without a shell."""
    env_override = os.environ.get("DSO_OPENCODE_BIN")
    if env_override:
        return [env_override]

    candidates = [
        Path(os.environ.get("APPDATA", "")) / "npm/node_modules/@opencode/cli/bin/opencode.exe",
        Path("C:/ProgramData/npm/node_modules/@opencode/cli/bin/opencode.exe"),
        Path("/usr/local/bin/opencode"),
        Path.home() / ".opencode/bin/opencode",
    ]
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate)]

    found = shutil.which("opencode")
    if found:
        return [found]
    raise RuntimeError(
        "opencode CLI not found. Install it or set DSO_OPENCODE_BIN to the binary path."
    )


@lru_cache(maxsize=1)
def opencode_version() -> str:
    try:
        proc = subprocess.run(
            [*resolve_opencode(), "--version"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return (proc.stdout or proc.stderr).strip().splitlines()[0]
    except Exception:  # noqa: BLE001 - version is best effort metadata
        return "unknown"


@dataclass
class AgentResult:
    cost_usd: float = 0.0
    tokens: dict[str, int] = field(
        default_factory=lambda: {
            "input": 0,
            "output": 0,
            "reasoning": 0,
            "cache_read": 0,
            "cache_write": 0,
        }
    )
    steps: int = 0
    timed_out: bool = False
    stderr: str = ""
    text_parts: list[str] = field(default_factory=list)


def _parse(stdout: str) -> tuple[float, dict[str, int], int, list[str]]:
    cost = 0.0
    tokens = {"input": 0, "output": 0, "reasoning": 0, "cache_read": 0, "cache_write": 0}
    steps = 0
    texts: list[str] = []

    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        part = event.get("part") or {}
        if event.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text)
            continue
        if event.get("type") != "step_finish":
            continue

        steps += 1
        cost += float(part.get("cost") or 0.0)
        usage = part.get("tokens") or {}
        tokens["input"] += int(usage.get("input") or 0)
        tokens["output"] += int(usage.get("output") or 0)
        tokens["reasoning"] += int(usage.get("reasoning") or 0)
        cache = usage.get("cache") or {}
        tokens["cache_read"] += int(cache.get("read") or 0)
        tokens["cache_write"] += int(cache.get("write") or 0)

    return cost, tokens, steps, texts


def execute(
    workspace: Path, model_id: str, prompt: str, timeout: int, log_path: Path
) -> AgentResult:
    argv = [
        *resolve_opencode(),
        "run",
        "--auto",
        "--format",
        "json",
        "--model",
        model_id,
    ]
    if os.environ.get("DSO_STANDALONE", "1") == "1":
        argv.append("--standalone")
    argv.append(prompt)

    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")

    timed_out = False
    try:
        proc = subprocess.run(
            argv,
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")

    log_path.write_text(stdout, encoding="utf-8")
    cost, tokens, steps, texts = _parse(stdout)

    return AgentResult(
        cost_usd=cost,
        tokens=tokens,
        steps=steps,
        timed_out=timed_out,
        stderr=stderr[-2000:],
        text_parts=texts,
    )
