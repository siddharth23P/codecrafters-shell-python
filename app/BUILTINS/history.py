"""History: the readline-backed store and the `history` builtin. The only history code."""
import os
import readline
import sys


class ReadlineHistory:
    def __init__(self):
        # input() only auto-adds lines when reading from a terminal; add them ourselves instead,
        # so history works the same with a tty or a pipe.
        readline.set_auto_history(False)
        self._saved = 0  # entries[:_saved] are already in the file (via -w or -a)

    def add(self, line):
        readline.add_history(line)

    def entries(self):
        n = readline.get_current_history_length()
        return [readline.get_history_item(i) for i in range(1, n + 1)]  # readline items are 1-based

    # File I/O is done here, not with readline.read/write_history_file: on macOS readline is
    # libedit, which writes a "_HiStOrY_V2_" header and escapes spaces. Plain lines everywhere.

    def mark_saved(self):
        """Treat every current entry as already in the file (e.g. just loaded from it)."""
        self._saved = readline.get_current_history_length()

    def read_file(self, path):
        """`history -r`: add each line of the file to history (so arrows see them too)."""
        with open(path) as f:
            for line in f:
                line = line.rstrip("\n")
                if line:
                    self.add(line)

    def write_file(self, path):
        """`history -w`: overwrite the file with the whole history."""
        entries = self.entries()
        with open(path, "w") as f:
            f.writelines(e + "\n" for e in entries)
        self._saved = len(entries)

    def append_file(self, path):
        """`history -a`: append only the lines not yet saved by an earlier -a or -w."""
        entries = self.entries()
        with open(path, "a") as f:
            f.writelines(e + "\n" for e in entries[self._saved:])
        self._saved = len(entries)


class HistoryCommand:
    """The `history` builtin. Also loads/saves $HISTFILE at startup/exit through its own -r/-a/-w."""

    def __init__(self, history):
        self._history = history  # ReadlineHistory: the same store the up/down arrows use
        self._file_ops = {       # add a file flag = add an entry here
            "-r": history.read_file,
            "-w": history.write_file,
            "-a": history.append_file,
        }

    def add(self, line):
        """Record a line the user entered (called by the REPL)."""
        self._history.add(line)

    def __call__(self, args, out=None, err=None):
        if args and args[0] in self._file_ops:
            self._file_op(args, err)
        else:
            self._list(args, out, err)

    def _file_op(self, args, err):
        flag = args[0]
        path = args[1] if len(args) > 1 else os.environ.get("HISTFILE")  # bash falls back to $HISTFILE
        if not path:
            print(f"history: {flag}: option requires an argument", file=err)
            return
        try:
            self._file_ops[flag](path)
        except OSError as e:
            print(f"history: {path}: {e.strerror}", file=err)

    def _list(self, args, out, err):
        entries = self._history.entries()
        start = 0
        if args:
            if not args[0].isdigit():
                print(f"history: {args[0]}: numeric argument required", file=err)
                return
            start = max(len(entries) - int(args[0]), 0)   # n bigger than the list -> show all
        for i, line in enumerate(entries[start:], start + 1):
            print(f"{i:>5}  {line}", file=out)

    # ---------- $HISTFILE: called by main at startup / exit ----------

    def load_histfile(self, path):
        """Startup: `history -r $HISTFILE` if it exists; those lines count as already saved."""
        if path and os.path.isfile(path):
            self(["-r", path], err=sys.stderr)
            self._history.mark_saved()  # so exit doesn't append them to the file again

    def save_histfile(self, path):
        """Exit: `history -a` if the file exists (only new lines), else `history -w`."""
        if path:
            self(["-a" if os.path.exists(path) else "-w", path], err=sys.stderr)


def create(ctx):
    return HistoryCommand(ReadlineHistory())
