class Complete:
    __spec = {}
    def __new__(cls):
        if cls.__spec is {}:
            cls.__spec = super().__new__(cls)
        return cls.__spec
    
    def __init__(self,args,out=None,err=None):
        self.args = args
        self.out = out
        self.err = err
        if not hasattr(self, "_initialized"):      
            self.FUNC_MAP = {"-p":self.print_spec}
            self.FUNC_TO_CALL = []
            
        self.parse_args()
        
        for flag,FUNC_ARGS in self.FUNC_TO_CALL:
            self.FUNC_MAP(flag)(FUNC_ARGS)
        
    def parse_args(self):
        last_arg = ""
        for arg in self.args:
            if arg.startswith("-") and arg in self.FUNC_MAP:
                self.FUNC_TO_CALL.append({arg:[]})
                last_arg = arg
            elif last_arg != "":
                self.FUNC_TO_CALL[-1][last_arg].append(arg)
            else:
                # Default behaviour
                continue
            
    def print_spec(self,spec):
        if spec not in self.__spec:
            print(f"complete: {spec}: no completion specification",file=self.err)
        else:
            pass