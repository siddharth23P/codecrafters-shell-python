"""Run a ParsedCommand: open its redirects, then hand it to the first handler that accepts it."""
import shutil
import sys
from typing import Protocol

from .redirects import RedirectError, open_redirects


class CommandHandler(Protocol):
    def can_handle(self, parsed) -> bool: ...
    def run(self, parsed, out, err) -> None: ...


class BuiltinHandler:
    def __init__(self, builtins):
        self._builtins = builtins  # name -> callable(args, out, err)

    def can_handle(self, parsed):
        return parsed.cmd in self._builtins

    def run(self, parsed, out, err):
        self._builtins[parsed.cmd](parsed.args, out, err)


class ExternalHandler:
    def __init__(self, runner):
        self._runner = runner

    def can_handle(self, parsed):
        return shutil.which(parsed.cmd) is not None

    def run(self, parsed, out, err):
        if parsed.background:
            self._runner.run_background(parsed.argv, out, err)
        else:
            self._runner.run_foreground(parsed.argv, out, err)


class NotFoundHandler:
    """Fallback when no handler accepts the command."""

    def run(self, parsed, out, err):
        print(f"{parsed.cmd}: command not found", file=err)


class Executor:
    def __init__(self, handlers: list[CommandHandler], fallback):
        self._handlers = handlers  # order matters: first that can_handle wins
        self._fallback = fallback  # used when none can_handle

    def execute(self, parsed):
        if not parsed.cmd:
            return
        handler = next((h for h in self._handlers if h.can_handle(parsed)), self._fallback)
        try:
            with open_redirects(parsed.redirects) as (out, err):
                handler.run(parsed, out, err)
        except RedirectError as e:
            print(f"shell: {e}", file=sys.stderr)
