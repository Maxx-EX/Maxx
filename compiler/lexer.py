"""
Maxx Lexer (Level 1 bootstrap - will be replaced by Maxx itself in Level 2).

Tokenizes .mxx source into a token stream, including offside-rule
(indentation) handling that emits INDENT / DEDENT tokens.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Token kinds
# ---------------------------------------------------------------------------
# We use string names rather than an enum for brevity in the bootstrap.
TOK_KEYWORD = "KEYWORD"
TOK_IDENT = "IDENT"
TOK_INT = "INT"
TOK_FLOAT = "FLOAT"
TOK_STRING = "STRING"
TOK_RAWSTRING = "RAWSTRING"
TOK_FSTRING = "FSTRING"
TOK_CHAR = "CHAR"
TOK_OP = "OP"
TOK_PUNCT = "PUNCT"
TOK_NEWLINE = "NEWLINE"
TOK_INDENT = "INDENT"
TOK_DEDENT = "DEDENT"
TOK_EOF = "EOF"

KEYWORDS = {
    "if", "elif", "else", "for", "while", "loop", "match", "ret",
    "let", "var", "as", "is", "in",
    "trait", "enum", "struct", "fn", "type", "import", "from",
    "pub", "priv",
    "task", "chan", "comptime", "true", "false", "none", "some",
    "ok", "err", "try", "break", "continue", "do", "nil_",
}

# Multi-character operators, longest first so the lexer greedily matches.
MULTI_OPS = [
    "...", "::", "=>", "==", "!=", "<=", ">=", "<<", ">>",
    "+=", "-=", "*=", "/=", "%=", "//", "..=", "..", "||", "&&",
    "|>", "->",
]
SINGLE_OPS = set("+-*/%<>=!&^|~?:")
PUNCT_CHARS = set("()[]{},:;@#.")


@dataclass
class Token:
    kind: str
    value: str
    line: int = 0
    col: int = 0

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        if self.kind in (TOK_NEWLINE, TOK_INDENT, TOK_DEDENT, TOK_EOF):
            return f"{self.kind}@{self.line}"
        return f"{self.kind}({self.value!r})@{self.line}:{self.col}"


class LexError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"lex error at {line}:{col}: {msg}")
        self.line = line
        self.col = col


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------
class Lexer:
    def __init__(self, src: str, filename: str = "<input>"):
        # Normalize line endings and ensure the source ends with a newline.
        self.src = src.replace("\r\n", "\n").replace("\r", "\n")
        if not self.src.endswith("\n"):
            self.src += "\n"
        self.filename = filename
        self.i = 0
        self.n = len(self.src)
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    # -- low-level helpers ---------------------------------------------------
    def peek(self, offset: int = 0) -> str:
        j = self.i + offset
        return self.src[j] if j < self.n else "\0"

    def advance(self) -> str:
        c = self.src[self.i]
        self.i += 1
        if c == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def emit(self, kind: str, value: str, line: int, col: int) -> None:
        self.tokens.append(Token(kind, value, line, col))

    # -- main entry ---------------------------------------------------------
    def tokenize(self) -> List[Token]:
        # Pass 1: produce a raw token stream with NEWLINE markers and capture
        # the indentation (leading spaces) of each logical line.
        self._raw_tokenize()
        # Pass 2: apply offside rule to insert INDENT / DEDENT tokens.
        self._apply_offside()
        return self.tokens

    # -- Pass 1 -------------------------------------------------------------
    def _raw_tokenize(self) -> None:
        while self.i < self.n:
            c = self.peek()

            # End of source.
            if c == "\0":
                break

            # Whitespace (space / tab) - skipped; indentation is captured per
            # logical line in _apply_offside.
            if c in (" ", "\t"):
                self.advance()
                continue

            # Newline -> emit a NEWLINE token.
            if c == "\n":
                line, col = self.line, self.col
                self.advance()
                self.emit(TOK_NEWLINE, "\n", line, col)
                continue

            # Line comment // ... (and doc comments ///, //!).
            if c == "/" and self.peek(1) == "/":
                self._skip_line_comment()
                continue

            # Block comment /* ... */ (nested).
            if c == "/" and self.peek(1) == "*":
                self._skip_block_comment()
                continue

            # f-string: f"..."
            if c == "f" and self.peek(1) == '"':
                self.advance()  # consume 'f'
                self._lex_string(prefix="f")
                continue

            # Raw string: `...`
            if c == "`":
                self._lex_raw_string()
                continue

            # Regular string: "..."
            if c == '"':
                self._lex_string(prefix="")
                continue

            # Char literal: '...'
            if c == "'":
                self._lex_char()
                continue

            # Number.
            if c.isdigit() or (c == "." and self.peek(1).isdigit()):
                self._lex_number()
                continue

            # Identifier / keyword.
            if c.isalpha() or c == "_":
                self._lex_ident()
                continue

            # Multi-character operator.
            matched = False
            for op in MULTI_OPS:
                if self.src.startswith(op, self.i):
                    line, col = self.line, self.col
                    for _ in op:
                        self.advance()
                    self.emit(TOK_OP, op, line, col)
                    matched = True
                    break
            if matched:
                continue

            # Single-character operator.
            if c in SINGLE_OPS:
                line, col = self.line, self.col
                self.advance()
                self.emit(TOK_OP, c, line, col)
                continue

            # Punctuation.
            if c in PUNCT_CHARS:
                line, col = self.line, self.col
                self.advance()
                kind = TOK_PUNCT
                self.emit(kind, c, line, col)
                continue

            raise LexError(f"unexpected character {c!r}", self.line, self.col)

    def _skip_line_comment(self) -> None:
        # Consume // and everything until newline (inclusive handled by caller
        # next iteration).
        while self.i < self.n and self.peek() != "\n":
            self.advance()

    def _skip_block_comment(self) -> None:
        # Nested block comments.
        line, col = self.line, self.col
        depth = 0
        while self.i < self.n:
            if self.peek() == "/" and self.peek(1) == "*":
                depth += 1
                self.advance()
                self.advance()
            elif self.peek() == "*" and self.peek(1) == "/":
                depth -= 1
                self.advance()
                self.advance()
                if depth == 0:
                    return
            else:
                self.advance()
        raise LexError("unterminated block comment", line, col)

    def _lex_string(self, prefix: str) -> None:
        line, col = self.line, self.col
        if self.peek() != '"':
            raise LexError("expected opening quote", line, col)
        self.advance()  # opening quote
        buf: List[str] = []
        while self.i < self.n and self.peek() != '"':
            c = self.peek()
            if c == "\\":
                self.advance()
                esc = self.peek()
                mapped = {
                    "n": "\n", "t": "\t", "r": "\r", "0": "\0",
                    '"': '"', "\\": "\\", "a": "\a", "b": "\b",
                    "f": "\f", "v": "\v",
                }
                if esc in mapped:
                    buf.append(mapped[esc])
                    self.advance()
                elif esc == "u":
                    # Unicode escape: \uXXXX
                    self.advance()  # consume 'u'
                    hex_digits = ""
                    for _ in range(4):
                        if self.i < self.n and self.peek() in "0123456789abcdefABCDEF":
                            hex_digits += self.peek()
                            self.advance()
                        else:
                            break
                    if len(hex_digits) == 4:
                        code_point = int(hex_digits, 16)
                        # For ASCII range, just use the character
                        if code_point < 128:
                            buf.append(chr(code_point))
                        else:
                            # For non-ASCII, encode as UTF-8
                            try:
                                buf.append(chr(code_point))
                            except ValueError:
                                buf.append("?")
                    else:
                        # Invalid \u escape, keep as-is
                        buf.append("\\u" + hex_digits)
                elif esc == "\n":
                    # line continuation
                    self.advance()
                else:
                    buf.append(esc)
                    self.advance()
            elif c == "\n":
                raise LexError("unterminated string literal", line, col)
            else:
                buf.append(self.advance())
        if self.peek() != '"':
            raise LexError("unterminated string literal", line, col)
        self.advance()  # closing quote
        kind = TOK_FSTRING if prefix == "f" else TOK_STRING
        self.emit(kind, "".join(buf), line, col)

    def _lex_raw_string(self) -> None:
        line, col = self.line, self.col
        assert self.peek() == "`"
        self.advance()
        start = self.i
        while self.i < self.n and self.peek() != "`":
            if self.peek() == "\n":
                raise LexError("unterminated raw string", line, col)
            self.advance()
        if self.peek() != "`":
            raise LexError("unterminated raw string", line, col)
        value = self.src[start:self.i]
        self.advance()
        self.emit(TOK_RAWSTRING, value, line, col)

    def _lex_char(self) -> None:
        line, col = self.line, self.col
        self.advance()  # opening '
        if self.peek() == "\\":
            self.advance()
            esc = self.peek()
            mapped = {
                "n": "\n", "t": "\t", "r": "\r", "0": "\0",
                "'": "'", "\\": "\\",
            }
            ch = mapped.get(esc, esc)
            self.advance()
        else:
            ch = self.advance()
        if self.peek() != "'":
            raise LexError("unterminated char literal", line, col)
        self.advance()  # closing '
        self.emit(TOK_CHAR, ch, line, col)

    def _lex_number(self) -> None:
        line, col = self.line, self.col
        start = self.i

        # Hex / binary.
        if self.peek() == "0" and self.peek(1) in ("x", "X"):
            self.advance()
            self.advance()
            while self.peek().isalnum() or self.peek() == "_":
                self.advance()
            raw = self.src[start:self.i].replace("_", "")
            self.emit(TOK_INT, raw, line, col)
            return
        if self.peek() == "0" and self.peek(1) in ("b", "B"):
            self.advance()
            self.advance()
            while self.peek() in ("0", "1", "_"):
                self.advance()
            raw = self.src[start:self.i].replace("_", "")
            self.emit(TOK_INT, raw, line, col)
            return

        # Decimal integer or float.
        is_float = False
        while self.peek().isdigit() or self.peek() == "_":
            self.advance()
        if self.peek() == "." and self.peek(1) != ".":
            is_float = True
            self.advance()
            while self.peek().isdigit() or self.peek() == "_":
                self.advance()
        if self.peek() in ("e", "E"):
            is_float = True
            self.advance()
            if self.peek() in ("+", "-"):
                self.advance()
            while self.peek().isdigit() or self.peek() == "_":
                self.advance()
        # Optional f32 / f64 suffix.
        if self.peek() == "f":
            # consume f32 / f64 suffix
            j = self.i
            if self.src.startswith("f32", j):
                is_float = True
                self.advance(); self.advance(); self.advance()
            elif self.src.startswith("f64", j):
                is_float = True
                self.advance(); self.advance(); self.advance()
        raw = self.src[start:self.i].replace("_", "")
        # Strip trailing f32/f64 marker for numeric parsing.
        for suf in ("f32", "f64"):
            if raw.endswith(suf):
                raw = raw[: -len(suf)]
                break
        # Integer overflow check (P1-5).
        if not is_float:
            try:
                val = int(raw, 0 if raw.startswith("0") else 10)
                if val > 9223372036854775807 or val < -9223372036854775808:
                    raise LexError(
                        f"integer literal overflow (exceeds i64 range): {raw}",
                        line, col)
            except ValueError:
                pass
        self.emit(TOK_FLOAT if is_float else TOK_INT, raw, line, col)

    def _lex_ident(self) -> None:
        line, col = self.line, self.col
        start = self.i
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        word = self.src[start:self.i]
        if word in KEYWORDS:
            self.emit(TOK_KEYWORD, word, line, col)
        else:
            self.emit(TOK_IDENT, word, line, col)

    # -- Pass 2: offside rule ----------------------------------------------
    def _apply_offside(self) -> None:
        """Insert INDENT / DEDENT tokens based on leading whitespace.

        We walk the raw tokens. A NEWLINE that precedes a non-blank line
        captures the indentation of that next line. We then compare it with
        the current indentation stack and emit INDENT/DEDENT accordingly.
        """
        raw = self.tokens
        out: List[Token] = []
        stack = [0]
        # We need to know the indentation level of each non-blank logical
        # line. We pre-compute it by scanning the original source.
        indent_of_line = self._compute_line_indents()

        idx = 0
        n = len(raw)
        pending_newlines = 0  # count NEWLINE tokens that need to be flushed
        at_line_start = True
        current_line = 1

        while idx < n:
            tok = raw[idx]

            if tok.kind == TOK_NEWLINE:
                # Collect all consecutive newlines (blank lines).
                pending_newlines += 1
                idx += 1
                continue

            if tok.kind == TOK_EOF:
                # Flush remaining dedents.
                while len(stack) > 1:
                    stack.pop()
                    out.append(Token(TOK_DEDENT, "", tok.line, 0))
                out.append(tok)
                break

            # We are at the start of a logical line (after newlines/blanks).
            if pending_newlines > 0 or at_line_start:
                indent = indent_of_line.get(tok.line, 0)
                if indent > stack[-1]:
                    out.append(Token(TOK_INDENT, "", tok.line, 0))
                    stack.append(indent)
                elif indent < stack[-1]:
                    # Pop until we match.
                    while len(stack) > 1 and indent < stack[-1]:
                        stack.pop()
                        out.append(Token(TOK_DEDENT, "", tok.line, 0))
                    if indent != stack[-1]:
                        raise LexError(
                            f"indentation error: unexpected indent {indent} "
                            f"(line {tok.line})",
                            tok.line, 0,
                        )
                # We emit at most one NEWLINE to separate statements; extra
                # blank lines are ignored.
                out.append(Token(TOK_NEWLINE, "\n", tok.line, 0))
                pending_newlines = 0
                at_line_start = False

            out.append(tok)
            idx += 1

        self.tokens = out

    def _compute_line_indents(self) -> dict:
        """Return {line_number: indentation_spaces} for every source line."""
        result = {}
        lines = self.src.split("\n")
        for ln, text in enumerate(lines, start=1):
            stripped = text.lstrip(" \t")
            if stripped == "" or stripped.startswith("//"):
                continue
            # Count leading spaces; treat tab as 4 spaces.
            indent = 0
            for ch in text:
                if ch == " ":
                    indent += 1
                elif ch == "\t":
                    indent += 4
                else:
                    break
            result[ln] = indent
        return result


# ---------------------------------------------------------------------------
# Convenience entry point.
# ---------------------------------------------------------------------------
def tokenize(src: str, filename: str = "<input>") -> List[Token]:
    return Lexer(src, filename).tokenize()
