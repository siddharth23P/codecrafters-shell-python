import subprocess
import sys
class Jobs:
    _jobs = {}
    def __init__(self,args,out=None,err=None):
        self.out = out
        self.print_job_results()
        
    @classmethod
    def _format(cls, num, nums):
        p, cmd = cls._jobs[num]
        if num == nums[-1]:
            mark = "+"
        elif len(nums) > 1 and num == nums[-2]:
            mark = "-"
        else:
            mark = " "

        if p.poll() is None:
            return f"[{num}]{mark}  {'Running':<24}{cmd} &", False
        return f"[{num}]{mark}  {'Done':<24}{cmd}", True

    def print_job_results(self):                         # all jobs
        nums = sorted(self._jobs)
        for num in nums:
            line, done = self._format(num, nums)
            print(line, file=self.out)
            if done:
                del self._jobs[num]

    @classmethod
    def reap(cls, out=sys.stdout):                       # finished jobs only
        nums = sorted(cls._jobs)
        for num in nums:
            line, done = cls._format(num, nums)
            if done:
                print(line, file=out)
                del cls._jobs[num]

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
        
    