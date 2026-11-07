import os


def run(args, out=None, err=None):
    path = os.path.expanduser(args[0] if args else "~")
    try:
        os.chdir(path)
    except OSError as e:  # missing, not a directory, no permission, ...
        print(f"cd: {path}: {e.strerror}", file=err)
