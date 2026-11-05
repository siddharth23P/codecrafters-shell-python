import os
class Cd:
    def __init__(self,args,out=None,err=None):
        path = os.path.expanduser(args[0] if args else "~")
        try:
            os.chdir(path)
        except FileNotFoundError:
            print(f"cd: {path}: No such file or directory", file=err)
