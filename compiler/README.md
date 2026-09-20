# Maxx Bootstrap Compiler (Level 1)

> **THIS IS A TEMPORARY BOOTSTRAP TOOL.**
>
> Per the Maxx ANCHOR spec (§8), this compiler is written in Python solely to
> bootstrap the Maxx language. The production compiler (Level 2/3) will be
> rewritten in Maxx itself.

## What is Maxx?

**Maxx** = Maximum simplicity × Maximum efficiency.

A statically-typed, indentation-blocked, null-free, ADT-native, AOT-compiled
high-level language that runs on both desktop and mobile.

## Four-Layer File Format (v1.0)

| Layer | Suffix | Meaning | Analogy |
|-------|--------|---------|---------|
| 1 | `.max` | Source file (human-written) | `.py` / `.go` / `.rs` |
| 2 | `.mxx` | Compiled shared library (native) | `.so` / `.dll` |
| 3 | `.smx` | Distribution package (whl-style zip) | `.whl` / `.jar` |
| 4 | `.zip` | Project archive (full release) | GitHub release tarball |

### Design principle: `.max` is both source and module

A `.max` file is a module. When you `~ othermod::foo`, the compiler locates
`othermod.max`, compiles it (caching to `.mxxcache/`), and links the symbols.
There is no intermediate `.o` / `.a` layer — `.mxx` IS Maxx's native library
format, self-contained with type metadata and GC bindings.

## Quick Start

```bash
# Run a .max program directly (codegen -> cc -> execute)
python3 maxxc.py run tests/hello.max

# Compile to .mxx shared library
python3 maxxc.py build tests/hello.max -o hello.mxx

# Pack into .smx distribution package
python3 maxxc.py pack hello.mxx -o hello.smx --src tests/

# Archive a project directory
python3 maxxc.py archive myproject/ -o myproject.zip

# Start interactive REPL
python3 maxxc.py repl
```

## Commands

| Command | Description |
|---------|-------------|
| `tokenize <file.max>` | Lex and print tokens |
| `parse <file.max>` | Parse and print AST |
| `ir <file.max>` | Dump normalized IR |
| `codegen <file.max> [-o out.c]` | Emit C source |
| `build <file.max> [-o output.mxx] [--target T]` | Compile to .mxx shared library |
| `pack <lib.mxx> [-o pkg.smx] [--src dir/]` | Pack into .smx distribution |
| `archive <project_dir> [-o project.zip]` | Archive project to .zip |
| `run <file.max>` | Codegen, compile, and execute |
| `repl` | Start interactive REPL |

### Build Targets

| Target | Description |
|--------|-------------|
| `x86_64-linux` | Native Linux x86_64 (default) |
| `arm64-android` | Android ARM64 (requires ANDROID_NDK env var) |
| `arm64-ios` | iOS ARM64 (planned) |
| `wasm32` | WebAssembly (planned) |

For `arm64-android`, set `ANDROID_NDK` or `NDK` environment variable:
```bash
export ANDROID_NDK=~/Android/Sdk/ndk/26.1.10909125
python3 maxxc.py build app.max --target arm64-android
```

## REPL

```
$ python3 maxxc.py repl
Maxx REPL (Level 1 bootstrap). Type :help for commands, :quit to exit.
maxx> io.println("hello from repl")
hello from repl
maxx> io.println(str(sqrt(16.0)))
4
maxx> :help
Maxx REPL commands:
  :help     show this help
  :reset    reset REPL state
  :quit     exit the REPL
maxx> :quit
```

## Architecture

```
maxxc.py          Main CLI entry point (REPL, build, pack, archive, run)
lexer.py          Lexer (tokenizer + offside rule / INDENT-DEDENT)
parser.py         Recursive-descent parser (Pratt expression parsing)
mxast.py          AST node definitions
checker.py        Type checker (basic, permissive bootstrap)
ir.py             Intermediate representation (textual dump)
codegen_c.py      IR -> C code generator (libc/libm mappings)
pack.py           .smx / .zip packager
runtime_minimal.c Minimal C runtime (strings, channels, IO, time, files)
runtime_minimal.h Runtime header
tests/            .max test files (5/5 passing)
examples/         Example programs (hello, math_demo, collections)
dist/maxxc        PyInstaller standalone binary (~14 MB)
```

## Standard Library (bootstrap subset)

### Math (libm)
`sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`,
`log`, `log2`, `log10`, `exp`, `pow`, `floor`, `ceil`, `round`,
`fabs`, `abs`, `min`, `max`

### IO
`io.println(...)`, `io.print(...)`, `read_line()`, `read_file(path)`,
`write_file(path, content)`

### Time
`now()`, `unix_time()`, `sleep(secs)`

### Conversions
`int()`, `i64()`, `f64()`, `f32()`, `str()`, `bool()`

## Test Files

| File | Features tested |
|------|----------------|
| `tests/hello.max` | Hello world, `io.println` |
| `tests/struct.max` | Structs, methods, `sqrt`, `^` power |
| `tests/enum_match.max` | ADT enums, `match`, tagged unions |
| `tests/loops.max` | `for` ranges, `while`, `if/elif/else`, `var` |
| `tests/option_result.max` | `Result<T,E>`, `ok()`, `err()`, field access |

Run all tests:
```bash
bash tests/run_tests.sh
```

## Examples

| File | Features demonstrated |
|------|----------------------|
| `examples/hello.max` | Basic hello world |
| `examples/math_demo.max` | Math library (sqrt, sin, pow, floor, ceil, abs) |
| `examples/collections.max` | Struct methods, loops, counters |

## Language Features (supported subset)

- ✅ Structs with methods (`# Point:` + `@ Point::dist(...)`)
- ✅ ADT enums with `match` (tagged unions)
- ✅ `if / elif / else` control flow
- ✅ `for i in 1..=n:` range loops
- ✅ `while` loops, `var` mutable bindings
- ✅ `Result<T, E>` with `ok()`, `err()` constructors
- ✅ String concatenation with `+`, `str()` conversion
- ✅ Math library (libm mappings)
- ✅ File IO (read_file, write_file)
- ✅ Time functions (now, sleep)
- ✅ Channels (stub: single-threaded ring buffer)
- ✅ REPL interactive mode
- ✅ Cross-compile target selection
- ⬜ Generics (parsed, not fully instantiated)
- ⬜ Full `?` try-propagation across Result types
- ⬜ Real GC, scheduler, JIT/AOT native codegen

## Standalone Binary

A PyInstaller-packaged standalone binary is available at `dist/maxxc` (~14 MB).
It includes all compiler modules and the runtime C files, and can be run
directly on any Linux x86_64 system with gcc installed.

```bash
./dist/maxxc run tests/hello.max
```

## Bootstrapping Roadmap

| Level | Description | Status |
|-------|-------------|--------|
| 0 | Hand-written machine-code bootstrap (doc only) | — |
| 1 | Python bootstrap compiler (this) | ✅ Complete |
| 2 | Self-hosted compiler (Lexer/Parser in Maxx) | Planned |
| 3 | Optimized native backend (SSA, regalloc) | Planned |
