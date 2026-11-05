import shutil
import subprocess
import os
import sys

BUILTINS = {"exit", "echo", "type", "pwd","cd"}


def type_of(cmd):
    if cmd in BUILTINS:
        return f"{cmd} is a shell builtin"
    if path := shutil.which(cmd):
        return f"{cmd} is {path}"
    return f"{cmd}: not found"

def parse(line):
    tokens, cur, in_quote, in_dbl_quote, in_slash, started = [], "", False, False, False, False
    for ch in line:
        if in_slash:
            in_slash = False
            if in_dbl_quote and ch not in '\\"$`':
                cur += "\\"
            cur += ch
            started = True
        elif ch == "\\" and not (in_quote):
            in_slash = not in_slash
            started = True
        elif ch == "\"":
            if not in_quote:
                in_dbl_quote = not in_dbl_quote
            else:
                cur += ch
            started = True
        elif ch == "\'":
            if not in_dbl_quote:
                in_quote = not in_quote
            else:
                cur += ch
            started = True
        elif ch == " " and not (in_quote or in_dbl_quote):
            if started:
                tokens.append(cur)
                cur, started = "", False
        else:
            cur += ch
            started = True
    if started:
        tokens.append(cur)
    return tokens

def split_redirect(tokens):
    cmd, out, err, outa, erra = [], None, None, None, None
    it = iter(tokens)
    for tok in it:
        if tok in (">", "1>"):
            out = next(it, None) 
        elif tok in (">>", "1>>"):
            outa = next(it, None)
        elif tok == "2>":
            err = next(it, None)
        elif tok in ("2>>"):
            erra = next(it, None)
        else:
            cmd.append(tok)
    return cmd, out, err, outa, erra

def main():
    while True:
        try:
            command = input("$ ")
        except EOFError:
            break
        
        if not command.strip():
            continue
        
        tokens, out_file, err_file, outa_file, erra_file = split_redirect(parse(command))
        cmd, *args = tokens
        
        if cmd == "exit":
            break
       
        if out_file:
            out = open(out_file, "w")
        elif outa_file:
            out = open(outa_file, "+a")
        else:
            out = sys.stdout
        
        if err_file:
            err = open(err_file, "w")
        elif erra_file:
            err = open(erra_file, "+a")
        else:
            err = sys.stderr
        
        if cmd == "echo":
            print(" ".join(args), file=out)
        elif cmd == "type":
            print(type_of(args[0]), file=out)
        elif cmd == "pwd":
            print(os.getcwd(), file=out)
        elif cmd == "cd":
            path = os.path.expanduser(args[0] if args else "~")
            try:
                os.chdir(path)
            except FileNotFoundError:
                print(f"cd: {path}: No such file or directory",file=err)
        elif shutil.which(cmd):
            subprocess.run([cmd, *args],stdout=out,stderr=err)
        else:
            print(f"{cmd}: command not found",file=err)
        # finally:
        if out_file:
            out.close()
        if err_file:
            err.close()


if __name__ == "__main__":
    main()
