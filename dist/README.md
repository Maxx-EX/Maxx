# Maxx 分发包

> Maxx 是一门静态强类型、缩进分块、无空值、内置代数数据类型的原创高级语言。
> 一套语法，编译到所有平台。

## 支持平台

| 平台 | 状态 | 下载 |
|------|------|------|
| Linux x86_64 | ✅ | [下载](#linux) |
| Linux ARM64 | ✅ | [下载](#linux) |
| Android (APK) | ✅ | [下载](#android) |
| Termux | ✅ | [下载](#termux) |
| Windows | ⏳ 规划中 | - |
| macOS | ⏳ 规划中 | - |
| Web (WASM) | ⏳ 规划中 | - |

## 快速安装

### Linux
```bash
curl -sSL https://raw.githubusercontent.com/Maxx-EX/Maxx/main/maxx-install | bash
```

### Termux
```bash
curl -sSL https://raw.githubusercontent.com/Maxx-EX/Maxx/main/maxx-install | bash
```

### 从源码编译
```bash
git clone https://github.com/Maxx-EX/Maxx.git
cd Maxx
bash install.sh
```

## 快速上手

```bash
# 进入 REPL
maxx

# 运行程序
maxx run hello.max

# 编译
maxx build hello.max
```

彩蛋：在 REPL 里输入 `hi！Maxx`（全角感叹号）

## 许可证

MIT License — 可自由商用、修改、分发。

## 常见问题

**Q: Maxx 是 Python 的 fork 吗？**
A: 不是。Maxx 是从零设计的原创语言，语法和语义都是全新的。

**Q: Maxx 支持 Windows 吗？**
A: 规划中。当前支持 Linux、Android、Termux。

**Q: 怎么贡献代码？**
A: Fork 仓库，提交 PR。
