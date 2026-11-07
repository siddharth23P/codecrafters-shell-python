import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class JobStatus(Enum):
    RUNNING = "Running"
    DONE = "Done"


@dataclass(frozen=True)
class Job:
    num: int
    process: subprocess.Popen
    cmd: str

    def status(self) -> JobStatus:
        return JobStatus.RUNNING if self.process.poll() is None else JobStatus.DONE


@dataclass(frozen=True)
class JobSnapshot:
    """A job's state at one moment, so printing and removal see the same status."""
    job: Job
    mark: str  # "+" most recent, "-" second most recent, " " otherwise
    status: JobStatus


class JobTable:
    """Storage and lifecycle of background jobs. Does no I/O."""

    def __init__(self):
        self._jobs: dict[int, Job] = {}

    def add(self, process: subprocess.Popen, cmd: str) -> Job:
        num = max(self._jobs, default=0) + 1  # bash: highest live number + 1
        job = Job(num, process, cmd)
        self._jobs[num] = job
        return job

    def snapshot(self) -> list[JobSnapshot]:
        """Query only: current jobs with marks and status, oldest first."""
        nums = sorted(self._jobs)
        current = nums[-1] if nums else None
        previous = nums[-2] if len(nums) > 1 else None

        def mark(num):
            if num == current:
                return "+"
            if num == previous:
                return "-"
            return " "

        return [JobSnapshot(self._jobs[n], mark(n), self._jobs[n].status()) for n in nums]

    def discard(self, nums):
        for num in nums:
            self._jobs.pop(num, None)


class JobFormatter:
    """bash-style text for job lines. The only place that knows the output format."""

    def status_line(self, snap: JobSnapshot) -> str:
        suffix = " &" if snap.status is JobStatus.RUNNING else ""
        return f"[{snap.job.num}]{snap.mark}  {snap.status.value:<24}{snap.job.cmd}{suffix}"

    def started_line(self, job: Job) -> str:
        return f"[{job.num}] {job.process.pid}"


class JobReporter:
    """Use case: print job status lines, then forget jobs that were reported Done."""

    def __init__(self, table: JobTable, formatter: JobFormatter):
        self._table = table
        self._formatter = formatter

    def _report(self, out, include_running):
        snaps = self._table.snapshot()
        for snap in snaps:
            if include_running or snap.status is JobStatus.DONE:
                print(self._formatter.status_line(snap), file=out)
        self._table.discard(s.job.num for s in snaps if s.status is JobStatus.DONE)

    def reap(self, out=None):
        """Finished jobs only. Call before each prompt."""
        self._report(out, include_running=False)

    def list(self, out=None):
        """Every job, for the `jobs` builtin."""
        self._report(out, include_running=True)


class JobRegistry(Protocol):
    """The only part of a job table that Runner needs."""

    def add(self, process: subprocess.Popen, cmd: str) -> Job: ...


class Runner:
    """Launches external programs; background ones are registered as jobs."""

    def __init__(self, registry: JobRegistry, formatter: JobFormatter, popen=subprocess.Popen):
        self._registry = registry
        self._formatter = formatter
        self._popen = popen  # injectable, so tests can pass a fake

    def run_foreground(self, argv, out, err):
        process = self._popen(argv, stdout=out, stderr=err)
        try:
            process.wait()
        except KeyboardInterrupt:
            # Ctrl-C reaches the child too (same terminal); wait for it to exit so it isn't left a zombie
            process.wait()
            print()

    def run_background(self, argv, out, err):
        process = self._popen(argv, stdout=out, stderr=err)
        job = self._registry.add(process, " ".join(argv))
        # always to the terminal, even when the job's output is redirected
        print(self._formatter.started_line(job), flush=True)


def create(ctx):
    """The `jobs` builtin, bound to the shell's job reporter."""
    def run(args, out=None, err=None):
        ctx.job_reporter.list(out)
    return run
