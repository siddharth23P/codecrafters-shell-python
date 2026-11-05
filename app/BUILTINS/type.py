import shutil
class Type:
    def __init__(self,args,out=None,err=None):
        for name in args:
            print(self.type_of(name), file=out)

    @staticmethod
    def type_of(cmd):
        from . import COMMANDS  # imported here, not at top, to avoid a circular import
        if cmd in COMMANDS:
            return f"{cmd} is a shell builtin"
        if path := shutil.which(cmd):
            return f"{cmd} is {path}"
        return f"{cmd}: not found"
