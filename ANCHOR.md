# Maxx 语言核心种子规范（Anchor Spec v1.0 终版）

> 本文件是所有子任务（规范文档/编译器/标准库/示例）必须严格对齐的语言基线。
> 任何子产物中的语法、关键字、类型名、语义若与本文件冲突，以本文件为准。

---

## 1. 设计哲学

**Maxx** = Maximum simplicity × Maximum efficiency。

### 1.0 哲学主张（Maxx 之道，六条原创原则）

这六条不是口号，而是**贯穿所有技术决策的最高判据**。任何语法、类型、并发、错误处理的设计选择，都必须能追溯到这六条之一。

**一、简而有力（Simple but Forceful）**
- 简单不是简陋，高效不是复杂。
- 用户看到的是一行代码，编译器背后做十行优化。
- 反例：Python 简单但慢（放弃效率换简单）；C++ 高效但复杂（放弃简单换效率）。Maxx 拒绝二选一。
- 设计推论：语法糖克制，类型推断兜底，性能靠编译器而非用户记忆。

**二、人即度量（Human as the Measure）**
- 语言首先是给人思考用的工具，其次才是给机器执行的指令。
- 一行代码被人读 100 次，被机器执行 1 次——优化阅读体验的杠杆更大。
- 设计推论：静态标注（参数/返回类型）强制可读；缩进分块让人一眼看出块结构；命名优先于缩写。

**三、透明无隐（No Hidden Magic）**
- 编译器做的事，用户从代码里能看出来、能预测。
- 没有隐式转换（int↔f64 必须显式）、没有隐式构造、没有隐藏 this、没有运行时反射魔法。
- 反例：Python 的隐式调用 `__init__`/`__new__`、JS 的原型链怪异行为。Maxx 拒绝。
- 设计推论：`?T` 强制解包，`Result` 强制处理，`self` 显式写出来。

**四、万物一理（One Rule for All）**
- 用最少的规则解释最多的概念。
- 函数即值（`fn(A)->R` 是一等类型）、错误即值（`Result<T,E>` 不是异常）、并发即通道（`chan T` 就是类型）、模块即文件。
- 不做"特殊情况"：没有第二套错误处理、没有第二套并发模型、没有第二套内存规则。
- 设计推论：`match` 同时拆 ADT、处理可选、处理结果；`task` 就是函数调用加调度。

**五、涌现之美（Beauty by Emergence）**
- 不堆砌特性，让少量规则组合涌现出大表达力。
- 核心原语只有：类型、函数、ADT、match、chan、task。剩下的表达力全靠组合。
- 反例：C++ 60+ 关键字、Java 20+ 特性互相叠加。Maxx 目标关键字 < 30。
- 设计推论：没有宏、没有重载、没有继承——泛型 + trait + ADT 足够覆盖 95% 场景。

**六、诚实即高效（Honesty is Efficiency）**
- 类型诚实、错误显式、依赖清晰——不偷偷做事。
- 表面上多写了几行（显式类型标注、显式错误处理），但换来编译器能静态消除 90% 运行时开销。
- 设计推论：无 null（编译期消灭 NPE）；无隐式转换（编译期消灭精度丢失）；无异常（编译期消灭未处理错误）。

> **对比现有语言的哲学标签**：
> - Python："有且只有一种明显的做法"——但简单靠运行时妥协。
> - Go："少即是多"——但放弃了类型表达力。
> - Rust："无畏并发"——但用借用检查把负担推给用户。
> - Haskell："纯函数即数学"——但把人挡在门外。
> - **Maxx："人写得少，机器做得多，但一切透明"**——这是它自己的标签。

> **后缀约定（v1.0 终版，四层文件格式）**：
>
> | 层 | 后缀 | 含义 | 类比 |
> |---|---|---|---|
> | 源代码 | `.max` | 用户手写的代码文件（UTF-8 文本） | `.c` / `.py` / `.go` |
> | 共享库 | `.mxx` | 编译后的动态库/原生库（机器码+元数据） | C 的 `.so`/`.dll`/`.dylib` |
> | 分发包 | `.smx` | 可安装资源包（多个 .mxx + .max 接口 + 元数据打包成 whl 式容器） | `.whl` / `.jar` |
> | 项目归档 | `.zip` | 整个项目/应用的归档发布 | GitHub Release tarball |
>
> **设计哲学**：
> - `.max` 是源代码，人类可读可编辑。
> - `.max` 经 `maxxc build` 编译为 `.mxx`——真正的原生共享库，运行时按平台 ABI 动态加载链接。
> - `.smx` 是"分发容器"：把一个或多个 `.mxx` + 头接口 `.max` + manifest 打成 zip 包，方便 `maxx install` 安装。
> - `.zip` 是整个项目的归档发布。
>
> **历史沿革**：v0.1–v0.4 草案中曾把源文件叫 `.mxx`、库叫 `.mex`，全部废弃。当前以 v1.0 为准。

- 一句话定位：**一门静态强类型、缩进分块、无空值、代数数据类型内置、可编译为原生码、移动端桌面端同源**的高级语言。
- 对标：取 Python 的易读、Go 的简洁并发、Rust 的类型安全（但无借用检查复杂度）、ML 的 ADT 与模式匹配。
- 三个"绝不"：
  1. 绝不有 `null`/`nil`——可空即 `?T`，编译期强制解包。
  2. 绝不隐式数字转换——`int` 与 `f64` 必须显式 `int()`/`f64()`。
  3. 绝不宏——元编程用编译期求值（`comptime`），不用文本宏。

## 2. 词法规则

### 2.1 关键字（全部小写）
```
if elif else for while loop match ret let var as is in
trait enum struct fn type import from pub priv
task chan comptime true false none some ok err try
break continue do nil_
```
注意：`fn`、`struct`、`enum` 是保留字但**在语法示例中实际使用声明符号**。
实际声明符号：`@` 声明函数，`#` 声明类型，`~` 声明导入，`::` 命名空间，`=>` lambda。

### 2.2 标识符
- 字母/下划线开头，后接字母数字下划线。
- 驼峰：类型 `Vec3`、函数 `readFile`、常量 `MAX_LEN`（全大写下划线）。
- 前缀 `_` 表示"故意未使用"。

### 2.3 字面量
- 整数：`42`、`-7`、`0xFF`、`0b1010`、`1_000_000`
- 浮点：`3.14`、`1e5`、`2.0f32`（默认 `f64`）
- 字符串：`"hello"`、`"带转义\n"`；原始串 `` `raw \n 不转义` ``；插值串 `f"x = {x}"`
- 字符：`'a'`（`char` 类型，4 字节 Unicode 码点）
- 布尔：`true` / `false`
- 可选：`none`、`some(v)`；结果：`ok(v)`、`err(e)`

### 2.4 运算符（优先级从高到低）
```
后缀:  .  ::  ()  []
单目:  -  !  ~(按位取反)  *  &
乘除:  *  /  %  //(整除)
加减:  +  -
移位:  <<  >>
比较:  <  <=  >  >=  is  as
相等:  ==  !=
按位与: &
按位异或: ^
按位或: |
逻辑与: &&
逻辑或: ||
条件:  ?:  (三目)
管道:  |>   (左值作为右参传入下一函数)
赋值:  =  +=  -=  *=  /=  %=
```

### 2.5 分隔符与结构
- **缩进分块（offside rule）**：4 空格缩进表示块；`:` 后换行缩进。
- 语句以换行结束；一行多语句用 `;`。
- 括号 `()` 用于表达式分组；方括号 `[]` 用于索引与列表字面量；花括号 `{}` 用于结构体字面量与块表达式。
- 注释：行注释 `// ...`；块注释 `/* ... */`（可嵌套）。文档注释 `/// 公共 API`、`//! 模块文档`。

## 3. 完整语法示例（编译器必须能解析的目标子集）

```
~ std.io
~ std.math::sqrt
~ std.collections::Vec

// 结构体
# Point:
    x: f64
    y: f64

// 带方法的结构体
@ Point::dist(self: Point, o: Point) -> f64:
    ret sqrt((self.x-o.x)^2 + (self.y-o.y)^2)

// ADT（代数数据类型）
# Shape:
    Circle(r: f64)
    Rect(w: f64, h: f64)
    Dot

@ area(s: Shape) -> f64:
    match s:
        Circle(r):   ret 3.14159265 * r * r
        Rect(w, h):  ret w * h
        Dot:         ret 0.0

// 泛型函数
@ identity<T>(x: T) -> T:
    ret x

// 可选类型
@ index_of(arr: Vec<int>, v: int) -> ?int:
    for i in 0..arr.len():
        if arr[i] == v:
            ret some(i)
    ret none

// Result 与 ? 传播
@ safe_div(a: f64, b: f64) -> Result<f64, str>:
    if b == 0.0:
        ret err("div by zero")
    ret ok(a / b)

@ use_div() -> Result<int, str>:
    let r = try safe_div(10.0, 2.0)?
    ret ok(int(r))

// 控制流
@ demo(n: int) -> str:
    if n < 0:
        ret "neg"
    elif n == 0:
        ret "zero"
    else:
        ret "pos"

// 循环
@ sum(n: int) -> int:
    var total = 0
    for i in 1..=n:
        total += i
    while total > 1000:
        total -= 100
    ret total

// 并发
@ worker(id: int, out: chan str):
    out.send("hello #" + str(id))

@ main() -> int:
    let p = Point{x: 3.0, y: 4.0}
    let q = Point{x: 0.0, y: 0.0}
    io.println("dist = " + str(p.dist(q)))

    let s = Rect{w: 3.0, h: 4.0}
    io.println("area = " + str(area(s)))

    let ch = chan str
    task worker(1, ch)
    task worker(2, ch)
    io.println(ch.recv())
    io.println(ch.recv())
    ret 0
```

## 4. 类型系统

### 4.1 内置标量类型
| 类型 | 位宽 | 说明 |
|---|---|---|
| `bool` | 1 | true/false |
| `i8 i16 i32 i64` | 8/16/32/64 | 有符号整数 |
| `u8 u16 u32 u64` | 8/16/32/64 | 无符号整数 |
| `int` | 64 | 平台默认有符号 |
| `f32 f64` | 32/64 | IEEE754，默认 f64 |
| `char` | 32 | Unicode 码点 |
| `str` | 引用 | UTF-8 不可变字符串 |
| `?T` | — | 可选（Some/None） |
| `Result<T,E>` | — | 结果类型 |
| `Vec<T>` | — | 动态数组（标准库） |
| `Map<K,V>` | — | 哈希表（标准库） |
| `Set<T>` | — | 哈希集合 |
| `chan T` | — | 通道 |
| `fn(A...) -> R` | — | 函数类型 |
| `()` | 0 | 单元类型（类似 void） |

### 4.2 类型推断
- `let x = 42` → `int`；`var y = 1.0` → `f64`。
- 函数参数与返回值**必须显式标注类型**（公共 API 可读性）。
- 泛型由调用点推断。

### 4.3 内存模型
- 值类型（struct/枚举/数字/char）默认栈分配；`Box<T>` 显式堆分配。
- 堆对象用**引用计数 + 循环分代回收**（简化：引导阶段用 Boehm GC，自举后自实现）。
- 无手动 free，无借用检查。

### 4.4 错误模型
- 无异常栈展开；错误用 `Result<T,E>` 显式返回，`?` 传播。
- `panic!` 用于不可恢复错误，运行时 abort + 堆栈。

## 5. 模块与包
- 一个 `.max` 源文件 = 一个模块；路径即模块名。
- `~ std.io` 导入；`~ std.collections::Vec` 导入具体符号。
- `pub` 前缀导出：`pub # Point: ...`、`pub @ area(...)`。
- 包 = 目录，含 `mod.max` 入口；`maxx build` 编译为 `.mxx` 共享库。

## 6. 四层文件格式（v1.0 终版）

### 6.1 `.max` 源文件格式
- UTF-8 文本，LF 换行，无 BOM。
- 模块即文件：`~ std.io` 对应 `std/io.max` 或 `std/io/mod.max`。
- 一行一语句；4 空格缩进分块；行尾 `;` 可选。
- 人类可读可编辑。

### 6.2 `.mxx` 共享库格式（类比 C 的 .so/.dll）
- 由 `maxxc build foo.max` 产出 `foo.mxx`。
- 二进制容器，包含：
  - **机器码段**：按目标平台 ABI（x86_64-linux / arm64-android / arm64-ios / wasm32）编译的原生码
  - **导出符号表**：该库 `pub` 出的函数/类型/常量
  - **导入符号表**：该库依赖的外部符号
  - **类型元数据**：泛型实例化信息、vtable、反射表
  - **运行时绑定**：GC 指针表、析构函数表
- **动态加载机制**：运行时通过 `dlopen`/`LoadLibrary` 等价接口加载 `.mxx`，按符号表链接。
- **链接**：`~ mylib::foo` 时编译器查 `mylib.mxx` 的导出符号表，链接到调用点。
- 与 C `.so` 的区别：`.mxx` 自带类型元数据与 GC 绑定，跨语言 ABI 不兼容（仅 Maxx 内部使用）。

### 6.3 `.smx` 分发包格式（类比 Python whl）
zip 容器，把一个或多个 `.mxx` + 头接口 `.max` + manifest 打包：
```
mypkg-1.0.0.smx
├── manifest.json          # 元数据
├── lib/                   # 预编译共享库
│   ├── x86_64-linux/libmypkg.mxx
│   ├── arm64-android/libmypkg.mxx
│   └── wasm32/libmypkg.mxx
├── include/               # 公共 .max 接口头文件
│   └── mypkg/*.max
├── src/                   # 源文件（可选，便于调试/重新编译）
│   └── mypkg/*.max
└── docs/                  # 文档
```
`manifest.json` schema：
```json
{
  "format": "smx@1",
  "name": "mypkg",
  "version": "1.0.0",
  "entry": "mypkg/mod.max",
  "targets": ["x86_64-linux", "arm64-android", "wasm32"],
  "dependencies": { "std::text": "^1.0", "thirdparty::json": "~>0.4" },
  "authors": ["..."],
  "license": "MIT"
}
```
**安装**：`maxx install mypkg` 拉取 `.smx`，解压到 `.maxx/vendor/mypkg-1.0.0/`，得到 `lib/<target>/mypkg.mxx` 与 `include/mypkg/*.max`。
**依赖解析**：SemVer 版本范围；`maxx build` 自动链接 vendor 目录。

### 6.4 `.zip` 项目归档格式
- 整个项目目录的 zip 归档（源码 `.max` + 已安装 `.smx` 依赖 + README + examples/）。
- 安装：`unzip myapp.zip && cd myapp && maxx run main.max`。
- 这是给最终用户/开发者的整包发布格式。

## 7. 跨平台目标
- **桌面**（Windows/macOS/Linux）：AOT 编译为原生可执行文件，静态链接运行时。
- **Android**：`.mxx` 即 `.so` 等价物，通过 JNI 包装在 APK 中加载；也支持 Termux 直接编译。
- **iOS**：`.mxx` 打包进 `.a` 静态库，嵌入 Xcode 工程。
- **Web（可选）**：编译为 WASM。
- 运行时核心：GC、调度器（task/chan）、IO 层（抽象 POSIX/WinAPI/Android Looper）。

## 8. 自举（Bootstrapping）层级
- **Level 0**：手写一个最小机器码汇编引导程序（仅 spec 文档描述，不实际交付二进制）。
- **Level 1（本次交付）**：用 **Python** 写的引导编译器 `maxxc-bootstrap/`，把 Maxx 子集编译为 C 代码再用宿主 gcc/clang 编译运行。**明确标注：这是临时引导工具。**
- **Level 2**：用 Maxx 自身重写 `maxxc` 前端（Lexer/Parser），能编译自身。
- **Level 3**：自举版编译器加上优化后端（SSA、寄存器分配），替换掉 Python 引导。
- 本次交付物 = Level 1 引导编译器 + 完整规范（描述 Level 0–3 路径）。

## 9. 标准库规模目标（凑 3000+ API）
按模块组织，每模块列出类型/函数/方法/常量：
- `std.core`：类型转换、panic、comptime、断言
- `std.prim`：i64/u64/f64/char/bool 的方法（算术、位运算、比较、转换）
- `std.text`：String 方法（约 80+）、StringBuilder、正则、Unicode
- `std.collections`：Vec、Deque、Map、Set、SortedMap、Iter（迭代器适配器 30+）
- `std.io`：文件、终端、字节流、Buffer
- `std.fs`：文件系统
- `std.math`：常量 + 60+ 数学函数
- `std.time`：Duration、Instant、日期
- `std.async`：task、chan、select、等待组
- `std.net`：TCP/UDP/HTTP 客户端
- `std.json` / `std.xml` / `std.base64`
- `std.random`
- `std.test`：单元测试框架
- `std.cli`：参数解析
- 每个方法/函数/常量都算 1 个"语法点"。
