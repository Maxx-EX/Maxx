#!/data/data/com.termux/files/usr/bin/bash
# Maxx Language Installer for Termux
# Usage: curl -sSL https://raw.githubusercontent.com/Maxx-EX/Maxx/main/install.sh | bash

set -e

echo "=========================================="
echo "  Maxx Language Installer (Termux)"
echo "=========================================="

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}[*]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }

# 检查是否在 Termux
if [ ! -d "/data/data/com.termux" ]; then
    info "非 Termux 环境，继续安装到 Linux..."
fi

# 安装依赖
info "安装依赖: python, clang, git..."
pkg install -y python clang git 2>/dev/null || apt install -y python3 clang git 2>/dev/null || true

# 创建安装目录
INSTALL_DIR="$HOME/.maxx"
info "创建安装目录: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR/compiler"

# 克隆仓库
info "下载 Maxx 编译器..."
if [ -d "$INSTALL_DIR/Maxx" ]; then
    cd "$INSTALL_DIR/Maxx"
    git pull origin main 2>/dev/null || true
else
    git clone --depth 1 https://github.com/Maxx-EX/Maxx.git "$INSTALL_DIR/Maxx"
fi

# 复制编译器
info "配置编译器..."
cp -r "$INSTALL_DIR/Maxx/compiler" "$INSTALL_DIR/"

# 创建 maxxc 命令
MAXXC_BIN="$PREFIX/bin/maxxc"
cat > "$MAXXC_BIN" << EOF
#!/data/data/com.termux/files/usr/bin/bash
python3 "$INSTALL_DIR/compiler/maxxc.py" "\$@"
EOF
chmod +x "$MAXXC_BIN"

# 配置 shell 补全
info "配置 PATH 和补全..."
if ! grep -q "MAXX_HOME" "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" << EOF

# Maxx Language
export MAXX_HOME="$INSTALL_DIR"
export PATH="\$MAXX_HOME/compiler:\$PATH"
alias maxx="maxxc run"
EOF
fi

# 验证安装
info "验证安装..."
if command -v maxxc &> /dev/null; then
    success "Maxx 编译器安装成功!"
else
    echo "请重新加载 shell: source ~/.bashrc"
fi

echo ""
echo "=========================================="
success "安装完成!"
echo "=========================================="
echo ""
echo "快速开始:"
echo "  1. source ~/.bashrc"
echo "  2. maxxc repl"
echo "  3. maxxc run hello.max"
echo ""
echo "彩蛋: 在 REPL 里输入 hi！Maxx"
echo ""
