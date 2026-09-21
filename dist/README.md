# Maxx 分发包

> 各平台预编译二进制和安装包下载。

## 快速安装

### Linux x86_64
```bash
curl -sSL https://raw.githubusercontent.com/Maxx-EX/Maxx/main/maxx-install | bash
```

### Termux (Android)
```bash
curl -sSL https://raw.githubusercontent.com/Maxx-EX/Maxx/main/maxx-install | bash
```

### 从源码编译
```bash
git clone https://github.com/Maxx-EX/Maxx.git
cd Maxx
bash install.sh
```

---

## 各平台包

### Linux
| 文件 | 说明 | 状态 |
|------|------|------|
| `linux/maxx-v1.0-linux-x86_64.tar.gz` | x86_64 二进制 | ⏳ 规划中 |
| `linux/maxx-v1.0-linux-arm64.tar.gz` | ARM64 二进制 | ⏳ 规划中 |

### Android
| 文件 | 说明 | 状态 |
|------|------|------|
| `android/maxx-android-app-v10.apk` | IDE APK | ✅ 已发布 |
| `android/maxx-v1.0-android-arm64.tar.gz` | CLI 二进制 | ⏳ 规划中 |

### Termux
| 文件 | 说明 | 状态 |
|------|------|------|
| `termux/maxx-v1.0-termux.deb` | Termux 包 | ⏳ 规划中 |

### Windows
| 文件 | 说明 | 状态 |
|------|------|------|
| `windows/maxx-v1.0-win64.exe` | Windows 安装包 | ⏳ 规划中 |

### macOS
| 文件 | 说明 | 状态 |
|------|------|------|
| `macos/maxx-v1.0-macos-arm64.pkg` | macOS ARM 安装包 | ⏳ 规划中 |

### Web
| 文件 | 说明 | 状态 |
|------|------|------|
| `web/maxx-v1.0-wasm.zip` | WASM 运行时 | ⏳ 规划中 |

---

## 版本历史

### v1.0 (当前)
- Level 1 Python 引导编译器
- 59 个测试通过
- 支持：变量、函数、if/for/while、结构体、枚举、match、泛型、lambda、f-string
- 平台：Linux x86_64、Android

---

## 验证安装

安装完成后运行：
```bash
maxx version
maxx repl
```

彩蛋：在 REPL 里输入 `hi！Maxx`（全角感叹号）
