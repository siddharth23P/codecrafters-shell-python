def create(ctx):
    history = ctx.history                         # same list object main appends to

    def run(args, out=None, err=None):
        start = 0
        if args:
            if not args[0].isdigit():
                print(f"history: {args[0]}: numeric argument required", file=err)
                return
            start = max(len(history) - int(args[0]), 0)   # n bigger than the list -> show all
        for i, line in enumerate(history[start:], start + 1):
            print(f"{i:>5}  {line}", file=out)
    return run