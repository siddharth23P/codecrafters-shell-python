import os

def run(args, out=None, err=None):
    print(os.getcwd(), file=out)
