import os
class Pwd:
    def __init__(self,args,out=None,err=None):
        print(os.getcwd(), file=out)
