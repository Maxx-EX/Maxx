#!/usr/bin/env python3
"""
Maxx Bootstrap Compiler (Level 1).

THIS IS A TEMPORARY BOOTSTRAP TOOL. Per ANCHOR §8, this compiler is written
in Python solely to bootstrap the Maxx language. The production compiler
(Level 2/3) will be rewritten in Maxx itself.

Four-layer file format (v1.0):
    .max   - source file (input)
    .mxx   - compiled shared library (native, like .so)
    .smx   - distribution package (whl-style zip)
    .zip   - project archive

Usage:
    python3 maxxc.py tokenize <file.max>
    python3 maxxc.py parse <file.max>
    python3 maxxc.py ir <file.max>
    python3 maxxc.py codegen <file.max> [-o out.c]
    python3 maxxc.py build <file.max> [-o output.mxx]
    python3 maxxc.py pack <lib.mxx> [-o pkg.smx] [--src src/]
    python3 maxxc.py archive <project_dir> [-o project.zip]
    python3 maxxc.py run <file.max>            # codegen + cc + execute
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile

# Make sure we can import the sibling modules when running as a script.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from lexer import Lexer, LexError  # noqa: E402
from parser import Parser, ParseError  # noqa: E402
from checker import Checker, CheckError  # noqa: E402
from ir import dump_ir  # noqa: E402
from codegen_c import CCodegen  # noqa: E402


def _read_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _compile_to_binary(c_src: str, runtime_dir: str) -> str:
    """Compile C source to a native binary. Returns path to binary."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".c", delete=False, dir=runtime_dir
    ) as tf:
        tf.write(c_src)
        c_path = tf.name
    bin_path = c_path + ".bin"
    cc = os.environ.get("CC", "cc")
    cmd = [
        cc, "-std=c11", "-O2", "-o", bin_path,
        c_path,
        os.path.join(runtime_dir, "runtime_minimal.c"),
        "-lm",
    ]
    print(f"# compiling: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("C compilation failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        try:
            os.unlink(c_path)
        except OSError:
            pass
        return None
    try:
        os.unlink(c_path)
    except OSError:
        pass
    return bin_path


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_tokenize(args) -> int:
    src = _read_source(args.file)
    try:
        tokens = Lexer(src, args.file).tokenize()
    except LexError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for t in tokens:
        if t.kind in ("NEWLINE",):
            print(f"  line {t.line}: <newline>")
        elif t.kind == "INDENT":
            print(f"  line {t.line}: <indent>")
        elif t.kind == "DEDENT":
            print(f"  line {t.line}: <dedent>")
        elif t.kind == "EOF":
            print("  <eof>")
        else:
            print(f"  line {t.line}: {t.kind:10s} {t.value!r}")
    return 0


def cmd_parse(args) -> int:
    src = _read_source(args.file)
    try:
        tokens = Lexer(src, args.file).tokenize()
        prog = Parser(tokens, args.file).parse_program()
    except (LexError, ParseError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"// Program: {prog.filename}")
    for imp in prog.imports:
        sym = f"::{imp.symbol}" if imp.symbol else ""
        print(f"import {imp.path}{sym}")
    for decl in prog.decls:
        print(_dump_decl_compact(decl))
    return 0


def _dump_decl_compact(d) -> str:
    from mxast import StructDecl, EnumDecl, FunctionDecl
    if isinstance(d, StructDecl):
        fields = ", ".join(f"{f.name}:{f.type}" for f in d.fields)
        return f"struct {d.name} {{ {fields} }}"
    if isinstance(d, EnumDecl):
        vs = " | ".join(
            f"{v.name}({', '.join(p.name for p in v.params)})"
            for v in d.variants
        )
        return f"enum {d.name} {{ {vs} }}"
    if isinstance(d, FunctionDecl):
        recv = f"{d.receiver}::" if d.receiver else ""
        params = ", ".join(f"{p.name}:{p.type}" for p in d.params)
        return (f"fn {recv}{d.name}({params}) -> {d.ret_type} "
                f"[body: {len(d.body)} stmts]")
    return str(d)


def cmd_ir(args) -> int:
    src = _read_source(args.file)
    try:
        tokens = Lexer(src, args.file).tokenize()
        prog = Parser(tokens, args.file).parse_program()
    except (LexError, ParseError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    try:
        print(dump_ir(prog))
    except CheckError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_codegen(args) -> int:
    src = _read_source(args.file)
    try:
        tokens = Lexer(src, args.file).tokenize()
        prog = Parser(tokens, args.file).parse_program()
        cg = CCodegen(prog)
        c_src = cg.generate()
    except (LexError, ParseError, CheckError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    out = args.output or "-"
    if out == "-":
        sys.stdout.write(c_src)
    else:
        with open(out, "w", encoding="utf-8") as f:
            f.write(c_src)
        print(f"# wrote {out}", file=sys.stderr)
    return 0


def cmd_build(args) -> int:
    """Build .max source into .mxx shared library."""
    src = _read_source(args.file)
    target = getattr(args, "target", "x86_64-linux")

    # Validate target.
    valid_targets = {"x86_64-linux", "arm64-android", "arm64-ios", "wasm32"}
    if target not in valid_targets:
        print(f"error: unknown target '{target}'", file=sys.stderr)
        print(f"valid targets: {', '.join(sorted(valid_targets))}", file=sys.stderr)
        return 1

    # For cross-compilation targets, we need the appropriate toolchain.
    if target == "arm64-android":
        ndk = os.environ.get("ANDROID_NDK", os.environ.get("NDK", ""))
        if not ndk:
            print("error: --target arm64-android requires the Android NDK.",
                  file=sys.stderr)
            print("Set ANDROID_NDK or NDK environment variable to your NDK path.",
                  file=sys.stderr)
            print("Example: export ANDROID_NDK=~/Android/Sdk/ndk/26.1.10909125",
                  file=sys.stderr)
            return 1
        print(f"# NOTE: arm64-android cross-compile via NDK not yet implemented "
              f"in bootstrap; emitting IR only.", file=sys.stderr)
        # For bootstrap, just emit IR and manifest without native codegen.
        output = args.output
        if output is None:
            base = os.path.splitext(args.file)[0]
            output = base + ".mxx"
        manifest = {
            "format": "mxx@1",
            "name": os.path.basename(output).replace(".mxx", ""),
            "source": os.path.basename(args.file),
            "entry": "mx_main",
            "target": target,
            "exports": ["mx_main"],
        }
        try:
            tokens = Lexer(src, args.file).tokenize()
            prog = Parser(tokens, args.file).parse_program()
            ir_text = dump_ir(prog)
        except (LexError, ParseError, CheckError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("ir/cache.mxbc", ir_text)
        print(f"# wrote {output} (IR only, no native code)", file=sys.stderr)
        return 0

    try:
        tokens = Lexer(src, args.file).tokenize()
        prog = Parser(tokens, args.file).parse_program()
        cg = CCodegen(prog)
        c_src = cg.generate()
        ir_text = dump_ir(prog)
    except (LexError, ParseError, CheckError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    runtime_dir = os.path.dirname(os.path.abspath(__file__))
    bin_path = _compile_to_binary(c_src, runtime_dir)
    if bin_path is None:
        return 1

    output = args.output
    if output is None:
        base = os.path.splitext(args.file)[0]
        output = base + ".mxx"

    # .mxx is a binary container: for bootstrap, it's a zip with
    # manifest + native binary + IR cache.
    manifest = {
        "format": "mxx@1",
        "name": os.path.basename(output).replace(".mxx", ""),
        "source": os.path.basename(args.file),
        "entry": "mx_main",
        "target": target,
        "exports": ["mx_main"],
    }

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("code/native/program", open(bin_path, "rb").read())
        zf.writestr("ir/cache.mxbc", ir_text)

    print(f"# wrote {output}", file=sys.stderr)
    os.unlink(bin_path)
    return 0


def cmd_pack(args) -> int:
    """Pack .mxx + interface .max files into .smx distribution package."""
    lib_path = args.lib
    if not os.path.exists(lib_path):
        print(f"error: library not found: {lib_path}", file=sys.stderr)
        return 1

    output = args.output
    if output is None:
        base = os.path.splitext(lib_path)[0]
        output = base + ".smx"

    pkg_name = os.path.basename(lib_path).replace(".mxx", "")
    manifest = {
        "format": "smx@1",
        "name": pkg_name,
        "version": "0.1.0",
        "entry": f"{pkg_name}/mod.max",
        "targets": ["x86_64-linux"],
        "dependencies": {},
        "authors": ["Maxx Bootstrap"],
        "license": "MIT",
    }

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        # Copy the .mxx library.
        zf.write(lib_path, f"lib/x86_64-linux/{pkg_name}.mxx")
        # Copy source files if provided.
        if args.src and os.path.isdir(args.src):
            for root, _, files in os.walk(args.src):
                for fn in files:
                    full = os.path.join(root, fn)
                    arc = os.path.relpath(full, args.src)
                    zf.write(full, f"src/{arc}")

    print(f"# wrote {output}", file=sys.stderr)
    return 0


def cmd_archive(args) -> int:
    """Archive a project directory into .zip."""
    project_dir = args.dir
    if not os.path.isdir(project_dir):
        print(f"error: directory not found: {project_dir}", file=sys.stderr)
        return 1

    output = args.output
    if output is None:
        base = os.path.basename(os.path.normpath(project_dir))
        output = base + ".zip"

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(project_dir):
            for fn in files:
                full = os.path.join(root, fn)
                arc = os.path.relpath(full, project_dir)
                zf.write(full, arc)

    print(f"# wrote {output}", file=sys.stderr)
    return 0


def cmd_run(args) -> int:
    src = _read_source(args.file)
    try:
        tokens = Lexer(src, args.file).tokenize()
        prog = Parser(tokens, args.file).parse_program()
        cg = CCodegen(prog)
        c_src = cg.generate()
    except (LexError, ParseError, CheckError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    runtime_dir = os.path.dirname(os.path.abspath(__file__))
    bin_path = _compile_to_binary(c_src, runtime_dir)
    if bin_path is None:
        return 1
    run = subprocess.run([bin_path], capture_output=True, text=True)
    sys.stdout.write(run.stdout)
    sys.stderr.write(run.stderr)
    os.unlink(bin_path)
    return run.returncode


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

def cmd_repl(args) -> int:
    """Maxx interactive REPL."""
    runtime_dir = os.path.dirname(os.path.abspath(__file__))

    print("Maxx REPL (Level 1 bootstrap). Type :help for commands, :quit to exit.")

    while True:
        try:
            line = input("maxx> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if line.startswith(":"):
            cmd = line[1:].strip()
            if cmd in ("quit", "exit", "q"):
                break
            elif cmd == "reset":
                print("(REPL reset)")
                continue
            elif cmd == "help":
                print("Maxx REPL commands:")
                print("  :help     show this help")
                print("  :reset    reset REPL state")
                print("  :quit     exit the REPL")
                print("")
                print("Examples:")
                print("  io.println(\"hello\")")
                print("  let x = 42")
                print("  io.println(str(sqrt(16.0)))")
                continue
            else:
                print(f"unknown command: :{cmd}")
                continue

        # Wrap line in a complete main() function.
        wrapper = f"@ main() -> int:\n    {line}\n    ret 0\n"

        try:
            tokens = Lexer(wrapper, "<repl>").tokenize()
            prog = Parser(tokens, "<repl>").parse_program()
            cg = CCodegen(prog)
            c_src = cg.generate()
        except Exception as e:
            print(f"error: {e}")
            continue

        bin_path = _compile_to_binary(c_src, runtime_dir)
        if bin_path is None:
            continue

        try:
            run = subprocess.run([bin_path], capture_output=True, text=True, timeout=5)
            if run.stdout:
                print(run.stdout, end="")
            if run.stderr:
                # Filter out compilation noise
                for l in run.stderr.splitlines():
                    if not l.startswith("# compiling"):
                        print(l, file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("(timeout)")
        finally:
            try:
                os.unlink(bin_path)
            except OSError:
                pass

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Maxx Level-1 bootstrap compiler (temporary Python tool)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_tok = sub.add_parser("tokenize", help="lex a .max file")
    p_tok.add_argument("file")
    p_tok.set_defaults(func=cmd_tokenize)

    p_par = sub.add_parser("parse", help="parse a .max file and print AST")
    p_par.add_argument("file")
    p_par.set_defaults(func=cmd_parse)

    p_ir = sub.add_parser("ir", help="dump normalized IR")
    p_ir.add_argument("file")
    p_ir.set_defaults(func=cmd_ir)

    p_cg = sub.add_parser("codegen", help="emit C source")
    p_cg.add_argument("file")
    p_cg.add_argument("-o", "--output", default=None)
    p_cg.set_defaults(func=cmd_codegen)

    p_b = sub.add_parser("build", help="compile .max to .mxx shared library")
    p_b.add_argument("file")
    p_b.add_argument("-o", "--output", default=None, help="output .mxx path")
    p_b.add_argument("--target", default="x86_64-linux",
                    help="target platform (x86_64-linux, arm64-android, arm64-ios, wasm32)")
    p_b.set_defaults(func=cmd_build)

    p_pk = sub.add_parser("pack", help="pack .mxx into .smx distribution")
    p_pk.add_argument("lib", help=".mxx library file")
    p_pk.add_argument("-o", "--output", default=None, help="output .smx path")
    p_pk.add_argument("--src", default=None, help="source directory to include")
    p_pk.set_defaults(func=cmd_pack)

    p_ar = sub.add_parser("archive", help="archive project directory to .zip")
    p_ar.add_argument("dir", help="project directory")
    p_ar.add_argument("-o", "--output", default=None, help="output .zip path")
    p_ar.set_defaults(func=cmd_archive)

    p_r = sub.add_parser("run", help="codegen, compile, and run")
    p_r.add_argument("file")
    p_r.set_defaults(func=cmd_run)

    p_repl = sub.add_parser("repl", help="start interactive REPL")
    p_repl.set_defaults(func=cmd_repl)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
