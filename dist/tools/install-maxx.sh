#!/data/data/com.termux/files/usr/bin/bash
# Maxx Termux Installer
# Usage: bash install-maxx.sh
set -e

echo "========================================="
echo "  Maxx Language Installer for Termux"
echo "========================================="
echo ""

# Step 1: Install dependencies
echo "[1/5] Installing dependencies (python, clang)..."
pkg update -y && pkg install -y python clang 2>/dev/null || {
    echo "Warning: pkg install failed, trying pip..."
    pip install --upgrade pip
}
echo ""

# Step 2: Find Maxx source
echo "[2/5] Locating Maxx compiler source..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAXX_SRC="$SCRIPT_DIR/../compiler"

if [ ! -f "$MAXX_SRC/maxxc.py" ]; then
    # Try to clone from GitHub if not found
    echo "Maxx source not found locally, cloning from GitHub..."
    git clone https://github.com/Maxx-EX/Maxx.git "$HOME/maxx" 2>/dev/null || {
        echo "ERROR: Cannot find maxxc.py and git clone failed."
        echo "Please run this script from within the Maxx repo."
        exit 1
    }
    MAXX_SRC="$HOME/maxx/compiler"
fi

echo "Found Maxx compiler at: $MAXX_SRC"
echo ""

# Step 3: Install maxxc to PATH
echo "[3/5] Installing maxxc to ~/.local/bin..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/maxxc" << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
exec python3 "$(dirname "$(readlink -f "$0")")/maxxc_runner.py" "$@"
EOF

# Copy compiler files
cp -r "$MAXX_SRC" "$HOME/.local/share/maxx-compiler"
chmod +x "$HOME/.local/bin/maxxc"

# Create runner
cat > "$HOME/.local/bin/maxxc_runner.py" << 'EOF'
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.local/share/maxx-compiler"))
from maxxc import main
sys.exit(main())
EOF

chmod +x "$HOME/.local/bin/maxxc_runner.py"
echo "maxxc installed to ~/.local/bin/maxxc"
echo ""

# Step 4: Configure shell
echo "[4/5] Configuring shell..."
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Add PATH if not already there
if ! grep -q "maxx-compiler" "$SHELL_RC" 2>/dev/null; then
    echo '' >> "$SHELL_RC"
    echo '# Maxx language' >> "$SHELL_RC"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    echo 'export MAXX_HOME="$HOME/.local/share/maxx-compiler"' >> "$SHELL_RC"
    echo 'Added Maxx config to '$SHELL_RC
fi

# Add shell completion
COMPL_DIR="$HOME/.local/share/maxx-compiler"
cat > "$COMPL_DIR/maxxc_completion.bash" << 'EOF'
# Maxx bash completion
_maxxc() {
    local cur prev commands
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="tokenize parse ir codegen build pack archive run repl help"

    if [ "$COMP_CWORD" -eq 1 ]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return
    fi

    case "$prev" in
        *.max|*.mxx|*.smx)
            COMPREPLY=( $(compgen -f -- "$cur") )
            ;;
    esac
}
complete -F _maxxc maxxc
EOF

if ! grep -q "maxxc_completion" "$SHELL_RC" 2>/dev/null; then
    echo 'source "$HOME/.local/share/maxx-compiler/maxxc_completion.bash" 2>/dev/null' >> "$SHELL_RC"
fi
echo "Shell completion configured"
echo ""

# Step 5: Verify
echo "[5/5] Verifying installation..."
export PATH="$HOME/.local/bin:$PATH"
export MAXX_HOME="$HOME/.local/share/maxx-compiler"

if command -v maxxc &>/dev/null; then
    echo "✓ maxxc found in PATH"
else
    echo "✗ maxxc not found in PATH (restart shell)"
fi

if python3 -c "import sys; sys.path.insert(0, '$MAXX_SRC'); import maxxc" 2>/dev/null; then
    echo "✓ maxxc module imports OK"
else
    echo "✗ maxxc module import failed"
fi

echo ""
echo "========================================="
echo "  Maxx installed successfully!"
echo "========================================="
echo ""
echo "Quick start:"
echo "  maxxc run hello.max    # Run a .max file"
echo "  maxxc repl             # Start interactive REPL"
echo "  maxxc build foo.max    # Compile to .mxx"
echo ""
echo "Restart your shell or run: source ~/.bashrc"
echo ""
