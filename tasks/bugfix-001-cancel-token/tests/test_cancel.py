import threading
import time

from jobs import Job, JobRunner


def test_cancel_interrupts_running_job():
    jobs = [Job("a"), Job("b"), Job("c")]
    runner = JobRunner(jobs)

    thread = threading.Thread(target=runner.run)
    thread.start()
    time.sleep(0.03)
    runner.cancel()
    thread.join(timeout=2)

    assert not thread.is_alive(), "run() did not return after cancellation"
    assert jobs[0].status == "cancelled"
    assert len(jobs[0].result) < 5, "the first job ran to completion"


def test_uncancelled_run_is_unchanged():
    jobs = [Job("a"), Job("b")]
    last = JobRunner(jobs).run()

    assert [job.status for job in jobs] == ["done", "done"]
    assert all(len(job.result) == 5 for job in jobs)
    assert last.id == "b"
