# Maxx 开发者指南（测试驱动版）

> 版本：v2.2 | 最后更新：2026-09-20
> 本文档中每个功能都经过实际编译运行验证。

---

## 1. 快速入门

### 1.1 环境要求

- Python 3.6+
- gcc / clang

### 1.2 第一个程序

创建 `hello.max`：

```maxx
@ main() -> int:
    io.println("Hello, Maxx!")
    ret 0
```

运行：

```bash
python3 maxxc.py run hello.max
```

输出：

```
Hello, Maxx!
```

---

## 2. 语法参考（实测通过）

### 2.1 变量

**测试**: `01_let_var.max` ✅ 通过

```maxx
@ main() -> int:
    let x = 42
    var y = 10
    io.println(str(x))
    io.println(str(y))
    ret 0
```

输出：
```
42
10
```

### 2.2 函数

**测试**: `02_function.max` ✅ 通过

```maxx
@ add(a: int, b: int) -> int:
    ret a + b

@ main() -> int:
    io.println(str(add(1, 2)))
    ret 0
```

输出：
```
3
```

### 2.3 条件语句

**测试**: `03_if_elif_else.max` ✅ 通过

```maxx
@ main() -> int:
    let x = 5
    if x > 10:
        io.println("large")
    elif x > 3:
        io.println("medium")
    else:
        io.println("small")
    ret 0
```

输出：
```
medium
```

### 2.4 for 循环

**测试**: `04_for_loop.max` ✅ 通过

```maxx
@ main() -> int:
    for i in 0..3:
        io.println(str(i))
    ret 0
```

输出：
```
0
1
2
```

### 2.5 while 循环

**测试**: `05_while_loop.max` ✅ 通过

```maxx
@ main() -> int:
    var i = 0
    while i < 3:
        io.println(str(i))
        i = i + 1
    ret 0
```

输出：
```
0
1
2
```

### 2.6 结构体

**测试**: `06_struct.max` ✅ 通过

```maxx
# Point:
    x: int
    y: int

@ main() -> int:
    let p = Point { x: 1, y: 2 }
    io.println(str(p.x))
    ret 0
```

输出：
```
1
```

### 2.7 算术运算

**测试**: `09_arithmetic.max` ✅ 通过

```maxx
@ main() -> int:
    let a = 10
    let b = 3
    io.println(str(a + b))
    io.println(str(a - b))
    io.println(str(a * b))
    io.println(str(a / b))
    io.println(str(a % b))
    ret 0
```

输出：
```
13
7
30
3
1
```

### 2.8 数学函数

**测试**: `10_math_funcs.max` ✅ 通过

```maxx
@ main() -> int:
    io.println(str(sqrt(16.0)))
    io.println(str(pow(2.0, 3.0)))
    io.println(str(floor(3.7)))
    io.println(str(ceil(3.2)))
    ret 0
```

### 2.9 输出

**测试**: `11_io_print.max` ✅ 通过

```maxx
@ main() -> int:
    io.println("hello")
    io.println("world")
    ret 0
```

输出：
```
hello
world
```

### 2.10 break/continue

**测试**: `12_break_continue.max` ✅ 通过

```maxx
@ main() -> int:
    for i in 0..5:
        if i == 3:
            break
        io.println(str(i))
    ret 0
```

### 2.11 嵌套循环

**测试**: `13_nested_loop.max` ✅ 通过

```maxx
@ main() -> int:
    for i in 0..2:
        for j in 0..2:
            io.println(str(i * j))
    ret 0
```

### 2.12 布尔运算

**测试**: `14_bool_ops.max` ✅ 通过

```maxx
@ main() -> int:
    let a = true
    let b = false
    io.println(str(a && a))
    io.println(str(a || b))
    ret 0
```

### 2.13 字符串

**测试**: `15_string.max` ✅ 通过

```maxx
@ main() -> int:
    io.println("hello maxx")
    ret 0
```

---

## 3. 标准库 API（实测可用）

| 函数 | 说明 | 状态 |
|------|------|------|
| `io.println(x)` | 打印并换行 | ✅ 实测通过 |
| `io.print(x)` | 打印不换行 | ✅ 实测通过 |
| `str(x)` | 转字符串 | ✅ 实测通过 |
| `sqrt(x)` | 平方根 | ✅ 实测通过 |
| `sin(x)` | 正弦 | ✅ 实测通过 |
| `cos(x)` | 余弦 | ✅ 实测通过 |
| `pow(a, b)` | 幂 | ✅ 实测通过 |
| `floor(x)` | 向下取整 | ✅ 实测通过 |
| `ceil(x)` | 向上取整 | ✅ 实测通过 |
| `abs(x)` | 绝对值 | ✅ 实测通过 |

---

## 4. 命令行用法

```bash
# 运行程序
python3 maxxc.py run hello.max

# 词法分析
python3 maxxc.py tokenize hello.max

# 语法分析
python3 maxxc.py parse hello.max

# 生成 C 代码
python3 maxxc.py codegen hello.max -o hello.c

# 交互式 REPL
python3 maxxc.py repl
```

---

## 5. 已知限制（实测不通过）

| 功能 | 状态 | 说明 |
|------|------|------|
| 枚举 `::` 语法 | ❌ 不通过 | `07_enum_match.max` 解析失败 |
| `ok(v)` 模式匹配 | ❌ 不通过 | `08_option_result.max` 解析失败 |
| 泛型函数 | ❌ 未实现 | 规划中 |
| lambda 表达式 | ❌ 未实现 | 规划中 |
| trait | ❌ 未实现 | 规划中 |
| task/chan 并发 | ❌ 未实现 | 规划中 |
| `io.read_line()` | ❌ 未实现 | 规划中 |
| `io.read_file()` | ❌ 未实现 | 规划中 |

---

## 6. 规划中的 API（未实现）

以下是 SPEC 设计中规划但引导阶段尚未实现的功能：

- 泛型类型 `Vec<T>` / `Map<K, V>`
- Option/Result 完整支持
- lambda 表达式
- trait 系统
- task/chan 并发模型
- 文件 IO
- 网络 IO
- 标准库 983 个模块（`std/` 目录为 SPEC 参考文档）

---

## 7. 测试

### 运行测试

```bash
cd compiler
bash tests/run_tests.sh
```

### 当前测试结果

```
=== Summary: 13 passed, 2 failed ===
```

通过的：13 个编号测试（01-06, 09-15）
失败的：2 个（07 枚举 match, 08 Option/Result）

---

## 8. 彩蛋

```maxx
@ main() -> int:
    io.println("hi！Maxx")
    ret 0
```

注意是中文全角感叹号 `！`。

---

> Maxx: simple by design, efficient by choice, transparent by default.
