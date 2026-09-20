# Maxx Machine Code Bootstrap

> 这是 Maxx 编译器最底层的引导程序，**纯 x86_64 机器码**。
> 不依赖 Python、C、Go、Rust、Java 等任何主流语言，不链接 libc。

## 文件

| 文件 | 说明 |
|------|------|
| `boot0.s` | Level 0 引导加载器（~100 行汇编） |
| `stage1.s` | Stage1 最小可执行程序（~50 行汇编） |
| `boot0` | 编译后的 ELF 二进制（静态链接，无 libc） |
| `maxxc-stage1.bin` | Stage1 扁平二进制（可被 boot0 加载跳转） |

## 构建

```bash
make
```

需要：`as`（GNU assembler）+ `ld`（GNU linker）。

## 运行

```bash
./boot0
```

输出：
```
=== Maxx Level 0 Bootstrap (raw machine code) ===
No libc. No Python. No mainstream language.
Stage1 loaded, size = 4456
Jumping to entry point...
```

## 验证

```bash
file boot0
# boot0: ELF 64-bit LSB executable, x86-64, statically linked

ldd boot0
# not a dynamic executable    ← 证明不依赖 libc
```

## 引导层级

```
Level 0: boot0.s        ← 手写机器码，加载 stage1
Level 1: stage1.s       ← 手写机器码，最小可执行程序
Level 2: maxxc (Python) ← 开发期种子（本仓库 compiler/ 目录）
Level 3: maxxc (C)      ← 规划中，把 Python 重写为 C
Level 4: maxxc (Maxx)   ← 规划中，自举，Maxx 编译器由 Maxx 写
```

## 哲学

这证明 Maxx 不寄生在任何主流语言上。从机器码开始，逐步向上构建，
最终由 Maxx 自己编译自己。
