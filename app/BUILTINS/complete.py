class Complete:
    specs = {}  # class-level: shared by every call, so specs persist between commands

    def __init__(self,args,out=None,err=None):
        self.args = args
        self.out = out
        self.err = err
        self.FUNC_MAP = {
            "-p": self.print_spec,
            "-C": self.register,
            }
        self.FUNC_TO_CALL = []  # list of (flag, [flag args])

        self.parse_args()

        for flag, FUNC_ARGS in self.FUNC_TO_CALL:
            self.FUNC_MAP[flag](FUNC_ARGS)

    def parse_args(self):
        for arg in self.args:
            if arg in self.FUNC_MAP:
                self.FUNC_TO_CALL.append((arg, []))
            elif self.FUNC_TO_CALL:
                self.FUNC_TO_CALL[-1][1].append(arg)
            else:
                # Default behaviour
                continue

    def print_spec(self,names):
        for name in names:
            if name not in self.specs:
                print(f"complete: {name}: no completion specification",file=self.err)
            else:
                print(f"complete -C \'{self.specs[name]}\' {name}",file=self.out)

    def register(self,args):
        if len(args) < 2:
            print("complete: usage: complete -C command name",file=self.err)
            return
        path, *names = args
        for name in names:
            self.specs[name] = path
