import os


def create(ctx):
    history = ctx.history  # ReadlineHistory: the same store the up/down arrows use
    file_ops = {           # add a file flag = add an entry here
        "-r": history.read_file,
        "-w": history.write_file,
        "-a": history.append_file,
    }

    def run(args, out=None, err=None):
        if args and args[0] in file_ops:
            path = args[1] if len(args) > 1 else os.environ.get("HISTFILE")  # bash falls back to $HISTFILE
            if not path:
                print(f"history: {args[0]}: option requires an argument", file=err)
                return
            try:
                file_ops[args[0]](path)
            except OSError as e:
                print(f"history: {path}: {e.strerror}", file=err)
            return

        entries = history.entries()
        start = 0
        if args:
            if not args[0].isdigit():
                print(f"history: {args[0]}: numeric argument required", file=err)
                return
            start = max(len(entries) - int(args[0]), 0)   # n bigger than the list -> show all
        for i, line in enumerate(entries[start:], start + 1):
            print(f"{i:>5}  {line}", file=out)
    return run
