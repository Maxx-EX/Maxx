"""
Maxx AST node definitions (Level 1 bootstrap).

All nodes carry line/col for readable diagnostics.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
@dataclass
class TypeNode:
    line: int = 0
    col: int = 0


@dataclass
class NamedType(TypeNode):
    name: str = ""
    args: List[TypeNode] = field(default_factory=list)  # generic args e.g. Vec<int>

    def __repr__(self) -> str:
        if self.args:
            return f"{self.name}<{', '.join(repr(a) for a in self.args)}>"
        return self.name


@dataclass
class OptionalType(TypeNode):
    inner: TypeNode = None  # type: ignore

    def __repr__(self) -> str:
        return f"?{self.inner!r}"


@dataclass
class ChannelType(TypeNode):
    inner: TypeNode = None  # type: ignore

    def __repr__(self) -> str:
        return f"chan {self.inner!r}"


@dataclass
class FuncType(TypeNode):
    params: List[TypeNode] = field(default_factory=list)
    ret: TypeNode = None  # type: ignore

    def __repr__(self) -> str:
        return f"fn({', '.join(repr(p) for p in self.params)}) -> {self.ret!r}"


@dataclass
class UnitType(TypeNode):
    def __repr__(self) -> str:
        return "()"


# ---------------------------------------------------------------------------
# Patterns (for match arms and let bindings)
# ---------------------------------------------------------------------------
@dataclass
class Pattern:
    line: int = 0
    col: int = 0


@dataclass
class VarPat(Pattern):
    name: str = ""

    def __repr__(self) -> str:
        return self.name


@dataclass
class CtorPat(Pattern):
    name: str = ""
    args: List[Pattern] = field(default_factory=list)

    def __repr__(self) -> str:
        if self.args:
            return f"{self.name}({', '.join(repr(a) for a in self.args)})"
        return self.name


@dataclass
class WildcardPat(Pattern):
    name: str = "_"

    def __repr__(self) -> str:
        return "_"


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------
@dataclass
class Expr:
    line: int = 0
    col: int = 0


@dataclass
class IntLit(Expr):
    value: int = 0

    def __repr__(self) -> str:
        return str(self.value)


@dataclass
class FloatLit(Expr):
    value: float = 0.0

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass
class StringLit(Expr):
    value: str = ""

    def __repr__(self) -> str:
        return f'"{self.value}"'


@dataclass
class RawStringLit(Expr):
    value: str = ""

    def __repr__(self) -> str:
        return f"`{self.value}`"


@dataclass
class FStringLit(Expr):
    # For bootstrap we store the literal template and a list of interpolated
    # expressions. Segments are (text, expr_or_None) pairs.
    parts: List[Tuple[str, Optional[Expr]]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"f<{self.parts!r}>"


@dataclass
class CharLit(Expr):
    value: str = ""

    def __repr__(self) -> str:
        return f"'{self.value}'"


@dataclass
class BoolLit(Expr):
    value: bool = False

    def __repr__(self) -> str:
        return "true" if self.value else "false"


@dataclass
class UnitLit(Expr):
    def __repr__(self) -> str:
        return "()"


@dataclass
class Ident(Expr):
    name: str = ""

    def __repr__(self) -> str:
        return self.name


@dataclass
class BinaryOp(Expr):
    op: str = ""
    left: Expr = None  # type: ignore
    right: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


@dataclass
class UnaryOp(Expr):
    op: str = ""
    operand: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"({self.op}{self.operand})"


@dataclass
class Call(Expr):
    func: Expr = None  # type: ignore
    args: List[Expr] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.func}({', '.join(repr(a) for a in self.args)})"


@dataclass
class Field(Expr):
    obj: Expr = None  # type: ignore
    name: str = ""

    def __repr__(self) -> str:
        return f"{self.obj}.{self.name}"


@dataclass
class Index(Expr):
    obj: Expr = None  # type: ignore
    index: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"{self.obj}[{self.index}]"


@dataclass
class Ternary(Expr):
    cond: Expr = None  # type: ignore
    then_expr: Expr = None  # type: ignore
    else_expr: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"({self.cond} ? {self.then_expr} : {self.else_expr})"


@dataclass
class AsCast(Expr):
    expr: Expr = None  # type: ignore
    type: TypeNode = None  # type: ignore

    def __repr__(self) -> str:
        return f"({self.expr} as {self.type!r})"


@dataclass
class IsType(Expr):
    expr: Expr = None  # type: ignore
    type: TypeNode = None  # type: ignore

    def __repr__(self) -> str:
        return f"({self.expr} is {self.type!r})"


@dataclass
class SomeExpr(Expr):
    value: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"some({self.value})"


@dataclass
class NoneExpr(Expr):
    def __repr__(self) -> str:
        return "none"


@dataclass
class OkExpr(Expr):
    value: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"ok({self.value})"


@dataclass
class ErrExpr(Expr):
    value: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"err({self.value})"


@dataclass
class TryExpr(Expr):
    expr: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"try {self.expr}?"


@dataclass
class StructLit(Expr):
    name: str = ""
    fields: List[Tuple[str, Expr]] = field(default_factory=list)

    def __repr__(self) -> str:
        inner = ", ".join(f"{k}: {v}" for k, v in self.fields)
        return f"{self.name}{{{inner}}}"


@dataclass
class Range(Expr):
    start: Expr = None  # type: ignore
    end: Expr = None  # type: ignore
    inclusive: bool = False

    def __repr__(self) -> str:
        op = "..=" if self.inclusive else ".."
        return f"({self.start}{op}{self.end})"


@dataclass
class Lambda(Expr):
    params: List[Tuple[str, Optional[TypeNode]]] = field(default_factory=list)
    body: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"|{', '.join(p[0] for p in self.params)}| => {self.body}"


@dataclass
class Assign(Expr):
    target: Expr = None  # type: ignore
    op: str = "="
    value: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return f"({self.target} {self.op} {self.value})"


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------
@dataclass
class Stmt:
    line: int = 0
    col: int = 0


@dataclass
class LetStmt(Stmt):
    name: str = ""
    type_ann: Optional[TypeNode] = None
    value: Expr = None  # type: ignore
    mutable: bool = False

    def __repr__(self) -> str:
        kw = "var" if self.mutable else "let"
        ann = f": {self.type_ann!r}" if self.type_ann else ""
        return f"{kw} {self.name}{ann} = {self.value}"


@dataclass
class ReturnStmt(Stmt):
    value: Optional[Expr] = None

    def __repr__(self) -> str:
        return f"ret {self.value}" if self.value is not None else "ret"


@dataclass
class ExprStmt(Stmt):
    expr: Expr = None  # type: ignore

    def __repr__(self) -> str:
        return repr(self.expr)


@dataclass
class IfStmt(Stmt):
    cond: Expr = None  # type: ignore
    then_body: List[Stmt] = field(default_factory=list)
    elifs: List[Tuple[Expr, List[Stmt]]] = field(default_factory=list)
    else_body: Optional[List[Stmt]] = None

    def __repr__(self) -> str:
        parts = [f"if {self.cond}: ..."]
        for c, b in self.elifs:
            parts.append(f"elif {c}: ...")
        if self.else_body is not None:
            parts.append("else: ...")
        return " ".join(parts)


@dataclass
class WhileStmt(Stmt):
    cond: Expr = None  # type: ignore
    body: List[Stmt] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"while {self.cond}: ..."


@dataclass
class LoopStmt(Stmt):
    body: List[Stmt] = field(default_factory=list)

    def __repr__(self) -> str:
        return "loop: ..."


@dataclass
class ForStmt(Stmt):
    var: str = ""
    iter: Expr = None  # type: ignore
    body: List[Stmt] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"for {self.var} in {self.iter}: ..."


@dataclass
class MatchArm:
    pattern: Pattern = None  # type: ignore
    body: List[Stmt] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class MatchStmt(Stmt):
    scrutinee: Expr = None  # type: ignore
    arms: List[MatchArm] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"match {self.scrutinee}: ..."


@dataclass
class BreakStmt(Stmt):
    def __repr__(self) -> str:
        return "break"


@dataclass
class ContinueStmt(Stmt):
    def __repr__(self) -> str:
        return "continue"


@dataclass
class SpawnStmt(Stmt):
    func: Expr = None  # type: ignore
    args: List[Expr] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"task {self.func}({', '.join(repr(a) for a in self.args)})"


# ---------------------------------------------------------------------------
# Top-level declarations
# ---------------------------------------------------------------------------
@dataclass
class ImportDecl:
    path: str = ""           # dotted path, e.g. "std.io"
    symbol: Optional[str] = None  # e.g. Vec for `~ std.collections::Vec`
    line: int = 0
    col: int = 0


@dataclass
class FieldDecl:
    name: str = ""
    type: TypeNode = None  # type: ignore
    line: int = 0
    col: int = 0


@dataclass
class VariantDecl:
    name: str = ""
    params: List[FieldDecl] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class StructDecl:
    name: str = ""
    fields: List[FieldDecl] = field(default_factory=list)
    is_pub: bool = False
    line: int = 0
    col: int = 0


@dataclass
class EnumDecl:
    name: str = ""
    variants: List[VariantDecl] = field(default_factory=list)
    is_pub: bool = False
    line: int = 0
    col: int = 0


@dataclass
class ParamDecl:
    name: str = ""
    type: TypeNode = None  # type: ignore
    line: int = 0
    col: int = 0


@dataclass
class FunctionDecl:
    name: str = ""
    receiver: Optional[str] = None  # e.g. "Point" for @ Point::dist(...)
    generics: List[str] = field(default_factory=list)
    params: List[ParamDecl] = field(default_factory=list)
    ret_type: TypeNode = None  # type: ignore
    body: List[Stmt] = field(default_factory=list)
    is_pub: bool = False
    line: int = 0
    col: int = 0


@dataclass
class Program:
    imports: List[ImportDecl] = field(default_factory=list)
    decls: List[Any] = field(default_factory=list)  # StructDecl/EnumDecl/FunctionDecl
    filename: str = "<input>"
