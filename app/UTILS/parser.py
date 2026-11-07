"""Command line -> ParsedCommand, in two steps: Lexer (characters) and CommandParser (grammar)."""
import re
from dataclasses import dataclass, field
from enum import Enum


class Kind(Enum):
    WORD = "word"
    OP = "op"


@dataclass(frozen=True)
class Token:
    text: str
    kind: Kind


@dataclass(frozen=True)
class Redirect:
    stream: str  # "stdout" | "stderr"
    mode: str    # "w" truncate | "a" append

# Add a redirect operator = add a line here. Lexer and CommandParser pick it up.
REDIRECTS = {
    ">":   Redirect("stdout", "w"),
    "1>":  Redirect("stdout", "w"),
    ">>":  Redirect("stdout", "a"),
    "1>>": Redirect("stdout", "a"),
    "2>":  Redirect("stderr", "w"),
    "2>>": Redirect("stderr", "a"),
}
BACKGROUND = "&"
PIPE = "|"
OPERATORS = set(REDIRECTS) | {BACKGROUND, PIPE}


class ParseError(Exception):
    pass


@dataclass
class ParsedCommand:
    argv: list[str] = field(default_factory=list)
    redirects: dict[str, tuple[str, str]] = field(default_factory=dict)  # stream -> (path, mode)

    @property
    def cmd(self):
        return self.argv[0] if self.argv else None

    @property
    def args(self):
        return self.argv[1:]

@dataclass
class Pipeline:
    commands: list[ParsedCommand]
    background: bool = False
    
    @property
    def text(self):
        return " | ".join(" ".join(c.argv) for c in self.commands)

class Lexer:
    """line -> tokens. Knows quotes, escapes, $variable expansion and operator spelling."""

    DOUBLE_QUOTE_ESCAPES = '\\"$`'  # inside "...", backslash only escapes these
    VAR_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    FIELD_SEPARATORS = re.compile(r"[ \t\n]+")  # bash's default IFS

    def __init__(self, operators, lookup=None):
        self._operators = set(operators)
        self._lookup = lookup  # name -> value or None; None disables expansion
        # operator text without an fd prefix ("2>>" -> ">>"), longest first so ">>" beats ">"
        self._base_ops = sorted({op.lstrip("0123456789") for op in operators}, key=len, reverse=True)

    def tokenize(self, line):
        tokens = []
        cur, started, quoted = "", False, False  # quoted: any part of cur was quoted/escaped
        in_single = in_double = False

        def flush():
            nonlocal cur, started, quoted
            if started:
                tokens.append(Token(cur, Kind.WORD))
            cur, started, quoted = "", False, False

        def expand_unquoted(value):
            """Unquoted $VAR: split on whitespace into separate words; empty adds nothing,
            so `echo a $EMPTY b` gets two args, not three."""
            nonlocal cur, started, quoted
            for n, field in enumerate(self.FIELD_SEPARATORS.split(value)):
                if n:
                    flush()
                if field:
                    cur += field
                    started = quoted = True  # quoted: an expanded "2" must not become the fd in `2>`

        i = 0
        while i < len(line):
            ch = line[i]
            if in_single:
                if ch == "'":
                    in_single = False
                else:
                    cur += ch
            elif in_double:
                if ch == '"':
                    in_double = False
                elif ch == "\\" and i + 1 < len(line):
                    nxt = line[i + 1]
                    cur += nxt if nxt in self.DOUBLE_QUOTE_ESCAPES else "\\" + nxt
                    i += 1
                elif ch == "$" and (var := self._read_var(line, i)):
                    value, length = var
                    cur += value                 # inside "...": no splitting, empty stays an arg
                    i += length
                    continue
                else:
                    cur += ch
            elif ch == "$" and (var := self._read_var(line, i)):
                value, length = var
                expand_unquoted(value)
                i += length
                continue
            elif ch == "\\":
                if i + 1 < len(line):
                    cur += line[i + 1]
                    i += 1
                started = quoted = True
            elif ch == "'":
                in_single = True
                started = quoted = True
            elif ch == '"':
                in_double = True
                started = quoted = True
            elif ch in " \t":
                flush()
            elif op := self._match_operator(line, i, cur, started, quoted):
                full, length = op
                if full != line[i:i + length]:  # fd digits in cur became part of the operator
                    cur, started, quoted = "", False, False
                else:
                    flush()
                tokens.append(Token(full, Kind.OP))
                i += length
                continue
            else:
                cur += ch
                started = True
            i += 1
        if in_single or in_double:
            quote = "'" if in_single else '"'
            raise ParseError(f"unexpected EOF while looking for matching `{quote}'")
        flush()
        return tokens

    def _read_var(self, line, i):
        """At a `$`: (value, chars consumed) for $NAME / ${NAME}, or None to keep `$` literal."""
        if self._lookup is None:
            return None
        if line.startswith("${", i):
            end = line.find("}", i + 2)
            if end == -1:
                raise ParseError("unexpected EOF while looking for matching `}'")
            name = line[i + 2:end]
            if not self.VAR_NAME.fullmatch(name):
                raise ParseError(f"${{{name}}}: bad substitution")
            return self._lookup(name) or "", end + 1 - i
        match = self.VAR_NAME.match(line, i + 1)
        if not match:
            return None  # `$` alone, `$5`, `$?`...: not supported, stays literal
        return self._lookup(match.group()) or "", match.end() - i

    def _match_operator(self, line, i, cur, started, quoted):
        """(operator text, chars consumed from line) or None."""
        for base in self._base_ops:
            if not line.startswith(base, i):
                continue
            with_fd = cur + base
            if started and not quoted and cur.isdigit() and with_fd in self._operators:
                return with_fd, len(base)  # "2" + ">" -> "2>"
            if base in self._operators:
                return base, len(base)
        return None

class CommandParser:
    """tokens -> Pipeline of ParsedCommands. Knows grammar (redirects, |, &), not characters."""

    def __init__(self, redirects, background=BACKGROUND, pipe=PIPE):
        self._redirects = redirects
        self._background = background
        self._pipe = pipe

    def parse(self, tokens) -> Pipeline:
        background = bool(tokens) and self._is(tokens[-1], self._background)
        if background:
            tokens = tokens[:-1]  # & applies to the whole pipeline
            if not tokens:
                raise self._unexpected(Token(self._background, Kind.OP))  # bare `&`
        segments = [[]]
        for tok in tokens:
            if self._is(tok,self._pipe):
                if not segments[-1]:
                    raise self._unexpected(tok)
                segments.append([])
            else:
                segments[-1].append(tok)
        if len(segments) > 1 and not segments[-1]:
            raise self._unexpected(None)
        return Pipeline([self._parse_command(s) for s in segments], background)
    
    def _parse_command(self,tokens) -> ParsedCommand:
        cmd = ParsedCommand()
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if tok.kind is Kind.OP and tok.text in self._redirects:
                if nxt is None or nxt.kind is Kind.OP:
                    raise self._unexpected(nxt)
                rule = self._redirects[tok.text]
                cmd.redirects[rule.stream] = (nxt.text, rule.mode)
                i += 2
                continue
            if self._is(tok, self._background):
                raise self._unexpected(tok)  # a trailing & was removed in parse(); any other is unsupported
            cmd.argv.append(tok.text)
            i += 1
        return cmd

    @staticmethod
    def _unexpected(tok):
        return ParseError(f"syntax error near unexpected token `{tok.text if tok else 'newline'}'")

    @staticmethod
    def _is(tok, op):
        return tok.kind is Kind.OP and tok.text == op

_parser = CommandParser(REDIRECTS)


def make_parse(lookup=None):
    """Build parse(line) -> Pipeline. lookup(name) -> value|None enables $VAR expansion.
    Raises ParseError on bad syntax."""
    lexer = Lexer(OPERATORS, lookup)
    return lambda line: _parser.parse(lexer.tokenize(line))


parse = make_parse()  # no variable expansion
