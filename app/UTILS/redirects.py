"""Open redirect targets for one command and always close them afterwards."""
import sys
from contextlib import ExitStack, contextmanager


class RedirectError(Exception):
    pass


@contextmanager
def open_redirects(redirects):
    """redirects: stream -> (path, mode), e.g. {"stdout": ("out.txt", "w")}.

    Yields (out, err): the opened files, or the terminal streams when not redirected.
    Files are closed on exit, even if the command raises (e.g. `exit`).
    Raises RedirectError if a target can't be opened; files already opened are closed.
    """
    defaults = {"stdout": sys.stdout, "stderr": sys.stderr}  # read at call time, not import time
    with ExitStack() as stack:
        streams = {}
        for name, default in defaults.items():
            if name not in redirects:
                streams[name] = default
                continue
            path, mode = redirects[name]
            try:
                streams[name] = stack.enter_context(open(path, mode))
            except OSError as e:
                raise RedirectError(f"{path}: {e.strerror}") from e
        yield streams["stdout"], streams["stderr"]
