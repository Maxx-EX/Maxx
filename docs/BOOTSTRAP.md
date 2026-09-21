# Maxx 自举路线图（Bootstrapping Roadmap）

> **最高优先级声明**：Maxx 编译器**不使用任何主流编程语言编写**。
> 最终交付的 `maxxc` 是一个**纯原生二进制文件**，从机器码层面构建，
> 不依赖 Python/C/Go/Rust/Java 等任何主流语言的运行时。
>
> 当前仓库中的 Python 代码仅为**开发期验证种子**（Development Seed），
> 用于在语言设计阶段快速验证语法和语义，**不是最终交付物**。
> 正式版 `maxxc` 通过本文档描述的 Level 0→3 自举链条产出。
>
> 与 `SPEC.md` 配套阅读。版本：v1.6。

---

## 0. 当前状态说明（重要）

| 层级 | 名称 | 实现语言 | 实际状态 |
|---|---|---|---|
| **L0** | 机器码引导 | 手写 x86_64 汇编 | **演示性实现**（`bootstrap-machine/`），无宿主链，不承担编译器职责 |
| **L1a** | 开发期种子引导 | Python | **当前实际运行的编译器**（`compiler/`） |
| **L1b** | 生产引导编译器 | C | 规划中 |
| **L2** | Maxx 自举编译器 | Maxx | **进行中**：词法分析器已写出（`selfhost/lexer.max`） |
| **L3** | 优化版自举编译器 | Maxx | 规划中 |

> **注意**：`bootstrap-machine/` 目录下的汇编实现是**无宿主链演示**，
> 证明"可以从机器码开始"，但它目前**不承担编译器职责**。
> 现在实际跑 `.max` 代码的是 **Python 版 `maxxc`**（L1a，`compiler/`）。
> 不要误以为汇编版已经在工作。

---

## 0. 为什么需要自举？

一门语言如果不能用自己写自己，它就永远是"寄生"在宿主语言上的玩具。Maxx 的目标是：**最终的 `maxxc` 编译器，是用 Maxx 写的**。

但"从零开始写一个能编译自己的编译器"在工程上不可能一步到位。我们采用**分层引导**（bootstrapping）策略：先用宿主语言写一个最小引导编译器，再用 Maxx 自身逐步重写，最终替换掉宿主实现。

这是所有成熟语言的标准做法：C 编译器最初是用 PDP-7 汇编写的，再用 C 重写；Rust 最初是用 OCaml 写的，再用 Rust 重写；Go 最初是用 C 写的，再用 Go 重写。Maxx 走同一条路。

---

## 1. 五层引导模型

| 层级 | 名称 | 实现语言 | 目标 | 状态 |
|---|---|---|---|---|
| Level 0 | 机器码引导 | 手写 x86_64 机器码（NASM 语法，~200 字节） | 把 Level 1b 的 C 编译器加载到内存并跳过去 | 仅文档描述 |
| Level 1a | 开发期种子引导 | Python | 快速验证语言设计，开发期使用 | **本次交付** |
| Level 1b | 生产引导编译器 | C | 把 Level 1a 的 Python 实现重写为 C，预编译为 ELF 二进制 | 规划中 |
| Level 2 | Maxx 自举编译器 | Maxx | 用 Maxx 重写 `maxxc` 前端（Lexer/Parser），能编译自身 | 规划中 |
| Level 3 | 优化版自举编译器 | Maxx | 加上 SSA、寄存器分配、优化后端，替换掉 C 引导 | 规划中 |

### 1.1 关键承诺：最终 `maxxc` 不依赖 libpython

> **这是本路线图最重要的一条承诺。**

当前交付的 Python 版 `maxxc-bootstrap` 是**开发期种子**——它需要 Python 3 解释器才能跑。但最终交付给用户的 `maxxc` 是一个**预编译的 ELF 二进制文件**：

```bash
$ file maxxc
maxxc: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked
$ ldd maxxc
    linux-vdso.so.1 (0x00007ffff7fc7000)
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007ffff7dfc000)
    /lib64/ld-linux-x86-64.so.2 (0x00007ffff7fc9000)
    # 注意：没有 libpython.so！没有 libpython3.x.so.1.0！
```

用户不需要安装 Python，不需要 `pip install`，不需要任何运行时。`maxxc` 就是一个静态链接了 libc 的原生二进制，扔到任何 Linux x86_64 机器上就能跑。

---

## 2. Level 0：机器码引导（~200 字节 NASM 伪机器码）

### 2.1 目标

在一台裸机上，不依赖任何现有语言或编译器，手写一段约 200 字节的 x86_64 机器码引导程序。它只做一件事：**把 Level 1b 的 C 编译器二进制加载到内存，并跳转过去执行**。

### 2.2 为什么不实际交付？

- 在现代操作系统上，你不可能"从零开始"——操作系统本身就是 C 写的，你跑在它上面。
- Level 0 的实际价值是**哲学上的**：它证明 Maxx 不依赖任何特定宿主语言，理论上可以在任何能跑机器码的环境上自举。
- 工程上，我们直接在 Linux 上用 Python 写 Level 1a（开发期），再用 C 重写为 Level 1b（生产），跳过 Level 0 的实际实现。

### 2.3 Level 0 的 NASM 伪机器码示例

以下是一段概念性的 x86_64 Linux NASM 汇编（约 200 字节，仅用于说明引导思路，不是真实可执行文件）：

```nasm
; ============================================================
; maxx_boot.nasm — Maxx Level 0 引导程序（概念性）
; 功能：打开 Level 1b 的 C 编译器二进制，mmap 到内存，跳过去执行
; 编译：nasm -f elf64 maxx_boot.nasm -o maxx_boot.o
; 链接：ld -o maxx_boot maxx_boot.o
; ============================================================

global _start

section .text
_start:
    ; ---- 1. 打开 Level 1b 的编译器二进制 ----
    ; int fd = open("/boot/maxxc_c.bin", O_RDONLY, 0)
    mov     rax, 2              ; syscall: open
    mov     rdi, boot_path      ; 文件名指针
    mov     rsi, 0              ; O_RDONLY
    mov     rdx, 0              ; mode (ignored)
    syscall
    test    rax, rax
    js      _panic              ; 打开失败，panic
    mov     r8, rax             ; 保存 fd 到 r8

    ; ---- 2. fstat 获取文件大小 ----
    ; struct stat st; fstat(fd, &st)
    sub     rsp, 144            ; struct stat 的大小（x86_64 Linux）
    mov     rax, 5              ; syscall: fstat
    mov     rdi, r8             ; fd
    mov     rsi, rsp            ; &st
    syscall
    test    rax, rax
    js      _panic
    mov     r9, [rsp + 48]      ; st.st_size 偏移 48，文件大小存到 r9

    ; ---- 3. mmap 分配内存 ----
    ; void *mem = mmap(NULL, size, PROT_READ|PROT_WRITE|PROT_EXEC,
    ;                  MAP_PRIVATE, fd, 0)
    mov     rax, 9              ; syscall: mmap
    mov     rdi, 0              ; addr = NULL（让内核选）
    mov     rsi, r9             ; length = 文件大小
    mov     rdx, 7              ; prot = READ|WRITE|EXEC
    mov     r10, 2              ; flags = MAP_PRIVATE
    mov     r8, r8              ; fd
    mov     r9, 0               ; offset = 0
    syscall
    test    rax, rax
    js      _panic
    mov     r10, rax            ; mmap 返回的内存基址存到 r10

    ; ---- 4. read 读取整个文件到内存 ----
    ; read(fd, mem, size)
    mov     rax, 0              ; syscall: read
    mov     rdi, r8             ; fd
    mov     rsi, r10            ; buf
    mov     rdx, r9             ; count
    syscall
    test    rax, rax
    js      _panic

    ; ---- 5. 关闭文件 ----
    mov     rax, 3              ; syscall: close
    mov     rdi, r8
    syscall

    ; ---- 6. 跳过去执行 Level 1b 编译器 ----
    ; 把 argc/argv 寄存器设置好，然后 jmp r10
    mov     rdi, [rsp + 160]    ; argc（栈上的假参数）
    lea     rsi, [rsp + 168]    ; argv
    jmp     r10                 ; 跳！Level 1b 从这里开始跑

_panic:
    ; 写 "boot failed\n" 到 stderr，然后 exit(1)
    mov     rax, 1              ; syscall: write
    mov     rdi, 2              ; fd = stderr
    mov     rsi, msg_fail
    mov     rdx, msg_fail_len
    syscall
    mov     rax, 60             ; syscall: exit
    mov     rdi, 1              ; status = 1
    syscall

section .rodata
boot_path   db  "/boot/maxxc_c.bin", 0
msg_fail    db  "maxx boot failed\n"
msg_fail_len equ $ - msg_fail
```

### 2.4 这段引导程序做了什么？

1. `open("/boot/maxxc_c.bin", O_RDONLY)` 打开 Level 1b 的 C 编译器二进制。
2. `fstat` 获取文件大小。
3. `mmap` 分配一块**可读可写可执行**的内存页。
4. `read` 把 Level 1b 的整个二进制读进这块内存。
5. `close` 关闭文件。
6. `jmp r10` 跳过去——从这一刻起，CPU 开始执行 Level 1b 的代码。

这就是 Level 0 的全部。约 200 字节，6 个系统调用，把控制权交给 Level 1b。

### 2.5 Level 0 不是交付物

- 这段 NASM 代码只是**概念性**的，证明"理论上可以从零引导"。
- 实际工程中，我们直接用系统的 `gcc` 编译 Level 1b 的 C 代码，得到 `maxxc` 二进制。
- Level 0 的存在是为了回答"你怎么能说这门语言不是寄生在 Python 上的？"——答案是：Level 0 证明了它可以不依赖 Python，Level 1b 用 C 重写后，`ldd maxxc` 就看不到 libpython 了。

---

## 3. Level 1：引导编译器（开发期种子 + 生产重写）

### 3.1 Level 1a：Python 开发期种子（本次交付）

**明确标注：这是临时开发工具，不是最终产品。**

选择 Python 的原因：
- 开发速度快（比 C/Rust 快 5-10 倍），适合快速验证语言设计。
- 跨平台（Windows/macOS/Linux 都有 Python）。
- 有成熟的解析库（`rply`、`lark`）。
- 引导编译器只需要"能跑"，不需要"跑得快"。

**它的生命周期**：
- 现在：用来写标准库、写示例、验证语法。
- Level 1b 完成后：退役，不再维护。
- 最终用户：永远不会接触到这个 Python 版本。

### 3.2 Level 1b：C 生产引导编译器（规划中）

把 Level 1a 的 Python 实现**逐行重写为 C**：

| 模块 | Level 1a（Python） | Level 1b（C） |
|---|---|---|
| 词法分析器 | `lexer.py` | `src/lexer.c` |
| 语法分析器 | `parser.py` | `src/parser.c` |
| AST 定义 | `ast.py` | `include/ast.h` |
| 类型检查 | `typecheck.py` | `src/typecheck.c` |
| IR 定义 | `ir.py` | `include/ir.h` |
| 代码生成 | `codegen_c.py` | `src/codegen_c.c` |
| 运行时 | `runtime/*.c` | `runtime/*.c`（不变） |
| 标准库 | `stdlib/*.max` | `stdlib/*.max`（不变） |

**编译方式**：

```bash
# 用系统的 gcc 编译 Level 1b
gcc -O2 -o maxxc src/*.c runtime/*.c -lgc -lpthread

# 验证：ldd 不依赖 libpython
$ ldd maxxc
    linux-vdso.so.1
    libc.so.6
    libgc.so.1       # Boehm GC
    libpthread.so.0
    # 没有 libpython！
```

**Level 1b 完成后**：
- 开发期 Python 种子退役。
- 所有后续开发（Level 2/3）都用 Level 1b 的 C 版 `maxxc` 来做。
- 最终用户拿到的 `maxxc` 就是 Level 1b 编译出来的 ELF 二进制。

### 3.3 编译流程（Level 1b）

```
.max 源文件
   │
   ├─ 1. Lexer: 源文件 → Token 流
   ├─ 2. Parser: Token 流 → AST
   ├─ 3. TypeCheck: AST → 带类型注解的 AST
   ├─ 4. IRGen: 带类型 AST → Maxx IR（平台无关）
   ├─ 5. CodeGenC: Maxx IR → C 代码
   └─ 6. 调用宿主 gcc/clang: C 代码 → 原生可执行文件
```

### 3.4 为什么 Level 1b 要用 C 而不是直接 Maxx 自举？

- 直接自举是"鸡生蛋"问题：你需要一个能跑的 Maxx 编译器来编译 Maxx 编译器，但你现在没有。
- C 是"最低风险的中间层"：C 编译器到处都是（gcc/clang/msvc），用 C 写 Level 1b 保证了"任何有 C 编译器的机器都能编译出 maxxc"。
- Level 1b 完成后，Level 2 用 Maxx 重写时，Level 1b 就是那个"能跑的 Maxx 编译器"。

### 3.5 本次交付的范围（Level 1a）

- 能解析并编译 `SPEC.md` §3 中的完整语法子集。
- 能编译运行 `examples/` 下的 5-10 个 `.max` 示例程序。
- 标准库覆盖 `std.core`、`std.prim`、`std.text`、`std.collections` 的核心 API。
- 明确标注：所有 Python 代码都是临时开发种子，Level 1b 会用 C 重写，最终用户拿到的 `maxxc` 不依赖 Python。

---

## 4. Level 2：Maxx 自举编译器（规划中）

### 4.1 目标

用 Maxx 自身重写 `maxxc` 的前端（Lexer + Parser + TypeCheck），使得：

- `maxxc` 的 Lexer 是用 Maxx 写的。
- `maxxc` 的 Parser 是用 Maxx 写的。
- `maxxc` 能编译自己的源码。

### 4.2 自举的关键步骤

```
步骤 1：用 Level 1b 编译 Maxx 写的 Lexer
   │
   ├─ 把 maxxc/lexer.max 用 Level 1b 编译为 C，再编译为可执行文件
   ├─ 得到 maxxc-lexer（一个能把 .max 源码切分成 Token 的程序）
   │
步骤 2：用 Level 1b 编译 Maxx 写的 Parser
   │
   ├─ 把 maxxc/parser.max 用 Level 1b 编译为 C，再编译为可执行文件
   ├─ 得到 maxxc-parser（一个能把 Token 流解析成 AST 的程序）
   │
步骤 3：组合
   │
   ├─ maxxc-lexer + maxxc-parser + Level 1b 的 TypeCheck + Level 1b 的 CodeGenC
   ├─ = 一个"前端是 Maxx、后端是 C"的混合编译器
   │
步骤 4：自举测试
   │
   ├─ 用混合编译器编译 maxxc-lexer.max 自己
   ├─ 得到 maxxc-lexer-self-hosted
   ├─ 对比 maxxc-lexer-self-hosted 和 maxxc-lexer 的输出是否一致
   ├─ 如果一致 → 自举成功
   │
步骤 5：逐步替换后端
   │
   ├─ 用 Maxx 重写 TypeCheck
   ├─ 用 Maxx 重写 IRGen
   ├─ 用 Maxx 重写 CodeGenC
   ├─ 最终：整个 maxxc 都是 Maxx 写的
```

### 4.3 自举的"鸡生蛋"问题

- 你需要一个编译器来编译编译器。
- 解决：先用 Level 1b 编译 Maxx 写的编译器，得到一个"Maxx 编译器"。
- 然后用这个"Maxx 编译器"编译它自己，得到一个"自举的 Maxx 编译器"。
- 验证：自举的 Maxx 编译器编译它自己的输出，应该和第一次编译的输出一致。

---

## 5. Level 3：优化版自举编译器（规划中）

### 5.1 目标

在 Level 2 的基础上，加上优化后端，替换掉 C 引导编译器。

### 5.2 优化后端的内容

| 优化 | 说明 |
|---|---|
| **SSA**（静态单赋值） | 把 IR 转为 SSA 形式，启用全局优化 |
| **寄存器分配** | 线性扫描 / 图着色，分配物理寄存器 |
| **指令选择** | 把 IR 映射为 x86_64 / ARM64 指令 |
| **指令调度** | 填充流水线气泡 |
| **死代码消除** | 删除不可达代码 |
| **内联展开** | 小函数内联 |
| **循环优化** | 循环不变量外提、向量化 |
| **尾调用优化** | 尾调用优化 |

### 5.3 为什么要替换掉 C 后端？

- C 后端依赖宿主 gcc/clang，不跨平台到 WASM / Android / iOS。
- 优化后端直接生成机器码，可以完全控制性能。
- 最终的 `maxxc` 应该是一个独立的二进制，不依赖任何外部编译器。

### 5.4 替换路径

```
Level 2: maxxc（Maxx 前端 + C 后端）
   │
   ├─ 用 maxxc 编译 maxxc 自己
   ├─ 得到 self-hosted-maxxc（Maxx 前端 + C 后端）
   │
Level 3: 给 self-hosted-maxxc 加上 SSA + 寄存器分配
   │
   ├─ self-hosted-maxxc 现在能直接生成 x86_64 机器码
   ├─ 不再需要 C 后端
   │
   ├─ 用 self-hosted-maxxc 编译 self-hosted-maxxc 自己
   ├─ 得到 optimized-maxxc（Maxx 前端 + 原生机器码后端）
   │
   ├─ 验证：optimized-maxxc 编译 optimized-maxxc 的输出，应该和 self-hosted-maxxc 的输出一致
   │
   └─ 替换掉 Level 1b 的 C 引导编译器
```

---

## 6. 时间线（规划）

| 阶段 | 内容 | 预估 |
|---|---|---|
| Level 1a | Python 开发期种子 + 标准库核心 + 示例 | 本次交付 |
| Level 1b | 用 C 重写 Level 1a，预编译为 ELF 二进制（无 libpython 依赖） | 3-6 个月 |
| Level 2 | 用 Maxx 重写 Lexer/Parser，自举成功 | 6-12 个月 |
| Level 3 | SSA + 寄存器分配 + 优化后端，替换 C 引导 | 12-24 个月 |

---

## 7. 本次交付物清单

| 文件 | 说明 |
|---|---|
| `SPEC.md` | Maxx 语言完整规范（3000+ API） |
| `BOOTSTRAP.md` | 本文档，自举路线图 |
| `ANDROID.md` | Maxx Android 开发套件专章 |
| `maxxc-bootstrap/` | Python 开发期种子（Level 1a，临时工具） |
| `stdlib/` | 标准库 Maxx 源码 |
| `examples/` | 示例 `.max` 程序 |

---

> **Maxx 之道在自举上的体现**：人写得少（Level 1a 用 Python 快速搭起脚手架），机器做得多（Level 1b 用 C 重写、Level 2/3 逐步替换为 Maxx 自身），但一切透明（每一步都验证输出一致性，最终交付的 `maxxc` 是 ELF 二进制，`ldd` 不依赖 libpython，不偷偷藏运行时依赖）。
