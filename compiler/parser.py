"""
Maxx Parser (Level 1 bootstrap - will be replaced by Maxx itself in Level 2).

Recursive-descent parser with a Pratt-style expression parser. Consumes the
token stream produced by lexer.py (including INDENT/DEDENT offside tokens).
"""

from typing import List, Optional, Tuple, Any

import mxast as ast
from lexer import (
    Token,
    TOK_KEYWORD, TOK_IDENT, TOK_INT, TOK_FLOAT, TOK_STRING, TOK_RAWSTRING,
    TOK_FSTRING, TOK_CHAR, TOK_OP, TOK_PUNCT, TOK_NEWLINE, TOK_INDENT,
    TOK_DEDENT, TOK_EOF,
)


class ParseError(Exception):
    def __init__(self, msg: str, line: int = 0, col: int = 0, got: str = ""):
        hint = f" (got {got!r})" if got else ""
        super().__init__(f"parse error at {line}:{col}: {msg}{hint}")
        self.line = line
        self.col = col


# Precedence table for Pratt parsing (lowest to highest).
PREC: dict = {}
def _add_prec(level: int, ops: List[str]) -> None:
    for op in ops:
        PREC[op] = level

_add_prec(1,  ["=", "+=", "-=", "*=", "/=", "%="])
_add_prec(2,  ["|>"])
_add_prec(4,  ["||"])
_add_prec(5,  ["&&"])
_add_prec(6,  ["|"])
_add_prec(7,  ["&"])
_add_prec(9,  ["==", "!="])
_add_prec(10, ["<", "<=", ">", ">=", "is", "as"])
_add_prec(11, ["<<", ">>"])
_add_prec(12, ["+", "-"])
_add_prec(13, ["*", "/", "%", "//"])
_add_prec(14, ["^"])   # exponentiation (bootstrap; spec lists ^ as XOR,
                       # but examples use it as power)
_add_prec(15, ["..", "..="])


class Parser:
    def __init__(self, tokens: List[Token], filename: str = "<input>"):
        self.toks = tokens
        self.pos = 0
        self.filename = filename
        self.depth = 0
        self.MAX_DEPTH = 500  # P1-9: prevent stack overflow on deep nesting

    # -- token stream helpers ----------------------------------------------
    def peek(self, offset: int = 0) -> Token:
        j = self.pos + offset
        if j < len(self.toks):
            return self.toks[j]
        return Token(TOK_EOF, "", 0, 0)

    def next(self) -> Token:
        t = self.peek()
        self.pos += 1
        return t

    def at(self, kind: str, value: Optional[str] = None) -> bool:
        t = self.peek()
        if t.kind != kind:
            return False
        return value is None or t.value == value

    def at_kw(self, word: str) -> bool:
        return self.at(TOK_KEYWORD, word)

    def at_op(self, op: str) -> bool:
        return self.at(TOK_OP, op)

    def at_punct(self, ch: str) -> bool:
        # Accept both PUNCT and OP tokens (some chars like ':' are in SINGLE_OPS).
        t = self.peek()
        return (t.kind == TOK_PUNCT or t.kind == TOK_OP) and t.value == ch

    def eat(self, kind: str, value: Optional[str] = None) -> Token:
        t = self.peek()
        if t.kind != kind or (value is not None and t.value != value):
            raise ParseError(
                f"expected {kind} {value!r}", t.line, t.col,
                f"{t.kind}:{t.value}",
            )
        self.pos += 1
        return t

    def eat_kw(self, word: str) -> Token:
        return self.eat(TOK_KEYWORD, word)

    def eat_op(self, op: str) -> Token:
        return self.eat(TOK_OP, op)

    def eat_punct(self, ch: str) -> Token:
        # Accept both PUNCT and OP tokens (some chars like ':' are in SINGLE_OPS).
        t = self.peek()
        if not ((t.kind == TOK_PUNCT or t.kind == TOK_OP) and t.value == ch):
            raise ParseError(
                f"expected punct {ch!r}", t.line, t.col,
                f"{t.kind}:{t.value}",
            )
        self.pos += 1
        return t

    def accept_op(self, op: str) -> Optional[Token]:
        if self.at_op(op):
            return self.next()
        return None

    def accept_punct(self, ch: str) -> Optional[Token]:
        if self.at_punct(ch):
            return self.next()
        return None

    def accept_kw(self, word: str) -> Optional[Token]:
        if self.at_kw(word):
            return self.next()
        return None

    # -- newline / block helpers -------------------------------------------
    def skip_newlines(self) -> None:
        while self.at(TOK_NEWLINE):
            self.next()

    def expect_block(self) -> List[ast.Stmt]:
        """Parse an indented block: INDENT stmt* DEDENT."""
        self.skip_newlines()
        if not self.at(TOK_INDENT):
            if self.at(TOK_DEDENT) or self.at(TOK_NEWLINE) or self.at(TOK_EOF):
                return []
            return [self.parse_stmt()]
        self.eat(TOK_INDENT)
        stmts: List[ast.Stmt] = []
        while not self.at(TOK_DEDENT) and not self.at(TOK_EOF):
            self.skip_newlines()
            if self.at(TOK_DEDENT) or self.at(TOK_EOF):
                break
            stmts.append(self.parse_stmt())
        self.skip_newlines()
        if self.at(TOK_DEDENT):
            self.next()
        return stmts

    # -- top-level ---------------------------------------------------------
    def parse_program(self) -> ast.Program:
        program = ast.Program(filename=self.filename)
        self.skip_newlines()
        while not self.at(TOK_EOF):
            self.skip_newlines()
            if self.at(TOK_EOF):
                break
            # Collect imports first.
            if self.at_op("~"):
                program.imports.append(self.parse_import())
                continue
            decl = self.parse_top_decl()
            if decl is not None:
                program.decls.append(decl)
            self.skip_newlines()
        return program

    def parse_top_decl(self) -> Optional[Any]:
        is_pub = False
        if self.at_kw("pub"):
            is_pub = True
            self.next()
            self.skip_newlines()

        if self.at_punct("#"):
            return self.parse_type_decl(is_pub)
        if self.at_punct("@"):
            return self.parse_fn_decl(is_pub)

        t = self.peek()
        raise ParseError(
            f"expected top-level declaration (#, @, ~), got {t.value!r}",
            t.line, t.col,
        )

    def parse_import(self) -> ast.ImportDecl:
        tok = self.eat_op("~")
        segments = [self.eat(TOK_IDENT).value]
        had_double_colon = False
        while True:
            if self.at_op("::"):
                self.next()
                had_double_colon = True
                segments.append(self.eat(TOK_IDENT).value)
            elif self.at_punct("."):
                self.next()
                segments.append(self.eat(TOK_IDENT).value)
            else:
                break
        if had_double_colon:
            path = ".".join(segments[:-1])
            symbol = segments[-1]
        else:
            path = ".".join(segments)
            symbol = None
        self.skip_newlines()
        return ast.ImportDecl(path=path, symbol=symbol,
                              line=tok.line, col=tok.col)

    # -- type declarations -------------------------------------------------
    def parse_type_decl(self, is_pub: bool) -> Any:
        tok = self.eat_punct("#")
        name = self.eat(TOK_IDENT).value
        self.eat_punct(":")
        self.skip_newlines()
        if not self.at(TOK_INDENT):
            # Empty type body.
            return ast.StructDecl(name=name, fields=[], is_pub=is_pub,
                                  line=tok.line, col=tok.col)
        self.eat(TOK_INDENT)

        fields: List[ast.FieldDecl] = []
        variants: List[ast.VariantDecl] = []
        kind: Optional[str] = None  # "struct" or "enum"

        while not self.at(TOK_DEDENT) and not self.at(TOK_EOF):
            self.skip_newlines()
            if self.at(TOK_DEDENT) or self.at(TOK_EOF):
                break
            line_tok = self.peek()
            # A line in a type body starts with an identifier.
            fname = self.eat(TOK_IDENT).value
            if self.at_punct("("):
                # Enum variant: Name(args)
                if kind is None:
                    kind = "enum"
                elif kind != "enum":
                    raise ParseError(
                        f"variant {fname} in struct {name}",
                        line_tok.line, line_tok.col,
                    )
                self.next()  # (
                params: List[ast.FieldDecl] = []
                if not self.at_punct(")"):
                    while True:
                        pname = self.eat(TOK_IDENT).value
                        self.eat_punct(":")
                        ptype = self.parse_type()
                        params.append(ast.FieldDecl(
                            name=pname, type=ptype,
                            line=line_tok.line, col=line_tok.col,
                        ))
                        if self.accept_punct(",") is None:
                            break
                self.eat_punct(")")
                variants.append(ast.VariantDecl(
                    name=fname, params=params,
                    line=line_tok.line, col=line_tok.col,
                ))
            elif self.at_punct(":"):
                # Struct field: name: type
                if kind is None:
                    kind = "struct"
                elif kind != "struct":
                    raise ParseError(
                        f"field {fname} in enum {name}",
                        line_tok.line, line_tok.col,
                    )
                self.next()  # :
                ftype = self.parse_type()
                fields.append(ast.FieldDecl(
                    name=fname, type=ftype,
                    line=line_tok.line, col=line_tok.col,
                ))
            else:
                # Bare identifier -> unit enum variant (e.g. `Dot`).
                if kind is None:
                    kind = "enum"
                elif kind != "enum":
                    raise ParseError(
                        f"unit variant {fname} in struct {name}",
                        line_tok.line, line_tok.col,
                    )
                variants.append(ast.VariantDecl(
                    name=fname, params=[],
                    line=line_tok.line, col=line_tok.col,
                ))
            self.skip_newlines()

        if self.at(TOK_DEDENT):
            self.next()

        if kind == "enum":
            return ast.EnumDecl(name=name, variants=variants, is_pub=is_pub,
                                line=tok.line, col=tok.col)
        return ast.StructDecl(name=name, fields=fields, is_pub=is_pub,
                              line=tok.line, col=tok.col)

    # -- function declarations ---------------------------------------------
    def parse_fn_decl(self, is_pub: bool) -> ast.FunctionDecl:
        tok = self.eat_punct("@")
        line, col = tok.line, tok.col

        first = self.eat(TOK_IDENT).value
        receiver: Optional[str] = None
        if self.accept_op("::") is not None:
            receiver = first
            fname = self.eat(TOK_IDENT).value
        else:
            fname = first

        generics: List[str] = []
        if self.accept_op("<") is not None:
            generics.append(self.eat(TOK_IDENT).value)
            while self.accept_punct(",") is not None:
                generics.append(self.eat(TOK_IDENT).value)
            self.eat_op(">")

        self.eat_punct("(")
        params: List[ast.ParamDecl] = []
        if not self.at_punct(")"):
            while True:
                pname = self.eat(TOK_IDENT).value
                self.eat_punct(":")
                ptype = self.parse_type()
                params.append(ast.ParamDecl(name=pname, type=ptype,
                                            line=line, col=col))
                if self.accept_punct(",") is None:
                    break
        self.eat_punct(")")

        if self.accept_op("->") is not None:
            ret_type = self.parse_type()
        else:
            ret_type = ast.UnitType(line=line, col=col)

        self.eat_punct(":")
        body = self.expect_block()

        return ast.FunctionDecl(
            name=fname, receiver=receiver, generics=generics,
            params=params, ret_type=ret_type, body=body,
            is_pub=is_pub, line=line, col=col,
        )

    # -- type parsing ------------------------------------------------------
    def parse_type(self) -> ast.TypeNode:
        t = self.peek()
        if self.accept_op("?") is not None:
            inner = self.parse_type_post()
            return ast.OptionalType(inner=inner, line=t.line, col=t.col)
        return self.parse_type_post()

    def parse_type_post(self) -> ast.TypeNode:
        t = self.peek()
        if self.at_kw("chan"):
            self.next()
            inner = self.parse_type_post()
            return ast.ChannelType(inner=inner, line=t.line, col=t.col)

        if self.at_kw("fn"):
            self.next()
            self.eat_punct("(")
            params: List[ast.TypeNode] = []
            if not self.at_punct(")"):
                while True:
                    params.append(self.parse_type())
                    if self.accept_punct(",") is None:
                        break
            self.eat_punct(")")
            self.eat_op("->")
            ret = self.parse_type()
            return ast.FuncType(params=params, ret=ret,
                                line=t.line, col=t.col)

        if self.at_punct("("):
            self.next()
            if self.accept_punct(")") is not None:
                return ast.UnitType(line=t.line, col=t.col)
            inner = self.parse_type()
            self.eat_punct(")")
            return inner

        name = self.eat(TOK_IDENT).value
        args: List[ast.TypeNode] = []
        if self.accept_op("<") is not None:
            if not self.at_op(">"):
                while True:
                    args.append(self.parse_type())
                    if self.accept_punct(",") is None:
                        break
            self.eat_op(">")
        return ast.NamedType(name=name, args=args,
                             line=t.line, col=t.col)

    # -- statements -------------------------------------------------------
    def parse_stmt(self) -> ast.Stmt:
        t = self.peek()

        if self.at_kw("let") or self.at_kw("var"):
            return self.parse_let()
        if self.at_kw("ret"):
            return self.parse_return()
        if self.at_kw("if"):
            return self.parse_if()
        if self.at_kw("while"):
            return self.parse_while()
        if self.at_kw("loop"):
            return self.parse_loop()
        if self.at_kw("for"):
            return self.parse_for()
        if self.at_kw("match"):
            return self.parse_match()
        if self.at_kw("break"):
            self.next()
            self.skip_line_end()
            return ast.BreakStmt(line=t.line, col=t.col)
        if self.at_kw("continue"):
            self.next()
            self.skip_line_end()
            return ast.ContinueStmt(line=t.line, col=t.col)
        if self.at_kw("task"):
            return self.parse_spawn()
        return self.parse_expr_stmt()

    def skip_line_end(self) -> None:
        self.skip_newlines()
        if self.accept_punct(";") is not None:
            self.skip_newlines()

    def parse_let(self) -> ast.Stmt:
        is_var = self.at_kw("var")
        tok = self.next()
        name = self.eat(TOK_IDENT).value
        type_ann: Optional[ast.TypeNode] = None
        if self.accept_punct(":") is not None:
            type_ann = self.parse_type()
        self.eat_op("=")
        value = self.parse_expr()
        self.skip_line_end()
        return ast.LetStmt(name=name, type_ann=type_ann, value=value,
                           mutable=is_var, line=tok.line, col=tok.col)

    def parse_return(self) -> ast.Stmt:
        tok = self.eat_kw("ret")
        value: Optional[ast.Expr] = None
        if not (self.at(TOK_NEWLINE) or self.at(TOK_DEDENT)
                or self.at(TOK_EOF) or self.at_punct(";")):
            value = self.parse_expr()
        self.skip_line_end()
        return ast.ReturnStmt(value=value, line=tok.line, col=tok.col)

    def parse_if(self) -> ast.Stmt:
        tok = self.eat_kw("if")
        cond = self.parse_expr()
        self.eat_punct(":")
        then_body = self.expect_block()
        elifs: List[Tuple[ast.Expr, List[ast.Stmt]]] = []
        else_body: Optional[List[ast.Stmt]] = None
        self.skip_newlines()
        while self.at_kw("elif"):
            self.next()
            econd = self.parse_expr()
            self.eat_punct(":")
            ebody = self.expect_block()
            elifs.append((econd, ebody))
            self.skip_newlines()
        if self.accept_kw("else") is not None:
            self.eat_punct(":")
            else_body = self.expect_block()
        return ast.IfStmt(cond=cond, then_body=then_body, elifs=elifs,
                          else_body=else_body, line=tok.line, col=tok.col)

    def parse_while(self) -> ast.Stmt:
        tok = self.eat_kw("while")
        cond = self.parse_expr()
        self.eat_punct(":")
        body = self.expect_block()
        return ast.WhileStmt(cond=cond, body=body,
                             line=tok.line, col=tok.col)

    def parse_loop(self) -> ast.Stmt:
        tok = self.eat_kw("loop")
        self.eat_punct(":")
        body = self.expect_block()
        return ast.LoopStmt(body=body, line=tok.line, col=tok.col)

    def parse_for(self) -> ast.Stmt:
        tok = self.eat_kw("for")
        var = self.eat(TOK_IDENT).value
        self.eat_kw("in")
        it = self.parse_expr()
        self.eat_punct(":")
        body = self.expect_block()
        return ast.ForStmt(var=var, iter=it, body=body,
                          line=tok.line, col=tok.col)

    def parse_match(self) -> ast.Stmt:
        tok = self.eat_kw("match")
        scrut = self.parse_expr()
        self.eat_punct(":")
        self.skip_newlines()
        arms: List[ast.MatchArm] = []
        if not self.at(TOK_INDENT):
            return ast.MatchStmt(scrutinee=scrut, arms=arms,
                                 line=tok.line, col=tok.col)
        self.eat(TOK_INDENT)
        while not self.at(TOK_DEDENT) and not self.at(TOK_EOF):
            self.skip_newlines()
            if self.at(TOK_DEDENT) or self.at(TOK_EOF):
                break
            arms.append(self.parse_match_arm())
        if self.at(TOK_DEDENT):
            self.next()
        return ast.MatchStmt(scrutinee=scrut, arms=arms,
                             line=tok.line, col=tok.col)

    def parse_match_arm(self) -> ast.MatchArm:
        ptok = self.peek()
        pattern = self.parse_pattern()
        # Accept either ':' or '=>' as match arm separator.
        if self.accept_punct(":") is None:
            self.accept_op("=>")
        self.skip_newlines()
        if self.at(TOK_INDENT):
            body = self.expect_block()
        else:
            body = [self.parse_stmt()]
        return ast.MatchArm(pattern=pattern, body=body,
                            line=ptok.line, col=ptok.col)

    def parse_pattern(self) -> ast.Pattern:
        t = self.peek()
        if self.at_punct("_"):
            self.next()
            return ast.WildcardPat(line=t.line, col=t.col)
        # Handle ok(v) and err(v) patterns.
        if self.at_kw("ok") or self.at_kw("err"):
            ctor_name = self.next().value
            self.eat_punct("(")
            args: List[ast.Pattern] = []
            if not self.at_punct(")"):
                args.append(self.parse_pattern())
            self.eat_punct(")")
            return ast.CtorPat(name=ctor_name, args=args,
                               line=t.line, col=t.col)
        if self.at(TOK_IDENT):
            name = self.next().value
            # Handle qualified names like Shape::Circle
            if self.at_op("::"):
                self.next()
                variant = self.next().value
                name = name + "::" + variant
            if self.at_punct("("):
                self.next()
                args: List[ast.Pattern] = []
                if not self.at_punct(")"):
                    while True:
                        args.append(self.parse_pattern())
                        if self.accept_punct(",") is None:
                            break
                self.eat_punct(")")
                return ast.CtorPat(name=name, args=args,
                                   line=t.line, col=t.col)
            return ast.VarPat(name=name, line=t.line, col=t.col)
        raise ParseError("expected pattern", t.line, t.col, t.value)

    def parse_spawn(self) -> ast.Stmt:
        tok = self.eat_kw("task")
        func = self.parse_postfix()
        self.eat_punct("(")
        args: List[ast.Expr] = []
        if not self.at_punct(")"):
            while True:
                args.append(self.parse_expr())
                if self.accept_punct(",") is None:
                    break
        self.eat_punct(")")
        self.skip_line_end()
        return ast.SpawnStmt(func=func, args=args,
                             line=tok.line, col=tok.col)

    def parse_expr_stmt(self) -> ast.Stmt:
        expr = self.parse_expr()
        if self.at_op("=") or self.at_op("+=") or self.at_op("-=") \
                or self.at_op("*=") or self.at_op("/=") or self.at_op("%="):
            op = self.next().value
            value = self.parse_expr()
            self.skip_line_end()
            return ast.ExprStmt(expr=ast.Assign(
                target=expr, op=op, value=value,
                line=expr.line, col=expr.col,
            ))
        self.skip_line_end()
        return ast.ExprStmt(expr=expr)

    # -- expression parsing (Pratt) ---------------------------------------
    def parse_expr(self, min_prec: int = 0) -> ast.Expr:
        self.depth += 1
        if self.depth > self.MAX_DEPTH:
            t = self.peek()
            raise ParseError("expression nesting too deep (max 500)",
                             t.line, t.col)
        left = self.parse_unary()
        while True:
            t = self.peek()
            if t.kind == TOK_OP and t.value in PREC:
                op = t.value
                prec = PREC[op]
                if prec < min_prec:
                    break

                # Assignment.
                if op in ("=", "+=", "-=", "*=", "/=", "%="):
                    self.next()
                    right = self.parse_expr(PREC[op])
                    left = ast.Assign(target=left, op=op, value=right,
                                      line=t.line, col=t.col)
                    continue

                # Pipe: |>
                if op == "|>":
                    self.next()
                    right = self.parse_expr(PREC[op] + 1)
                    if isinstance(right, ast.Call):
                        right.args.append(left)
                    else:
                        right = ast.Call(func=right, args=[left],
                                         line=right.line, col=right.col)
                    left = right
                    continue

                # `as` / `is`: RHS is a type.
                if op == "as":
                    self.next()
                    ty = self.parse_type()
                    left = ast.AsCast(expr=left, type=ty,
                                      line=t.line, col=t.col)
                    continue
                if op == "is":
                    self.next()
                    ty = self.parse_type()
                    left = ast.IsType(expr=left, type=ty,
                                      line=t.line, col=t.col)
                    continue

                # Range operators: `..` and `..=`.
                if op in ("..", "..="):
                    self.next()
                    right = self.parse_expr(prec + 1)
                    left = ast.Range(start=left, end=right,
                                     inclusive=(op == "..="),
                                     line=t.line, col=t.col)
                    continue

                # Binary operator.
                self.next()
                right = self.parse_expr(prec + 1)
                left = ast.BinaryOp(op=op, left=left, right=right,
                                    line=t.line, col=t.col)
                continue
            break
        return left

    def parse_unary(self) -> ast.Expr:
        t = self.peek()
        if t.kind == TOK_OP and t.value in ("-", "!", "~"):
            self.next()
            operand = self.parse_unary()
            return ast.UnaryOp(op=t.value, operand=operand,
                               line=t.line, col=t.col)
        if t.kind == TOK_KEYWORD and t.value == "try":
            self.next()
            expr = self.parse_postfix()
            # The postfix ? may already have wrapped it in TryExpr.
            if not isinstance(expr, ast.TryExpr):
                if not self.accept_op("?"):
                    raise ParseError("expected '?' after try expression",
                                     t.line, t.col)
                expr = ast.TryExpr(expr=expr, line=t.line, col=t.col)
            return expr
        return self.parse_postfix()

    def parse_postfix(self) -> ast.Expr:
        expr = self.parse_primary()
        while True:
            t = self.peek()
            if self.at_punct("."):
                self.next()
                name = self.eat(TOK_IDENT).value
                expr = ast.Field(obj=expr, name=name,
                                 line=t.line, col=t.col)
                continue
            if self.at_op("::"):
                self.next()
                name = self.eat(TOK_IDENT).value
                expr = ast.Field(obj=expr, name=name,
                                 line=t.line, col=t.col)
                continue
            if self.at_punct("("):
                self.next()
                args: List[ast.Expr] = []
                if not self.at_punct(")"):
                    while True:
                        args.append(self.parse_expr())
                        if self.accept_punct(",") is None:
                            break
                self.eat_punct(")")
                expr = ast.Call(func=expr, args=args,
                                line=t.line, col=t.col)
                continue
            if self.at_punct("["):
                self.next()
                idx = self.parse_expr()
                self.eat_punct("]")
                expr = ast.Index(obj=expr, index=idx,
                                line=t.line, col=t.col)
                continue
            if self.at_punct("{") and isinstance(expr, ast.Ident):
                self.next()
                fields: List[Tuple[str, ast.Expr]] = []
                while not self.at_punct("}"):
                    fname = self.eat(TOK_IDENT).value
                    self.eat_punct(":")
                    fval = self.parse_expr()
                    fields.append((fname, fval))
                    if self.accept_punct(",") is None:
                        break
                self.eat_punct("}")
                expr = ast.StructLit(name=expr.name, fields=fields,
                                     line=t.line, col=t.col)
                continue
            if self.at_op("?"):
                self.next()
                expr = ast.TryExpr(expr=expr, line=t.line, col=t.col)
                continue
            break
        return expr

    def parse_primary(self) -> ast.Expr:
        t = self.peek()

        if self.at_punct("("):
            self.next()
            if self.accept_punct(")") is not None:
                return ast.UnitLit(line=t.line, col=t.col)
            inner = self.parse_expr()
            self.eat_punct(")")
            return inner

        if self.at(TOK_INT):
            self.next()
            raw = t.value
            if raw.startswith(("0x", "0X")):
                val = int(raw, 16)
            elif raw.startswith(("0b", "0B")):
                val = int(raw, 2)
            else:
                val = int(raw, 10)
            return ast.IntLit(value=val, line=t.line, col=t.col)

        if self.at(TOK_FLOAT):
            self.next()
            return ast.FloatLit(value=float(t.value),
                                line=t.line, col=t.col)

        if self.at(TOK_STRING):
            self.next()
            return ast.StringLit(value=t.value, line=t.line, col=t.col)
        if self.at(TOK_RAWSTRING):
            self.next()
            return ast.RawStringLit(value=t.value, line=t.line, col=t.col)
        if self.at(TOK_FSTRING):
            self.next()
            return ast.StringLit(value=t.value, line=t.line, col=t.col)

        if self.at(TOK_CHAR):
            self.next()
            return ast.CharLit(value=t.value, line=t.line, col=t.col)

        if self.at_kw("true"):
            self.next()
            return ast.BoolLit(value=True, line=t.line, col=t.col)
        if self.at_kw("false"):
            self.next()
            return ast.BoolLit(value=False, line=t.line, col=t.col)

        if self.at_kw("none"):
            self.next()
            return ast.NoneExpr(line=t.line, col=t.col)
        if self.at_kw("some"):
            self.next()
            self.eat_punct("(")
            v = self.parse_expr()
            self.eat_punct(")")
            return ast.SomeExpr(value=v, line=t.line, col=t.col)

        if self.at_kw("ok"):
            self.next()
            self.eat_punct("(")
            v = self.parse_expr()
            self.eat_punct(")")
            return ast.OkExpr(value=v, line=t.line, col=t.col)
        if self.at_kw("err"):
            self.next()
            self.eat_punct("(")
            v = self.parse_expr()
            self.eat_punct(")")
            return ast.ErrExpr(value=v, line=t.line, col=t.col)

        if self.at(TOK_IDENT):
            self.next()
            return ast.Ident(name=t.value, line=t.line, col=t.col)

        if self.at_punct("|"):
            return self.parse_lambda()

        raise ParseError("unexpected token in expression",
                         t.line, t.col, f"{t.kind}:{t.value}")

    def parse_lambda(self) -> ast.Expr:
        tok = self.next()
        params: List[Tuple[str, Optional[ast.TypeNode]]] = []
        while not self.at_punct("|"):
            pname = self.eat(TOK_IDENT).value
            tann: Optional[ast.TypeNode] = None
            if self.accept_punct(":") is not None:
                tann = self.parse_type()
            params.append((pname, tann))
            if self.accept_punct(",") is None:
                break
        self.eat_punct("|")
        self.eat_op("=>")
        body = self.parse_expr()
        return ast.Lambda(params=params, body=body,
                          line=tok.line, col=tok.col)


def parse(tokens: List[Token], filename: str = "<input>") -> ast.Program:
    p = Parser(tokens, filename)
    return p.parse_program()
