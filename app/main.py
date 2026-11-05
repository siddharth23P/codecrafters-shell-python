import shutil
import subprocess
import os
from collections import deque
BUILTINS = {"exit", "echo", "type", "pwd"}


def type_of(cmd):
    if cmd in BUILTINS:
        return f"{cmd} is a shell builtin"
    if path := shutil.which(cmd):
        return f"{cmd} is {path}"
    return f"{cmd}: not found"

def parse(line):
    args, cur, in_quote, started = [], "", False, False
    for ch in line:
        if ch == "\'":
            in_quote = not in_quote
            started = True
        elif ch == " " and not in_quote:
            if started:
                args.append(cur)
                cur, started = "", False
        else:
            cur += ch
            started = True
    if started:
        args.append(cur)
    return args
    
def main():
    while True:
        try:
            command = input("$ ")
        except EOFError:
            break
        cmd, *args = parse(command)
        if cmd == "exit":
            break
        if cmd == "echo":
            print(" ".join(args))
        elif cmd == "type":
            print(type_of(args[0]))
        elif cmd == "pwd":
            print(os.getcwd())
        elif cmd == "cd":
            path = os.path.expanduser(args[0] if args else "~")
            try:
                os.chdir(path)
            except FileNotFoundError:
                print(f"cd: {path}: No such file or directory")
        elif shutil.which(cmd):
            subprocess.run([cmd, *args])
        else:
            print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()
