import sys
import os

def find_executable(cmd):
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        path = os.path.join(directory, cmd)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None

__shell_builtins__ = ["exit","echo","type"]
def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            command = input()
        except EOFError:
            break
        if command == "exit":
            break
        if command.startswith("echo "):
            cmd = command[5:]
            print(f"{cmd}")
        elif command.startswith("type "):
            cmd = command[5:]
            if command[5:] in __shell_builtins__:
                print(f"{cmd} is a shell builtin")
            elif path := find_executable(cmd):
                print(f"{cmd} is {path}")
            else:
                print(f"{cmd}: not found")
        else:
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
