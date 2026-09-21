# Maxx

> **Maximum simplicity × Maximum efficiency** — 一门静态强类型、缩进分块、无空值、内置代数数据类型、可 AOT 编译为原生码、手机端与桌面端同源的原创高级语言。

## 安装

```bash
git clone https://github.com/Maxx-EX/Maxx.git
cd Maxx
bash install.sh
```

安装完成后：
- `maxx` — 直接进入 REPL
- `maxx run hello.max` — 运行 .max 文件
- `maxx build hello.max` — 编译 .max 文件
- `maxx version` — 查看版本

> Termux 用户：安装脚本自动检测环境并配置 PATH。
> Linux 用户：安装到 ~/.local/bin/，自动添加到 PATH。

---

Maxx 不是任何现有语言的 fork：它取 Python 的易读、Go 的简洁并发、Rust 的类型安全（但去掉借用检查）、ML 的 ADT 与模式匹配，合成一门**为了"写起来舒服、跑起来快、跨端一致"**而生的新语言。

## 三个"绝不"

1. **绝不有 `null`/`nil`** — 可空即 `?T`，编译期强制解包。
2. **绝不隐式数字转换** — `int` 与 `f64` 必须显式 `int()` / `f64()`。
3. **绝不宏** — 元编程走编译期求值（`comptime`），不做文本替换。

## 一分钟看 Maxx

```maxx
~ std.io

@ fib(n: int) -> int:
    if n < 2: ret n
    ret fib(n - 1) + fib(n - 2)

@ main() -> int:
    for i in 0..10:
        io.println(f"fib({i}) = {fib(i)}")
    ret 0
```

- `@` 声明函数，`#` 声明类型，`~` 导入，`ret` 返回，`?T` 可空，`Result<T,E>` 错误模型，`match` 模式匹配，`task`/`chan` 并发。

## 目录结构

```
maxx/
├── ANCHOR.md            # 语言基线规范（v1.0 终版）
├── docs/                # 完整语言规范 SPEC.md（3000+ API）
├── std/                 # 标准库 stub（.max 源文件）
│   ├── io.max           #   终端 / 文件 IO
│   ├── math.max         #   数学常量与函数
│   ├── collections.max  #   Vec / Map / Set / Iter
│   ├── text.max         #   字符串方法 / StringBuilder
│   ├── time.max         #   Duration / Instant / sleep
│   ├── async.max        #   task / chan / WaitGroup / select
│   ├── random.max        #   xoshiro256** RNG
│   └── test.max         #   单元测试框架
├── examples/            # 10 个递进示例（.max 源文件）
│   ├── hello.max
│   ├── fibonacci.max
│   ├── struct_shape.max
│   ├── optional_result.max
│   ├── generics.max
│   ├── collections.max
│   ├── math_demo.max
│   ├── concurrency.max
│   ├── primes.max
│   └── cli_greeting.max
├── compiler/            # 引导编译器（Level 1，Python 实现）
└── tools/
    └── pack.py          # 打包工具：.max → .mxx → .smx；项目 → .zip 归档
```

编译链路示意（运行 `pack.py` 后产生）：

```
hello.max                # ① 源代码（人类可读）
   │  maxxc build
   ▼
hello.mxx                # ② 动态共享库（二进制，类比 .so/.dll）
   │  pack into whl
   ▼
hello.smx                # ③ 分发包（zip，类比 .whl）
├── manifest.json        #    format="smx@1"
├── lib/host/hello.mxx   #    预编译共享库
├── include/hello.max    #    公共接口头文件
├── src/hello.max        #    源文件（调试用）
└── docs/                 #    抽取的文档注释

maxx-0.1.0.zip           # ④ 项目归档（类比 GitHub Release tarball）
└── maxx/                #    整个项目目录（含 .max + .smx + README）
```

## 快速上手

```bash
# 1. 编译单个源文件：hello.max → hello.mxx → hello.smx
python3 tools/pack.py build examples/hello.max -o hello.smx

# 2. 编译整个标准库目录
python3 tools/pack.py build std -o std.smx

# 3. 发布为项目归档
python3 tools/pack.py release . -o maxx-0.1.0.zip
```

> 当前为 **Level 1 引导阶段**：编译器由 Python 写成（临时引导工具），把 Maxx 子集编译为 C 再用宿主 gcc/clang 编译运行。完整自举路线见 `docs/SPEC.md` §自举层级。

## 与现有语言的定位差异

| 维度 | Python | Go | Rust | Maxx |
|---|---|---|---|---|
| 类型 | 动态 | 静态弱推断 | 静态强 | **静态强 + 推断** |
| 空值 | `None` 随处 | `nil` 坑多 | `Option<T>` | **`?T` 内置，无 null** |
| 错误 | 异常栈展开 | `if err != nil` | `Result` + `?` | **`Result` + `?`，无异常** |
| ADT/模式匹配 | 无 | 无 | `enum` + `match` | **内置，一等公民** |
| 并发 | GIL 多线程 | goroutine/chan | async/await | **`task`/`chan` 内建** |
| 内存 | GC | GC（tracing） | 借用检查 | **引用计数 + 分代回收，无借用** |
| 分块 | 缩进 | 花括号 | 花括号 | **缩进（offside rule）** |
| 移动端 | 弱 | 弱 | 通过 NDK | **原生目标（Android .so / iOS .a）** |

## 四层文件格式（ANCHOR v1.0 终版）

| 层 | 后缀 | 角色 | 类比 |
|---|---|---|---|
| ① 源代码 | `.max` | 人类可读可编辑的 UTF-8 文本；模块即文件 | `.py` / `.go` / `.rs` |
| ② 动态共享库 | `.mxx` | 编译产物：机器码 + 导出/导入符号表 + 类型元数据 + GC 绑定；运行时 `dlopen` 等价加载 | `.so` / `.dll` / `.dylib` |
| ③ 分发包 | `.smx` | whl 式 zip：把 `.mxx` + `.max` 头接口 + manifest 打包分发 | `.whl` / `.jar` |
| ④ 项目归档 | `.zip` | 整个项目的最终发布（源码 + `.smx` 依赖 + README + examples/） | GitHub Release tarball |

**`.smx` 内部结构**（对齐 ANCHOR §6.3）：

```
mypkg-1.0.0.smx
├── manifest.json            # format="smx@1" + name/version/entry/targets/dependencies
├── lib/<target>/<name>.mxx  # 预编译共享库（二进制）
├── include/<pkg>/*.max      # 公共 .max 接口头文件
├── src/<pkg>/*.max          # 源文件（调试/重新编译用）
└── docs/                    # 抽取的文档注释
```

> 历史沿革：早期草案用过 `.mex`，v0.2 退役为 `.smx`，v0.3 明确三层职责，v0.4 提出"源即库"，v1.0 终版定为四层（`.max` 源 / `.mxx` 库 / `.smx` 包 / `.zip` 归档）。

## 链接

- 完整规范：[`docs/SPEC.md`](docs/SPEC.md)
- 语言基线：[`ANCHOR.md`](ANCHOR.md)
- 标准库：[`std/`](std/)
- 示例：[`examples/`](examples/)
- 编译器：[`compiler/`](compiler/)
