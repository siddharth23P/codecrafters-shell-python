import shutil
import subprocess
import os
BUILTINS = {"exit", "echo", "type", "pwd"}


def type_of(cmd):
    if cmd in BUILTINS:
        return f"{cmd} is a shell builtin"
    if path := shutil.which(cmd):
        return f"{cmd} is {path}"
    return f"{cmd}: not found"


def main():
    while True:
        try:
            command = input("$ ")
        except EOFError:
            break
        cmd = command.split()[0]
        if cmd == "exit":
            break
        if len(command) >= len(cmd)+1:
            args_string = command[len(cmd)+1:]
            args = args_string.split()
        if cmd == "echo":
            print(args_string)
        elif cmd == "type":
            print(type_of(args_string))
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
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
