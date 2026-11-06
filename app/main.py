import shutil
import sys
from .parser import Parser
from .completer import Completer
from .BUILTINS import COMMANDS, jobs

BUILTINS = set(COMMANDS)
Completer(BUILTINS).install()

def main():
    while True:
        jobs.Jobs.reap()
        try:
            command = input("$ ")
        except EOFError:
            break
        
        if not command.strip():
            continue
        
        parsed_command = Parser(command)
        
        cmd = parsed_command.get_cmd()
        
        if not cmd:
            continue
        
        args = parsed_command.get_args()
        out_file, out_file_perm = parsed_command.get_out()
        err_file, err_file_perm = parsed_command.get_err()
        
        out = open(out_file, out_file_perm) if out_file else sys.stdout
        err = open(err_file, err_file_perm) if err_file else sys.stderr
        
        bg_task = bool(args) and args[-1] == "&"
        if bg_task:
            args = args[:-1]
            
        if cmd in COMMANDS:
            COMMANDS[cmd](args,out,err)
        elif shutil.which(cmd):
            if bg_task:
                jobs.Jobs.run_bg_task([cmd, *args], out, err)
            else:
                jobs.Jobs.run_fg_task([cmd, *args], out, err)
        else:
            print(f"{cmd}: command not found",file=err)
       
        if out is not sys.stdout:
            out.close()
        if err is not sys.stderr:
            err.close()


if __name__ == "__main__":
    main()
