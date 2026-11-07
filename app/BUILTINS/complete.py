"""TAB completion: the `complete` builtin and the readline completer, one class per job."""
import os
import readline
import subprocess
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol


# ---------- spec storage ----------

class CompletionSpecs:
    """The only owner of registered specs: command name -> completer program."""

    def __init__(self):
        self._specs = {}

    def register(self, name, program):
        self._specs[name] = program

    def remove(self, name):
        self._specs.pop(name, None)

    def get(self, name):
        return self._specs.get(name)


# ---------- the `complete` builtin ----------

class ArgParser:
    """Groups args under the flag before them: "-C prog git -p svn" -> [("-C", ["prog", "git"]), ("-p", ["svn"])]."""

    def parse(self, args, flags):
        calls = []
        for arg in args:
            if arg in flags:
                calls.append((arg, []))
            elif calls:
                calls[-1][1].append(arg)
            # args before the first known flag are ignored
        return calls


class SpecFormatter:
    """bash-style text for `complete` output. The only place that knows the format."""

    def spec(self, name, program):
        return f"complete -C '{program}' {name}"

    def missing(self, name):
        return f"complete: {name}: no completion specification"

    def usage(self):
        return "complete: usage: complete -C command name"


class CompleteCommand:
    """The `complete` builtin: parse flags, dispatch to a handler, print results."""

    def __init__(self, specs: CompletionSpecs, parser: ArgParser, formatter: SpecFormatter):
        self._specs = specs
        self._parser = parser
        self._formatter = formatter
        self._handlers = {
            "-p": self._print,
            "-C": self._register,
            "-r": self._remove,
        }

    def __call__(self, args, out=None, err=None):
        for flag, flag_args in self._parser.parse(args, self._handlers):
            self._handlers[flag](flag_args, out, err)

    def _print(self, names, out, err):
        for name in names:
            program = self._specs.get(name)
            if program is None:
                print(self._formatter.missing(name), file=err)
            else:
                print(self._formatter.spec(name, program), file=out)

    def _register(self, args, out, err):
        if len(args) < 2:
            print(self._formatter.usage(), file=err)
            return
        program, *names = args
        for name in names:
            self._specs.register(name, program)

    def _remove(self, names, out, err):
        for name in names:
            self._specs.remove(name)


# ---------- TAB completion ----------

@dataclass(frozen=True)
class CompletionContext:
    """What is being completed. Built from readline once, so sources never touch readline."""
    text: str    # the word under the cursor
    line: str    # the whole input line
    begidx: int  # where `text` starts in `line`
    endidx: int  # where `text` ends in `line`

    @cached_property  # split once per TAB, not on every access
    def words_before(self):
        return self.line[:self.begidx].split()

    @property
    def is_first_word(self):
        return not self.words_before


class CompletionSource(Protocol):
    def applies(self, ctx: CompletionContext) -> bool: ...
    def matches(self, ctx: CompletionContext) -> list[str]: ...


class CommandSource:
    """First word: builtins and executables on $PATH."""

    def __init__(self, builtin_names):
        self._builtins = set(builtin_names)  # fixed after the loader runs
        self._cache = {}  # directory -> (mtime_ns, executable names)

    def applies(self, ctx):
        return ctx.is_first_word

    def matches(self, ctx):
        names = sorted(self._executables() | self._builtins)
        return [n + " " for n in names if n.startswith(ctx.text)]

    def _executables(self):
        names = set()
        for directory in os.environ.get("PATH", "").split(os.pathsep):  # read per TAB: PATH can change
            if directory:
                names |= self._executables_in(directory)
        return names

    def _executables_in(self, directory):
        """Rescan a directory only when its mtime changed (a file was added, removed or renamed).
        A chmod +x on an existing file doesn't change the mtime, so that case shows up late."""
        try:
            mtime = os.stat(directory).st_mtime_ns
        except OSError:
            return frozenset()
        cached = self._cache.get(directory)
        if cached is None or cached[0] != mtime:
            try:
                with os.scandir(directory) as entries:
                    found = frozenset(e.name for e in entries
                                      if e.is_file() and os.access(e.path, os.X_OK))
            except OSError:
                found = frozenset()
            cached = self._cache[directory] = (mtime, found)
        return cached[1]


class SpecSource:
    """Later words of a command registered with `complete -C`: ask its completer program."""

    TIMEOUT = 2  # seconds; a hung completer program must not freeze the shell

    def __init__(self, specs: CompletionSpecs):
        self._specs = specs  # same object the builtin writes to, so -C / -r show up live

    def applies(self, ctx):
        return not ctx.is_first_word and self._specs.get(ctx.words_before[0]) is not None

    def matches(self, ctx):
        words = ctx.words_before
        cmd, prev = words[0], words[-1]
        env = {**os.environ, "COMP_LINE": ctx.line, "COMP_POINT": str(ctx.endidx)}
        try:
            result = subprocess.run([self._specs.get(cmd), cmd, ctx.text, prev],
                                    capture_output=True, text=True, env=env, timeout=self.TIMEOUT)
        except (OSError, subprocess.TimeoutExpired):  # missing / not executable / hung
            return []
        return [m + " " for m in result.stdout.splitlines() if m]


class PathSource:
    """Later words: files and directories."""

    def applies(self, ctx):
        return not ctx.is_first_word

    def matches(self, ctx):
        dirname, prefix = os.path.split(ctx.text)
        try:
            with os.scandir(dirname or ".") as it:  # read per TAB: files change
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            return []
        matches = []
        for entry in entries:
            name = entry.name
            if not name.startswith(prefix):
                continue
            if name.startswith(".") and not prefix.startswith("."):
                continue  # hide dotfiles unless asked
            full = os.path.join(dirname, name)
            matches.append(full + ("/" if entry.is_dir() else " "))  # is_dir from scandir: no extra stat
        return matches


class Completer:
    """readline glue: build the context, ask the first source that applies."""

    def __init__(self, sources: list[CompletionSource]):
        self._sources = sources  # order matters: first that applies wins
        self._matches = []

    def complete(self, text, state):
        if state == 0:  # readline calls with state 0, 1, 2... per TAB; compute once
            ctx = CompletionContext(text, readline.get_line_buffer(),
                                    readline.get_begidx(), readline.get_endidx())
            source = next((s for s in self._sources if s.applies(ctx)), None)
            self._matches = source.matches(ctx) if source else []
        return self._matches[state] if state < len(self._matches) else None

    def install(self):
        readline.set_completer(self.complete)
        readline.set_completer_delims(" \t\n")
        if "libedit" in (readline.__doc__ or ""):
            readline.parse_and_bind("bind ^I rl_complete")
        else:  # GNU readline (Linux / Codecrafters)
            readline.parse_and_bind("tab: complete")


# ---------- loader entry point ----------

def create(ctx):
    return CompleteCommand(ctx.completion_specs, ArgParser(), SpecFormatter())
