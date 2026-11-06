import subprocess
class Jobs:
    _jobs = {}
    def __init__(self,args,out=None,err=None):
        self.out = out
        self.print_job_results()
        
    def print_job_results(self):
        nums = sorted(self._jobs)
        for num in nums:
            p, cmd = self._jobs[num]
            if num == nums[-1]:
                mark = "+"
            elif len(nums) > 1 and num == nums[-2]:
                mark = "-"
            else:
                mark = " "
            
            if p.poll() is None:
                print(f"[{num}]{mark}   {'Running':<24}{cmd} &", file=self.out)
            else:
                print(f"[{num}]{mark}   {'Done':<24}{cmd} &", file=self.out)
                del self._jobs[num]
    
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
        
    