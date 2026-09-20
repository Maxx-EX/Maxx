"""
Maxx Language Bootstrap Compiler - Level 1 (Python bootstrap).

THIS IS A TEMPORARY BOOTSTRAP TOOL (Level 1). Per ANCHOR §8, the final
production compiler (Level 2/3) will be rewritten in Maxx itself. This Python
implementation exists only to bootstrap the language: it parses the Maxx subset
described in ANCHOR §3, lowers it to an IR, and emits C code that the host C
compiler (gcc/clang/cc) builds.

Source files use the suffix `.mxx`. The compiled artifact (a zip container)
uses the suffix `.smx`.
"""

__version__ = "0.1.0-bootstrap"
