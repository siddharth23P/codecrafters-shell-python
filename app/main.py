import shutil
import subprocess
import os
import sys
from collections import deque
BUILTINS = {"exit", "echo", "type", "pwd"}


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
            in_slash = not in_slash
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
    stdout = None
    stderr = None
    for i, tok in enumerate(tokens):
        if tok in (">","1>"):
            stdout = tokens[i+1] if i+1 < len(tokens) else None
        elif tok in ("2>"):
            stderr = tokens[i+1] if i+1 < len(tokens) else None
    return tokens, stdout, stderr

def main():
    while True:
        try:
            command = input("$ ")
        except EOFError:
            break
        tokens, out_file, err_file = split_redirect(parse(command))
        cmd, *args = tokens
        out = open(out_file, "w") if out_file else sys.stdout
        err = open(err_file, "w") if err_file else sys.stderr
        if cmd == "exit":
            break
        if cmd == "echo":
            print(" ".join(args), file=out)
        elif cmd == "type":
            print(type_of(args[0]), file=out)
        elif cmd == "pwd":
            print(os.getcwd(), file=out)
        elif cmd == "cd":
            path = os.path.expanduser(args[0] if args else "~")
            try:
                os.chdir(path)
            except FileNotFoundError:
                print(f"cd: {path}: No such file or directory",file=err)
        elif shutil.which(cmd):
            subprocess.run([cmd, *args],stdout=out)
        else:
            print(f"{cmd}: command not found",file=err)
        # finally:
        if out_file:
            out.close()
        if err_file:
            err.close()


if __name__ == "__main__":
    main()
