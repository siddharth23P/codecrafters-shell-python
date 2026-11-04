import sys

__shell_builtins__ = ["exit","echo","type"]
def main():
    while True:
        sys.stdout.write("$ ")
        command=input()
        if command == "exit":
            break
        if command.startswith("echo "):
            print(f"{command[5:]}")
        if command.startswith("type "):
            if command[5:] in __shell_builtins__:
                print(f"{command[5:]} is a shell builtin")
            else:
                print(f"{command[5:]}: not found")
        else:
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
