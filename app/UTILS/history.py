"""Command history backed by readline, so up/down arrows and the `history` builtin share one store."""
import readline


class ReadlineHistory:
    def __init__(self):
        # input() only auto-adds lines when reading from a terminal; add them ourselves instead,
        # so history works the same with a tty or a pipe.
        readline.set_auto_history(False)

    def add(self, line):
        readline.add_history(line)

    def entries(self):
        n = readline.get_current_history_length()
        return [readline.get_history_item(i) for i in range(1, n + 1)]  # readline items are 1-based
