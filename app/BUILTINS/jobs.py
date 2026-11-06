import subprocess
from collections import deque
class Jobs:
    __jobs__ = deque()
    def __init__(self,args,out=None,err=None):
        self.print_job_results()
        
    def print_job_results(self):
        pass
    
    def get_jobs(self):
        pass
    
    @classmethod
    def run_bg_task(cls,argv,out,err):
        p = subprocess.run(argv,stdout=out,stderr=err)
        
        return p.pid
    
    @classmethod
    def run_fg_task(cls,cmd,argv,out,err):
        p = subprocess.Popen(argv,stdout=out,stderr=err)
        p.wait()
        return p.pid
        
    