#!/usr/bin/env python3
"""
Maxx pack — v1.0 四层文件格式打包工具。

四层：
    .max  = 源代码（人类可读）
    .mxx  = 编译后的动态共享库（类比 .so/.dll，二进制）
    .smx  = 分发包（whl 式 zip：lib/ + include/ + src/ + manifest.json + docs/）
    .zip  = 项目归档（最终发布整个项目）

用法：
    # 1) 把 foo.max 编译为 foo.mxx（Level 1 占位二进制），再打成 foo.smx
    python3 pack.py build foo.max -o foo.smx [--name NAME] [--version VER]
                            [--entry ENTRY] [--target TARGET] [--dep DEP ...]

    # 2) 把整个项目目录（含 mod.max）打包为 .smx
    python3 pack.py build mypkg/ -o mypkg-1.0.0.smx

    # 3) 项目归档
    python3 pack.py release <project_dir> -o project.zip

.smx 内部结构（对齐 ANCHOR v1.0 §6.3）：
    manifest.json          # 元数据（format="smx@1"）
    lib/<target>/<name>.mxx # 预编译共享库（二进制，类比 .so）
    include/<pkg>/*.max    # 公共接口头文件
    src/<pkg>/*.max        # 源文件（便于调试/重新编译）
    docs/                  # 抽取的文档注释
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


# Level 1 bootstrap：.mxx 还不是真正的机器码，这里写一个占位魔数头
MXX_MAGIC = b"MXX1"
MXX_PLACEHOLDER = b"""// Level 1 bootstrap placeholder shared library.
// Final .mxx will contain: machine code section, export/import symbol tables,
// type metadata (generics, vtables), GC binding tables.
"""


def collect_sources(src: Path) -> list[Path]:
    """返回要收录的 .max 源文件列表。"""
    files: list[Path] = []
    if src.is_file():
        files.append(src)
    elif src.is_dir():
        files.extend(sorted(src.rglob("*.max")))
    else:
        raise FileNotFoundError(src)
    return files


def detect_entry(src: Path, files: list[Path]) -> str:
    """确定入口：目录里找 mod.max；单文件用文件 stem。"""
    if src.is_dir():
        mod = src / "mod.max"
        if mod.exists():
            return "mod"
        main = src / "main.max"
        if main.exists():
            return "main"
    if src.is_file():
        return src.stem
    return files[0].stem if files else "main"


def build_manifest(name: str, version: str, entry: str,
                   target: str, deps: list[str]) -> dict:
    """ANCHOR v1.0 §6.3 manifest.json schema。"""
    dep_map: dict[str, str] = {}
    for d in deps:
        if "=" in d:
            k, v = d.split("=", 1)
            dep_map[k] = v
        else:
            dep_map[d] = "*"
    return {
        "format": "smx@1",
        "name": name,
        "version": version,
        "entry": entry,
        "targets": [target],
        "dependencies": dep_map,
        "authors": [],
        "license": "MIT",
    }


def compile_to_mxx(name: str, sources: list[Path], target: str) -> bytes:
    """Level 1 引导阶段：把 .max 源码"编译"为 .mxx 占位二进制。

    真实 Level 2+：这里会跑 maxxc 后端生成机器码 + 符号表 + 元数据。
    本阶段：写魔数头 + 源文件清单占位。
    """
    body = json.dumps({
        "name": name,
        "target": target,
        "sources": [s.name for s in sources],
    }, indent=2).encode("utf-8")
    return MXX_MAGIC + body + b"\n" + MXX_PLACEHOLDER


def cmd_build(args: argparse.Namespace) -> int:
    src = Path(args.src).resolve()
    out = Path(args.out).resolve()

    if not src.exists():
        print(f"error: src not found: {src}", file=sys.stderr)
        return 2

    files = collect_sources(src)
    if not files:
        print("error: no .max sources found", file=sys.stderr)
        return 2

    name = args.name or (src.stem if src.is_file() else src.name)
    entry = args.entry or detect_entry(src, files)
    manifest = build_manifest(name, args.version, entry, args.target, args.dep or [])

    # Level 1：先"编译"出 .mxx 共享库占位
    mxx_blob = compile_to_mxx(name, files, args.target)

    out.parent.mkdir(parents=True, exist_ok=True)
    base = src if src.is_dir() else src.parent

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        # 1) manifest.json
        z.writestr("manifest.json",
                   json.dumps(manifest, indent=2, ensure_ascii=False))

        # 2) lib/<target>/<name>.mxx — 预编译共享库（二进制）
        z.writestr(f"lib/{args.target}/{name}.mxx", mxx_blob)

        # 3) include/<pkg>/*.max — 公共接口头文件
        for f in files:
            rel = f.relative_to(base)
            z.write(f, arcname=str(Path("include") / rel))

        # 4) src/<pkg>/*.max — 源文件（调试用）
        for f in files:
            rel = f.relative_to(base)
            z.write(f, arcname=str(Path("src") / rel))

        # 5) docs/
        z.writestr("docs/.gitkeep", b"")

    size = out.stat().st_size
    print(f"ok: built {out} ({size} bytes, "
          f"{len(files)} .max sources, {args.target}/{name}.mxx, entry={entry})")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    out = Path(args.out).resolve()

    if not project.is_dir():
        print(f"error: project dir not found: {project}", file=sys.stderr)
        return 2

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        # 1) 项目内 .smx 产物（若存在）
        for smx in project.rglob("*.smx"):
            z.write(smx, arcname=smx.relative_to(project.parent))
        # 2) README
        for readme in ("README.md", "README", "readme.md"):
            p = project / readme
            if p.exists():
                z.write(p, arcname=Path(project.name) / readme)
                break
        # 3) 所有 .max 源文件
        for f in sorted(project.rglob("*.max")):
            z.write(f, arcname=Path(project.name) / f.relative_to(project))

    size = out.stat().st_size
    print(f"ok: released {out} ({size} bytes)")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="maxx-pack",
        description="Pack Maxx projects: .max -> .mxx (shared lib) -> .smx (whl), then .zip archive",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="compile .max -> .mxx, then pack into .smx")
    b.add_argument("src", help="source .max file or project directory")
    b.add_argument("-o", "--out", required=True, help="output .smx path")
    b.add_argument("--name", default=None)
    b.add_argument("--version", default="0.1.0")
    b.add_argument("--entry", default=None, help="entry symbol (default: mod or <file>)")
    b.add_argument("--target", default="host",
                   help="host|x86_64-linux|arm64-android|arm64-ios|wasm32")
    b.add_argument("--dep", action="append", default=[])
    b.set_defaults(func=cmd_build)

    r = sub.add_parser("release", help="release project as distributable .zip")
    r.add_argument("project", help="project directory")
    r.add_argument("-o", "--out", required=True, help="output .zip path")
    r.set_defaults(func=cmd_release)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
