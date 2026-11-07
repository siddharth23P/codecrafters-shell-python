"""Command history backed by readline, so up/down arrows and the `history` builtin share one store."""
import readline


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
