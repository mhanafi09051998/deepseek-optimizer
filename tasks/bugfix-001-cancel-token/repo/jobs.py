"""Minimal in-memory job runner."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    status: str = "pending"
    result: list[str] = field(default_factory=list)


class JobRunner:
    """Runs jobs sequentially, one step at a time."""

    def __init__(self, jobs: list[Job]):
        self.jobs = jobs
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def run(self) -> Job:
        for job in self.jobs:
            if self.cancelled:
                job.status = "cancelled"
                return job
            job.status = "running"
            for step in range(5):
                time.sleep(0.01)
                job.result.append(f"step-{step}")
            job.status = "done"
        return self.jobs[-1]
