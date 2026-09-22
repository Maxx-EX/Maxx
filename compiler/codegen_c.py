"""
Maxx -> C Code Generator (Level 1 bootstrap).

Lowers the Maxx AST to C source that can be compiled by the host C compiler.
In Level 2/3 this will be replaced by a direct native/LLVM backend written
in Maxx itself.

Conventions:
- User structs become `mx_<Name>` C structs.
- User enums become tagged unions `mx_<Name>` with a `tag` field.
- Functions become `mx_<name>` (or `mx_<Receiver>_<name>` for methods).
- `str` maps to the `mx_str` struct from runtime_minimal.c.
- `?T` maps to `mx_opt_<T>` `{int64_t tag; T val;}`.
- `Result<T,E>` maps to `mx_Result_<T>_<E>` `{int64_t tag; T ok_val; E err_val;}`.
"""

from typing import Dict, List, Optional, Tuple, Any

import mxast as ast
from checker import Checker, CheckError, TypeInfo, type_to_c, BUILTIN_TYPES


class CCodegen:
    def __init__(self, program: ast.Program):
        self.program = program
        self.checker = Checker(program)
        # Build variant index: variant_name -> (enum_name, tag_index)
        self.variants: Dict[str, Tuple[str, int]] = {}
        # Method map: method_name -> (receiver_type, c_function_name)
        self.methods: Dict[str, Tuple[str, str]] = {}
        # Struct names and declarations for positional construction.
        self.struct_names: Set[str] = set()
        self.struct_decls: Dict[str, ast.StructDecl] = {}
        # Collected C declarations (structs, enums, prototypes).
        self.type_decls: List[str] = []
        self.func_decls: List[str] = []
        self._tmp_counter = 0
        self._pending_result_type: Optional[TypeInfo] = None
        # Track variable types for codegen (without relying on checker scopes).
        self._var_types: Dict[str, TypeInfo] = {}
        # Track function return types.
        self._fn_ret_types: Dict[str, TypeInfo] = {}
        # Helper functions generated on-the-fly (lambdas etc).
        self.helper_funcs: List[str] = []

    # ------------------------------------------------------------------
    # Entry point.
    # ------------------------------------------------------------------
    def generate(self) -> str:
        self.checker.check()
        self._collect_variants_and_methods()
        # Emit type declarations first.
        for decl in self.program.decls:
            if isinstance(decl, ast.StructDecl):
                self.type_decls.append(self._gen_struct(decl))
            elif isinstance(decl, ast.EnumDecl):
                self.type_decls.append(self._gen_enum(decl))
        # Emit Result typedefs.
        self.type_decls.append(self._gen_result_typedefs())
        # Emit function declarations.
        for decl in self.program.decls:
            if isinstance(decl, ast.FunctionDecl):
                self.func_decls.append(self._gen_function(decl))
        return self._assemble_c()

    def _gen_result_typedefs(self) -> str:
        """Emit typedefs for all Result<T,E> types used in the program."""
        results: List[str] = []
        seen = set()
        # Add common Result types used by ok()/err() constructors.
        common_results = [
            ("mx_Result_int64_t_mx_str", "int64_t", "mx_str"),
            ("mx_Result_double_mx_str", "double", "mx_str"),
        ]
        for name, ok_c, err_c in common_results:
            seen.add(name)
            results.append(
                f"typedef struct {{\n"
                f"    int64_t tag;\n"
                f"    {ok_c} ok_val;\n"
                f"    {err_c} err_val;\n"
                f"}} {name};"
            )
        for decl in self.program.decls:
            if not isinstance(decl, ast.FunctionDecl):
                continue
            rt = decl.ret_type
            if isinstance(rt, ast.NamedType) and rt.name == "Result" \
                    and len(rt.args) == 2:
                ok_t = self.checker.resolve_type(rt.args[0])
                err_t = self.checker.resolve_type(rt.args[1])
                ok_c = type_to_c(ok_t)
                err_c = type_to_c(err_t)
                name = f"mx_Result_{ok_c}_{err_c}"
                if name in seen:
                    continue
                seen.add(name)
                results.append(
                    f"typedef struct {{\n"
                    f"    int64_t tag;\n"
                    f"    {ok_c} ok_val;\n"
                    f"    {err_c} err_val;\n"
                    f"}} {name};"
                )
        return "\n".join(results)

    def _collect_variants_and_methods(self) -> None:
        for decl in self.program.decls:
            if isinstance(decl, ast.EnumDecl):
                for idx, v in enumerate(decl.variants):
                    # Store both qualified and unqualified names.
                    self.variants[v.name] = (decl.name, idx)
                    self.variants[f"{decl.name}::{v.name}"] = (decl.name, idx)
            if isinstance(decl, ast.StructDecl):
                self.struct_names.add(decl.name)
                self.struct_decls[decl.name] = decl
            if isinstance(decl, ast.FunctionDecl):
                if decl.receiver:
                    cname = f"mx_{decl.receiver}_{decl.name}"
                    self.methods[decl.name] = (decl.receiver, cname)
                # Record return type.
                self._fn_ret_types[decl.name] = self.checker.resolve_type(decl.ret_type)

    # ------------------------------------------------------------------
    # Type generation.
    # ------------------------------------------------------------------
    def _c_type(self, t: ast.TypeNode) -> str:
        info = self.checker.resolve_type(t)
        return type_to_c(info)

    def _gen_struct(self, s: ast.StructDecl) -> str:
        fields = []
        for f in s.fields:
            ct = self._c_type(f.type)
            fields.append(f"    {ct} {f.name};")
        body = "\n".join(fields) if fields else "    /* no fields */"
        return f"typedef struct {{\n{body}\n}} mx_{s.name};"

    def _gen_enum(self, e: ast.EnumDecl) -> str:
        # Build a tagged union.
        # For recursive enums (variants contain the enum type itself), use pointers.
        union_fields = []
        for v in e.variants:
            if not v.params:
                continue  # unit variant needs no union member
            pdecls = []
            for i, p in enumerate(v.params):
                ct = self._c_type(p.type)
                # If the param type is the same as this enum, use a pointer.
                if isinstance(p.type, ast.NamedType) and p.type.name == e.name:
                    ct = f"mx_{e.name}*"
                field_name = p.name if p.name else f"_{i}"
                pdecls.append(f"{ct} {field_name}")
            pdecls_str = "; ".join(pdecls)
            union_fields.append(f"        struct {{ {pdecls_str}; }} {v.name};")
        union_body = "\n".join(union_fields) if union_fields else "        /* none */"
        # Check if this enum is recursive (has a variant containing the enum type).
        is_recursive = any(
            isinstance(p.type, ast.NamedType) and p.type.name == e.name
            for v in e.variants for p in v.params
        )
        decls = []
        if is_recursive:
            # Forward declaration for recursive enums (C requires named struct).
            decls.append(f"typedef struct mx_{e.name} mx_{e.name};")
            decls.append(f"struct mx_{e.name} {{")
            decls.append(f"    int64_t tag;")
            decls.append(f"    union {{")
            decls.append(union_body)
            decls.append(f"    }} data;")
            decls.append(f"}};")
        else:
            decls.append(f"typedef struct {{")
            decls.append(f"    int64_t tag;")
            decls.append(f"    union {{")
            decls.append(union_body)
            decls.append(f"    }} data;")
            decls.append(f"}} mx_{e.name};")
        # Emit tag constants.
        for idx, v in enumerate(e.variants):
            decls.append(f"#define mx_{e.name}_{v.name}_TAG {idx}")
        return "\n".join(decls)

    # ------------------------------------------------------------------
    # Function generation.
    # ------------------------------------------------------------------
    def _gen_function(self, fn: ast.FunctionDecl) -> str:
        # Set current function in checker for generic type resolution.
        self.checker.current_fn = fn
        ret_c = self._c_type(fn.ret_type)
        # C name.
        if fn.receiver:
            cname = f"mx_{fn.receiver}_{fn.name}"
        else:
            cname = f"mx_{fn.name}"
        # Parameters.
        params = []
        for p in fn.params:
            params.append(f"{self._c_type(p.type)} {p.name}")
        param_str = ", ".join(params) if params else "void"
        self._current_fn = fn
        self._pending_result_type = None
        if isinstance(fn.ret_type, ast.NamedType) and fn.ret_type.name == "Result":
            self._pending_result_type = self.checker.resolve_type(fn.ret_type)
        # Reset local variable type tracking and seed with parameters.
        self._var_types = {}
        for p in fn.params:
            self._var_types[p.name] = self.checker.resolve_type(p.type)
        if fn.receiver:
            self._var_types["self"] = TypeInfo(kind="struct", name=fn.receiver)
        # Push a scope for locals.
        self._local_scope: List[Tuple[str, str]] = []
        body_lines = self._gen_block(fn.body)
        self._current_fn = None
        # If return type is void and no explicit return, add `return;`.
        body = "\n".join(body_lines)
        return f"{ret_c} {cname}({param_str}) {{\n{body}\n}}"

    def _gen_block(self, stmts: List[ast.Stmt],
                   indent: int = 1) -> List[str]:
        out: List[str] = []
        pad = "    " * indent
        for s in stmts:
            out.extend(self._gen_stmt(s, indent))
        return out

    def _gen_stmt(self, s: ast.Stmt, indent: int = 1) -> List[str]:
        pad = "    " * indent
        out: List[str] = []

        if isinstance(s, ast.LetStmt):
            return self._gen_let(s, indent)
        if isinstance(s, ast.ReturnStmt):
            if s.value is not None:
                val = self._gen_expr(s.value)
                out.append(f"{pad}return {val};")
            else:
                out.append(f"{pad}return;")
            return out
        if isinstance(s, ast.ExprStmt):
            out.append(f"{pad}{self._gen_expr(s.expr)};")
            return out
        if isinstance(s, ast.IfStmt):
            cond = self._gen_expr(s.cond)
            out.append(f"{pad}if ({cond}) {{")
            out.extend(self._gen_block(s.then_body, indent + 1))
            out.append(f"{pad}}}")
            for ec, eb in s.elifs:
                econd = self._gen_expr(ec)
                out.append(f"{pad}else if ({econd}) {{")
                out.extend(self._gen_block(eb, indent + 1))
                out.append(f"{pad}}}")
            if s.else_body is not None:
                out.append(f"{pad}else {{")
                out.extend(self._gen_block(s.else_body, indent + 1))
                out.append(f"{pad}}}")
            return out
        if isinstance(s, ast.WhileStmt):
            cond = self._gen_expr(s.cond)
            out.append(f"{pad}while ({cond}) {{")
            out.extend(self._gen_block(s.body, indent + 1))
            out.append(f"{pad}}}")
            return out
        if isinstance(s, ast.LoopStmt):
            out.append(f"{pad}for (;;) {{")
            out.extend(self._gen_block(s.body, indent + 1))
            out.append(f"{pad}}}")
            return out
        if isinstance(s, ast.ForStmt):
            return self._gen_for(s, indent)
        if isinstance(s, ast.MatchStmt):
            return self._gen_match(s, indent)
        if isinstance(s, ast.BreakStmt):
            out.append(f"{pad}break;")
            return out
        if isinstance(s, ast.ContinueStmt):
            out.append(f"{pad}continue;")
            return out
        if isinstance(s, ast.SpawnStmt):
            out.append(f"{pad}{self._gen_spawn(s)};")
            return out
        return [f"{pad}/* unhandled stmt {type(s).__name__} */;"]

    def _gen_let(self, s: ast.LetStmt, indent: int) -> List[str]:
        pad = "    " * indent
        out: List[str] = []
        # Handle `let r = try expr?` specially (early return on error).
        if isinstance(s.value, ast.TryExpr):
            tmp = self._new_tmp()
            result_t = self._infer_type(s.value.expr)
            result_c = type_to_c(result_t)
            out.append(f"{pad}{result_c} {tmp} = {self._gen_expr(s.value.expr)};")
            out.append(f"{pad}if ({tmp}.tag != 0) return {tmp};")
            if s.type_ann is not None:
                ct = self._c_type(s.type_ann)
            else:
                ct = type_to_c(result_t.ok_type) if result_t.ok_type else "int64_t"
            out.append(f"{pad}{ct} {s.name} = {tmp}.ok_val;")
            self._var_types[s.name] = result_t.ok_type or TypeInfo(kind="scalar", name="int")
            return out
        # Normal let.
        if s.type_ann is not None:
            ct = self._c_type(s.type_ann)
            t = self.checker.resolve_type(s.type_ann)
        else:
            t = self._infer_type(s.value)
            ct = type_to_c(t)
            # Fallback: if type is unknown, use int64_t.
            if ct == "void*":
                ct = "int64_t"
        out.append(f"{pad}{ct} {s.name} = {self._gen_expr(s.value)};")
        self._var_types[s.name] = t
        return out

    def _infer_type(self, e: ast.Expr) -> TypeInfo:
        """Infer the type of an expression without relying on checker scopes."""
        if isinstance(e, ast.IntLit):
            return TypeInfo(kind="scalar", name="int")
        if isinstance(e, ast.FloatLit):
            return TypeInfo(kind="scalar", name="f64")
        if isinstance(e, (ast.StringLit, ast.RawStringLit)):
            return TypeInfo(kind="scalar", name="str")
        if isinstance(e, ast.BoolLit):
            return TypeInfo(kind="scalar", name="bool")
        if isinstance(e, ast.UnaryOp):
            # P1-12: propagate type through unary negation.
            return self._infer_type(e.operand)
        if isinstance(e, ast.Ident):
            if e.name in self._var_types:
                return self._var_types[e.name]
            # Unit enum variant.
            if e.name in self.variants:
                enum_name, _ = self.variants[e.name]
                return TypeInfo(kind="enum", name=enum_name)
            return TypeInfo(kind="scalar", name="int")
        if isinstance(e, ast.Call):
            if isinstance(e.func, ast.Ident):
                fname = e.func.name
                # Struct constructor: returns struct type
                if fname in self.struct_names:
                    return TypeInfo(kind="struct", name=fname)
                if fname in ("str",):
                    return TypeInfo(kind="scalar", name="str")
                if fname in ("int", "i64", "i32", "u32", "u64"):
                    return TypeInfo(kind="scalar", name="int")
                if fname in ("f64", "f32"):
                    return TypeInfo(kind="scalar", name=fname)
                if fname == "sqrt":
                    return TypeInfo(kind="scalar", name="f64")
                # String functions return str.
                str_funcs = {"to_upper", "to_lower", "trim", "substr", "char_at", "replace",
                             "read_line", "read_file", "http_recv"}
                if fname in str_funcs:
                    return TypeInfo(kind="scalar", name="str")
                # Numeric functions return int/f64.
                int_funcs = {"len", "find", "parse_int", "randint"}
                if fname in int_funcs:
                    return TypeInfo(kind="scalar", name="int")
                f64_funcs = {"rand", "parse_float"}
                if fname in f64_funcs:
                    return TypeInfo(kind="scalar", name="f64")
                if fname == "ok":
                    return TypeInfo(kind="result",
                                    ok_type=TypeInfo(kind="scalar", name="int"),
                                    err_type=TypeInfo(kind="scalar", name="str"))
                if fname == "err":
                    return TypeInfo(kind="result",
                                    ok_type=TypeInfo(kind="scalar", name="int"),
                                    err_type=TypeInfo(kind="scalar", name="str"))
                if fname in self._fn_ret_types:
                    return self._fn_ret_types[fname]
                # Generic functions: default to int64_t.
                if fname in self.checker.generic_funcs:
                    return TypeInfo(kind="scalar", name="int")
            if isinstance(e.func, ast.Field):
                mname = e.func.name
                if mname in self.methods:
                    _, cname = self.methods[mname]
                    # Look up the method's return type.
                    for fn in self.program.decls:
                        if isinstance(fn, ast.FunctionDecl) and fn.receiver \
                                and fn.name == mname:
                            return self.checker.resolve_type(fn.ret_type)
                if mname == "len":
                    return TypeInfo(kind="scalar", name="int")
                if mname == "recv":
                    return TypeInfo(kind="scalar", name="str")
        if isinstance(e, ast.BinaryOp):
            lt = self._infer_type(e.left)
            rt = self._infer_type(e.right)
            if e.op in ("+", "-", "*", "/"):
                if lt.is_float() or rt.is_float():
                    return TypeInfo(kind="scalar", name="f64")
                return TypeInfo(kind="scalar", name="int")
            if e.op in ("==", "!=", "<", ">", "<=", ">="):
                return TypeInfo(kind="scalar", name="bool")
        if isinstance(e, ast.SomeExpr):
            return TypeInfo(kind="option", inner=TypeInfo(kind="scalar", name="int"))
        if isinstance(e, ast.OkExpr):
            return TypeInfo(kind="result",
                            ok_type=TypeInfo(kind="scalar", name="int"),
                            err_type=TypeInfo(kind="scalar", name="str"))
        if isinstance(e, ast.ErrExpr):
            return TypeInfo(kind="result",
                            ok_type=TypeInfo(kind="scalar", name="int"),
                            err_type=TypeInfo(kind="scalar", name="str"))
        if isinstance(e, ast.StructLit):
            if e.name in self.variants:
                enum_name, _ = self.variants[e.name]
                return TypeInfo(kind="enum", name=enum_name)
            return TypeInfo(kind="struct", name=e.name)
        if isinstance(e, ast.Field):
            # Check if this is an enum variant access (Shape::Circle).
            variant_name = f"{e.obj.name}::{e.name}" if hasattr(e.obj, 'name') else None
            if variant_name and variant_name in self.variants:
                enum_name, _ = self.variants[variant_name]
                return TypeInfo(kind="enum", name=enum_name)
        return TypeInfo(kind="scalar", name="int")

    def _gen_for(self, s: ast.ForStmt, indent: int) -> List[str]:
        pad = "    " * indent
        out: List[str] = []
        it = s.iter
        # Track loop variable type.
        self._var_types[s.var] = TypeInfo(kind="scalar", name="int")
        if isinstance(it, ast.Range):
            start = self._gen_expr(it.start)
            end = self._gen_expr(it.end)
            op = "<" if not it.inclusive else "<="
            out.append(f"{pad}for (int64_t {s.var} = {start}; "
                       f"{s.var} {op} {end}; {s.var}++) {{")
            out.extend(self._gen_block(s.body, indent + 1))
            out.append(f"{pad}}}")
        else:
            # Generic iterable bootstrap: treat as integer loop.
            out.append(f"{pad}{{ /* TODO: generic for over {type(it).__name__} */")
            out.extend(self._gen_block(s.body, indent + 1))
            out.append(f"{pad}}}")
        return out

    def _gen_match(self, s: ast.MatchStmt, indent: int) -> List[str]:
        pad = "    " * indent
        out: List[str] = []
        scrut = self._gen_expr(s.scrutinee)
        out.append(f"{pad}switch ({scrut}.tag) {{")
        for arm in s.arms:
            pat = arm.pattern
            if isinstance(pat, ast.CtorPat):
                # Handle Result patterns: ok(v) and err(v).
                if pat.name == "ok":
                    out.append(f"{pad}    case 0: {{")
                    if pat.args and isinstance(pat.args[0], ast.VarPat):
                        arg_name = pat.args[0].name
                        out.append(f"{pad}        int64_t {arg_name} = {scrut}.ok_val;")
                    for b in arm.body:
                        out.extend(self._gen_stmt(b, indent + 2))
                    out.append(f"{pad}        break;")
                    out.append(f"{pad}    }}")
                    continue
                if pat.name == "err":
                    out.append(f"{pad}    case 1: {{")
                    if pat.args and isinstance(pat.args[0], ast.VarPat):
                        arg_name = pat.args[0].name
                        out.append(f"{pad}        mx_str {arg_name} = {scrut}.err_val;")
                    for b in arm.body:
                        out.extend(self._gen_stmt(b, indent + 2))
                    out.append(f"{pad}        break;")
                    out.append(f"{pad}    }}")
                    continue
                # Regular enum variant.
                enum_name, tag_idx = self.variants.get(pat.name, ("?", 0))
                out.append(f"{pad}    case {tag_idx}: {{")
                # Bind variant fields.
                vdecl = self._find_variant(enum_name, pat.name)
                if vdecl:
                    for i, vparam in enumerate(vdecl.params):
                        arg_pat = pat.args[i] if i < len(pat.args) else None
                        if isinstance(arg_pat, ast.VarPat):
                            ct = self._c_type(vparam.type)
                            field_name = vparam.name if vparam.name else f"_{i}"
                            out.append(f"{pad}        {ct} {arg_pat.name} = "
                                       f"{scrut}.data.{pat.name}.{field_name};")
                for b in arm.body:
                    out.extend(self._gen_stmt(b, indent + 2))
                out.append(f"{pad}        break;")
                out.append(f"{pad}    }}")
            elif isinstance(pat, ast.WildcardPat) or isinstance(pat, ast.VarPat):
                # Check if this VarPat is actually a qualified enum variant.
                if isinstance(pat, ast.VarPat) and pat.name in self.variants:
                    enum_name, tag_idx = self.variants[pat.name]
                    out.append(f"{pad}    case {tag_idx}: {{")
                    for b in arm.body:
                        out.extend(self._gen_stmt(b, indent + 2))
                    out.append(f"{pad}        break;")
                    out.append(f"{pad}    }}")
                else:
                    out.append(f"{pad}    default: {{")
                    for b in arm.body:
                        out.extend(self._gen_stmt(b, indent + 2))
                    out.append(f"{pad}        break;")
                    out.append(f"{pad}    }}")
        out.append(f"{pad}}}")
        return out

    def _find_variant(self, enum_name: str, vname: str):
        e = self.checker.enums.get(enum_name)
        if e:
            for v in e.variants:
                if v.name == vname:
                    return v
        return None

    def _gen_spawn(self, s: ast.SpawnStmt) -> str:
        # Bootstrap: task f(args) -> just call f(args) synchronously.
        func = self._gen_expr(s.func)
        args = ", ".join(self._gen_expr(a) for a in s.args)
        return f"{func}({args})"

    # ------------------------------------------------------------------
    # Expression generation.
    # ------------------------------------------------------------------
    def _new_tmp(self) -> str:
        self._tmp_counter += 1
        return f"_tmp{self._tmp_counter}"

    def _gen_expr(self, e: ast.Expr) -> str:
        if isinstance(e, ast.IntLit):
            return f"({e.value}LL)"
        if isinstance(e, ast.FloatLit):
            return f"({e.value})"
        if isinstance(e, ast.StringLit):
            escaped = e.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'mx_str_lit("{escaped}")'
        if isinstance(e, ast.FStringLit):
            # Build concatenation of literal parts and interpolated expressions.
            parts_c = []
            for text, expr in e.parts:
                if text:
                    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
                    parts_c.append(f'mx_str_lit("{escaped}")')
                if expr is not None:
                    # Convert expression to string based on inferred type.
                    expr_type = self._infer_type(expr)
                    expr_c = self._gen_expr(expr)
                    if expr_type.kind == "scalar" and expr_type.name == "str":
                        parts_c.append(expr_c)  # already a string
                    elif expr_type.kind == "scalar" and expr_type.name == "f64":
                        parts_c.append(f"mx_double_to_str({expr_c})")
                    elif expr_type.kind == "scalar" and expr_type.name == "bool":
                        parts_c.append(f"mx_bool_to_str({expr_c})")
                    else:
                        parts_c.append(f"mx_int_to_str({expr_c})")
            if not parts_c:
                return 'mx_str_lit("")'
            result = parts_c[0]
            for p in parts_c[1:]:
                result = f"mx_str_concat({result}, {p})"
            return result
        if isinstance(e, ast.RawStringLit):
            escaped = e.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'mx_str_lit("{escaped}")'
        if isinstance(e, ast.CharLit):
            return f"'{e.value}'"
        if isinstance(e, ast.BoolLit):
            return "true" if e.value else "false"
        if isinstance(e, ast.UnitLit):
            return "/* unit */"
        if isinstance(e, ast.Ident):
            # Unit enum variant (e.g. `Dot`) constructs the enum type.
            if e.name in self.variants:
                enum_name, tag_idx = self.variants[e.name]
                return f"((mx_{enum_name}){{.tag = {tag_idx}, .data = {{0}}}})"
            return e.name
        if isinstance(e, ast.BinaryOp):
            return self._gen_binary(e)
        if isinstance(e, ast.UnaryOp):
            operand = self._gen_expr(e.operand)
            if e.op == "!":
                return f"(!{operand})"
            if e.op == "~":
                return f"(~{operand})"
            return f"({e.op}{operand})"
        if isinstance(e, ast.Call):
            return self._gen_call(e)
        if isinstance(e, ast.Field):
            return self._gen_field(e)
        if isinstance(e, ast.Index):
            obj = self._gen_expr(e.obj)
            idx = self._gen_expr(e.index)
            return f"{obj}.data[{idx}]"
        if isinstance(e, ast.AsCast):
            inner = self._gen_expr(e.expr)
            ct = self._c_type(e.type)
            return f"(({ct})({inner}))"
        if isinstance(e, ast.IsType):
            # `is` type check is not implemented in bootstrap.
            # Output a warning at compile time.
            self.type_decls.append(
                '#warning "is type check is not implemented in bootstrap compiler"'
            )
            return "0 /* is not implemented in bootstrap */"
        if isinstance(e, ast.SomeExpr):
            inner = self._gen_expr(e.value)
            return f"((mx_opt_int){{1, (int64_t)({inner})}})"
        if isinstance(e, ast.NoneExpr):
            return "((mx_opt_int){0, 0})"
        if isinstance(e, ast.OkExpr):
            inner = self._gen_expr(e.value)
            # Use pending result type if available
            if self._pending_result_type and self._pending_result_type.kind == "result":
                ok_t = self._pending_result_type.ok_type
                err_t = self._pending_result_type.err_type
                ok_c = type_to_c(ok_t) if ok_t else "int64_t"
                err_c = type_to_c(err_t) if err_t else "mx_str"
                rname = f"mx_Result_{ok_c}_{err_c}"
                return f"(({rname}){{0, ({inner}), {{0}}}})"
            return f"((mx_Result_int64_t_mx_str){{0, ({inner}), {{0}}}})"
        if isinstance(e, ast.ErrExpr):
            inner = self._gen_expr(e.value)
            # Use pending result type if available
            if self._pending_result_type and self._pending_result_type.kind == "result":
                ok_t = self._pending_result_type.ok_type
                err_t = self._pending_result_type.err_type
                ok_c = type_to_c(ok_t) if ok_t else "int64_t"
                err_c = type_to_c(err_t) if err_t else "mx_str"
                rname = f"mx_Result_{ok_c}_{err_c}"
                return f"(({rname}){{1, {{0}}, ({inner})}})"
            return f"((mx_Result_int64_t_mx_str){{1, {{0}}, ({inner})}})"
        if isinstance(e, ast.TryExpr):
            # Bare `x?` outside a let: should not normally happen in
            # bootstrap. Evaluate and extract.
            inner = self._gen_expr(e.expr)
            return f"({inner}.ok_val)"
        if isinstance(e, ast.StructLit):
            return self._gen_struct_lit(e)
        if isinstance(e, ast.Range):
            # Ranges only appear in for loops, handled there.
            return f"({self._gen_expr(e.start)}..{self._gen_expr(e.end)})"
        if isinstance(e, ast.Assign):
            target = self._gen_expr(e.target)
            val = self._gen_expr(e.value)
            if e.op == "=":
                return f"({target} = {val})"
            return f"({target} {e.op} {val})"
        if isinstance(e, ast.Lambda):
            # Bootstrap: generate a C function and return a pointer.
            fn_name = f"mx_lambda_{id(e) & 0xFFFF}"
            # Build function signature. Params are tuples (name, type).
            param_strs = []
            for p in e.params:
                pname = p[0] if isinstance(p, tuple) else p.name
                param_strs.append(f"int64_t {pname}")
            params_c = ", ".join(param_strs)
            # Body can be a single expression or a block.
            if isinstance(e.body, list):
                body_lines = "\n".join(self._gen_block(e.body, 1))
            else:
                body_expr = self._gen_expr(e.body)
                body_lines = f"return {body_expr};"
            fn_code = f"static int64_t {fn_name}({params_c}) {{ {body_lines} }}"
            self.helper_funcs.append(fn_code)
            return f"((void*){fn_name})"
        return f"/* unhandled expr {type(e).__name__} */"

    def _gen_binary(self, e: ast.BinaryOp) -> str:
        lt = self._infer_type(e.left)
        rt = self._infer_type(e.right)
        l = self._gen_expr(e.left)
        r = self._gen_expr(e.right)
        op = e.op
        # Division by zero guard (P1-5).
        if op in ("/", "//"):
            return f"(({r}) == 0 ? (fprintf(stderr, \"maxx: runtime error: division by zero\\n\"), exit(1), 0) : (({l}) {op} ({r})))"
        # `^` is treated as power (pow) in bootstrap per the example.
        if op == "^":
            return f"pow((double)({l}), (double)({r}))"
        # String concatenation.
        if op == "+" and lt.kind == "scalar" and lt.name == "str":
            return f"mx_str_concat({l}, {r})"
        # Comparison / logical.
        if op in ("==", "!=", "<", "<=", ">", ">="):
            # String comparison uses runtime functions.
            if lt.kind == "scalar" and lt.name == "str" and rt.kind == "scalar" and rt.name == "str":
                if op == "==":
                    return f"mx_str_eq({l}, {r})"
                if op == "!=":
                    return f"!mx_str_eq({l}, {r})"
                if op == "<":
                    return f"mx_str_lt({l}, {r})"
                if op == ">":
                    return f"mx_str_gt({l}, {r})"
                if op == "<=":
                    return f"(!mx_str_gt({l}, {r}))"
                if op == ">=":
                    return f"(!mx_str_lt({l}, {r}))"
            return f"({l} {op} {r})"
        if op == "is":
            # Bootstrap: `x is Type` always returns true (static types are known at compile time).
            return "true"
        if op == "as":
            # Type cast: just return the value (C handles it implicitly).
            return f"({l})"
        if op == "&&":
            return f"({l} && {r})"
        if op == "||":
            return f"({l} || {r})"
        if op == "//":
            return f"({l} / {r})"
        # Arithmetic.
        return f"({l} {op} {r})"

    def _gen_call(self, e: ast.Call) -> str:
        # Builtin conversion functions.
        if isinstance(e.func, ast.Ident):
            name = e.func.name
            if name == "int" or name == "i64":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"((int64_t)({arg}))"
            if name == "i32":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"((int32_t)({arg}))"
            if name == "u32":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"((uint32_t)({arg}))"
            if name == "u64":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"((uint64_t)({arg}))"
            if name == "f64":
                arg = self._gen_expr(e.args[0]) if e.args else "0.0"
                return f"((double)({arg}))"
            if name == "f32":
                arg = self._gen_expr(e.args[0]) if e.args else "0.0f"
                return f"((float)({arg}))"
            if name == "str":
                return self._gen_str_conversion(e.args[0])
            if name == "bool":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"((bool)({arg}))"
            # Math functions (map directly to libm).
            math_map = {
                "sqrt": "sqrt", "sin": "sin", "cos": "cos",
                "tan": "tan", "asin": "asin", "acos": "acos",
                "atan": "atan", "atan2": "atan2",
                "log": "log", "log2": "log2", "log10": "log10",
                "exp": "exp", "pow": "pow",
                "floor": "floor", "ceil": "ceil", "round": "round",
                "fabs": "fabs", "abs": "llabs",
                "min": "fmin", "max": "fmax",
                # Additional math functions.
                "cbrt": "cbrt", "hypot": "hypot",
                "sinh": "sinh", "cosh": "cosh", "tanh": "tanh",
                "asinh": "asinh", "acosh": "acosh", "atanh": "atanh",
                "erf": "erf", "erfc": "erfc", "tgamma": "tgamma",
                "lgamma": "lgamma", "expm1": "expm1", "log1p": "log1p",
                "fmod": "fmod", "remainder": "remainder",
                "copysign": "copysign", "nan": "nan",
            }
            if name in math_map:
                c_fn = math_map[name]
                args = ", ".join(f"(double)({self._gen_expr(a)})" for a in e.args)
                return f"{c_fn}({args})"
            # Integer-only functions.
            if name == "rand":
                return "((double)rand())"
            if name == "randint":
                args_c = ", ".join(self._gen_expr(a) for a in e.args)
                return f"((double)(rand() % (int)({args_c})))"
            # String length.
            if name == "len":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"((double)({arg}.len))"
            # String conversion functions.
            if name == "to_upper":
                arg = self._gen_expr(e.args[0]) if e.args else 'mx_str_lit("")'
                return f"mx_str_upper({arg})"
            if name == "to_lower":
                arg = self._gen_expr(e.args[0]) if e.args else 'mx_str_lit("")'
                return f"mx_str_lower({arg})"
            if name == "trim":
                arg = self._gen_expr(e.args[0]) if e.args else 'mx_str_lit("")'
                return f"mx_str_trim({arg})"
            if name == "substr":
                args_c = ", ".join(self._gen_expr(a) for a in e.args)
                return f"mx_str_substr({args_c})"
            if name == "find":
                args_c = ", ".join(self._gen_expr(a) for a in e.args)
                return f"((double)mx_str_find({args_c}))"
            if name == "char_at":
                arg = self._gen_expr(e.args[0]) if e.args else 'mx_str_lit("")'
                idx = self._gen_expr(e.args[1]) if len(e.args) > 1 else "0"
                return f"mx_str_char_at({arg}, (int64_t)({idx}))"
            if name == "replace":
                args_c = ", ".join(self._gen_expr(a) for a in e.args)
                return f"mx_str_replace({args_c})"
            if name == "split":
                args_c = ", ".join(self._gen_expr(a) for a in e.args)
                return f"mx_str_split({args_c})"
            if name == "parse_int":
                arg = self._gen_expr(e.args[0]) if e.args else 'mx_str_lit("0")'
                return f"((double)mx_parse_int({arg}))"
            if name == "parse_float":
                arg = self._gen_expr(e.args[0]) if e.args else 'mx_str_lit("0")'
                return f"mx_parse_float({arg})"
            if name == "format_int":
                args_c = ", ".join(self._gen_expr(a) for a in e.args)
                return f"mx_format_int({args_c})"
            # Time functions.
            if name == "now":
                return "mx_now_sec()"
            if name == "unix_time":
                return "mx_now_sec()"
            if name == "sleep":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"mx_sleep({arg})"
            # IO functions.
            if name == "read_line":
                return "mx_read_line()"
            if name == "read_file":
                arg = self._gen_expr(e.args[0]) if e.args else '""'
                return f"mx_read_file({arg})"
            if name == "write_file":
                args = ", ".join(self._gen_expr(a) for a in e.args)
                return f"mx_write_file({args})"
            # HTTP server functions.
            if name == "http_listen":
                arg = self._gen_expr(e.args[0]) if e.args else "8080"
                return f"mx_http_listen({arg})"
            if name == "http_accept":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"mx_http_accept({arg})"
            if name == "http_recv":
                arg = self._gen_expr(e.args[0]) if e.args else "0"
                return f"mx_http_recv({arg})"
            if name == "http_send":
                args = ", ".join(self._gen_expr(a) for a in e.args)
                return f"mx_http_send({args})"
            # Regular function call.
            # Check if it's a struct constructor (positional args)
            if name in self.struct_names:
                # Get struct fields
                sdecl = self.struct_decls.get(name)
                if sdecl:
                    field_inits = []
                    for i, f in enumerate(sdecl.fields):
                        if i < len(e.args):
                            fval_c = self._gen_expr(e.args[i])
                            field_inits.append(f".{f.name} = {fval_c}")
                        else:
                            field_inits.append(f".{f.name} = 0")
                    inits = ", ".join(field_inits)
                    return f"((mx_{name}){{{inits}}})"
            args = ", ".join(self._gen_expr(a) for a in e.args)
            return f"mx_{name}({args})"

        # Method call: obj.method(args)
        if isinstance(e.func, ast.Field):
            obj = self._gen_expr(e.func.obj)
            mname = e.func.name
            # Special: arr.len() -> arr.len
            if mname == "len" and not e.args:
                return f"{obj}.len"
            # Channel methods.
            if mname == "send" and e.args:
                arg = self._gen_expr(e.args[0])
                return f"mx_chan_str_send({obj}, {arg})"
            if mname == "recv" and not e.args:
                return f"mx_chan_str_recv({obj})"
            # Str methods: s.to_upper(), s.substr(...)
            str_methods = {
                "to_upper": "mx_str_upper",
                "to_lower": "mx_str_lower",
                "trim": "mx_str_trim",
                "replace": "mx_str_replace",
                "find": "mx_str_find",
            }
            if mname in str_methods:
                cfunc = str_methods[mname]
                args_list = [obj] + [self._gen_expr(a) for a in e.args]
                args_c = ", ".join(args_list)
                return f"{cfunc}({args_c})"
            if mname == "substr" and len(e.args) >= 2:
                start = self._gen_expr(e.args[0])
                length = self._gen_expr(e.args[1])
                return f"mx_str_substr({obj}, (int64_t)({start}), (int64_t)({length}))"
            if mname == "char_at" and e.args:
                idx = self._gen_expr(e.args[0])
                return f"mx_str_char_at({obj}, (int64_t)({idx}))"
            # Look up method.
            if mname in self.methods:
                recv_type, cname = self.methods[mname]
                arg_list = ", ".join(self._gen_expr(a) for a in e.args)
                if arg_list:
                    return f"{cname}({obj}, {arg_list})"
                return f"{cname}({obj})"
            # Module functions: io.println(...)
            if isinstance(e.func.obj, ast.Ident) and e.func.obj.name == "io":
                args = ", ".join(self._gen_expr(a) for a in e.args)
                # Easter egg: println("hi！Maxx") prints philosophy.
                if mname == "println" and len(e.args) == 1:
                    arg = e.args[0]
                    if isinstance(arg, ast.StringLit) and "hi！Maxx" in arg.value:
                        return (
                            'mx_println(mx_str_lit("Maxx: simple by design, efficient by choice, transparent by default."))'
                        )
                if mname == "println":
                    return f"mx_println({args})"
                if mname == "print":
                    return f"mx_print({args})"
                if mname == "read_line":
                    return "mx_read_line()"
            # Fallback: obj.method(args)
            args = ", ".join(self._gen_expr(a) for a in e.args)
            return f"/* method */ {obj}.{mname}({args})"

        # Generic call.
        args = ", ".join(self._gen_expr(a) for a in e.args)
        return f"{self._gen_expr(e.func)}({args})"

    def _gen_str_conversion(self, arg: ast.Expr) -> str:
        t = self._infer_type(arg)
        v = self._gen_expr(arg)
        if t.kind == "scalar" and t.name == "str":
            return v
        if t.kind == "scalar" and t.name in ("int", "i64", "i32"):
            return f"mx_int_to_str({v})"
        if t.kind == "scalar" and t.name in ("f64", "f32"):
            return f"mx_double_to_str({v})"
        if t.kind == "scalar" and t.name == "bool":
            return f"mx_bool_to_str({v})"
        # Unknown type (e.g. generic T): treat as int64_t.
        if t.kind == "scalar":
            return f"mx_int_to_str((int64_t)({v}))"
        return f"mx_str_lit(\"?\")"

    def _gen_field(self, e: ast.Field) -> str:
        obj = self._gen_expr(e.obj)
        # Check if this is an enum variant access (Shape::Circle).
        variant_name = f"{e.obj.name}::{e.name}" if hasattr(e.obj, 'name') else None
        if variant_name and variant_name in self.variants:
            enum_name, tag_idx = self.variants[variant_name]
            return f"((mx_{enum_name}){{.tag = {tag_idx}, .data = {{0}}}})"
        # Channel creation: `chan str` is a type, not a field.
        # `ch.send(...)` etc. handled in call.
        return f"{obj}.{e.name}"

    def _gen_struct_lit(self, e: ast.StructLit) -> str:
        # Is it an enum variant?
        if e.name in self.variants:
            enum_name, tag_idx = self.variants[e.name]
            vdecl = self._find_variant(enum_name, e.name)
            field_inits = []
            if vdecl:
                for i, vparam in enumerate(vdecl.params):
                    if i < len(e.fields):
                        _, fval = e.fields[i]
                        field_name = vparam.name if vparam.name else f"_{i}"
                        fval_c = self._gen_expr(fval)
                        # If this is a recursive field (same enum type), allocate on heap.
                        if isinstance(vparam.type, ast.NamedType) and vparam.type.name == enum_name:
                            tmp = self._new_tmp()
                            # We'll handle this differently - for now just cast.
                            field_inits.append(f".{field_name} = {fval_c}")
                        else:
                            field_inits.append(f".{field_name} = {fval_c}")
                inner = ", ".join(field_inits)
                return (f"((mx_{enum_name}){{.tag = {tag_idx}, "
                        f".data.{e.name} = {{{inner}}}}})")
            return f"((mx_{enum_name}){{.tag = {tag_idx}, .data = {{0}}}})"
        # Regular struct literal.
        inits = ", ".join(f".{k} = {self._gen_expr(v)}" for k, v in e.fields)
        return f"((mx_{e.name}){{{inits}}})"

    # ------------------------------------------------------------------
    # Assemble the final C source.
    # ------------------------------------------------------------------
    def _assemble_c(self) -> str:
        parts = [
            "/*",
            " * Generated by Maxx Level-1 bootstrap compiler (Python).",
            " * This file is temporary; the real backend will be written in Maxx.",
            " */",
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <string.h>",
            "#include <stdbool.h>",
            "#include <stdint.h>",
            "#include <math.h>",
            "#include \"runtime_minimal.h\"",
            "",
        ]
        parts.append("/* ---- type declarations ---- */")
        parts.extend(self.type_decls)
        parts.append("")
        parts.append("/* ---- helper functions (lambdas etc) ---- */")
        parts.extend(self.helper_funcs)
        parts.append("")
        parts.append("/* ---- function declarations ---- */")
        parts.extend(self.func_decls)
        # Emit a main() that calls mx_main if present.
        parts.append("")
        parts.append("int main(void) {")
        parts.append("    return mx_main();")
        parts.append("}")
        parts.append("")
        return "\n".join(parts)
