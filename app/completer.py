import readline
import os
class Completer:
    def __init__(self, builtins):
        self.builtins = builtins
        self.matches = []

    @staticmethod
    def executables_in(directory):
        try:
            return [e.name for e in os.scandir(directory)
                    if e.is_file() and os.access(e.path, os.X_OK)]
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return []

    def get_executables(self):
        names = set()
        for d in os.environ.get("PATH", "").split(os.pathsep):
            names.update(self.executables_in(d))
        return names

    @staticmethod
    def complete_path(text):
        dirname, prefix = os.path.split(text)
        try:
            entries = sorted(os.listdir(dirname or "."))
        except OSError:
            return []
        matches = []
        for name in entries:
            if not name.startswith(prefix):
                continue
            if name.startswith(".") and not prefix.startswith("."):
                continue
            full = os.path.join(dirname, name)
            matches.append(full + ("/" if os.path.isdir(full) else " "))
        return matches

    def complete(self, text, state):
        if state == 0:
            before = readline.get_line_buffer()[:readline.get_begidx()]
            if before.strip() == "":
                match_list = sorted(self.get_executables() | self.builtins)
                self.matches = [c + " " for c in match_list if c.startswith(text)]
            else:
                self.matches = self.complete_path(text)
        return self.matches[state] if state < len(self.matches) else None

    def install(self):
        readline.set_completer(self.complete)
        readline.set_completer_delims(" \t\n")
        if "libedit" in (readline.__doc__ or ""):
            readline.parse_and_bind("bind ^I rl_complete")
        else:                                             
            readline.parse_and_bind("tab: complete")

