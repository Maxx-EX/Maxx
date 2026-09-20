"""
Maxx Intermediate Representation (Level 1 bootstrap).

For the bootstrap, the IR is a normalized, flat textual dump of the typed
AST. In Level 2 (self-hosted) this will become a proper SSA IR with a
serialization format (.mxbc).

The `dump_ir` function produces a human-readable Lisp-like s-expression so
the `maxxc ir` command can show the middle end output.
"""

from typing import List

import mxast as ast
from checker import Checker, TypeInfo


def _tname(t) -> str:
    if isinstance(t, TypeInfo):
        return t.c_name()
    return repr(t)


def dump_ir(program: ast.Program) -> str:
    """Return a normalized IR dump of the program."""
    lines: List[str] = []
    lines.append("; Maxx IR (bootstrap)")
    lines.append(f"; module: {program.filename}")
    for imp in program.imports:
        sym = f"::{imp.symbol}" if imp.symbol else ""
        lines.append(f"(import {imp.path}{sym})")
    for decl in program.decls:
        lines.extend(_dump_decl(decl))
    return "\n".join(lines)


def _dump_decl(d) -> List[str]:
    out: List[str] = []
    if isinstance(d, ast.StructDecl):
        fields = " ".join(f"{f.name}:{_type_ir(f.type)}" for f in d.fields)
        out.append(f"(struct {d.name} ({fields}))")
    elif isinstance(d, ast.EnumDecl):
        vs = " ".join(
            f"{v.name}({', '.join(_type_ir(p.type) for p in v.params)})"
            for v in d.variants
        )
        out.append(f"(enum {d.name} ({vs}))")
    elif isinstance(d, ast.FunctionDecl):
        recv = f"::{d.receiver}" if d.receiver else ""
        g = f"<{','.join(d.generics)}>" if d.generics else ""
        params = " ".join(f"{p.name}:{_type_ir(p.type)}" for p in d.params)
        out.append(f"(fn{recv} {d.name}{g} ({params}) -> {_type_ir(d.ret_type)})")
        for s in d.body:
            out.append("  " + _dump_stmt(s))
    return out


def _type_ir(t) -> str:
    if isinstance(t, ast.UnitType):
        return "()"
    if isinstance(t, ast.OptionalType):
        return f"?{_type_ir(t.inner)}"
    if isinstance(t, ast.ChannelType):
        return f"chan {_type_ir(t.inner)}"
    if isinstance(t, ast.NamedType):
        if t.args:
            return f"{t.name}<{', '.join(_type_ir(a) for a in t.args)}>"
        return t.name
    return str(t)


def _dump_stmt(s) -> str:
    if isinstance(s, ast.LetStmt):
        kw = "var" if s.mutable else "let"
        ann = f":{_type_ir(s.type_ann)}" if s.type_ann else ""
        return f"({kw} {s.name}{ann} {_dump_expr(s.value)})"
    if isinstance(s, ast.ReturnStmt):
        if s.value is not None:
            return f"(ret {_dump_expr(s.value)})"
        return "(ret)"
    if isinstance(s, ast.ExprStmt):
        return _dump_expr(s.expr)
    if isinstance(s, ast.IfStmt):
        parts = [f"(if {_dump_expr(s.cond)}"]
        for st in s.then_body:
            parts.append("    " + _dump_stmt(st))
        for c, b in s.elifs:
            parts.append(f"  (elif {_dump_expr(c)}")
            for st in b:
                parts.append("      " + _dump_stmt(st))
        if s.else_body is not None:
            parts.append("  (else")
            for st in s.else_body:
                parts.append("      " + _dump_stmt(st))
        parts.append(")")
        return "\n".join(parts)
    if isinstance(s, ast.WhileStmt):
        inner = "\n    ".join(_dump_stmt(b) for b in s.body)
        return f"(while {_dump_expr(s.cond)}\n    {inner})"
    if isinstance(s, ast.ForStmt):
        inner = "\n    ".join(_dump_stmt(b) for b in s.body)
        return f"(for {s.var} in {_dump_expr(s.iter)}\n    {inner})"
    if isinstance(s, ast.MatchStmt):
        arms = []
        for arm in s.arms:
            b = "\n      ".join(_dump_stmt(x) for x in arm.body)
            arms.append(f"    ({_dump_pat(arm.pattern)}\n      {b})")
        return f"(match {_dump_expr(s.scrutinee)}\n" + "\n".join(arms) + ")"
    if isinstance(s, ast.BreakStmt):
        return "(break)"
    if isinstance(s, ast.ContinueStmt):
        return "(continue)"
    if isinstance(s, ast.SpawnStmt):
        args = " ".join(_dump_expr(a) for a in s.args)
        return f"(task {_dump_expr(s.func)} {args})"
    return f"<{type(s).__name__}>"


def _dump_pat(p) -> str:
    if isinstance(p, ast.VarPat):
        return p.name
    if isinstance(p, ast.CtorPat):
        args = " ".join(_dump_pat(a) for a in p.args)
        return f"{p.name}({args})"
    if isinstance(p, ast.WildcardPat):
        return "_"
    return "?"


def _dump_expr(e) -> str:
    if isinstance(e, ast.IntLit):
        return str(e.value)
    if isinstance(e, ast.FloatLit):
        return repr(e.value)
    if isinstance(e, ast.StringLit):
        return f'"{e.value}"'
    if isinstance(e, ast.Ident):
        return e.name
    if isinstance(e, ast.BinaryOp):
        return f"({e.op} {_dump_expr(e.left)} {_dump_expr(e.right)})"
    if isinstance(e, ast.UnaryOp):
        return f"({e.op} {_dump_expr(e.operand)})"
    if isinstance(e, ast.Call):
        args = " ".join(_dump_expr(a) for a in e.args)
        return f"(call {_dump_expr(e.func)} {args})"
    if isinstance(e, ast.Field):
        return f"(field {_dump_expr(e.obj)} .{e.name})"
    if isinstance(e, ast.Index):
        return f"(index {_dump_expr(e.obj)} {_dump_expr(e.index)})"
    if isinstance(e, ast.AsCast):
        return f"(as {_dump_expr(e.expr)} {_type_ir(e.type)})"
    if isinstance(e, ast.StructLit):
        fields = " ".join(f"{k}:{_dump_expr(v)}" for k, v in e.fields)
        return f"(structlit {e.name} {fields})"
    if isinstance(e, ast.Range):
        op = "..=" if e.inclusive else ".."
        return f"({op} {_dump_expr(e.start)} {_dump_expr(e.end)})"
    if isinstance(e, ast.SomeExpr):
        return f"(some {_dump_expr(e.value)})"
    if isinstance(e, ast.NoneExpr):
        return "none"
    if isinstance(e, ast.OkExpr):
        return f"(ok {_dump_expr(e.value)})"
    if isinstance(e, ast.ErrExpr):
        return f"(err {_dump_expr(e.value)})"
    if isinstance(e, ast.TryExpr):
        return f"(try? {_dump_expr(e.expr)})"
    if isinstance(e, ast.BoolLit):
        return "true" if e.value else "false"
    if isinstance(e, ast.UnitLit):
        return "()"
    return f"<{type(e).__name__}>"
