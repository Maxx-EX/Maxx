#!/usr/bin/env bash
# Maxx Language Installer
# Usage: git clone https://github.com/Maxx-EX/Maxx.git && cd Maxx && bash install.sh

set -e

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${BLUE}[*]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo "=========================================="
echo "  Maxx Language Installer"
echo "=========================================="
echo ""

# ---- 1. 检测环境 ----
info "检测运行环境..."

# 检测 Python
if command -v python3 &> /dev/null; then
    PY=python3
    success "找到 Python: $(python3 --version 2>&1)"
elif command -v python &> /dev/null; then
    PY=python
    success "找到 Python: $(python --version 2>&1)"
else
    warn "未找到 Python，尝试安装..."
    if command -v pkg &> /dev/null; then
        pkg install -y python
    elif command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3 python3-pip
    else
        error "请先安装 Python 3"
    fi
    PY=python3
fi

# 检测 gcc
if command -v cc &> /dev/null; then
    CC=cc
    success "找到 C 编译器: $(cc --version | head -1)"
elif command -v gcc &> /dev/null; then
    CC=gcc
    success "找到 C 编译器: $(gcc --version | head -1)"
else
    warn "未找到 C 编译器，尝试安装..."
    if command -v pkg &> /dev/null; then
        pkg install -y clang
    elif command -v apt &> /dev/null; then
        sudo apt install -y build-essential
    fi
fi

# ---- 2. 确定安装路径 ----
info "配置安装路径..."

# 检测是否在 Termux
if [ -d "/data/data/com.termux" ]; then
    PREFIX_DIR="/data/data/com.termux/files/usr"
    info "检测到 Termux 环境"
else
    PREFIX_DIR="$HOME/.local"
    info "检测到 Linux 环境，安装到 ~/.local"
fi

BIN_DIR="$PREFIX_DIR/bin"
mkdir -p "$BIN_DIR"

# 确定项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
info "项目目录: $PROJECT_DIR"

# ---- 3. 安装编译器 ----
info "安装 Maxx 编译器..."

# 创建 maxx 命令
cat > "$BIN_DIR/maxx" << EOF
#!/usr/bin/env bash
# Maxx 命令行工具
MAXX_HOME="$PROJECT_DIR"
MAXXC="\$MAXX_HOME/compiler/maxxc.py"

if [ ! -f "\$MAXXC" ]; then
    echo "错误: 找不到 Maxx 编译器 (\$MAXXC)"
    echo "请重新运行 install.sh"
    exit 1
fi

case "\${1:-}" in
    "")
        # 无参数: 进 REPL
        $PY \$MAXXC repl
        ;;
    "repl")
        $PY \$MAXXC repl
        ;;
    "run")
        shift
        $PY \$MAXXC run "\$@"
        ;;
    "build")
        shift
        $PY \$MAXXC build "\$@"
        ;;
    "tokenize")
        shift
        $PY \$MAXXC tokenize "\$@"
        ;;
    "parse")
        shift
        $PY \$MAXXC parse "\$@"
        ;;
    "codegen")
        shift
        $PY \$MAXXC codegen "\$@"
        ;;
    "version"|"--version"|"-v")
        echo "Maxx v1.0.0 (bootstrap)"
        echo "编译器: Python Level-1"
        echo "仓库: https://github.com/Maxx-EX/Maxx"
        ;;
    "help"|"--help"|"-h")
        echo "Maxx 命令行工具"
        echo ""
        echo "用法:"
        echo "  maxx              进入 REPL"
        echo "  maxx run <file>   运行 .max 文件"
        echo "  maxx build <file> 编译 .max 文件"
        echo "  maxx version      显示版本"
        echo "  maxx help         显示帮助"
        ;;
    *)
        $PY \$MAXXC "\$@"
        ;;
esac
EOF

chmod +x "$BIN_DIR/maxx"
success "maxx 命令已安装到: $BIN_DIR/maxx"

# ---- 4. 配置 PATH ----
info "配置 PATH..."

SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "MAXX_HOME" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Maxx Language" >> "$SHELL_RC"
        echo "export MAXX_HOME=\"$PROJECT_DIR\"" >> "$SHELL_RC"
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
        success "已添加到 $SHELL_RC"
    else
        info "PATH 已配置，跳过"
    fi
fi

# ---- 5. 验证安装 ----
info "验证安装..."

export PATH="$BIN_DIR:$PATH"

if command -v maxx &> /dev/null; then
    success "maxx 命令可用: $(which maxx)"
else
    warn "maxx 命令不在 PATH，请运行: source $SHELL_RC"
fi

# 测试编译
TEST_FILE="/tmp/maxx_hello.max"
cat > "$TEST_FILE" << 'EOF'
@ main() -> int:
    io.println("Hello, Maxx!")
    ret 0
EOF

info "运行测试程序..."
if $PY "$PROJECT_DIR/compiler/maxxc.py" run "$TEST_FILE" 2>&1 | grep -q "Hello"; then
    success "编译器工作正常!"
else
    warn "测试编译失败，请检查编译器是否完整"
fi

rm -f "$TEST_FILE"

# ---- 6. 完成 ----
echo ""
echo "=========================================="
success "Maxx 安装完成!"
echo "=========================================="
echo ""
echo "快速开始:"
echo "  1. source $SHELL_RC   (刷新环境变量)"
echo "  2. maxx               (进入 REPL)"
echo "  3. maxx run hello.max (运行文件)"
echo ""
echo "彩蛋: 在 REPL 里输入 hi！Maxx"
echo ""
