import importlib
import pkgutil


def load(ctx):
    """Import every module in this package and register its command in ctx.registry.

    A module provides either:
      create(ctx) -> callable(args, out, err)   when it needs shared services or state
      run(args, out, err)                       when it is stateless
    The module name is the command name.
    """
    for mod in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f".{mod.name}", __name__)
        if hasattr(module, "create"):
            command = module.create(ctx)
        elif hasattr(module, "run"):
            command = module.run
        else:
            raise TypeError(f"builtin module {mod.name!r} must define create(ctx) or run(args, out, err)")
        ctx.registry[mod.name] = command
    return ctx.registry
