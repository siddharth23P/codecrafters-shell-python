import shutil

BUILTINS = {"exit", "echo", "type"}


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
        if command == "exit":
            break
        if command.startswith("echo "):
            print(command[5:])
        elif command.startswith("type "):
            print(type_of(command[5:]))
        else:
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
