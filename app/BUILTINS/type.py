import shutil


class TypeCommand:
    """The `type` builtin. Gets the builtin registry injected instead of importing it."""

    def __init__(self, registry):
        self._registry = registry  # filled by the loader; complete by the time `type` runs

    def type_of(self, cmd):
        if cmd in self._registry:
            return f"{cmd} is a shell builtin"
        if path := shutil.which(cmd):
            return f"{cmd} is {path}"
        return f"{cmd}: not found"

    def __call__(self, args, out=None, err=None):
        for name in args:
            print(self.type_of(name), file=out)


def create(ctx):
    return TypeCommand(ctx.registry)
