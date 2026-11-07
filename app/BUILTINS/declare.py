"""Shell variables: the store and the `declare` builtin. The only variable code; the lexer
reaches values only through `DeclareCommand.lookup`, which main passes to the lexer."""
import os
import re

NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
UNSET = object()  # `declare X` with no value: declared, but has no value yet


class Variables:
    """Shell variables, falling back to the environment (so $HOME, $PATH expand)."""

    def __init__(self, environ=os.environ):
        self._vars = {}           # name -> value, or UNSET
        self._environ = environ   # injectable for tests

    @staticmethod
    def is_valid_name(name):
        return bool(NAME.match(name))

    def set(self, name, value):
        self._vars[name] = value

    def declare(self, name):
        self._vars.setdefault(name, UNSET)  # keep an existing value, as bash does

    def get(self, name):
        """Value for expansion, or None if unset (shell vars win over the environment)."""
        if name in self._vars:
            value = self._vars[name]
            return None if value is UNSET else value
        return self._environ.get(name)

    def describe(self, name):
        """(attribute flag, value or UNSET) for `declare -p`, or None if not found."""
        if name in self._vars:
            return "--", self._vars[name]
        if name in self._environ:
            return "-x", self._environ[name]  # environment variables are exported
        return None

    def shell_names(self):
        return sorted(self._vars)


class DeclareFormatter:
    """bash-style text for `declare` output. The only place that knows the format."""

    @staticmethod
    def _quote(value):
        return '"' + re.sub(r'([\\"$`])', r"\\\1", value) + '"'  # bash escapes these inside "..."

    def variable(self, name, flag, value):
        if value is UNSET:
            return f"declare {flag} {name}"
        return f"declare {flag} {name}={self._quote(value)}"

    def not_found(self, name):
        return f"declare: {name}: not found"

    def invalid(self, arg):
        return f"declare: `{arg}': not a valid identifier"


class DeclareCommand:
    """The `declare` builtin: `declare NAME[=VALUE]...` and `declare -p [NAME...]`."""

    def __init__(self, variables: Variables, formatter: DeclareFormatter):
        self._vars = variables
        self._formatter = formatter

    def lookup(self, name):
        """For the lexer's $NAME / ${NAME} expansion."""
        return self._vars.get(name)

    def __call__(self, args, out=None, err=None):
        if args and args[0] == "-p":
            self._print(args[1:] or self._vars.shell_names(), out, err)
        elif not args:
            self._print(self._vars.shell_names(), out, err)
        else:
            self._assign(args, err)

    def _print(self, names, out, err):
        for name in names:
            found = self._vars.describe(name)
            if found is None:
                print(self._formatter.not_found(name), file=err)
            else:
                print(self._formatter.variable(name, *found), file=out)

    def _assign(self, args, err):
        for arg in args:
            name, eq, value = arg.partition("=")
            if not self._vars.is_valid_name(name):
                print(self._formatter.invalid(arg), file=err)  # bad ones are skipped, the rest still set
            elif eq:
                self._vars.set(name, value)
            else:
                self._vars.declare(name)


def create(ctx):
    return DeclareCommand(Variables(), DeclareFormatter())
