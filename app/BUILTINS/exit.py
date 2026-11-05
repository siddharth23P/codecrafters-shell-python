class Exit:
    def __init__(self,args,out=None,err=None):
        raise SystemExit(int(args[0]) if args and args[0].isdigit() else 0)
