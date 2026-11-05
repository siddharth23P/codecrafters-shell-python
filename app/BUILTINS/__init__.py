import importlib
import pkgutil

COMMANDS = {}
for mod in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f".{mod.name}", __name__)
    COMMANDS[mod.name] = getattr(module, mod.name.capitalize())
