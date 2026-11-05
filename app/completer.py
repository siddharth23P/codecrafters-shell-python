import readline
import os
import subprocess
from .BUILTINS import Complete
class Completer:
    def __init__(self, builtins, ):
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
    
    @staticmethod
    def complete_with_spec(prog,text):
        line = readline.get_line_buffer()
        words = line[:readline.get_begidx()].split()
        cmd, prev = words[0], words[-1]
        env = {
            **os.envirom, 
            "COMP_LINE": line,
            "COMP_POINT": str(readline,get_endidx())
            }
        result = subprocess.run(
            [prog,cmd,text,prev],
            capture_output=True,
            text=True,
            env=env
            )
        return [m + " " for m in result.stdout.splitlines() if m]

    def complete(self, text, state):
        if state == 0:
            before = readline.get_line_buffer()[:readline.get_begidx()]
            if before.strip() == "":
                match_list = sorted(self.get_executables() | self.builtins)
                self.matches = [c + " " for c in match_list if c.startswith(text)]
            else:
                cmd = before.split()[0]
                if cmd in Complete.specs:
                    self.matches = self.complete_with_spec(Complete.specs[cmd], text)
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

