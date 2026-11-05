class Echo:
    def __init__(self,args,out=None,err=None):
        self.__arg = " ".join(args)
        print(self.__arg, file=out)