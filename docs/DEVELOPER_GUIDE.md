# Maxx 开发者指南

> 版本：v2.0 | 最后更新：2026-09-20

---

## 目录

1. [快速上手](#1-快速上手)
2. [安装和环境配置](#2-安装和环境配置)
3. [语言基础语法教程](#3-语言基础语法教程)
4. [标准库使用指南](#4-标准库使用指南)
5. [编译器使用手册](#5-编译器使用手册)
6. [文件格式详解](#6-文件格式详解)
7. [如何写 Maxx UI 应用](#7-如何写-maxx-ui-应用)
8. [如何打包 APK](#8-如何打包-apk)
9. [常见问题 FAQ](#9-常见问题-faq)
10. [最佳实践](#10-最佳实践)

---

## 1. 快速上手

### 5 分钟写出第一个 Maxx 程序

创建文件 `hello.max`：

```maxx
@ main() -> int:
    io.println("Hello, Maxx!")
    ret 0
```

编译运行：

```bash
maxxc run hello.max
```

输出：

```
Hello, Maxx!
```

### 程序结构

每个 Maxx 程序从 `@ main() -> int:` 开始：

```maxx
// 这是注释
@ main() -> int:
    // 你的代码写在这里
    ret 0  // 返回 0 表示成功
```

### 变量

```maxx
let x = 42          // 不可变变量
var y = 10          // 可变变量
let pi: f64 = 3.14  // 类型注解
```

---

## 2. 安装和环境配置

### Linux

```bash
git clone https://github.com/Maxx-EX/Maxx.git
cd Maxx/compiler
python3 maxxc.py run hello.max
```

### Termux (Android)

```bash
pkg install python clang
git clone https://github.com/Maxx-EX/Maxx.git
cd Maxx
bash tools/install-maxx.sh
maxxc run hello.max
```

### Android App

安装 `maxx-android-app-v7.apk`，直接在手机上写 Maxx 代码并运行。

---

## 3. 语言基础语法教程

### 3.1 变量

```maxx
let x = 42          // 不可变
var y = 10          // 可变
let pi: f64 = 3.14  // 显式类型
```

### 3.2 函数

```maxx
@ add(a: int, b: int) -> int:
    ret a + b

@ main() -> int:
    io.println(str(add(1, 2)))
    ret 0
```

### 3.3 控制流

```maxx
// if/elif/else
let x = 5
if x > 10:
    io.println("large")
elif x > 3:
    io.println("medium")
else:
    io.println("small")

// for 循环
for i in 0..10:
    io.println(str(i))

// while 循环
var i = 0
while i < 5:
    io.println(str(i))
    i = i + 1
```

### 3.4 结构体

```maxx
# Point:
    x: int
    y: int

@ main() -> int:
    let p = Point { x: 1, y: 2 }
    io.println(str(p.x))
    ret 0
```

### 3.5 枚举和 match

```maxx
# Color:
    Red
    Green
    Blue

@ main() -> int:
    let c = Color::Red
    match c:
        Color::Red => io.println("red")
        Color::Green => io.println("green")
        Color::Blue => io.println("blue")
    ret 0
```

### 3.6 Option 和 Result

```maxx
@ divide(a: int, b: int) -> Result<f64, str>:
    if b == 0:
        ret err("division by zero")
    ret ok(a as f64 / b as f64)

@ main() -> int:
    match divide(10, 2):
        ok(v) => io.println(str(v))
        err(e) => io.println(e)
    ret 0
```

---

## 4. 标准库使用指南

### 4.1 io 模块

```maxx
io.println("hello")
io.print("no newline")
let line = io.read_line()
let content = io.read_file("test.txt")
io.write_file("out.txt", "hello")
```

### 4.2 math 模块

```maxx
let x = sqrt(16.0)      // 4.0
let y = pow(2.0, 3.0)  // 8.0
let z = sin(0.0)        // 0.0
```

### 4.3 类型转换

```maxx
let s = str(42)        // "42"
let i = int("42")      // 42
let f = f64(42)        // 42.0
```

---

## 5. 编译器使用手册

### 5.1 子命令

| 命令 | 说明 |
|------|------|
| `tokenize` | 词法分析 |
| `parse` | 语法分析，打印 AST |
| `ir` | 打印中间表示 |
| `codegen` | 生成 C 代码 |
| `build` | 编译为 .mxx 共享库 |
| `pack` | 打包为 .smx 分发包 |
| `archive` | 项目归档为 .zip |
| `run` | 编译并运行 |
| `repl` | 交互式 REPL |

### 5.2 示例

```bash
maxxc run hello.max
maxxc codegen hello.max -o hello.c
maxxc build lib.max -o lib.mxx
maxxc pack lib.mxx -o lib.smx
maxxc repl
```

---

## 6. 文件格式详解

| 后缀 | 说明 |
|------|------|
| `.max` | Maxx 源代码文件 |
| `.mxx` | 编译后的动态共享库（类似 .so） |
| `.smx` | 分发包（whl 式 zip 容器） |
| `.zip` | 项目归档（最终发布） |

---

## 7. 如何写 Maxx UI 应用

Maxx UI 使用声明式语法：

```maxx
@ main() -> int:
    let app = UI::new("My App")
    app.add(Button::new("Click Me"))
    app.run()
    ret 0
```

---

## 8. 如何打包 APK

使用 Maxx Packer App：

1. 选择项目文件夹
2. 确认项目信息
3. 点「打包」
4. 安装生成的 APK

---

## 9. 常见问题 FAQ

### Q: Maxx 是解释型还是编译型？
A: 引导阶段是编译到 C 再用 gcc 编译，最终目标是原生机器码。

### Q: 为什么用 Python 写编译器？
A: 这是 Level 1 引导种子，最终会用 Maxx 自身重写。

### Q: 支持哪些平台？
A: Linux x86_64 完整支持，Android/iOS/WASM 规划中。

### Q: 有 GC 吗？
A: 引导阶段用 malloc，生产版计划用 Boehm GC。

---

## 10. 最佳实践

1. 用 `let` 声明不可变变量，`var` 只在必要时用
2. 函数名用 snake_case
3. 类型名用 PascalCase
4. 错误用 Result 类型处理，不用异常
5. 模块名用小写
6. 注释写在函数上方
7. 每个文件一个主要模块
8. 先写测试再写实现
9. 保持函数短小
10. 用类型注解提高可读性

---

## 彩蛋

试试看 `io.println("hi！Maxx")` —— 注意是中文全角感叹号！

---

> Maxx: simple by design, efficient by choice, transparent by default.
