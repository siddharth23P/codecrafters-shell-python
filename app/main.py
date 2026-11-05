import shutil
import subprocess
import os
import sys
import readline

BUILTINS = {"exit", "echo", "type", "pwd", "cd", "complete"}
_matches = []
def executables_in(directory):
    try:
        return [e.name for e in os.scandir(directory)
                if e.is_file() and os.access(e.path, os.X_OK)]
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return []

def get_executables():
    names = set()
    for d in os.environ.get("PATH", "").split(os.pathsep):
        names.update(executables_in(d))
    return names

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

_matches = []
    
def completer(text,state):
    global _matches
    if state == 0:
        before = readline.get_line_buffer()[:readline.get_begidx()]
        if before.strip() == "":
            execs = get_executables()
            match_list = sorted(execs | BUILTINS)
            _matches = [c + " " for c in match_list if c.startswith(text)]
        else:
            _matches = complete_path(text)
    return _matches[state] if state < len(_matches) else None

readline.set_completer(completer)
readline.set_completer_delims(" \t\n")
if "libedit" in (readline.__doc__ or ""):
    readline.parse_and_bind("bind ^I rl_complete")
else:                                             # GNU readline (Linux / Codecrafters)
    readline.parse_and_bind("tab: complete")
    
def type_of(cmd):
    if cmd in BUILTINS:
        return f"{cmd} is a shell builtin"
    if path := shutil.which(cmd):
        return f"{cmd} is {path}"
    return f"{cmd}: not found"

def parse(line):
    tokens, cur, in_quote, in_dbl_quote, in_slash, started = [], "", False, False, False, False
    for ch in line:
        if in_slash:
            in_slash = False
            if in_dbl_quote and ch not in '\\"$`':
                cur += "\\"
            cur += ch
            started = True
        elif ch == "\\" and not (in_quote):
            in_slash = not in_slash
            started = True
        elif ch == "\"":
            if not in_quote:
                in_dbl_quote = not in_dbl_quote
            else:
                cur += ch
            started = True
        elif ch == "\'":
            if not in_dbl_quote:
                in_quote = not in_quote
            else:
                cur += ch
            started = True
        elif ch == " " and not (in_quote or in_dbl_quote):
            if started:
                tokens.append(cur)
                cur, started = "", False
        else:
            cur += ch
            started = True
    if started:
        tokens.append(cur)
    return tokens

def split_redirect(tokens):
    cmd, out, err, outa, erra = [], None, None, None, None
    it = iter(tokens)
    for tok in it:
        if tok in (">", "1>"):
            out = next(it, None) 
        elif tok in (">>", "1>>"):
            outa = next(it, None)
        elif tok == "2>":
            err = next(it, None)
        elif tok == "2>>":
            erra = next(it, None)
        else:
            cmd.append(tok)
    return cmd, out, err, outa, erra

def main():
    while True:
        try:
            command = input("$ ")
        except EOFError:
            break
        
        if not command.strip():
            continue
        
        tokens, out_file, err_file, outa_file, erra_file = split_redirect(parse(command))
        if not tokens:
            continue
        cmd, *args = tokens
        
        if cmd == "exit":
            break
       
        if out_file:
            out = open(out_file, "w")
        elif outa_file:
            out = open(outa_file, "a")
        else:
            out = sys.stdout
        
        if err_file:
            err = open(err_file, "w")
        elif erra_file:
            err = open(erra_file, "a")
        else:
            err = sys.stderr
        
        if cmd == "echo":
            print(" ".join(args), file=out)
        elif cmd == "type":
            for name in args:
                print(type_of(name), file=out)
        elif cmd == "pwd":
            print(os.getcwd(), file=out)
        elif cmd == "cd":
            path = os.path.expanduser(args[0] if args else "~")
            try:
                os.chdir(path)
            except FileNotFoundError:
                print(f"cd: {path}: No such file or directory",file=err)
        elif cmd == "complete":
            continue
        elif shutil.which(cmd):
            subprocess.run([cmd, *args],stdout=out,stderr=err)
        else:
            print(f"{cmd}: command not found",file=err)
        if out is not sys.stdout:
            out.close()
        if err is not sys.stderr:
            err.close()


if __name__ == "__main__":
    main()
