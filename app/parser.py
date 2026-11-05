PERM_ENUM = {0:None, 1:"w", 2:"a"}

class Parser:
    def __init__(self,line):
        self.__cmd = None
        self.__args = None
        self.__out = None
        self.__err = None
        self.__out_perm = 0
        self.__err_perm = 0
        self.__tokens = []
        self.__split_redirect(self.__parse(line))
        
    def __parse(self,line):
        self.tokens, cur, in_quote, in_dbl_quote, in_slash, started = [], "", False, False, False, False
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
                    self.tokens.append(cur)
                    cur, started = "", False
            else:
                cur += ch
                started = True
        if started:
            self.tokens.append(cur)
        
    def __split_redirect(self,tokens):
        cmd = []
        it = iter(tokens)
        for tok in it:
            if tok in (">", "1>" ,"1>>"):
                self.__out = next(it, None) 
                self.__out_perm = 1
                if tok == "1>>":
                    self.__out_perm = 2 
            elif tok in ("2>", "2>>"):
                self.__err = next(it, None)
                self.__err_perm = 1
                if tok == "1>>":
                    self.__err_perm = 2
            else:
                cmd.append(tok)
        self.__cmd ,self.__args = cmd
    
    def get_cmd(self):
        return self.__cmd
    
    def get_args(self):
        return self.__args
    
    def get_out(self):
        return self.__out,PERM_ENUM[self.__out_perm]
    
    def get_err(self):
            return self.__err,PERM_ENUM[self.__err_perm]
    
    