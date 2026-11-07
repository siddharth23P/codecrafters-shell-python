"""Run a Pipeline: resolve each stage to an action, wire pipes and redirects, then wait or background."""
import os
import shutil
import sys
from contextlib import ExitStack, contextmanager
from typing import Callable, Optional, Protocol

from .redirects import RedirectError, open_redirects

# action(stdin, out, err) -> Popen for an external program, None for an in-process command
Action = Callable[[object, object, object], Optional[object]]


class CommandHandler(Protocol):
    def resolve(self, parsed) -> Optional[Action]:
        """Return an action if this handler runs the command, else None."""


class BuiltinHandler:
    def __init__(self, builtins):
        self._builtins = builtins  # name -> callable(args, out, err)

    def resolve(self, parsed):
        command = self._builtins.get(parsed.cmd)
        if command is None:
            return None

        def action(stdin, out, err):
            command(parsed.args, out, err)  # builtins don't read stdin
            return None
        return action


class ExternalHandler:
    def __init__(self, runner):
        self._runner = runner

    def resolve(self, parsed):
        path = shutil.which(parsed.cmd)  # the only PATH lookup; the action reuses it
        if path is None:
            return None
        return lambda stdin, out, err: self._runner.spawn(parsed.argv, stdin, out, err, executable=path)


class NotFoundHandler:
    """Fallback: always resolves, so it must not sit in the normal handler list."""

    def resolve(self, parsed):
        def action(stdin, out, err):
            print(f"{parsed.cmd}: command not found", file=err)
            return None
        return action


def _no_op(stdin, out, err):
    return None  # stage with only redirects (`> file`): the file is created, nothing runs


@contextmanager
def _pipe_writer(fd):
    """File object over a pipe's write end, for builtins. If the reader already exited
    (`echo x | head -c0`), the final flush raises BrokenPipeError; bash ignores that, so do we."""
    f = os.fdopen(fd, "w")
    try:
        yield f
    finally:
        try:
            f.close()  # closes the fd even when the flush fails
        except BrokenPipeError:
            pass


class Executor:
    def __init__(self, handlers: list[CommandHandler], fallback: CommandHandler, runner):
        self._handlers = handlers  # order matters: first that resolves wins
        self._fallback = fallback  # used when none resolves
        self._runner = runner

    def execute(self, pipeline):
        stages = pipeline.commands
        if len(stages) == 1 and not stages[0].cmd and not stages[0].redirects:
            return  # empty line

        processes = []
        with ExitStack() as stack:  # every redirect file and parent pipe end is closed on exit
            stdin = None
            for i, cmd in enumerate(stages):
                read_end, write_end = os.pipe() if i < len(stages) - 1 else (None, None)
                try:
                    out, err = stack.enter_context(open_redirects(cmd.redirects))
                except RedirectError as e:
                    print(f"shell: {e}", file=sys.stderr)
                    action, out, err = _no_op, None, None  # this stage fails; the rest still run
                else:
                    action = self._resolve(cmd)

                if write_end is not None:
                    if out is sys.stdout:  # no `>` on this stage: write into the pipe
                        out = stack.enter_context(_pipe_writer(write_end))
                    else:                  # an explicit `>` wins over the pipe
                        os.close(write_end)

                try:
                    process = action(stdin, out, err)
                except BrokenPipeError:  # builtin's output filled a pipe nobody reads any more
                    process = None
                if process is not None:
                    processes.append(process)

                if stdin is not None:
                    os.close(stdin)  # parent's copy; the child holds its own
                stdin = read_end
        # Leaving the with closed the parent's write ends, so each next stage sees EOF.
        # Wait only after that, or a reader would wait forever for the shell to close its end.

        if pipeline.background and processes:
            self._runner.background(processes, pipeline.text)
        else:
            self._runner.wait_all(processes)

    def _resolve(self, cmd):
        if not cmd.cmd:
            return _no_op
        action = next((a for h in self._handlers if (a := h.resolve(cmd))), None)
        return action or self._fallback.resolve(cmd)
