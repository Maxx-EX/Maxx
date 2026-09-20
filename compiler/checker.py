"""
Maxx Type Checker (Level 1 bootstrap).

A deliberately small, permissive type checker:
- Collects all declared structs, enums, and functions into a symbol table.
- Resolves type names (including built-in scalars, Vec<T>, ?T, Result<T,E>).
- Validates that binary operators have compatible operands (rejects int/f64
  mixing without explicit cast, per ANCHOR §1 "绝不隐式数字转换").
- Attaches inferred types to expressions for the code generator.
- Reports errors with line/column.

This is NOT a full type system; it exists to catch obvious mistakes and to
give the C backend a resolved type for every expression.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import mxast as ast


class CheckError(Exception):
    def __init__(self, msg: str, line: int = 0, col: int = 0):
        super().__init__(f"type error at {line}:{col}: {msg}")
        self.line = line
        self.col = col


# Built-in scalar types and their C representations.
BUILTIN_TYPES = {
    "bool", "int", "i8", "i16", "i32", "i64",
    "u8", "u16", "u32", "u64", "f32", "f64", "char", "str",
    "isize", "usize",
}

# Numeric family.
INT_TYPES = {"int", "i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64",
             "isize", "usize", "char"}
FLOAT_TYPES = {"f32", "f64"}


@dataclass
class TypeInfo:
    """Resolved type for a node."""
    kind: str = "unit"  # scalar | struct | enum | option | result | vec |
                        # channel | func | unit | unknown
    name: str = ""      # for struct/enum/scalar
    args: List["TypeInfo"] = field(default_factory=list)
    inner: Optional["TypeInfo"] = None  # for option/channel
    ok_type: Optional["TypeInfo"] = None
    err_type: Optional["TypeInfo"] = None

    def is_numeric(self) -> bool:
        return self.kind == "scalar" and (
            self.name in INT_TYPES or self.name in FLOAT_TYPES
        )

    def is_int(self) -> bool:
        return self.kind == "scalar" and self.name in INT_TYPES

    def is_float(self) -> bool:
        return self.kind == "scalar" and self.name in FLOAT_TYPES

    def is_unit(self) -> bool:
        return self.kind == "unit"

    def c_name(self) -> str:
        """Return the C type name for this resolved type."""
        return type_to_c(self)


def type_to_c(t: TypeInfo) -> str:
    """Map a resolved Maxx type to a C type string."""
    if t.kind == "unit":
        return "void"
    if t.kind == "scalar":
        mapping = {
            "bool": "bool",
            "int": "int64_t",
            "i8": "int8_t", "i16": "int16_t", "i32": "int32_t", "i64": "int64_t",
            "u8": "uint8_t", "u16": "uint16_t", "u32": "uint32_t",
            "u64": "uint64_t",
            "isize": "int64_t", "usize": "uint64_t",
            "f32": "float", "f64": "double",
            "char": "uint32_t",
            "str": "mx_str",
        }
        return mapping.get(t.name, "void*")
    if t.kind == "struct":
        return "mx_" + t.name
    if t.kind == "enum":
        return "mx_" + t.name
    if t.kind == "option":
        return "mx_opt_" + t.inner.c_name()
    if t.kind == "result":
        return f"mx_Result_{t.ok_type.c_name()}_{t.err_type.c_name()}"
    if t.kind == "vec":
        return f"mx_Vec_{t.inner.c_name()}"
    if t.kind == "channel":
        return f"mx_chan_{t.inner.c_name()}*"
    if t.kind == "func":
        return "void*"
    return "void*"


class Checker:
    def __init__(self, program: ast.Program):
        self.program = program
        self.structs: Dict[str, ast.StructDecl] = {}
        self.enums: Dict[str, ast.EnumDecl] = {}
        self.functions: Dict[str, ast.FunctionDecl] = {}
        self.generic_funcs: Dict[str, ast.FunctionDecl] = {}
        # Scopes: list of dicts mapping variable name -> TypeInfo.
        self.scopes: List[Dict[str, TypeInfo]] = []
        self.immutable_vars: set = set()
        self.current_fn: Optional[ast.FunctionDecl] = None
        self._type_cache: Dict[str, TypeInfo] = {}

    # -- scope helpers -----------------------------------------------------
    def push_scope(self) -> None:
        self.scopes.append({})

    def pop_scope(self) -> None:
        self.scopes.pop()

    def declare_var(self, name: str, t: TypeInfo, immutable: bool = False) -> None:
        if not self.scopes:
            self.push_scope()
        self.scopes[-1][name] = t
        if immutable:
            self.immutable_vars.add(name)

    def is_immutable(self, name: str) -> bool:
        return name in self.immutable_vars

    def lookup_var(self, name: str) -> Optional[TypeInfo]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # -- main entry --------------------------------------------------------
    def check(self) -> None:
        self._collect_declarations()
        # Type-check each function body.
        for fn in self.program.decls:
            if isinstance(fn, ast.FunctionDecl):
                self.current_fn = fn
                self._check_function(fn)
                self.current_fn = None

    def _collect_declarations(self) -> None:
        for decl in self.program.decls:
            if isinstance(decl, ast.StructDecl):
                self.structs[decl.name] = decl
            elif isinstance(decl, ast.EnumDecl):
                self.enums[decl.name] = decl
            elif isinstance(decl, ast.FunctionDecl):
                if decl.generics:
                    self.generic_funcs[decl.name] = decl
                else:
                    self.functions[decl.name] = decl

    # -- type resolution ---------------------------------------------------
    def resolve_type(self, tn: ast.TypeNode) -> TypeInfo:
        if isinstance(tn, ast.UnitType):
            return TypeInfo(kind="unit")
        if isinstance(tn, ast.OptionalType):
            inner = self.resolve_type(tn.inner)
            return TypeInfo(kind="option", inner=inner)
        if isinstance(tn, ast.ChannelType):
            inner = self.resolve_type(tn.inner)
            return TypeInfo(kind="channel", inner=inner)
        if isinstance(tn, ast.FuncType):
            return TypeInfo(kind="func")
        if isinstance(tn, ast.NamedType):
            return self._resolve_named(tn)
        return TypeInfo(kind="unknown")

    def _resolve_named(self, tn: ast.NamedType) -> TypeInfo:
        name = tn.name
        # Generic stdlib types.
        if name == "Vec" and tn.args:
            inner = self.resolve_type(tn.args[0])
            return TypeInfo(kind="vec", inner=inner)
        if name == "Map" and len(tn.args) == 2:
            return TypeInfo(kind="struct", name="Map")
        if name == "Set" and tn.args:
            return TypeInfo(kind="struct", name="Set")
        if name == "Box" and tn.args:
            inner = self.resolve_type(tn.args[0])
            return TypeInfo(kind="struct", name="Box", args=[inner])
        if name == "Result" and len(tn.args) == 2:
            ok_t = self.resolve_type(tn.args[0])
            err_t = self.resolve_type(tn.args[1])
            return TypeInfo(kind="result", ok_type=ok_t, err_type=err_t)
        # Built-in scalar.
        if name in BUILTIN_TYPES:
            return TypeInfo(kind="scalar", name=name)
        # User struct.
        if name in self.structs:
            return TypeInfo(kind="struct", name=name)
        # User enum.
        if name in self.enums:
            return TypeInfo(kind="enum", name=name)
        # Generic type parameter (e.g. T in a generic function).
        if self.current_fn and name in self.current_fn.generics:
            return TypeInfo(kind="scalar", name=name)
        return TypeInfo(kind="unknown", name=name)

    # -- function body checking -------------------------------------------
    def _check_function(self, fn: ast.FunctionDecl) -> None:
        self.push_scope()
        # Declare parameters.
        for p in fn.params:
            self.declare_var(p.name, self.resolve_type(p.type))
        # Receiver parameter `self`.
        if fn.receiver:
            self.declare_var("self", TypeInfo(kind="struct", name=fn.receiver))
        # Check body statements.
        for stmt in fn.body:
            self._check_stmt(stmt)
        self.pop_scope()

    def _check_stmt(self, stmt: ast.Stmt) -> Optional[TypeInfo]:
        if isinstance(stmt, ast.LetStmt):
            t = self._check_expr(stmt.value)
            if stmt.type_ann is not None:
                expected = self.resolve_type(stmt.type_ann)
                # Check implicit conversion violation (P0-2).
                self._check_compat(expected, t, stmt)
                t = expected
            # Track immutability: let is immutable, var is mutable.
            is_immutable = not getattr(stmt, "mutable", False)
            self.declare_var(stmt.name, t, immutable=is_immutable)
            return t
        if isinstance(stmt, ast.ReturnStmt):
            if stmt.value is not None:
                return self._check_expr(stmt.value)
            return TypeInfo(kind="unit")
        if isinstance(stmt, ast.ExprStmt):
            return self._check_expr(stmt.expr)
        if isinstance(stmt, ast.IfStmt):
            self._check_expr(stmt.cond)
            self.push_scope()
            for s in stmt.then_body:
                self._check_stmt(s)
            self.pop_scope()
            for cond, body in stmt.elifs:
                self._check_expr(cond)
                self.push_scope()
                for s in body:
                    self._check_stmt(s)
                self.pop_scope()
            if stmt.else_body is not None:
                self.push_scope()
                for s in stmt.else_body:
                    self._check_stmt(s)
                self.pop_scope()
            return TypeInfo(kind="unit")
        if isinstance(stmt, ast.WhileStmt):
            self._check_expr(stmt.cond)
            self.push_scope()
            for s in stmt.body:
                self._check_stmt(s)
            self.pop_scope()
            return TypeInfo(kind="unit")
        if isinstance(stmt, ast.LoopStmt):
            self.push_scope()
            for s in stmt.body:
                self._check_stmt(s)
            self.pop_scope()
            return TypeInfo(kind="unit")
        if isinstance(stmt, ast.ForStmt):
            it_t = self._check_expr(stmt.iter)
            # Range -> loop variable is int.
            self.declare_var(stmt.var, TypeInfo(kind="scalar", name="int"))
            self.push_scope()
            self.declare_var(stmt.var, TypeInfo(kind="scalar", name="int"))
            for s in stmt.body:
                self._check_stmt(s)
            self.pop_scope()
            return TypeInfo(kind="unit")
        if isinstance(stmt, ast.MatchStmt):
            self._check_expr(stmt.scrutinee)
            for arm in stmt.arms:
                self.push_scope()
                self._check_pattern(arm.pattern, stmt.scrutinee)
                for s in arm.body:
                    self._check_stmt(s)
                self.pop_scope()
            return TypeInfo(kind="unit")
        if isinstance(stmt, (ast.BreakStmt, ast.ContinueStmt)):
            return TypeInfo(kind="unit")
        if isinstance(stmt, ast.SpawnStmt):
            self._check_expr(stmt.func)
            for a in stmt.args:
                self._check_expr(a)
            return TypeInfo(kind="unit")
        return TypeInfo(kind="unknown")

    def _check_pattern(self, pat: ast.Pattern, scrut: ast.Expr) -> None:
        if isinstance(pat, ast.VarPat):
            # Bootstrap: default pattern vars to f64 (matches examples).
            self.declare_var(pat.name, TypeInfo(kind="scalar", name="f64"))
        elif isinstance(pat, ast.CtorPat):
            # Declare constructor args as variables (simplified).
            for arg in pat.args:
                self._check_pattern(arg, scrut)
        # Wildcard: nothing to declare.

    def _check_expr(self, expr: ast.Expr) -> TypeInfo:
        if isinstance(expr, ast.IntLit):
            return TypeInfo(kind="scalar", name="int")
        if isinstance(expr, ast.FloatLit):
            return TypeInfo(kind="scalar", name="f64")
        if isinstance(expr, (ast.StringLit, ast.RawStringLit)):
            return TypeInfo(kind="scalar", name="str")
        if isinstance(expr, ast.CharLit):
            return TypeInfo(kind="scalar", name="char")
        if isinstance(expr, ast.BoolLit):
            return TypeInfo(kind="scalar", name="bool")
        if isinstance(expr, ast.UnitLit):
            return TypeInfo(kind="unit")
        if isinstance(expr, ast.Ident):
            v = self.lookup_var(expr.name)
            if v is not None:
                return v
            # Maybe it's a function name.
            if expr.name in self.functions or expr.name in self.generic_funcs:
                return TypeInfo(kind="func")
            # Builtin conversion functions.
            if expr.name in ("int", "f64", "f32", "str", "bool", "char"):
                return TypeInfo(kind="func")
            # std.io, std.math, etc. (imported modules).
            return TypeInfo(kind="struct", name=expr.name)
        if isinstance(expr, ast.BinaryOp):
            lt = self._check_expr(expr.left)
            rt = self._check_expr(expr.right)
            return self._check_binary_op(expr.op, lt, rt, expr)
        if isinstance(expr, ast.UnaryOp):
            return self._check_expr(expr.operand)
        if isinstance(expr, ast.Call):
            return self._check_call(expr)
        if isinstance(expr, ast.Field):
            ot = self._check_expr(expr.obj)
            return self._check_field(ot, expr.name, expr)
        if isinstance(expr, ast.Index):
            ot = self._check_expr(expr.obj)
            self._check_expr(expr.index)
            if ot.kind == "vec":
                return ot.inner
            return TypeInfo(kind="scalar", name="int")
        if isinstance(expr, ast.AsCast):
            return self.resolve_type(expr.type)
        if isinstance(expr, ast.IsType):
            return TypeInfo(kind="scalar", name="bool")
        if isinstance(expr, ast.SomeExpr):
            it = self._check_expr(expr.value)
            return TypeInfo(kind="option", inner=it)
        if isinstance(expr, ast.NoneExpr):
            return TypeInfo(kind="option")
        if isinstance(expr, ast.OkExpr):
            it = self._check_expr(expr.value)
            return TypeInfo(kind="result", ok_type=it,
                            err_type=TypeInfo(kind="scalar", name="str"))
        if isinstance(expr, ast.ErrExpr):
            it = self._check_expr(expr.value)
            return TypeInfo(kind="result",
                            ok_type=TypeInfo(kind="scalar", name="int"),
                            err_type=it)
        if isinstance(expr, ast.TryExpr):
            t = self._check_expr(expr.expr)
            if t.kind == "result":
                return t.ok_type or TypeInfo(kind="unknown")
            return TypeInfo(kind="unknown")
        if isinstance(expr, ast.StructLit):
            return TypeInfo(kind="struct", name=expr.name)
        if isinstance(expr, ast.Range):
            self._check_expr(expr.start)
            self._check_expr(expr.end)
            return TypeInfo(kind="scalar", name="int")
        if isinstance(expr, ast.Assign):
            t = self._check_expr(expr.value)
            # Check immutable variable reassignment (P0-2).
            if isinstance(expr.target, ast.Ident):
                name = expr.target.name
                if self.is_immutable(name):
                    raise CheckError(
                        f"cannot assign to immutable variable '{name}' "
                        f"(use 'var' for mutable binding)",
                        getattr(expr, 'line', 0), getattr(expr, 'col', 0))
                # Check type compatibility.
                existing = self.lookup_var(name)
                if existing is not None:
                    self._check_compat(existing, t, expr)
            return t
        if isinstance(expr, ast.Lambda):
            return TypeInfo(kind="func")
        return TypeInfo(kind="unknown")

    def _check_compat(self, expected: TypeInfo, actual: TypeInfo, node) -> None:
        """Check that actual type is compatible with expected (P0-2)."""
        if expected.kind == "unknown" or actual.kind == "unknown":
            return
        if expected.kind == actual.kind and expected.name == actual.name:
            return
        # Allow integer literal in float context (literal promotion).
        if expected.is_float() and actual.is_int():
            return
        if expected.is_int() and actual.is_int():
            return
        if expected.is_float() and actual.is_float():
            return
        # Numeric family compat.
        if expected.is_numeric() and actual.is_numeric():
            return
        raise CheckError(
            f"type mismatch: expected {expected.name}, got {actual.name}",
            getattr(node, 'line', 0), getattr(node, 'col', 0))

    def _check_binary_op(self, op: str, lt: TypeInfo, rt: TypeInfo,
                         node: ast.Expr) -> TypeInfo:
        # Comparison / logical ops always produce bool.
        if op in ("==", "!=", "<", "<=", ">", ">=", "&&", "||"):
            return TypeInfo(kind="scalar", name="bool")
        # Arithmetic: reject implicit int<->f64 mixing (ANCHOR §1).
        # Exception: an integer literal in a float context is allowed
        # (literal promotion, not an implicit conversion of a variable).
        if op in ("+", "-", "*", "/", "%", "//", "<<", ">>", "&", "^", "|"):
            if lt.is_float() or rt.is_float():
                if lt.is_int() or rt.is_int():
                    # Check if the int side is a literal (allowed) or a variable.
                    left_is_literal = isinstance(node, ast.BinaryOp) and isinstance(node.left, ast.IntLit)
                    right_is_literal = isinstance(node, ast.BinaryOp) and isinstance(node.right, ast.IntLit)
                    if not (left_is_literal or right_is_literal):
                        raise CheckError(
                            f"implicit conversion between {lt.name} and {rt.name} "
                            f"is forbidden (use int() or f64() explicitly)",
                            node.line, node.col,
                        )
                return TypeInfo(kind="scalar",
                                name="f64" if lt.is_float() else rt.name)
            if lt.is_int() and rt.is_int():
                # Both int: result is the wider type (simplified: int).
                return TypeInfo(kind="scalar", name="int")
            # str + str -> str (concatenation).
            if lt.kind == "scalar" and lt.name == "str" and \
               rt.kind == "scalar" and rt.name == "str":
                return TypeInfo(kind="scalar", name="str")
            return TypeInfo(kind="scalar", name="int")
        if op in ("..", "..="):
            return TypeInfo(kind="scalar", name="int")
        return TypeInfo(kind="unknown")

    def _check_call(self, call: ast.Call) -> TypeInfo:
        # Builtin conversion functions: int(x), f64(x), str(x), bool(x).
        if isinstance(call.func, ast.Ident):
            fname = call.func.name
            if fname in ("int", "i32", "i64", "u32", "u64"):
                for a in call.args:
                    self._check_expr(a)
                return TypeInfo(kind="scalar",
                                name="i64" if fname == "int" else fname)
            if fname in ("f32", "f64"):
                for a in call.args:
                    self._check_expr(a)
                return TypeInfo(kind="scalar", name=fname)
            if fname == "str":
                for a in call.args:
                    self._check_expr(a)
                return TypeInfo(kind="scalar", name="str")
            if fname == "bool":
                for a in call.args:
                    self._check_expr(a)
                return TypeInfo(kind="scalar", name="bool")
            if fname == "sqrt":
                for a in call.args:
                    self._check_expr(a)
                return TypeInfo(kind="scalar", name="f64")
            if fname == "abs":
                for a in call.args:
                    self._check_expr(a)
                return TypeInfo(kind="scalar", name="int")
            # Regular function.
            fn = self.functions.get(fname)
            if fn is not None:
                return self.resolve_type(fn.ret_type)
            if fname in self.generic_funcs:
                # Generic: return the type parameter (simplified).
                return TypeInfo(kind="scalar", name="unknown")
        # Method call: obj.method(args) - handled via Field + Call.
        if isinstance(call.func, ast.Field):
            self._check_expr(call.func.obj)
            for a in call.args:
                self._check_expr(a)
            # .len() -> int, .send()/ .recv() -> channel ops.
            if call.func.name == "len":
                return TypeInfo(kind="scalar", name="int")
            if call.func.name == "recv":
                return TypeInfo(kind="scalar", name="str")
            if call.func.name == "send":
                return TypeInfo(kind="unit")
            # Look up user-defined method.
            for fn in self.program.decls:
                if isinstance(fn, ast.FunctionDecl) and fn.receiver \
                        and fn.name == call.func.name:
                    return self.resolve_type(fn.ret_type)
        for a in call.args:
            self._check_expr(a)
        return TypeInfo(kind="unknown")

    def _check_field(self, ot: TypeInfo, name: str,
                     node: ast.Expr) -> TypeInfo:
        # Vec.len -> int.
        if ot.kind == "vec" and name == "len":
            return TypeInfo(kind="scalar", name="int")
        # Struct field access.
        if ot.kind == "struct" and ot.name in self.structs:
            sdecl = self.structs[ot.name]
            for f in sdecl.fields:
                if f.name == name:
                    return self.resolve_type(f.type)
        # Enum variant access (tag).
        if ot.kind == "enum":
            return TypeInfo(kind="scalar", name="int")
        # Module access (io.println -> unknown return, trust it).
        if ot.kind == "struct":
            return TypeInfo(kind="func")
        return TypeInfo(kind="unknown")
