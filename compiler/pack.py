"""
Maxx .smx packager (Level 1 bootstrap).

The .smx file is a zip container (per ANCHOR §6) containing:
  - manifest.json   (version, target platform, entry symbol)
  - code/           (compiled object / native binary)
  - ast.ir          (serialized IR, for LSP / incremental builds)
  - docs/           (doc-comment extraction, optional)

For the bootstrap, we pack:
  - manifest.json
  - the generated C source
  - the compiled native binary (if available)
  - a text IR dump
"""

import json
import os
import zipfile
from typing import List, Optional


def build_mex(
    output_path: str,
    source_name: str,
    c_source: str,
    ir_text: str,
    binary_path: Optional[str] = None,
    target: str = "native-bootstrap",
) -> str:
    """Create a .smx (zip) package and return its path."""
    manifest = {
        "format": "maxx-mex",
        "version": "0.1.0",
        "language": "Maxx",
        "source": source_name,
        "target": target,
        "entry": "mx_main",
        "containers": [
            "manifest.json",
            "code/main.c",
            "ast.ir",
        ],
    }
    if binary_path and os.path.exists(binary_path):
        manifest["containers"].append("code/native/program")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("code/main.c", c_source)
        zf.writestr("ast.ir", ir_text)
        if binary_path and os.path.exists(binary_path):
            zf.write(binary_path, "code/native/program")

    return output_path
