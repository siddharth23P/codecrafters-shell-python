def create(ctx):
    history = ctx.history                         # same list object main appends to

    def run(args, out=None, err=None):
        for i, line in enumerate(history, 1):
            print(f"{i:>5}  {line}", file=out)
    return run