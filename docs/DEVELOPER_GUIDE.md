# Maxx 开发者指南（诚实版）

> 版本：v2.1 | 最后更新：2026-09-20
> 本文档只记录**实际实测通过**的功能。规划中的功能单独标注。

---

## 1. 快速入门

### 1.1 环境要求

- Python 3.6+
- gcc / clang（用于编译生成的 C 代码）

### 1.2 安装

```bash
git clone https://github.com/Maxx-EX/Maxx.git
cd Maxx/compiler
```

### 1.3 第一个程序

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

## 2. 语法参考（已实现）

### 2.1 变量

**已实现：**
- `let` 声明不可变变量
- `var` 声明可变变量
- 类型注解（可选）

```maxx
let x = 42
var y = 10
let pi: f64 = 3.14
```

### 2.2 函数

**已实现：**
- `@ 函数名(参数: 类型) -> 返回类型:` 语法
- `ret` 返回语句
- 多参数函数

```maxx
@ add(a: int, b: int) -> int:
    ret a + b

@ main() -> int:
    io.println(str(add(1, 2)))
    ret 0
```

### 2.3 控制流

**已实现：**
- `if / elif / else`
- `for i in 0..N` 范围循环
- `while` 循环
- `break` / `continue`

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
for i in 0..5:
    io.println(str(i))

// while 循环
var i = 0
while i < 3:
    io.println(str(i))
    i = i + 1
```

### 2.4 结构体

**已实现：**
- `# 结构体名:` 定义
- 字段初始化
- 字段访问 `.`

```maxx
# Point:
    x: int
    y: int

@ main() -> int:
    let p = Point { x: 1, y: 2 }
    io.println(str(p.x))
    ret 0
```

### 2.5 枚举和 match

**已实现：**
- `# 枚举名:` 定义
- 变体 `Color::Red`
- `match` + `=>` 语法

```maxx
# Shape:
    Circle
    Rect

@ main() -> int:
    let s = Shape::Circle
    match s:
        Shape::Circle => io.println("circle")
        Shape::Rect => io.println("rect")
    ret 0
```

### 2.6 Option / Result

**已实现：**
- `some()` / `none()`
- `ok()` / `err()`
- match 解构

```maxx
@ main() -> int:
    let r = ok(42)
    match r:
        ok(v) => io.println(str(v))
        err(e) => io.println(e)
    ret 0
```

### 2.7 内置函数

**已实现（实测通过）：**

| 函数 | 说明 |
|------|------|
| `io.println(x)` | 打印并换行 |
| `io.print(x)` | 打印不换行 |
| `str(x)` | 转字符串 |
| `sqrt(x)` | 平方根 |
| `sin(x)` | 正弦 |
| `cos(x)` | 余弦 |
| `pow(a, b)` | 幂 |
| `floor(x)` | 向下取整 |
| `ceil(x)` | 向上取整 |
| `abs(x)` | 绝对值 |

**规划中（未实现）：**
- `io.read_line()` — 规划中
- `io.read_file()` — 规划中
- `io.write_file()` — 规划中
- `now()` / `sleep()` — 规划中
- 泛型函数 — 规划中
- lambda 表达式 — 规划中
- trait — 规划中
- task/chan 并发 — 规划中

---

## 3. 命令行用法

### 3.1 可用子命令（实测）

```bash
# 运行程序（编译 + 执行）
python3 maxxc.py run hello.max

# 词法分析
python3 maxxc.py tokenize hello.max

# 语法分析（打印 AST）
python3 maxxc.py parse hello.max

# 生成 C 代码
python3 maxxc.py codegen hello.max -o hello.c

# 交互式 REPL
python3 maxxc.py repl
```

### 3.2 REPL 示例

```
maxx> let x = 42
maxx> io.println(str(x))
42
maxx> :quit
```

---

## 4. 测试

### 4.1 运行测试

```bash
cd compiler
bash tests/run_tests.sh
```

### 4.2 当前测试通过情况

| 测试文件 | 状态 | 说明 |
|----------|------|------|
| hello.max | ✅ 通过 | 基础输出 |
| struct.max | ✅ 通过 | 结构体 |
| loops.max | ✅ 通过 | 循环 + 条件 |
| enum_match.max | ✅ 通过 | 枚举 + match |
| option_result.max | ✅ 通过 | Option/Result |
| test_variables.max | ✅ 通过 | 变量声明 |
| test_arithmetic.max | ✅ 通过 | 算术运算 |
| test_float.max | ✅ 通过 | 浮点数 |
| test_bool.max | ✅ 通过 | 布尔值 |
| test_for.max | ✅ 通过 | for 循环 |
| test_sqrt.max | ✅ 通过 | sqrt 函数 |
| test_pow.max | ✅ 通过 | pow 函数 |
| ... 共 37 个 | ✅ 全部通过 | |

---

## 5. 常见问题

### Q: 为什么 `io.read_line()` 不能用？
A: 引导阶段还没实现，规划中。

### Q: 为什么泛型函数报错？
A: 泛型还没实现，规划中。

### Q: 为什么 lambda 不工作？
A: Lambda 还没实现，规划中。

### Q: 标准库的文件能直接编译吗？
A: 不能。`std/` 下的文件是 SPEC 参考文档，用的是完整 Maxx 语法，引导编译器只支持子集。

---

## 6. 彩蛋

试试看：

```maxx
@ main() -> int:
    io.println("hi！Maxx")
    ret 0
```

注意是中文全角感叹号 `！`。

---

## 7. 项目结构

```
maxx/
├── compiler/          # 引导编译器（Python）
│   ├── maxxc.py       # 主程序
│   ├── lexer.py       # 词法分析
│   ├── parser.py      # 语法分析
│   ├── checker.py     # 类型检查
│   ├── codegen_c.py   # C 代码生成
│   ├── runtime_minimal.c  # C 运行时
│   └── tests/         # 测试用例
├── std/               # 标准库（SPEC 参考）
├── docs/              # 文档
└── android-app/       # Android IDE
```

---

> Maxx: simple by design, efficient by choice, transparent by default.
