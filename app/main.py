import sys
from .UTILS.context import ShellContext
from .UTILS.parser import parse, ParseError
from .UTILS.executor import Executor, BuiltinHandler, ExternalHandler, NotFoundHandler
from .BUILTINS import load as load_builtins
from .BUILTINS.jobs import JobTable, JobFormatter, JobReporter, Runner
from .BUILTINS.complete import (Completer, CommandSource, SpecSource,
                                PathSource, CompletionSpecs)


def build_shell():
    """Composition root: the only place concrete objects are created and wired together."""
    job_table = JobTable()
    job_formatter = JobFormatter()
    ctx = ShellContext(
        job_table=job_table,
        job_reporter=JobReporter(job_table, job_formatter),
        runner=Runner(job_table, job_formatter),
        completion_specs=CompletionSpecs(),
    )
    load_builtins(ctx)  # fills ctx.registry

    completer = Completer([
        CommandSource(ctx.registry),        # first word: builtins + $PATH executables
        SpecSource(ctx.completion_specs),   # args of commands registered with `complete -C`
        PathSource(),                       # any other args: files and directories
    ])
    executor = Executor(
        [BuiltinHandler(ctx.registry),      # order matters: first that can_handle wins
         ExternalHandler(ctx.runner)],
        fallback=NotFoundHandler(),
    )
    return ctx, completer, executor


def main():
    ctx, completer, executor = build_shell()
    completer.install()

    while True:
        ctx.job_reporter.reap()
        try:
            command = input("$ ")
        except EOFError:
            break
        except KeyboardInterrupt:  # Ctrl-C at the prompt: drop the line, new prompt (like bash)
            print()
            continue

        try:
            executor.execute(parse(command))
        except ParseError as e:
            print(f"shell: {e}", file=sys.stderr)
        except KeyboardInterrupt:  # Ctrl-C while a builtin runs
            print()


if __name__ == "__main__":
    main()
