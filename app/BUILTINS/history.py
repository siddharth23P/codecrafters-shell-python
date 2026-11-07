def create(ctx):
    history = ctx.history  # ReadlineHistory: the same store the up/down arrows use

    def run(args, out=None, err=None):
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
