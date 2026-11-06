import subprocess
class Jobs:
    _jobs = {}
    def __init__(self,args,out=None,err=None):
        self.print_job_results()
        
    def print_job_results(self):
        pass
    
    def get_jobs(self):
        pass
    
    @classmethod
    def run_bg_task(cls,argv,out,err):
        p = subprocess.Popen(argv,stdout=out,stderr=err)
        job_num = max(cls._jobs, default=0) + 1
        cls._jobs[job_num] = (p, " ".join(argv))
        print(f"[{job_num}] {p.pid}", flush=True)
        return p.pid

    @classmethod
    def run_fg_task(cls,argv,out,err):
        p = subprocess.Popen(argv,stdout=out,stderr=err)
        p.wait()
        return p.pid
        
    