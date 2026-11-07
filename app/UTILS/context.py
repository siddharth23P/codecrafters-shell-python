"""Shared services handed to builtins by the loader, so no module keeps global state."""
from dataclasses import dataclass, field


@dataclass
class ShellContext:
    job_table: object
    job_reporter: object
    runner: object
    completion_specs: object
    history: object  # add(line), entries()
    registry: dict = field(default_factory=dict)  # builtin name -> callable(args, out, err)
