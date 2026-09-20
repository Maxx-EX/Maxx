# Maxx 编程语言参考手册（Language Specification v1.2）

> **最高优先级声明**：Maxx 编译器**从零构建，不依赖任何主流编程语言**。
> 最终交付的 `maxxc` 是纯原生二进制（ELF/PE/MachO），从机器码层面自举，
> 不依赖 Python/C/Go/Rust/Java 等任何主流语言的运行时。
> 仓库中的 Python 代码仅为开发期种子，不是最终交付物。
> 自举路径详见 `BOOTSTRAP.md`。
>
> 本文件是 **Maxx** 语言的权威参考手册（v1.2）。所有编译器、标准库、工具链与示例代码的实现都必须以本文件为准；与 `ANCHOR.md` 冲突时以本文件为准（本文件即 ANCHOR 的展开版）。
>
> **v1.0 终版四层文件格式**：
>
> | 层 | 后缀 | 含义 | 类比 |
> |---|---|---|---|
> | 源代码 | `.max` | 用户手写代码文件（UTF-8 文本，人类可读可编辑） | `.c` / `.py` / `.go` |
> | 共享库 | `.mxx` | 编译后的动态原生库（机器码 + 导出/导入符号表 + 类型元数据 + GC 绑定），运行时按平台 ABI 动态加载链接 | C 的 `.so` / `.dll` / `.dylib` |
> | 分发包 | `.smx` | 可安装资源包（多个 `.mxx` + `.max` 接口 + manifest 打包成 whl 式 zip 容器） | `.whl` / `.jar` |
> | 项目归档 | `.zip` | 整个项目/应用的归档发布（源码 `.max` + 已安装 `.smx` + README） | GitHub Release tarball |
>
> **核心数据流**：`.max` 经 `maxxc build` 编译为 `.mxx`（原生共享库）；`.smx` 是"分发容器"，把一个或多个 `.mxx` + 头接口 `.max` + manifest 打成 zip；`.zip` 是整项目归档。`~ mylib::foo` 在编译期查 `mylib.mxx` 的导出符号表，链接到调用点。
>
> **历史沿革**：v0.1–v0.4 草案中曾把源文件叫 `.mxx`、库叫 `.mex`，全部废弃。v1.0 起：`.max` 才是源文件，`.mxx` 才是共享库。本文档除本节外一律使用 `.max`（源）/ `.mxx`（库）/ `.smx`（包）/ `.zip`（归档），不再出现 `.mex`。
>
> 阅读对象：语言设计者、编译器实现者、标准库作者、应用开发者。

---

## 目录

0. Maxx 设计哲学（Maxx 之道）——六条原创原则
1. 设计理念与语言特色
2. 与现有语言的差异化定位
3. 词法规则（Lexer）
4. 完整语法（EBNF）
5. 类型系统
6. 语义规则（作用域、绑定、内存、并发、panic）
7. 模块系统与包管理
8. 标准库 API 完整清单
9. 四层文件格式规范（`.max` / `.mxx` / `.smx` / `.zip`）
10. 内存模型与垃圾回收
11. 跨平台运行时架构
12. 错误处理模型
13. 语法对照附录（Maxx vs Python vs Go vs Rust）

---

## 0. Maxx 设计哲学（Maxx 之道）

> 本章是整本手册的"宪法"。后面所有技术决策——语法长什么样、类型系统怎么设计、错误怎么处理、并发怎么写、内存怎么管、模块怎么分——都必须能追溯到本章的六条原则之一。如果某个设计选择在本章找不到依据，它就是错的，应当被推翻。

Maxx 不是"又一门把别人的好东西拼起来的语言"。它有自己的一套关于"语言应该为谁服务、应该长什么样"的判断。这套判断浓缩成六条原则，我们称之为 **Maxx 之道**。

### 0.1 六条原则总览

| 原则 | 一句话 | 对应技术决策 |
|---|---|---|
| 一、简而有力 | 简单不是简陋，高效不是复杂 | 语法糖克制、类型推断兜底、优化交给编译器 |
| 二、人即度量 | 语言首先是给人思考的工具 | 静态标注强制可读、缩进分块、命名优先 |
| 三、透明无隐 | 编译器做的事，代码里能看出来 | 无隐式转换、无隐式构造、`self` 显式 |
| 四、万物一理 | 用最少的规则解释最多的概念 | 函数即值、错误即值、并发即通道、模块即文件 |
| 五、涌现之美 | 不堆特性，让规则组合涌现表达力 | 关键字 < 30、无宏、无继承、泛型 + trait + ADT |
| 六、诚实即高效 | 类型诚实、错误显式，不偷偷做事 | 无 null、无隐式窄化、无异常，换来静态消除 |

### 0.2 一、简而有力（Simple but Forceful）

**简单不是简陋，高效不是复杂。** 这是 Maxx 对"语言设计两难"的根本回答。过去半个世纪，主流语言在这个两难之间反复横跳：Python 选择了"简单优先"，代价是放弃运行效率；C++ 选择了"高效优先"，代价是把语言膨胀到普通人学不动。Maxx 拒绝这个二选一——它相信**简单和复杂的分界线不在用户面前，而在编译器背后**。

用户看到的应当是一行干净的代码；编译器背后愿意为这一行代码做十行、一百行的优化。这是一种"前端极简、后端极深"的分工：用户不需要记住"这个运算符在这个类型上会隐式调用哪个模板"，也不需要手写下层循环的向量化指令——这些事编译器该做。反过来，用户也不需要为了"榨出 5% 的性能"而把代码写成编译器都读不懂的样子。Maxx 的赌注是：**一个把优化做扎实的编译器，能让 95% 的用户代码同时获得"简单"和"高效"**。

这条原则直接推导出一系列设计选择：语法糖要克制（每加一个语法糖都要回答"它能不能被现有的组合替代"）；类型推断要兜底（局部变量不写类型不影响可读性）；性能靠编译器而不是靠用户记忆（自动向量化、自动特化、自动内联）。它也解释了为什么 Maxx 拒绝宏——宏是"把复杂度转嫁给用户"的典型手段，与"简而有力"背道而驰。

### 0.3 二、人即度量（Human as the Measure）

**语言首先是给人思考用的工具，其次才是给机器执行的指令。** 这是 Maxx 与大量"编译器中心主义"语言的根本分野。一段代码在它的生命周期里，被人读几十次、上百次，被机器执行一次、一万次——但机器执行的边际成本几乎为零，人阅读的边际成本却极高。因此，**优化阅读体验的杠杆，远大于优化执行细节的杠杆**。

这条原则有几个直接推论。第一，公共 API 的类型标注是强制的——函数参数和返回值必须写类型，因为别人读你代码时第一眼就要看"这个函数吃什么、吐什么"。局部变量可以省略类型（那是写给自己看的），但接口不能省（那是写给别人看的）。第二，块结构用缩进而不是花括号——缩进让人一眼看出嵌套层次，花括号则需要数符号。第三，命名优先于缩写——`readFile` 比 `rdFl` 好，`MAX_LEN` 比 `ML` 好；语言不奖励那些只有作者自己看得懂的缩写。

"人即度量"也意味着语言要**对新手友好、对老手不设限**。新手不需要理解借用检查器才能写出第一个正确的程序；老手需要表达复杂不变量时，有 trait 和泛型兜底。Maxx 不追求"一行代码能干多少事"的极致（那是给机器看的），而追求"一行代码多快能被人读懂"。

### 0.4 三、透明无隐（No Hidden Magic）

**编译器做的事，用户从代码里能看出来、能预测。** 隐式，是语言复杂性的最大来源。Python 的 `__init__`/`__new__` 隐式构造、JavaScript 的原型链怪异行为、C++ 的隐式类型转换——这些"魔法"让代码在 80% 的情况下省事，但在 20% 的情况下让程序员调试到深夜。Maxx 的态度是：**凡是编译器偷偷做的事，都应当在代码里显式写出来**。

这条原则最著名的落地就是"三个绝不"：绝不有 `null`（可空即 `?T`，编译期强制解包）、绝不隐式数字转换（`int` 和 `f64` 必须显式 `int(x)`/`f64(x)`）、绝不宏。它还要求 `self` 必须显式写在方法参数里（不像某些语言把 `this` 藏起来）；要求类型转换必须用 `as` 而不是自动发生；要求错误必须用 `Result` 显式返回而不是抛一个看不见的异常。

"透明无隐"的代价是表面上多写几行。但这几行换来的是**可预测性**：程序员看一行代码，不需要知道"这个类型在标准库里有没有偷偷定义一个隐式转换"，就能准确预测它的行为。可预测性，在大型系统里，是比"少写两行"宝贵得多的品质。

### 0.5 四、万物一理（One Rule for All）

**用最少的规则解释最多的概念。** 语言设计里最浪费的事，是为相似的概念发明不同的规则。Maxx 坚持：函数就是值（`fn(A)->R` 是一等类型，可以传参、可以返回）、错误就是值（`Result<T,E>` 不是异常，它和 `?T` 一样是普通的代数数据类型）、并发就是通道（`chan T` 就是一个类型，不是第二套并发机制）、模块就是文件（一个 `.max` 对应一个模块，没有"包"和"模块"两套概念）。

这条原则的关键推论是"不做特殊情况"。Maxx 没有第二套错误处理（不像 Java 既有受检异常又有运行时异常）；没有第二套并发模型（不像某些语言既有线程又有 async/await 又有 actor）；没有第二套内存规则（不像有些语言值类型和引用类型各有各的生命周期）。`match` 一个结构同时完成"拆 ADT、处理可选、处理结果"三件事——因为它们本质上都是"代数数据类型的分支"。`task` 就是"函数调用加调度"——它和普通函数调用长一样，只是多了一个并发语义。

"万物一理"让语言的认知负担骤降：学会一个规则，就能用在三个地方。这比"学会三个规则，每个规则用在一个地方"要高效得多——尤其对一个团队而言。

### 0.6 五、涌现之美（Beauty by Emergence）

**不堆砌特性，让少量规则组合涌现出大表达力。** Maxx 的核心原语只有六个：类型、函数、ADT、`match`、`chan`、`task`。剩下的表达力全靠这六个原语的组合涌现出来——不需要 60 个关键字，不需要 20 个互相叠加的特性，不需要"设计模式"作为补偿。

这背后是一种对"语言丰富度"的重新理解。C++ 之所以复杂，不是因为它有太多"必须有的特性"，而是因为它在不同年代往上叠加了太多"当时觉得有用"的特性，彼此之间没有统一的原理。Maxx 反过来：先把六个原语设计到极致一致，再让它们组合。一个典型例子：没有继承，没有面向对象的那一套"多态 + 虚函数 + 访问修饰符"，而是用泛型 + trait + ADT 覆盖 95% 的场景。前者是"特性堆叠"，后者是"原理涌现"——后者更难设计，但用起来更优雅。

"涌现之美"也意味着 Maxx 拒绝"为了 5% 的场景加一个语法"。每一个新语法都要回答：它是不是可以用现有原语的组合表达？如果是，就不加。这让 Maxx 的关键字数量刻意压在 30 个以内，成为一门"小而美"的语言。

### 0.7 六、诚实即高效（Honesty is Efficiency）

**类型诚实、错误显式、依赖清晰——不偷偷做事。** 这条原则听起来像"工程纪律"，但它有一个非常实际的推论：**表面上多写的几行，换来编译器能在编译期静态消除 90% 的运行时开销**。

没有 `null`，编译器就不需要插入运行时空指针检查——它在编译期证明"这里不可能为空"。没有隐式窄化，编译器就不需要插入运行时精度检查——它在编译期证明"这里不会丢精度"。没有异常栈展开，编译器就不需要维护异常表和展开表——错误就是普通返回值，走寄存器或栈帧即可。这就是"诚实即高效"的核心：**程序员诚实地把约束写出来，编译器就诚实地把约束消化掉，运行时代码就不需要再为"可能的欺骗"付费**。

这条原则解释了 Maxx 为什么选择引用计数 + 分代循环回收而不是全停顿 GC：引用计数是"诚实"的——它在每次赋值时明确告诉你"这个引用多了一个"，在每次 drop 时明确告诉你"这个引用少了一个"。全停顿 GC 则是"偷偷"的——它在你不知道的时刻停下来扫描堆。对移动端（电池敏感、时延敏感）而言，"诚实"的引用计数比分代 GC 更合适。

### 0.8 与现有语言的哲学标签对比

| 语言 | 哲学标签 | 它在两难里选了哪一边 | Maxx 的评价 |
|---|---|---|---|
| Python | "There should be one obvious way" | 简单优先，放弃运行效率 | 简单值得借鉴，但运行时妥协不接受 |
| Go | "Less is more" | 工程简单，放弃类型表达力 | 简洁值得借鉴，但 ADT/trait 不能少 |
| Rust | "Fearless concurrency" | 安全优先，把借用检查负担推给用户 | 安全值得借鉴，但不应让用户当编译器的搬运工 |
| Haskell | "Pure functions as mathematics" | 纯粹优先，把人挡在门外 | 数学优美值得借鉴，但门槛不能高到劝退 |
| Java | "Write once, run anywhere" | 生态与兼容优先，三十年历史包袱 | 跨平台值得借鉴，但不应累积包袱 |
| **Maxx** | **"人写得少，机器做得多，但一切透明"** | 拒绝二选一 | 这是它自己的标签 |

> **Maxx 之道的一句话总结**：人写得少（简而有力、人即度量），机器做得多（透明无隐、诚实即高效），但一切透明（万物一理、涌现之美）。这三者缺一，就不是 Maxx。

---

## 1. 设计理念与语言特色

### 1.1 一句话定位

**Maxx** = Maximum simplicity × Maximum efficiency。

一门 **静态强类型、缩进分块、无空值、代数数据类型（ADT）内置、可 AOT 编译为原生码、移动端与桌面端同源** 的高级语言。

它不是"再做一门 C"，也不是"又一个脚本语言"。Maxx 的目标是：让一个初学者在 30 分钟内写出第一个正确的程序，同时让一个资深工程师写出与 C/Rust 同一量级运行效率的原生二进制——并且这两件事用的是**同一套语法、同一套标准库、同一个 `.smx` 产物**。

### 1.2 三个"绝不"（Non-Negotiables）

1. **绝不有 `null` / `nil`**。可空即 `?T`，编译期强制解包。没有空指针异常，没有 `NullReferenceException`。`nil_` 关键字仅在编译器内部保留，用户代码中永远不可见、不可写。
2. **绝不隐式数字转换**。`int` 与 `f64` 必须显式 `int(x)` / `f64(x)`；`i32` 与 `i64` 必须显式 `i64(x)`。每一次窄化、每一次精度损失都是一次显式书写。
3. **绝不宏**。元编程用编译期求值（`comptime`）与泛型实例化，不用文本替换宏。没有"宏展开后到底生成了什么"的不确定性。

### 1.3 设计支柱（Pillars）

| 支柱 | 含义 |
|---|---|
| **Simplicity（简单）** | 关键字数量刻意压到 30 个以内；无分号强制、无花括号竞争、无借用检查器、无宏卫生问题。一个概念只对应一种写法。 |
| **Safety（安全）** | 编译期消除空值、消除未初始化变量、消除隐式窄化；运行期只保留数组越界 panic 一类"无法在编译期证明"的错误。 |
| **Efficiency（高效）** | AOT 到原生码；值类型默认栈分配；引用计数 + 分代循环回收；无 GC 全停顿；无运行时反射开销。 |
| **Portability（同源）** | 同一份 `.max` 源码，编译后可以跑在 Windows / macOS / Linux 桌面，也可以打包进 Android APK、iOS Xcode 工程，甚至编译成 WASM 跑在浏览器里。 |
| **Expressiveness（表达力）** | ADT + 模式匹配 + 管道 `|>` + 可选/结果类型，让"不可能的状态不可表示"成为默认，而不是训练有素后的纪律。 |

### 1.4 特色符号（为什么是这些符号）

Maxx 故意使用了一组与主流 C 系语言不同的"声明符号"，目的是在阅读代码时**一眼区分"声明"与"调用"**：

| 符号 | 含义 | 为什么这么设计 |
|---|---|---|
| `@` | 声明函数 / 方法（`@ main()`） | `@` 在键盘左手区，敲一次就到位；视觉上像"新的入口"。 |
| `#` | 声明类型（`# Point:`、`# Shape:`） | `#` 让"类型块"在长文件里跳读时极其醒目。 |
| `~` | 声明导入（`~ std.io`） | `~` 像"把东西拉进来"。 |
| `::` | 命名空间路径（`std.math::sqrt`、`Point::dist`） | 与 `::` 调用区分开——`. ` 是实例方法，`::` 是关联函数/模块项。 |
| `=>` | lambda（`x => x + 1`） | 与 Rust/ML 家族一致，学习曲线最低。 |
| `?` | 可选类型后缀（`?int`）与错误传播（`expr?`） | 把"可空"和"错误传播"两个概念用同一个符号家族表达，降低心智负担。 |
| `|>` | 管道（`data |> filter(...) |> map(...)`） | 让链式调用从"左→右"读起来自然。 |
| `:` | 类型标注 + 块引导（`x: int`、`if cond:`） | 一个符号承担两个高频角色，减少符号总数。 |

### 1.5 与其他语言的差异速览

| 维度 | Python | Go | Rust | C | **Maxx** |
|---|---|---|---|---|---|
| 类型检查 | 动态 | 静态 | 静态（借用检查） | 静态 | 静态推断，无借用检查 |
| 空值 | `None` 运行时炸 | `nil` 运行时炸 | `Option<T>` | `NULL` | `?T` 编译期强制 |
| 错误处理 | 异常 | `if err != nil` | `Result` + `?` | errno | `Result` + `?`，无异常栈展开 |
| ADT / 模式匹配 | 无 | 无 | enum + match | 无 | 原生 `enum` + `match` |
| 内存管理 | GC 全停顿 | GC 全停顿 | 编译期借用 | 手动 free | 引用计数 + 分代循环回收 |
| 并发模型 | 线程 + GIL | goroutine + chan | async/await | pthread | task + chan + select |
| 元编程 | 装饰器 | 无 | 宏 | 宏 | `comptime` 求值 + 泛型实例化 |
| 语法块 | 缩进 | 花括号 | 花括号 | 花括号 | **缩进（offside rule）** |
| 数字隐式转换 | 随意 | 无 | 无 | 随意 | **绝不** |
| 移动端 | 打包麻烦 | NDK 麻烦 | NDK 麻烦 | NDK 麻烦 | **`.smx` 同源嵌入** |
| 共享库格式 | `.pyc` 字节码 | `.so`/`.a` 原生库 | `.rlib`/`.so` | `.so`/`.a` | **`.mxx`（自带类型元数据与 GC 绑定）** |
| AOT 原生码 | 否 | 是 | 是 | 是 | 是（`.max` → `.mxx` 原生库） |

Maxx 不试图在任何一个维度上"做到世界第一"。它的赌注是：**把上述这些维度里最被工程师认可的那几个选择，用最少的语法符号整合到一起**。

---

## 2. 词法规则（Lexer）

### 2.1 源文件编码

- 源文件 `.max` 使用 **UTF-8** 编码，无 BOM。
- 行结束符：`\n`（LF）；CRLF（`\r\n`）在词法阶段被规整化为 LF。
- Tab 字符禁止出现在缩进中（仅允许 4 空格）。Tab 出现在非缩进位置是词法错误。

### 2.2 关键字（Keywords）

全部关键字均为小写字母，共 **30 个**：

```
if  elif  else  for  while  loop  match  ret  let  var
as  is  in  trait  enum  struct  fn  type  import  from
pub  priv  task  chan  comptime  true  false  none  some
ok  err  try  break  continue  do  nil_
```

> 说明：`fn`、`struct`、`import`、`from`、`type` 是**保留关键字**，但在语法示例与最终推荐写法中，实际声明符号是 `@`（函数）、`#`（类型）、`~`（导入）。保留它们是为了：(a) 让从 C/Java 转来的工程师在文档里能"猜"到语义；(b) 未来若开启"兼容模式"可降级使用。普通 Maxx 代码不使用它们。
>
> `nil_` 仅编译器内部可见，用户源码中出现即报词法错误。

### 2.3 标识符（Identifiers）

- 首字符：ASCII 字母 `a-z A-Z` 或下划线 `_`。
- 后续字符：ASCII 字母、数字 `0-9`、下划线 `_`。
- 风格约定（编译器不强制，但 `maxx lint` 会警告）：
  - 类型名 / trait 名：大驼峰，如 `Point`、`Vec3`、`Readable`。
  - 函数 / 变量：小驼峰，如 `readFile`、`totalSum`。
  - 常量：全大写下划线，如 `MAX_LEN`、`PI`。
  - 以 `_` 开头的标识符表示"故意未使用"，编译器对其不报"未使用变量"警告。
- 标识符最大长度：255 字符（UTF-8 码点），超过即报错。
- 运算符重载标识符：`@add`、`@mul`、`@eq` 等（见 §5.7）。

### 2.4 字面量（Literals）

#### 2.4.1 整数字面量

| 形式 | 示例 | 推断类型 |
|---|---|---|
| 十进制 | `42`、`-7` | `int`（即 i64） |
| 十六进制 | `0xFF`、`0xDEAD_BEEF` | `int` |
| 八进制 | `0o755` | `int` |
| 二进制 | `0b1010`、`0b1111_0000` | `int` |
| 带类型后缀 | `42i32`、`7u64`、`100_000u32` | 显式指定 |

- 数字中间允许插入 `_` 作为分隔符（仅美观，词法上等同无下划线）。
- 整数字面量在不溢出的前提下，会根据上下文自动"加宽"——例如赋给 `i32` 的 `255` 是合法的；但一旦溢出即报编译期错误（绝不静默回绕）。

#### 2.4.2 浮点字面量

| 形式 | 示例 | 推断类型 |
|---|---|---|
| 普通小数 | `3.14`、`.5`、`2.` | `f64` |
| 科学计数 | `1e5`、`2.5E-3` | `f64` |
| 带后缀 | `2.0f32`、`1.5f64` | 显式指定 |

- IEEE 754 双精度（f64）/ 单精度（f32）。
- 特殊值：`f64::inf`、`f64::neg_inf`、`f64::nan`（通过关联常量获取，不是字面量）。

#### 2.4.3 字符串字面量

- 普通字符串：`"hello\nworld"`，支持转义 `\n \t \r \\ \" \0 \xNN \uNNNN \UNNNNNNNN`。
- 原始字符串：`` `raw \n 不转义` ``，反引号之间的所有字符（除了反引号本身）原样保留，包括换行。
- 插值字符串：`f"x = {x}, y = {y + 1}"`，花括号内是任意表达式。
- 多行字符串：三个双引号 `"""\n  ...\n"""`，公共缩进按首行 `"""` 后的缩进对齐剥离。

#### 2.4.4 字符字面量

- `'a'`、`'\n'`、`'\u4e2d'`，类型恒为 `char`（32 位 Unicode 码点）。
- 不支持 C 那种 `'ab'` 多字符字符常量。

#### 2.4.5 布尔与单元

- `true` / `false`：类型 `bool`。
- 空元组 `()`：类型 `()`（单元类型，类似 void，但它是一个真正的值，可以被返回、被存储）。

#### 2.4.6 可选与结果字面量构造器

- `none`：`?T` 的"空"分支（具体 T 由上下文推断）。
- `some(v)`：`?T` 的"有值"分支。
- `ok(v)`：`Result<T,E>` 的成功分支。
- `err(e)`：`Result<T,E>` 的失败分支。

> `some` / `ok` / `err` 在词法上是**关键字**而不是普通函数，以便编译器在类型推断阶段把它们识别为 ADT 构造器，而不是等待重载决议。

### 2.5 运算符（Operators）

按优先级从高到低排列（同一行优先级相同）：

| 优先级 | 类别 | 运算符 | 结合性 |
|---|---|---|---|
| 16（最高） | 后缀 | `.` `::` `()` `[]` | 左结合 |
| 15 | 单目前缀 | `-` `!` `~`（按位取反） `*`（解引用） `&`（取地址/借用） | 右结合 |
| 14 | 乘除模 | `*` `/` `%` `//`（整除） | 左结合 |
| 13 | 加减 | `+` `-` | 左结合 |
| 12 | 移位 | `<<` `>>` | 左结合 |
| 11 | 比较 | `<` `<=` `>` `>=` `is` `as` | 左结合 |
| 10 | 相等 | `==` `!=` | 左结合 |
| 9 | 按位与 | `&` | 左结合 |
| 8 | 按位异或 | `^` | 左结合 |
| 7 | 按位或 | `|` | 左结合 |
| 6 | 逻辑与 | `&&` | 左结合（短路） |
| 5 | 逻辑或 | `||` | 左结合（短路） |
| 4 | 三目 | `? :` | 右结合 |
| 3 | 管道 | `|>` | 左结合 |
| 2 | 赋值 | `=` `+=` `-=` `*=` `/=` `%=` `<<=` `>>=` `&=` `^=` `|=` | 右结合 |
| 1（最低） | 块级 | `,` `:` `;` | — |

管道 `|>` 的语义：`a |> f` 等价于 `f(a)`；`a |> f(x)` 等价于 `f(a, x)`；`a |> f(x, y)` 等价于 `f(a, x, y)`。也就是说，左侧表达式作为右侧函数调用的**第一个位置参数**注入。

`is` 运算符用于动态类型判断（`x is ?int`、`x is Shape`）；`as` 用于显式类型转换（见 §5.6）。

### 2.6 分隔符与结构符号

- `()`：表达式分组、函数参数列表、元组。
- `[]`：索引、数组/切片字面量 `[1, 2, 3]`。
- `{}`：结构体字面量 `Point{x: 1, y: 2}`、块表达式。
- `:`：类型标注（`x: int`）、块引导（`if cond:`、`# Point:`、`@ main():`）。
- `::`：命名空间 / 关联项路径分隔。
- `,`：参数分隔、列表分隔。
- `;`：行内多语句分隔（可选；一行只写一条语句时可省略）。
- `=>`：lambda 箭头、match 分支（`Pattern => expr`）。
- `.`：字段访问 / 实例方法调用。
- `..` `..=`：半开区间 `0..n`、闭区间 `0..=n`。

### 2.7 注释

- 行注释：`// 注释`。
- 块注释：`/* ... */`，**可嵌套**。
- 文档注释：
  - `/// 公共 API 文档`——紧邻其后的 `pub` 项。
  - `//! 模块级文档`——放在文件顶部，描述整个模块。
  - 文档注释支持 Markdown 子集，`maxx doc` 会抽取并生成 HTML。

### 2.8 缩进与 offside rule

- 块由 `:` 引导，其后必须换行并**多缩进至少 1 个 4 空格层级**。
- 同一层的语句必须严格对齐（同列）。
- 反缩进回到上一层即表示块结束。
- 允许在括号/方括号/花括号内跨行而**不**触发 offside（"括号内换行自由"）。
- 空行与纯注释行不影响缩进层级。

---

## 3. 完整语法（EBNF）

> **设计决策溯源**：本章的语法选择呼应"简而有力"（§0.2）与"人即度量"（§0.3）。`@` 声明函数、`#` 声明类型、`~` 声明导入——三个符号一眼区分"声明"与"调用"，让人在长文件里跳读时极其醒目。缩进分块让人一眼看出嵌套层次，不需要数花括号。关键字压到 30 个以内，是"涌现之美"（§0.6）的直接体现。

本节用扩展巴科斯-瑙尔范式（EBNF）给出 Maxx v1.0 的完整语法。约定：

- 大写非终结符：`Program`、`Expr`、`Stmt` 等。
- 小写终结符：`if`、`+`、`IDENT`、`INT_LIT` 等。
- `|`：选择；`[ x ]`：可选；`{ x }`：零次或多次；`( x )`：分组。
- 词法符号以全大写表示：`IDENT`、`INT`、`FLOAT`、`STRING`、`CHAR`、`TRUE`、`FALSE` 等。

### 3.1 程序与文件

```ebnf
Program        ::= { TopLevelItem } EOF ;
TopLevelItem    ::= ImportDecl
                 | FuncDecl
                 | TypeDecl
                 | TraitDecl
                 | PubItem
                 | DocCommentLine
                 | ComptimeBlock ;

PubItem         ::= "pub" ( FuncDecl | TypeDecl | TraitDecl | ConstDecl ) ;
ConstDecl       ::= "let" IDENT ":" Type "=" Expr ;
```

### 3.2 导入与导出

```ebnf
ImportDecl      ::= "~" Path [ "as" IDENT ] ;
Path            ::= IDENT { "::" IDENT } ;
```

例：`~ std.io`、`~ std.math::sqrt`、`~ collections::Vec as V`。

### 3.3 函数声明

```ebnf
FuncDecl        ::= "@" [ Receiver ] IDENT [ GenericParams ]
                    "(" [ ParamList ] ")" [ "->" Type ] ":"
                    Block ;
Receiver        ::= IDENT "::" ;
GenericParams   ::= "<" IDENT { "," IDENT } [ TraitBound ] ">" ;
TraitBound      ::= ":" IDENT { "+" IDENT } ;
ParamList       ::= Param { "," Param } [ "," ] ;
Param           ::= IDENT ":" Type [ "=" Expr ] ;
Block           ::= IndentedStmtList ;
```

例：

```
@ Point::dist(self: Point, o: Point) -> f64:
    ret sqrt((self.x - o.x)^2 + (self.y - o.y)^2)

@ identity<T>(x: T) -> T:
    ret x
```

### 3.4 类型声明（struct / enum / ADT）

```ebnf
TypeDecl        ::= "#" IDENT [ GenericParams ] ":" TypeBody ;
TypeBody        ::= StructBody | EnumBody ;
StructBody      ::= IndentedFieldList ;
IndentedFieldList ::= { FieldDecl } ;
FieldDecl       ::= IDENT ":" Type ;
EnumBody        ::= IndentedVariantList ;
IndentedVariantList ::= { VariantDecl } ;
VariantDecl     ::= IDENT [ "(" [ TypeList ] ")" ] ;
TypeList        ::= Type { "," Type } ;
```

例：

```
# Point:
    x: f64
    y: f64

# Shape:
    Circle(r: f64)
    Rect(w: f64, h: f64)
    Dot
```

### 3.5 trait 声明

```ebnf
TraitDecl       ::= "trait" IDENT [ GenericParams ] ":"
                    { TraitMethodSig } ;
TraitMethodSig  ::= "@" IDENT "(" [ ParamList ] ")" [ "->" Type ] ;
```

例：

```
trait Hashable:
    @ hash(self: Self) -> u64
    @ eq(a: Self, b: Self) -> bool
```

### 3.6 语句

```ebnf
Stmt            ::= LetStmt | VarStmt | AssignStmt
                 | IfStmt | WhileStmt | ForStmt | LoopStmt
                 | MatchStmt | RetStmt | BreakStmt | ContinueStmt
                 | TaskStmt | ChanStmt
                 | ExprStmt
                 | Block ;

LetStmt         ::= "let" Pattern [ ":" Type ] "=" Expr ;
VarStmt         ::= "var" Pattern [ ":" Type ] "=" Expr ;
AssignStmt      ::= UnaryExpr AssignOp Expr ;
AssignOp        ::= "=" | "+=" | "-=" | "*=" | "/=" | "%="
                 | "<<=" | ">>=" | "&=" | "^=" | "|=" ;

IfStmt          ::= "if" Expr ":" Block
                    { "elif" Expr ":" Block }
                    [ "else" ":" Block ] ;

WhileStmt       ::= "while" Expr ":" Block ;
LoopStmt        ::= "loop" ":" Block ;
ForStmt         ::= "for" Pattern "in" Expr ":" Block ;

MatchStmt       ::= "match" Expr ":" { MatchArm } ;
MatchArm        ::= Pattern [ "if" Expr ] "=>" Expr
                  | Pattern [ "if" Expr ] ":" Block ;

RetStmt         ::= "ret" [ Expr ] ;
BreakStmt       ::= "break" [ Expr ] ;
ContinueStmt    ::= "continue" ;

TaskStmt        ::= "task" CallExpr ;
ChanStmt        ::= "var" IDENT "=" "chan" Type ;

ExprStmt        ::= Expr ;
```

### 3.7 表达式（按优先级递归）

```ebnf
Expr            ::= PipeExpr ;
PipeExpr        ::= AsExpr { "|>" AsExpr } ;
AsExpr          ::= CondExpr [ ("is" | "as") Type ] ;
CondExpr        ::= OrExpr [ "?" Expr ":" OrExpr ] ;
OrExpr          ::= AndExpr { "||" AndExpr } ;
AndExpr         ::= BitOrExpr { "&&" BitOrExpr } ;
BitOrExpr       ::= BitXorExpr { "|" BitXorExpr } ;
BitXorExpr      ::= BitAndExpr { "^" BitAndExpr } ;
BitAndExpr      ::= EqExpr { "&" EqExpr } ;
EqExpr          ::= CmpExpr [ ("==" | "!=") CmpExpr ] ;
CmpExpr         ::= ShiftExpr [ ("<" | "<=" | ">" | ">=") ShiftExpr ] ;
ShiftExpr       ::= AddExpr [ ("<<" | ">>") AddExpr ] ;
AddExpr         ::= MulExpr { ("+" | "-") MulExpr } ;
MulExpr         ::= UnaryExpr { ("*" | "/" | "%" | "//") UnaryExpr } ;
UnaryExpr       ::= ("-" | "!" | "~" | "*" | "&") UnaryExpr
                 | PostfixExpr ;
PostfixExpr     ::= Primary { "." IDENT | "::" IDENT | CallArgs | "[" Expr "]" } ;
```

### 3.8 基本表达式

```ebnf
Primary         ::= Literal
                 | IDENT
                 | "(" [ ExprList ] ")"          // 括号或元组
                 | "[" [ ExprList ] [ "..." Expr ] "]"   // 数组/切片
                 | StructLit
                 | Lambda
                 | RangeExpr
                 | ComptimeExpr
                 | "(" Expr ")" ;

Literal         ::= INT | FLOAT | STRING | CHAR | TRUE | FALSE
                 | "none" | "some" "(" Expr ")"
                 | "ok" "(" Expr ")" | "err" "(" Expr ")" ;

CallArgs        ::= "(" [ ArgList ] ")" ;
ArgList         ::= Expr { "," Expr } [ "," ] ;
StructLit       ::= Path "{" [ FieldInitList ] "}" ;
FieldInitList   ::= FieldInit { "," FieldInit } [ "," ] ;
FieldInit       ::= IDENT ":" Expr | IDENT ;

Lambda          ::= "(" [ ParamList ] ")" "=>" Expr
                 | IDENT "=>" Expr ;

RangeExpr       ::= Expr (".." | "..=") Expr ;

ComptimeExpr    ::= "comptime" Block ;
```

### 3.9 模式（Pattern）

```ebnf
Pattern         ::= LitPattern
                 | WildPattern            // _
                 | IdentPattern           // x
                 | EnumPattern            // Variant(...) / Variant
                 | StructPattern          // Point{x, y}
                 | TuplePattern
                 | OptionalPattern        // some(p) / none
                 | ResultPattern           // ok(p) / err(p)
                 | BindingPattern          // x @ Pattern
                 | OrPattern               // P1 | P2 ;

WildPattern     ::= "_" ;
EnumPattern     ::= Path [ "(" [ PatternList ] ")" ] ;
StructPattern   ::= Path "{" [ FieldPatternList ] "}" ;
FieldPatternList ::= Pattern { "," Pattern } [ "," ] ;
PatternList     ::= Pattern { "," Pattern } [ "," ] ;
TuplePattern    ::= "(" [ Pattern { "," Pattern } [ "," ] ")" ;
BindingPattern  ::= IDENT "@" Pattern ;
OrPattern       ::= Pattern "|" Pattern ;
```

### 3.10 类型表达式

```ebnf
Type            ::= Path [ GenericArgs ]
                 | "?" Type
                 | "Result" "<" Type "," Type ">"
                 | "chan" Type
                 | "fn" "(" [ TypeList ] ")" "->" Type
                 | "(" [ TypeList ] ")"          // 元组 / 单元
                 | Type "[" INT "]"               // 定长数组
                 | "[" Type "]" ;                 // 切片
GenericArgs     ::= "<" Type { "," Type } ">" ;
```

### 3.11 一个完整可解析例子

```max
~ std.io
~ std.math::sqrt
~ std.collections::Vec

# Point:
    x: f64
    y: f64

@ Point::dist(self: Point, o: Point) -> f64:
    ret sqrt((self.x - o.x)^2 + (self.y - o.y)^2)

@ main() -> int:
    let p = Point{x: 3.0, y: 4.0}
    let q = Point{x: 0.0, y: 0.0}
    io.println("dist = " + str(p.dist(q)))
    ret 0
```

---

## 4. 类型系统

> **设计决策溯源**：本章的类型系统选择呼应"诚实即高效"（§0.7）与"万物一理"（§0.5）。`?T` 强制解包让编译器在编译期消灭空指针；`Result<T,E>` 不是异常而是普通值；绝不隐式数字转换让编译器消灭精度丢失。泛型单态化（monomorphization）让性能等于手写 C——这是"简而有力"（§0.2）在类型系统上的落地：用户写泛型，编译器背后做单态化。

### 4.1 内置标量类型

| 类型 | 位宽 | 说明 |
|---|---|---|
| `bool` | 1 | `true` / `false` |
| `i8` | 8 | 有符号字节 |
| `i16` | 16 | 有符号短整型 |
| `i32` | 32 | 有符号整型 |
| `i64` | 64 | 有符号长整型 |
| `int` | 64 | 平台默认有符号整数（在 64 位平台等同 `i64`） |
| `u8` | 8 | 无符号字节 |
| `u16` | 16 | 无符号短整型 |
| `u32` | 32 | 无符号整型 |
| `u64` | 64 | 无符号长整型 |
| `usize` | 平台 | 与指针同宽，用于数组索引 |
| `isize` | 平台 | 与指针同宽的有符号整数 |
| `f32` | 32 | IEEE 754 单精度浮点 |
| `f64` | 64 | IEEE 754 双精度浮点（默认浮点） |
| `char` | 32 | Unicode 码点（不是字节） |
| `str` | 引用 | UTF-8 不可变字符串切片 |
| `()` | 0 | 单元类型（类似 void，但它是值） |
| `?T` | — | 可选类型（Some / None） |
| `Result<T,E>` | — | 结果类型（Ok / Err） |
| `chan T` | — | 通道类型 |
| `fn(A...) -> R` | — | 函数类型 |

### 4.2 引用类型与容器

| 类型 | 说明 |
|---|---|
| `Box<T>` | 显式堆分配的拥有者指针，离开作用域自动 drop |
| `&T` / `&mut T` | 不可变 / 可变借用（编译期借用检查仅保证"同一时刻要么一个 mut 要么多个 &"，不做生命周期标注） |
| `Vec<T>` | 动态数组（标准库） |
| `String` | 可增长 UTF-8 字符串（标准库） |
| `Map<K,V>` | 哈希表（标准库） |
| `Set<T>` | 哈希集合（标准库） |
| `Deque<T>` | 双端队列（标准库） |
| `SortedMap<K,V>` | 有序映射（标准库） |
| `[T; N]` | 定长数组（栈分配） |
| `[T]` | 动态切片（视图） |

### 4.3 类型推断

- `let x = 42` → `int`；`var y = 1.0` → `f64`。
- `let b = true` → `bool`；`let c = '中'` → `char`。
- 函数参数与返回值**必须显式标注类型**（公共 API 可读性优先；局部表达式可省略）。
- 泛型参数由调用点推断：`identity(42)` → `T = int`。
- 当推断出现歧义时（例如 `let x = none`），编译器报错并要求显式标注：`let x: ?int = none`。

### 4.4 静态 vs 动态

Maxx 是**静态强类型**语言。所有类型错误在编译期报告。运行时仅保留以下错误：

- 数组越界访问（可通过 `maxx build --checked off` 关闭，对应 C 风格 UB）。
- 对 `?T` 的 `unwrap()` 在 `none` 上调用。
- 对 `Result` 的 `unwrap()` 在 `err` 上调用。
- 整数除法 / 取模为零（编译期无法证明时）。
- 这些运行时错误一律走 `panic!`，不展开异常。

### 4.5 泛型

```max
@ identity<T>(x: T) -> T:
    ret x

@ pair<A, B>(a: A, b: B) -> (A, B):
    ret (a, b)

# Box<T>:
    inner: T
```

- 泛型在编译期**单态化（monomorphization）**：每个具体类型实例化出一份机器码。无虚表开销。
- trait 约束：`fn max<T: Ord>(a: T, b: T) -> T`。
- 泛型 trait：`trait Iterator<T>: ...`。

### 4.6 代数数据类型（ADT）与模式匹配

```max
# Shape:
    Circle(r: f64)
    Rect(w: f64, h: f64)
    Dot

@ area(s: Shape) -> f64:
    match s:
        Circle(r):   ret 3.14159265 * r * r
        Rect(w, h):  ret w * h
        Dot:         ret 0.0
```

- `match` 必须**穷尽**所有分支；编译器检查"覆盖率"。遗漏分支即编译错误。
- 支持 `_` 通配、`or` 模式（`A | B`）、绑定（`x @ Pattern`）、守卫（`Pattern if cond`）。
- 解构嵌套 ADT、struct、元组、数组。

### 4.7 trait 与运算符重载

```max
trait Hashable:
    @ hash(self: Self) -> u64

# Point:
    x: f64
    y: f64

impl Hashable for Point:
    @ hash(self: Point) -> u64:
        ret (self.x.to_bits() as u64) ^ (self.y.to_bits() as u64)
```

- 运算符重载通过特定 trait 名实现：`@add(a, b)`、`@mul`、`@eq`、`@lt`、`@index` 等。
- trait 可以有默认方法。
- trait 对象 `&dyn Drawable` 可用于运行时分派（当静态单态化不必要时）。

### 4.8 类型转换（`as`）

- `as` 是**显式、截断行为定义良好**的转换：
  - 整数 → 整数：窄化按模 2^N 截断；加宽按符号扩展（有符号）或零扩展（无符号）。
  - 浮点 → 整数：向零截断；`nan` → 0；`inf` / `-inf` → 目标类型极值。
  - 整数 → 浮点：不能精确表示时按 round-to-nearest-even。
  - `char` ↔ `i32`（码点）。
- **绝不**隐式转换。`1 + 1.0` 是编译错误；必须写 `1 + int(1.0)` 或 `int(1) + 1.0`。

### 4.9 类型类（`is` 动态判断）

`is` 用于在 trait 对象或 `?dyn` 上做运行时类型测试：

```max
@ describe(x: &dyn Any) -> str:
    if x is ?int:
        ret "an int"
    elif x is ?str:
        ret "a str"
    else:
        ret "something else"
```

---

## 5. 语义规则

> **设计决策溯源**：本章的并发模型（task + chan）呼应"万物一理"（§0.5）——并发不是第二套模型，`chan T` 就是一个普通类型，`task` 就是函数调用加调度。`comptime` 编译期求值呼应"透明无隐"（§0.4）——元编程不是文本宏，而是"在编译期跑 Maxx 代码"，一切透明可预测。

### 5.1 作用域与绑定

- **块级作用域**：每个 `:` 引导的块引入新作用域。
- **词法作用域**：内层可访问外层绑定；同名内层遮蔽外层。
- **声明提升**：`let` / `var` 不提升；首次使用前必须初始化。
- **常量**：`let` 在模块级且无副作用初始化时即编译期常量；`comptime` 块内强制编译期求值。
- **`self`**：方法的第一个参数固定为 `self`（值接收者）或 `&self` / `&mut self`（借用接收者）。

### 5.2 所有权与借用（简化版）

Maxx **没有 Rust 那种生命周期标注**，但保留了核心安全规则：

- 值类型（struct / 枚举 / 数字 / char / 元组）默认**移动语义**：赋值、传参、返回即移动，原绑定失效。
- `&T` 是不可变借用；`&mut T` 是可变借用。编译器在函数级作用域内强制：**同一时刻，一个值要么有一个 `&mut`，要么有任意多个 `&`**。跨函数边界的借用通过生命周期"匿名标注"自动推导，不写出来。
- `Box<T>` 是显式堆拥有者；离开作用域自动调用析构。
- 没有 double-free，没有 use-after-free。

### 5.3 内存模型概览

- **栈**：局部值类型、`[T; N]` 定长数组、借用指针。
- **堆**：`Box<T>`、`Vec<T>`、`String`、`Map<K,V>`、ADT 中的堆字段。
- **引用计数**：所有堆对象头部有一个 `refcount` 字段；拷贝 `Box` / `Rc<T>` 即 `refcount += 1`；drop 时 `refcount -= 1`，归零即释放。
- **循环引用**：由分代循环 GC（见 §10）周期性扫描并断开。
- **析构时机**：确定性的 drop（作用域结束），不需要析构函数调用语法。

### 5.4 并发模型：task + chan

```max
@ worker(id: int, out: chan str):
    out.send("hello #" + str(id))

@ main() -> int:
    let ch = chan str
    task worker(1, ch)
    task worker(2, ch)
    io.println(ch.recv())
    io.println(ch.recv())
    ret 0
```

- `task f(args...)` 派生一个协程（M:N 调度到 OS 线程池）。
- `chan T` 是带缓冲或无缓冲通道；`send` / `recv` 是阻塞语义，但只阻塞当前 task，不阻塞 OS 线程。
- `select` 语句：

```max
select:
    ch1.recv() => msg1
    ch2.recv() => msg2
    _ => timeout
```

- 无数据竞争：通道是 task 间唯一安全的通信方式；共享内存需要 `Mutex<T>` / `RwLock<T>`（标准库）。

### 5.5 panic 语义

- `panic!("msg")` 立即终止当前 task；若是 main task，则打印堆栈并以非零状态退出进程。
- panic **不展开**栈；没有 `catch`。错误一律用 `Result<T,E>` 表达。
- 标准库所有"可能失败但不该 panic"的 API 都返回 `Result`。
- `panic!` 用于"不可恢复、编程错误"：越界、`unwrap()` on `none`、整数除零（运行期）、断言失败。

### 5.6 编译期求值（`comptime`）

```max
comptime:
    let N = 1024
    const TABLE = [i for i in 0..N]
```

- `comptime` 块在编译期执行；其中所有变量成为编译期常量。
- 泛型函数体在实例化时，若参数是 `comptime` 值，则整个表达式被折叠。
- 无文本宏；一切元编程通过"在编译期跑 Maxx 代码"实现。

### 5.7 运算符重载约定

| 运算符 | trait 方法名 |
|---|---|
| `+` | `@add` |
| `-` | `@sub` |
| `*` | `@mul` |
| `/` | `@div` |
| `%` | `@mod` |
| `==` | `@eq` |
| `!=` | `@ne`（默认 `!@eq`） |
| `<` `<=` `>` `>=` | `@lt` `@le` `@gt` `@ge` |
| `[]` | `@index` |
| `[]=` | `@index_set` |
| `()` | `@call` |

---

## 6. 模块系统与包管理

> **设计决策溯源**：本章的"四层文件格式"直接呼应 Maxx 之道的"万物一理"（§0.5）与"透明无隐"（§0.4）。`.max`（源）、`.mxx`（库）、`.smx`（包）、`.zip`（归档）四层各司其职，互不混淆——这就是"万物一理"在文件格式上的体现：每一层只做一件事，层与层之间的转换关系完全透明（`maxx build` / `maxx install` / `maxx pack`）。

### 6.1 模块 = 源文件

Maxx 的模块系统遵循一个简洁的设计：**一个 `.max` 源文件 = 一个模块**。

- 模块名 = 文件相对包根的路径（去掉 `.max`，`/` → `::`）。
- `src/geo/point.max` → 模块路径 `geo::point`。
- `.max` 是 UTF-8 文本，人类可读可编辑（详见 §9.1）。

### 6.2 导入与链接

```maxx
~ std.io                  // 导入整个模块，调用为 io.println(...)
~ std.math::sqrt          // 仅导入 sqrt，直接调用 sqrt(...)
~ std.collections::Vec as V   // 别名
```

- 未使用的导入是**警告**（不是错误）；`_` 前缀可抑制。
- `~ geo::point` 会在以下位置依次查找：
  1. 当前包的 `src/geo/point.max`（源码模式）；
  2. `.maxx/vendor/<pkg>/lib/<target>/geo_point.mxx`（已安装的 `.smx` 依赖解压出的共享库）；
  3. 标准库安装路径下的 `std/geo/point.max` 或 `lib/<target>/std_geo_point.mxx`。
- **链接语义**：编译期 `~ mylib::foo` 会查 `mylib.mxx` 的**导出符号表**（见 §9.2），把调用点链接到该库的导出符号；运行时通过 `dlopen`/`LoadLibrary` 等价接口动态加载 `.mxx`。

### 6.3 导出

- 项默认私有。
- `pub` 前缀导出：`pub # Point:`、`pub @ area(...)`。
- `pub(pkg)` 表示对整个包可见，对外部包不可见。
- 只有 `pub` 项才会进入 `.mxx` 的导出符号表。

### 6.4 包结构

```
myapp/
├── mod.max              # 包入口（必须）
├── maxx.toml            # 包元数据（名、版本、依赖、目标）
├── src/
│   ├── main.max
│   └── geo/
│       ├── mod.max
│       ├── point.max
│       └── shape.max
├── .maxx/               # 构建产物与 vendor 依赖（自动生成，可删除）
│   ├── build/           # 编译出的 .mxx
│   └── vendor/          # maxx install 解压的依赖
└── tests/
    └── geo_test.max
```

### 6.5 `maxx.toml`

```toml
[package]
name = "myapp"
version = "0.1.0"
edition = "2026"

[dependencies]
clii = { version = "1.2.0", registry = "maxx-pkgs" }

[build]
targets = ["desktop", "android", "ios", "wasm"]
opt-level = 3
```

### 6.6 构建命令

| 命令 | 作用 |
|---|---|
| `maxx build` | 编译 `.max` 源码为 `.mxx` 共享库（原生机器码 + 符号表 + 元数据） |
| `maxx build --exe` | 链接为平台原生可执行文件（AOT，静态链接运行时） |
| `maxx pack` | 把一个或多个 `.mxx` + `.max` 接口 + manifest 打包为 `.smx` 分发包 |
| `maxx install <pkg>` | 从 registry 拉取 `.smx`，解压到 `.maxx/vendor/<pkg>-<ver>/` |
| `maxx run` | 编译并运行 `src/main.max` |
| `maxx test` | 运行 `#[test]` 标记的函数 |
| `maxx doc` | 抽取文档注释生成 HTML |
| `maxx fmt` | 自动格式化 |
| `maxx lint` | 静态检查 |
| `maxx new myapp` | 新建包脚手架 |
| `maxx add <pkg>` | 添加依赖（写入 `maxx.toml`） |
| `maxx archive` | 将整个项目目录打包为 `.zip` 项目归档 |
| `maxx clean` | 清理构建产物（含 `.maxx/build/` 与 `.maxx/vendor/`） |

### 6.7 三层转换流程（`.max` → `.mxx` → `.smx` → `.zip`）

Maxx 的四层文件之间有清晰、透明的转换关系：

```
.max  ──maxx build──▶  .mxx  ──maxx pack──▶  .smx  ──maxx archive──▶  .zip
源码（人写）           共享库（机器码+元数据）    分发包（whl 式 zip）      项目归档（整包）
```

- **`.max` → `.mxx`**：`maxx build foo.max`。编译器把源码编译为原生共享库，内含机器码段、导出/导入符号表、类型元数据、GC 绑定（详见 §9.2）。
- **`.mxx` → `.smx`**：`maxx pack`。把一个或多个 `.mxx`（按 target 分目录）+ 公共 `.max` 头接口 + `manifest.json` 打成 zip 容器。这是"分发容器"，不是新语言格式。
- **`.smx` → 安装**：`maxx install mypkg`。解压到 `.maxx/vendor/mypkg-1.0.0/`，得到 `lib/<target>/mylib.mxx` 与 `include/mypkg/*.max`。`maxx build` 自动 `~` 链接 vendor 目录。
- **项目 → `.zip`**：`maxx archive`。把整个项目目录（`.max` 源码 + `.maxx/vendor/` 里已安装的 `.smx` 依赖 + README + examples/）打成归档。用户 `unzip myapp.zip && cd myapp && maxx run main.max` 即可运行。

> **为什么是四层而不是两层？** 因为"源码"、"可链接的原生库"、"可安装的包"、"可分发的整项目"是四个语义不同的概念。把它们混在一个文件里（像 v0.4 草案那样）会导致"改源码就要重编译"和"分发时还要带编译器"两个问题。四层分开后：开发者写 `.max`、链接器吃 `.mxx`、包管理器吃 `.smx`、最终用户吃 `.zip`——各取所需，互不干扰。

---

## 7. 标准库 API 完整清单

> **设计决策溯源**：标准库的设计呼应"万物一理"（§0.5）与"涌现之美"（§0.6）。所有容器都实现同一个 `Iter` trait，所有 IO 类型都实现同一个 `Read`/`Write` trait——学会一个迭代器适配器，就能用在 `Vec`、`Map`、文件流、网络流上。这就是"用最少的规则解释最多的概念"在标准库上的落地。

本章按模块列出 Maxx 标准库的全部公共 API。每个函数、方法、常量、类型都算一个"语法点"。本章 API 条目总数超过 3200 条。

**约定**：
- `T` / `K` / `V` 为泛型参数。
- 返回 `Result<T, E>` 的 API 表示可能失败；`?T` 表示可能为空。
- `self: T` 表示值接收者；`self: &T` 表示借用；`self: &mut T` 表示可变借用。
- 所有方法均在其所属类型/模块上调用。

### 8.1 `std.core`

语言内置、panic、断言、comptime 与核心类型转换函数。

| 签名 | 说明 |
|---|---|
| panic!(msg: str) | 立即 panic，打印消息与堆栈 |
| assert(cond: bool) | 断言，失败即 panic |
| assert_eq(a, b) | 断言两值相等 |
| assert_ne(a, b) | 断言两值不等 |
| debug_assert(cond) | 调试构建下断言，release 下移除 |
| unreachable!() | 标记不可达分支，命中即 panic |
| todo!() | 标记未实现，命中即 panic |
| unimplemented!() | 同 todo!() |
| str(v) -> String | 任意值转字符串 |
| int(v) -> i64 | 任意值转 i64 |
| i32(v) -> i32 | 任意值转 i32 |
| i64(v) -> i64 | 任意值转 i64 |
| u32(v) -> u32 | 任意值转 u32 |
| u64(v) -> u64 | 任意值转 u64 |
| f32(v) -> f32 | 任意值转 f32 |
| f64(v) -> f64 | 任意值转 f64 |
| bool(v) -> bool | 任意值转 bool |
| char(v) -> char | 任意值转 char |
| type_of(v) -> TypeId | 获取值的运行时类型 ID |
| comptime block | 编译期执行块 |
| size_of<T>() -> usize | 类型 T 的字节大小 |
| align_of<T>() -> usize | 类型 T 的对齐 |
| min(a, b) -> T | 泛型最小值 |
| max(a, b) -> T | 泛型最大值 |
| clamp(v, lo, hi) -> T | 夹取 |
| swap(a: &mut T, b: &mut T) | 交换两值 |
| ptr_eq(a: &T, b: &T) -> bool | 指针相等判断 |
| dbg(x: T) -> T | 调试打印并返回原值 |
| line!() -> u32 | 当前行号 |
| file!() -> &str | 当前文件路径 |
| column!() -> u32 | 当前列号 |

### 8.2 `std.prim`

所有标量类型的方法。整数类型族（i8/i16/i32/i64/u8/u16/u32/u64/usize/isize）共享同一套方法表，下表以 `Int` 代表任意整数类型。

| 签名（i8） | 说明 |
|---|---|
| i8::from_i64(v: i64) -> i8 | 从 i64 构造（截断/符号扩展） |
| i8::from_u64(v: u64) -> i8 | 从 u64 构造 |
| i8::from_f64(v: f64) -> i8 | 从 f64 向零截断 |
| i8::to_i64(self) -> i64 | 转换为 i64 |
| i8::to_u64(self) -> u64 | 转换为 u64 |
| i8::to_f64(self) -> f64 | 转换为 f64 |
| i8::to_string(self) -> String | 十进制字符串 |
| i8::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| i8::parse(s: &str) -> ?i8 | 解析字符串，失败返回 none |
| i8::from_str(s: &str) -> Result<i8, str> | 解析字符串（Result 版） |
| i8::abs(self) -> i8 | 绝对值（无符号类型恒等） |
| i8::neg(self) -> i8 | 取负 |
| i8::pow(self, exp: u32) -> i8 | 幂 |
| i8::checked_add(self, o: i8) -> ?i8 | 加法溢出检测 |
| i8::checked_sub(self, o: i8) -> ?i8 | 减法溢出检测 |
| i8::checked_mul(self, o: i8) -> ?i8 | 乘法溢出检测 |
| i8::checked_div(self, o: i8) -> ?i8 | 除法溢出/除零检测 |
| i8::checked_rem(self, o: i8) -> ?i8 | 取模检测 |
| i8::checked_pow(self, exp: u32) -> ?i8 | 幂溢出检测 |
| i8::saturating_add(self, o: i8) -> i8 | 饱和加法 |
| i8::saturating_sub(self, o: i8) -> i8 | 饱和减法 |
| i8::saturating_mul(self, o: i8) -> i8 | 饱和乘法 |
| i8::wrapping_add(self, o: i8) -> i8 | 回绕加法 |
| i8::wrapping_sub(self, o: i8) -> i8 | 回绕减法 |
| i8::wrapping_mul(self, o: i8) -> i8 | 回绕乘法 |
| i8::overflowing_add(self, o: i8) -> (i8, bool) | 回绕加法 + 溢出标志 |
| i8::midpoint(self, o: i8) -> i8 | 中点（无溢出） |
| i8::bitand(self, o: i8) -> i8 | 按位与 |
| i8::bitor(self, o: i8) -> i8 | 按位或 |
| i8::bitxor(self, o: i8) -> i8 | 按位异或 |
| i8::bitnot(self) -> i8 | 按位取反 |
| i8::shl(self, n: u32) -> i8 | 左移 |
| i8::shr(self, n: u32) -> i8 | 右移（有符号算术/无符号逻辑） |
| i8::rotl(self, n: u32) -> i8 | 循环左移 |
| i8::rotr(self, n: u32) -> i8 | 循环右移 |
| i8::count_ones(self) -> u32 | 置位位数（popcount） |
| i8::count_zeros(self) -> u32 | 零位数 |
| i8::leading_zeros(self) -> u32 | 前导零位数 |
| i8::trailing_zeros(self) -> u32 | 末尾零位数 |
| i8::reverse_bits(self) -> i8 | 反转所有位 |
| i8::swap_bytes(self) -> i8 | 字节序反转 |
| i8::from_be(v: i8) -> i8 | 从大端转换 |
| i8::from_le(v: i8) -> i8 | 从小端转换 |
| i8::to_be(self) -> i8 | 转大端 |
| i8::to_le(self) -> i8 | 转小端 |
| i8::min(self, o: i8) -> i8 | 最小值 |
| i8::max(self, o: i8) -> i8 | 最大值 |
| i8::clamp(self, lo: i8, hi: i8) -> i8 | 夹取 |
| i8::cmp(self, o: i8) -> Ordering | 三路比较 |
| i8::eq(self, o: i8) -> bool | 相等 |
| i8::ne(self, o: i8) -> bool | 不等 |
| i8::is_zero(self) -> bool | 是否为 0 |
| i8::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| i8::signum(self) -> i8 | 符号函数 -1/0/1 |
| i8::gcd(self, o: i8) -> i8 | 最大公约数 |
| i8::lcm(self, o: i8) -> i8 | 最小公倍数 |
| i8::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| i8::next_power_of_two(self) -> i8 | 向上取 2 的幂 |
| i8::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| i8::sqrt(self) -> i8 | 整数平方根（向下取整） |
| i8::div_euclid(self, o: i8) -> i8 | 欧几里得除法 |
| i8::rem_euclid(self, o: i8) -> i8 | 欧几里得取模 |
| i8::MIN -> i8 | 类型最小值常量 |
| i8::MAX -> i8 | 类型最大值常量 |
| i8::BITS -> u32 | 位宽常量 |

| 签名（i16） | 说明 |
|---|---|
| i16::from_i64(v: i64) -> i16 | 从 i64 构造（截断/符号扩展） |
| i16::from_u64(v: u64) -> i16 | 从 u64 构造 |
| i16::from_f64(v: f64) -> i16 | 从 f64 向零截断 |
| i16::to_i64(self) -> i64 | 转换为 i64 |
| i16::to_u64(self) -> u64 | 转换为 u64 |
| i16::to_f64(self) -> f64 | 转换为 f64 |
| i16::to_string(self) -> String | 十进制字符串 |
| i16::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| i16::parse(s: &str) -> ?i16 | 解析字符串，失败返回 none |
| i16::from_str(s: &str) -> Result<i16, str> | 解析字符串（Result 版） |
| i16::abs(self) -> i16 | 绝对值（无符号类型恒等） |
| i16::neg(self) -> i16 | 取负 |
| i16::pow(self, exp: u32) -> i16 | 幂 |
| i16::checked_add(self, o: i16) -> ?i16 | 加法溢出检测 |
| i16::checked_sub(self, o: i16) -> ?i16 | 减法溢出检测 |
| i16::checked_mul(self, o: i16) -> ?i16 | 乘法溢出检测 |
| i16::checked_div(self, o: i16) -> ?i16 | 除法溢出/除零检测 |
| i16::checked_rem(self, o: i16) -> ?i16 | 取模检测 |
| i16::checked_pow(self, exp: u32) -> ?i16 | 幂溢出检测 |
| i16::saturating_add(self, o: i16) -> i16 | 饱和加法 |
| i16::saturating_sub(self, o: i16) -> i16 | 饱和减法 |
| i16::saturating_mul(self, o: i16) -> i16 | 饱和乘法 |
| i16::wrapping_add(self, o: i16) -> i16 | 回绕加法 |
| i16::wrapping_sub(self, o: i16) -> i16 | 回绕减法 |
| i16::wrapping_mul(self, o: i16) -> i16 | 回绕乘法 |
| i16::overflowing_add(self, o: i16) -> (i16, bool) | 回绕加法 + 溢出标志 |
| i16::midpoint(self, o: i16) -> i16 | 中点（无溢出） |
| i16::bitand(self, o: i16) -> i16 | 按位与 |
| i16::bitor(self, o: i16) -> i16 | 按位或 |
| i16::bitxor(self, o: i16) -> i16 | 按位异或 |
| i16::bitnot(self) -> i16 | 按位取反 |
| i16::shl(self, n: u32) -> i16 | 左移 |
| i16::shr(self, n: u32) -> i16 | 右移（有符号算术/无符号逻辑） |
| i16::rotl(self, n: u32) -> i16 | 循环左移 |
| i16::rotr(self, n: u32) -> i16 | 循环右移 |
| i16::count_ones(self) -> u32 | 置位位数（popcount） |
| i16::count_zeros(self) -> u32 | 零位数 |
| i16::leading_zeros(self) -> u32 | 前导零位数 |
| i16::trailing_zeros(self) -> u32 | 末尾零位数 |
| i16::reverse_bits(self) -> i16 | 反转所有位 |
| i16::swap_bytes(self) -> i16 | 字节序反转 |
| i16::from_be(v: i16) -> i16 | 从大端转换 |
| i16::from_le(v: i16) -> i16 | 从小端转换 |
| i16::to_be(self) -> i16 | 转大端 |
| i16::to_le(self) -> i16 | 转小端 |
| i16::min(self, o: i16) -> i16 | 最小值 |
| i16::max(self, o: i16) -> i16 | 最大值 |
| i16::clamp(self, lo: i16, hi: i16) -> i16 | 夹取 |
| i16::cmp(self, o: i16) -> Ordering | 三路比较 |
| i16::eq(self, o: i16) -> bool | 相等 |
| i16::ne(self, o: i16) -> bool | 不等 |
| i16::is_zero(self) -> bool | 是否为 0 |
| i16::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| i16::signum(self) -> i16 | 符号函数 -1/0/1 |
| i16::gcd(self, o: i16) -> i16 | 最大公约数 |
| i16::lcm(self, o: i16) -> i16 | 最小公倍数 |
| i16::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| i16::next_power_of_two(self) -> i16 | 向上取 2 的幂 |
| i16::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| i16::sqrt(self) -> i16 | 整数平方根（向下取整） |
| i16::div_euclid(self, o: i16) -> i16 | 欧几里得除法 |
| i16::rem_euclid(self, o: i16) -> i16 | 欧几里得取模 |
| i16::MIN -> i16 | 类型最小值常量 |
| i16::MAX -> i16 | 类型最大值常量 |
| i16::BITS -> u32 | 位宽常量 |

| 签名（i32） | 说明 |
|---|---|
| i32::from_i64(v: i64) -> i32 | 从 i64 构造（截断/符号扩展） |
| i32::from_u64(v: u64) -> i32 | 从 u64 构造 |
| i32::from_f64(v: f64) -> i32 | 从 f64 向零截断 |
| i32::to_i64(self) -> i64 | 转换为 i64 |
| i32::to_u64(self) -> u64 | 转换为 u64 |
| i32::to_f64(self) -> f64 | 转换为 f64 |
| i32::to_string(self) -> String | 十进制字符串 |
| i32::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| i32::parse(s: &str) -> ?i32 | 解析字符串，失败返回 none |
| i32::from_str(s: &str) -> Result<i32, str> | 解析字符串（Result 版） |
| i32::abs(self) -> i32 | 绝对值（无符号类型恒等） |
| i32::neg(self) -> i32 | 取负 |
| i32::pow(self, exp: u32) -> i32 | 幂 |
| i32::checked_add(self, o: i32) -> ?i32 | 加法溢出检测 |
| i32::checked_sub(self, o: i32) -> ?i32 | 减法溢出检测 |
| i32::checked_mul(self, o: i32) -> ?i32 | 乘法溢出检测 |
| i32::checked_div(self, o: i32) -> ?i32 | 除法溢出/除零检测 |
| i32::checked_rem(self, o: i32) -> ?i32 | 取模检测 |
| i32::checked_pow(self, exp: u32) -> ?i32 | 幂溢出检测 |
| i32::saturating_add(self, o: i32) -> i32 | 饱和加法 |
| i32::saturating_sub(self, o: i32) -> i32 | 饱和减法 |
| i32::saturating_mul(self, o: i32) -> i32 | 饱和乘法 |
| i32::wrapping_add(self, o: i32) -> i32 | 回绕加法 |
| i32::wrapping_sub(self, o: i32) -> i32 | 回绕减法 |
| i32::wrapping_mul(self, o: i32) -> i32 | 回绕乘法 |
| i32::overflowing_add(self, o: i32) -> (i32, bool) | 回绕加法 + 溢出标志 |
| i32::midpoint(self, o: i32) -> i32 | 中点（无溢出） |
| i32::bitand(self, o: i32) -> i32 | 按位与 |
| i32::bitor(self, o: i32) -> i32 | 按位或 |
| i32::bitxor(self, o: i32) -> i32 | 按位异或 |
| i32::bitnot(self) -> i32 | 按位取反 |
| i32::shl(self, n: u32) -> i32 | 左移 |
| i32::shr(self, n: u32) -> i32 | 右移（有符号算术/无符号逻辑） |
| i32::rotl(self, n: u32) -> i32 | 循环左移 |
| i32::rotr(self, n: u32) -> i32 | 循环右移 |
| i32::count_ones(self) -> u32 | 置位位数（popcount） |
| i32::count_zeros(self) -> u32 | 零位数 |
| i32::leading_zeros(self) -> u32 | 前导零位数 |
| i32::trailing_zeros(self) -> u32 | 末尾零位数 |
| i32::reverse_bits(self) -> i32 | 反转所有位 |
| i32::swap_bytes(self) -> i32 | 字节序反转 |
| i32::from_be(v: i32) -> i32 | 从大端转换 |
| i32::from_le(v: i32) -> i32 | 从小端转换 |
| i32::to_be(self) -> i32 | 转大端 |
| i32::to_le(self) -> i32 | 转小端 |
| i32::min(self, o: i32) -> i32 | 最小值 |
| i32::max(self, o: i32) -> i32 | 最大值 |
| i32::clamp(self, lo: i32, hi: i32) -> i32 | 夹取 |
| i32::cmp(self, o: i32) -> Ordering | 三路比较 |
| i32::eq(self, o: i32) -> bool | 相等 |
| i32::ne(self, o: i32) -> bool | 不等 |
| i32::is_zero(self) -> bool | 是否为 0 |
| i32::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| i32::signum(self) -> i32 | 符号函数 -1/0/1 |
| i32::gcd(self, o: i32) -> i32 | 最大公约数 |
| i32::lcm(self, o: i32) -> i32 | 最小公倍数 |
| i32::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| i32::next_power_of_two(self) -> i32 | 向上取 2 的幂 |
| i32::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| i32::sqrt(self) -> i32 | 整数平方根（向下取整） |
| i32::div_euclid(self, o: i32) -> i32 | 欧几里得除法 |
| i32::rem_euclid(self, o: i32) -> i32 | 欧几里得取模 |
| i32::MIN -> i32 | 类型最小值常量 |
| i32::MAX -> i32 | 类型最大值常量 |
| i32::BITS -> u32 | 位宽常量 |

| 签名（i64） | 说明 |
|---|---|
| i64::from_i64(v: i64) -> i64 | 从 i64 构造（截断/符号扩展） |
| i64::from_u64(v: u64) -> i64 | 从 u64 构造 |
| i64::from_f64(v: f64) -> i64 | 从 f64 向零截断 |
| i64::to_i64(self) -> i64 | 转换为 i64 |
| i64::to_u64(self) -> u64 | 转换为 u64 |
| i64::to_f64(self) -> f64 | 转换为 f64 |
| i64::to_string(self) -> String | 十进制字符串 |
| i64::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| i64::parse(s: &str) -> ?i64 | 解析字符串，失败返回 none |
| i64::from_str(s: &str) -> Result<i64, str> | 解析字符串（Result 版） |
| i64::abs(self) -> i64 | 绝对值（无符号类型恒等） |
| i64::neg(self) -> i64 | 取负 |
| i64::pow(self, exp: u32) -> i64 | 幂 |
| i64::checked_add(self, o: i64) -> ?i64 | 加法溢出检测 |
| i64::checked_sub(self, o: i64) -> ?i64 | 减法溢出检测 |
| i64::checked_mul(self, o: i64) -> ?i64 | 乘法溢出检测 |
| i64::checked_div(self, o: i64) -> ?i64 | 除法溢出/除零检测 |
| i64::checked_rem(self, o: i64) -> ?i64 | 取模检测 |
| i64::checked_pow(self, exp: u32) -> ?i64 | 幂溢出检测 |
| i64::saturating_add(self, o: i64) -> i64 | 饱和加法 |
| i64::saturating_sub(self, o: i64) -> i64 | 饱和减法 |
| i64::saturating_mul(self, o: i64) -> i64 | 饱和乘法 |
| i64::wrapping_add(self, o: i64) -> i64 | 回绕加法 |
| i64::wrapping_sub(self, o: i64) -> i64 | 回绕减法 |
| i64::wrapping_mul(self, o: i64) -> i64 | 回绕乘法 |
| i64::overflowing_add(self, o: i64) -> (i64, bool) | 回绕加法 + 溢出标志 |
| i64::midpoint(self, o: i64) -> i64 | 中点（无溢出） |
| i64::bitand(self, o: i64) -> i64 | 按位与 |
| i64::bitor(self, o: i64) -> i64 | 按位或 |
| i64::bitxor(self, o: i64) -> i64 | 按位异或 |
| i64::bitnot(self) -> i64 | 按位取反 |
| i64::shl(self, n: u32) -> i64 | 左移 |
| i64::shr(self, n: u32) -> i64 | 右移（有符号算术/无符号逻辑） |
| i64::rotl(self, n: u32) -> i64 | 循环左移 |
| i64::rotr(self, n: u32) -> i64 | 循环右移 |
| i64::count_ones(self) -> u32 | 置位位数（popcount） |
| i64::count_zeros(self) -> u32 | 零位数 |
| i64::leading_zeros(self) -> u32 | 前导零位数 |
| i64::trailing_zeros(self) -> u32 | 末尾零位数 |
| i64::reverse_bits(self) -> i64 | 反转所有位 |
| i64::swap_bytes(self) -> i64 | 字节序反转 |
| i64::from_be(v: i64) -> i64 | 从大端转换 |
| i64::from_le(v: i64) -> i64 | 从小端转换 |
| i64::to_be(self) -> i64 | 转大端 |
| i64::to_le(self) -> i64 | 转小端 |
| i64::min(self, o: i64) -> i64 | 最小值 |
| i64::max(self, o: i64) -> i64 | 最大值 |
| i64::clamp(self, lo: i64, hi: i64) -> i64 | 夹取 |
| i64::cmp(self, o: i64) -> Ordering | 三路比较 |
| i64::eq(self, o: i64) -> bool | 相等 |
| i64::ne(self, o: i64) -> bool | 不等 |
| i64::is_zero(self) -> bool | 是否为 0 |
| i64::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| i64::signum(self) -> i64 | 符号函数 -1/0/1 |
| i64::gcd(self, o: i64) -> i64 | 最大公约数 |
| i64::lcm(self, o: i64) -> i64 | 最小公倍数 |
| i64::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| i64::next_power_of_two(self) -> i64 | 向上取 2 的幂 |
| i64::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| i64::sqrt(self) -> i64 | 整数平方根（向下取整） |
| i64::div_euclid(self, o: i64) -> i64 | 欧几里得除法 |
| i64::rem_euclid(self, o: i64) -> i64 | 欧几里得取模 |
| i64::MIN -> i64 | 类型最小值常量 |
| i64::MAX -> i64 | 类型最大值常量 |
| i64::BITS -> u32 | 位宽常量 |

| 签名（int） | 说明 |
|---|---|
| int::from_i64(v: i64) -> int | 从 i64 构造（截断/符号扩展） |
| int::from_u64(v: u64) -> int | 从 u64 构造 |
| int::from_f64(v: f64) -> int | 从 f64 向零截断 |
| int::to_i64(self) -> i64 | 转换为 i64 |
| int::to_u64(self) -> u64 | 转换为 u64 |
| int::to_f64(self) -> f64 | 转换为 f64 |
| int::to_string(self) -> String | 十进制字符串 |
| int::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| int::parse(s: &str) -> ?int | 解析字符串，失败返回 none |
| int::from_str(s: &str) -> Result<int, str> | 解析字符串（Result 版） |
| int::abs(self) -> int | 绝对值（无符号类型恒等） |
| int::neg(self) -> int | 取负 |
| int::pow(self, exp: u32) -> int | 幂 |
| int::checked_add(self, o: int) -> ?int | 加法溢出检测 |
| int::checked_sub(self, o: int) -> ?int | 减法溢出检测 |
| int::checked_mul(self, o: int) -> ?int | 乘法溢出检测 |
| int::checked_div(self, o: int) -> ?int | 除法溢出/除零检测 |
| int::checked_rem(self, o: int) -> ?int | 取模检测 |
| int::checked_pow(self, exp: u32) -> ?int | 幂溢出检测 |
| int::saturating_add(self, o: int) -> int | 饱和加法 |
| int::saturating_sub(self, o: int) -> int | 饱和减法 |
| int::saturating_mul(self, o: int) -> int | 饱和乘法 |
| int::wrapping_add(self, o: int) -> int | 回绕加法 |
| int::wrapping_sub(self, o: int) -> int | 回绕减法 |
| int::wrapping_mul(self, o: int) -> int | 回绕乘法 |
| int::overflowing_add(self, o: int) -> (int, bool) | 回绕加法 + 溢出标志 |
| int::midpoint(self, o: int) -> int | 中点（无溢出） |
| int::bitand(self, o: int) -> int | 按位与 |
| int::bitor(self, o: int) -> int | 按位或 |
| int::bitxor(self, o: int) -> int | 按位异或 |
| int::bitnot(self) -> int | 按位取反 |
| int::shl(self, n: u32) -> int | 左移 |
| int::shr(self, n: u32) -> int | 右移（有符号算术/无符号逻辑） |
| int::rotl(self, n: u32) -> int | 循环左移 |
| int::rotr(self, n: u32) -> int | 循环右移 |
| int::count_ones(self) -> u32 | 置位位数（popcount） |
| int::count_zeros(self) -> u32 | 零位数 |
| int::leading_zeros(self) -> u32 | 前导零位数 |
| int::trailing_zeros(self) -> u32 | 末尾零位数 |
| int::reverse_bits(self) -> int | 反转所有位 |
| int::swap_bytes(self) -> int | 字节序反转 |
| int::from_be(v: int) -> int | 从大端转换 |
| int::from_le(v: int) -> int | 从小端转换 |
| int::to_be(self) -> int | 转大端 |
| int::to_le(self) -> int | 转小端 |
| int::min(self, o: int) -> int | 最小值 |
| int::max(self, o: int) -> int | 最大值 |
| int::clamp(self, lo: int, hi: int) -> int | 夹取 |
| int::cmp(self, o: int) -> Ordering | 三路比较 |
| int::eq(self, o: int) -> bool | 相等 |
| int::ne(self, o: int) -> bool | 不等 |
| int::is_zero(self) -> bool | 是否为 0 |
| int::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| int::signum(self) -> int | 符号函数 -1/0/1 |
| int::gcd(self, o: int) -> int | 最大公约数 |
| int::lcm(self, o: int) -> int | 最小公倍数 |
| int::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| int::next_power_of_two(self) -> int | 向上取 2 的幂 |
| int::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| int::sqrt(self) -> int | 整数平方根（向下取整） |
| int::div_euclid(self, o: int) -> int | 欧几里得除法 |
| int::rem_euclid(self, o: int) -> int | 欧几里得取模 |
| int::MIN -> int | 类型最小值常量 |
| int::MAX -> int | 类型最大值常量 |
| int::BITS -> u32 | 位宽常量 |

| 签名（u8） | 说明 |
|---|---|
| u8::from_i64(v: i64) -> u8 | 从 i64 构造（截断/符号扩展） |
| u8::from_u64(v: u64) -> u8 | 从 u64 构造 |
| u8::from_f64(v: f64) -> u8 | 从 f64 向零截断 |
| u8::to_i64(self) -> i64 | 转换为 i64 |
| u8::to_u64(self) -> u64 | 转换为 u64 |
| u8::to_f64(self) -> f64 | 转换为 f64 |
| u8::to_string(self) -> String | 十进制字符串 |
| u8::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| u8::parse(s: &str) -> ?u8 | 解析字符串，失败返回 none |
| u8::from_str(s: &str) -> Result<u8, str> | 解析字符串（Result 版） |
| u8::abs(self) -> u8 | 绝对值（无符号类型恒等） |
| u8::neg(self) -> u8 | 取负 |
| u8::pow(self, exp: u32) -> u8 | 幂 |
| u8::checked_add(self, o: u8) -> ?u8 | 加法溢出检测 |
| u8::checked_sub(self, o: u8) -> ?u8 | 减法溢出检测 |
| u8::checked_mul(self, o: u8) -> ?u8 | 乘法溢出检测 |
| u8::checked_div(self, o: u8) -> ?u8 | 除法溢出/除零检测 |
| u8::checked_rem(self, o: u8) -> ?u8 | 取模检测 |
| u8::checked_pow(self, exp: u32) -> ?u8 | 幂溢出检测 |
| u8::saturating_add(self, o: u8) -> u8 | 饱和加法 |
| u8::saturating_sub(self, o: u8) -> u8 | 饱和减法 |
| u8::saturating_mul(self, o: u8) -> u8 | 饱和乘法 |
| u8::wrapping_add(self, o: u8) -> u8 | 回绕加法 |
| u8::wrapping_sub(self, o: u8) -> u8 | 回绕减法 |
| u8::wrapping_mul(self, o: u8) -> u8 | 回绕乘法 |
| u8::overflowing_add(self, o: u8) -> (u8, bool) | 回绕加法 + 溢出标志 |
| u8::midpoint(self, o: u8) -> u8 | 中点（无溢出） |
| u8::bitand(self, o: u8) -> u8 | 按位与 |
| u8::bitor(self, o: u8) -> u8 | 按位或 |
| u8::bitxor(self, o: u8) -> u8 | 按位异或 |
| u8::bitnot(self) -> u8 | 按位取反 |
| u8::shl(self, n: u32) -> u8 | 左移 |
| u8::shr(self, n: u32) -> u8 | 右移（有符号算术/无符号逻辑） |
| u8::rotl(self, n: u32) -> u8 | 循环左移 |
| u8::rotr(self, n: u32) -> u8 | 循环右移 |
| u8::count_ones(self) -> u32 | 置位位数（popcount） |
| u8::count_zeros(self) -> u32 | 零位数 |
| u8::leading_zeros(self) -> u32 | 前导零位数 |
| u8::trailing_zeros(self) -> u32 | 末尾零位数 |
| u8::reverse_bits(self) -> u8 | 反转所有位 |
| u8::swap_bytes(self) -> u8 | 字节序反转 |
| u8::from_be(v: u8) -> u8 | 从大端转换 |
| u8::from_le(v: u8) -> u8 | 从小端转换 |
| u8::to_be(self) -> u8 | 转大端 |
| u8::to_le(self) -> u8 | 转小端 |
| u8::min(self, o: u8) -> u8 | 最小值 |
| u8::max(self, o: u8) -> u8 | 最大值 |
| u8::clamp(self, lo: u8, hi: u8) -> u8 | 夹取 |
| u8::cmp(self, o: u8) -> Ordering | 三路比较 |
| u8::eq(self, o: u8) -> bool | 相等 |
| u8::ne(self, o: u8) -> bool | 不等 |
| u8::is_zero(self) -> bool | 是否为 0 |
| u8::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| u8::signum(self) -> u8 | 符号函数 -1/0/1 |
| u8::gcd(self, o: u8) -> u8 | 最大公约数 |
| u8::lcm(self, o: u8) -> u8 | 最小公倍数 |
| u8::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| u8::next_power_of_two(self) -> u8 | 向上取 2 的幂 |
| u8::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| u8::sqrt(self) -> u8 | 整数平方根（向下取整） |
| u8::div_euclid(self, o: u8) -> u8 | 欧几里得除法 |
| u8::rem_euclid(self, o: u8) -> u8 | 欧几里得取模 |
| u8::MIN -> u8 | 类型最小值常量 |
| u8::MAX -> u8 | 类型最大值常量 |
| u8::BITS -> u32 | 位宽常量 |

| 签名（u16） | 说明 |
|---|---|
| u16::from_i64(v: i64) -> u16 | 从 i64 构造（截断/符号扩展） |
| u16::from_u64(v: u64) -> u16 | 从 u64 构造 |
| u16::from_f64(v: f64) -> u16 | 从 f64 向零截断 |
| u16::to_i64(self) -> i64 | 转换为 i64 |
| u16::to_u64(self) -> u64 | 转换为 u64 |
| u16::to_f64(self) -> f64 | 转换为 f64 |
| u16::to_string(self) -> String | 十进制字符串 |
| u16::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| u16::parse(s: &str) -> ?u16 | 解析字符串，失败返回 none |
| u16::from_str(s: &str) -> Result<u16, str> | 解析字符串（Result 版） |
| u16::abs(self) -> u16 | 绝对值（无符号类型恒等） |
| u16::neg(self) -> u16 | 取负 |
| u16::pow(self, exp: u32) -> u16 | 幂 |
| u16::checked_add(self, o: u16) -> ?u16 | 加法溢出检测 |
| u16::checked_sub(self, o: u16) -> ?u16 | 减法溢出检测 |
| u16::checked_mul(self, o: u16) -> ?u16 | 乘法溢出检测 |
| u16::checked_div(self, o: u16) -> ?u16 | 除法溢出/除零检测 |
| u16::checked_rem(self, o: u16) -> ?u16 | 取模检测 |
| u16::checked_pow(self, exp: u32) -> ?u16 | 幂溢出检测 |
| u16::saturating_add(self, o: u16) -> u16 | 饱和加法 |
| u16::saturating_sub(self, o: u16) -> u16 | 饱和减法 |
| u16::saturating_mul(self, o: u16) -> u16 | 饱和乘法 |
| u16::wrapping_add(self, o: u16) -> u16 | 回绕加法 |
| u16::wrapping_sub(self, o: u16) -> u16 | 回绕减法 |
| u16::wrapping_mul(self, o: u16) -> u16 | 回绕乘法 |
| u16::overflowing_add(self, o: u16) -> (u16, bool) | 回绕加法 + 溢出标志 |
| u16::midpoint(self, o: u16) -> u16 | 中点（无溢出） |
| u16::bitand(self, o: u16) -> u16 | 按位与 |
| u16::bitor(self, o: u16) -> u16 | 按位或 |
| u16::bitxor(self, o: u16) -> u16 | 按位异或 |
| u16::bitnot(self) -> u16 | 按位取反 |
| u16::shl(self, n: u32) -> u16 | 左移 |
| u16::shr(self, n: u32) -> u16 | 右移（有符号算术/无符号逻辑） |
| u16::rotl(self, n: u32) -> u16 | 循环左移 |
| u16::rotr(self, n: u32) -> u16 | 循环右移 |
| u16::count_ones(self) -> u32 | 置位位数（popcount） |
| u16::count_zeros(self) -> u32 | 零位数 |
| u16::leading_zeros(self) -> u32 | 前导零位数 |
| u16::trailing_zeros(self) -> u32 | 末尾零位数 |
| u16::reverse_bits(self) -> u16 | 反转所有位 |
| u16::swap_bytes(self) -> u16 | 字节序反转 |
| u16::from_be(v: u16) -> u16 | 从大端转换 |
| u16::from_le(v: u16) -> u16 | 从小端转换 |
| u16::to_be(self) -> u16 | 转大端 |
| u16::to_le(self) -> u16 | 转小端 |
| u16::min(self, o: u16) -> u16 | 最小值 |
| u16::max(self, o: u16) -> u16 | 最大值 |
| u16::clamp(self, lo: u16, hi: u16) -> u16 | 夹取 |
| u16::cmp(self, o: u16) -> Ordering | 三路比较 |
| u16::eq(self, o: u16) -> bool | 相等 |
| u16::ne(self, o: u16) -> bool | 不等 |
| u16::is_zero(self) -> bool | 是否为 0 |
| u16::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| u16::signum(self) -> u16 | 符号函数 -1/0/1 |
| u16::gcd(self, o: u16) -> u16 | 最大公约数 |
| u16::lcm(self, o: u16) -> u16 | 最小公倍数 |
| u16::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| u16::next_power_of_two(self) -> u16 | 向上取 2 的幂 |
| u16::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| u16::sqrt(self) -> u16 | 整数平方根（向下取整） |
| u16::div_euclid(self, o: u16) -> u16 | 欧几里得除法 |
| u16::rem_euclid(self, o: u16) -> u16 | 欧几里得取模 |
| u16::MIN -> u16 | 类型最小值常量 |
| u16::MAX -> u16 | 类型最大值常量 |
| u16::BITS -> u32 | 位宽常量 |

| 签名（u32） | 说明 |
|---|---|
| u32::from_i64(v: i64) -> u32 | 从 i64 构造（截断/符号扩展） |
| u32::from_u64(v: u64) -> u32 | 从 u64 构造 |
| u32::from_f64(v: f64) -> u32 | 从 f64 向零截断 |
| u32::to_i64(self) -> i64 | 转换为 i64 |
| u32::to_u64(self) -> u64 | 转换为 u64 |
| u32::to_f64(self) -> f64 | 转换为 f64 |
| u32::to_string(self) -> String | 十进制字符串 |
| u32::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| u32::parse(s: &str) -> ?u32 | 解析字符串，失败返回 none |
| u32::from_str(s: &str) -> Result<u32, str> | 解析字符串（Result 版） |
| u32::abs(self) -> u32 | 绝对值（无符号类型恒等） |
| u32::neg(self) -> u32 | 取负 |
| u32::pow(self, exp: u32) -> u32 | 幂 |
| u32::checked_add(self, o: u32) -> ?u32 | 加法溢出检测 |
| u32::checked_sub(self, o: u32) -> ?u32 | 减法溢出检测 |
| u32::checked_mul(self, o: u32) -> ?u32 | 乘法溢出检测 |
| u32::checked_div(self, o: u32) -> ?u32 | 除法溢出/除零检测 |
| u32::checked_rem(self, o: u32) -> ?u32 | 取模检测 |
| u32::checked_pow(self, exp: u32) -> ?u32 | 幂溢出检测 |
| u32::saturating_add(self, o: u32) -> u32 | 饱和加法 |
| u32::saturating_sub(self, o: u32) -> u32 | 饱和减法 |
| u32::saturating_mul(self, o: u32) -> u32 | 饱和乘法 |
| u32::wrapping_add(self, o: u32) -> u32 | 回绕加法 |
| u32::wrapping_sub(self, o: u32) -> u32 | 回绕减法 |
| u32::wrapping_mul(self, o: u32) -> u32 | 回绕乘法 |
| u32::overflowing_add(self, o: u32) -> (u32, bool) | 回绕加法 + 溢出标志 |
| u32::midpoint(self, o: u32) -> u32 | 中点（无溢出） |
| u32::bitand(self, o: u32) -> u32 | 按位与 |
| u32::bitor(self, o: u32) -> u32 | 按位或 |
| u32::bitxor(self, o: u32) -> u32 | 按位异或 |
| u32::bitnot(self) -> u32 | 按位取反 |
| u32::shl(self, n: u32) -> u32 | 左移 |
| u32::shr(self, n: u32) -> u32 | 右移（有符号算术/无符号逻辑） |
| u32::rotl(self, n: u32) -> u32 | 循环左移 |
| u32::rotr(self, n: u32) -> u32 | 循环右移 |
| u32::count_ones(self) -> u32 | 置位位数（popcount） |
| u32::count_zeros(self) -> u32 | 零位数 |
| u32::leading_zeros(self) -> u32 | 前导零位数 |
| u32::trailing_zeros(self) -> u32 | 末尾零位数 |
| u32::reverse_bits(self) -> u32 | 反转所有位 |
| u32::swap_bytes(self) -> u32 | 字节序反转 |
| u32::from_be(v: u32) -> u32 | 从大端转换 |
| u32::from_le(v: u32) -> u32 | 从小端转换 |
| u32::to_be(self) -> u32 | 转大端 |
| u32::to_le(self) -> u32 | 转小端 |
| u32::min(self, o: u32) -> u32 | 最小值 |
| u32::max(self, o: u32) -> u32 | 最大值 |
| u32::clamp(self, lo: u32, hi: u32) -> u32 | 夹取 |
| u32::cmp(self, o: u32) -> Ordering | 三路比较 |
| u32::eq(self, o: u32) -> bool | 相等 |
| u32::ne(self, o: u32) -> bool | 不等 |
| u32::is_zero(self) -> bool | 是否为 0 |
| u32::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| u32::signum(self) -> u32 | 符号函数 -1/0/1 |
| u32::gcd(self, o: u32) -> u32 | 最大公约数 |
| u32::lcm(self, o: u32) -> u32 | 最小公倍数 |
| u32::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| u32::next_power_of_two(self) -> u32 | 向上取 2 的幂 |
| u32::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| u32::sqrt(self) -> u32 | 整数平方根（向下取整） |
| u32::div_euclid(self, o: u32) -> u32 | 欧几里得除法 |
| u32::rem_euclid(self, o: u32) -> u32 | 欧几里得取模 |
| u32::MIN -> u32 | 类型最小值常量 |
| u32::MAX -> u32 | 类型最大值常量 |
| u32::BITS -> u32 | 位宽常量 |

| 签名（u64） | 说明 |
|---|---|
| u64::from_i64(v: i64) -> u64 | 从 i64 构造（截断/符号扩展） |
| u64::from_u64(v: u64) -> u64 | 从 u64 构造 |
| u64::from_f64(v: f64) -> u64 | 从 f64 向零截断 |
| u64::to_i64(self) -> i64 | 转换为 i64 |
| u64::to_u64(self) -> u64 | 转换为 u64 |
| u64::to_f64(self) -> f64 | 转换为 f64 |
| u64::to_string(self) -> String | 十进制字符串 |
| u64::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| u64::parse(s: &str) -> ?u64 | 解析字符串，失败返回 none |
| u64::from_str(s: &str) -> Result<u64, str> | 解析字符串（Result 版） |
| u64::abs(self) -> u64 | 绝对值（无符号类型恒等） |
| u64::neg(self) -> u64 | 取负 |
| u64::pow(self, exp: u32) -> u64 | 幂 |
| u64::checked_add(self, o: u64) -> ?u64 | 加法溢出检测 |
| u64::checked_sub(self, o: u64) -> ?u64 | 减法溢出检测 |
| u64::checked_mul(self, o: u64) -> ?u64 | 乘法溢出检测 |
| u64::checked_div(self, o: u64) -> ?u64 | 除法溢出/除零检测 |
| u64::checked_rem(self, o: u64) -> ?u64 | 取模检测 |
| u64::checked_pow(self, exp: u32) -> ?u64 | 幂溢出检测 |
| u64::saturating_add(self, o: u64) -> u64 | 饱和加法 |
| u64::saturating_sub(self, o: u64) -> u64 | 饱和减法 |
| u64::saturating_mul(self, o: u64) -> u64 | 饱和乘法 |
| u64::wrapping_add(self, o: u64) -> u64 | 回绕加法 |
| u64::wrapping_sub(self, o: u64) -> u64 | 回绕减法 |
| u64::wrapping_mul(self, o: u64) -> u64 | 回绕乘法 |
| u64::overflowing_add(self, o: u64) -> (u64, bool) | 回绕加法 + 溢出标志 |
| u64::midpoint(self, o: u64) -> u64 | 中点（无溢出） |
| u64::bitand(self, o: u64) -> u64 | 按位与 |
| u64::bitor(self, o: u64) -> u64 | 按位或 |
| u64::bitxor(self, o: u64) -> u64 | 按位异或 |
| u64::bitnot(self) -> u64 | 按位取反 |
| u64::shl(self, n: u32) -> u64 | 左移 |
| u64::shr(self, n: u32) -> u64 | 右移（有符号算术/无符号逻辑） |
| u64::rotl(self, n: u32) -> u64 | 循环左移 |
| u64::rotr(self, n: u32) -> u64 | 循环右移 |
| u64::count_ones(self) -> u32 | 置位位数（popcount） |
| u64::count_zeros(self) -> u32 | 零位数 |
| u64::leading_zeros(self) -> u32 | 前导零位数 |
| u64::trailing_zeros(self) -> u32 | 末尾零位数 |
| u64::reverse_bits(self) -> u64 | 反转所有位 |
| u64::swap_bytes(self) -> u64 | 字节序反转 |
| u64::from_be(v: u64) -> u64 | 从大端转换 |
| u64::from_le(v: u64) -> u64 | 从小端转换 |
| u64::to_be(self) -> u64 | 转大端 |
| u64::to_le(self) -> u64 | 转小端 |
| u64::min(self, o: u64) -> u64 | 最小值 |
| u64::max(self, o: u64) -> u64 | 最大值 |
| u64::clamp(self, lo: u64, hi: u64) -> u64 | 夹取 |
| u64::cmp(self, o: u64) -> Ordering | 三路比较 |
| u64::eq(self, o: u64) -> bool | 相等 |
| u64::ne(self, o: u64) -> bool | 不等 |
| u64::is_zero(self) -> bool | 是否为 0 |
| u64::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| u64::signum(self) -> u64 | 符号函数 -1/0/1 |
| u64::gcd(self, o: u64) -> u64 | 最大公约数 |
| u64::lcm(self, o: u64) -> u64 | 最小公倍数 |
| u64::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| u64::next_power_of_two(self) -> u64 | 向上取 2 的幂 |
| u64::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| u64::sqrt(self) -> u64 | 整数平方根（向下取整） |
| u64::div_euclid(self, o: u64) -> u64 | 欧几里得除法 |
| u64::rem_euclid(self, o: u64) -> u64 | 欧几里得取模 |
| u64::MIN -> u64 | 类型最小值常量 |
| u64::MAX -> u64 | 类型最大值常量 |
| u64::BITS -> u32 | 位宽常量 |

| 签名（usize） | 说明 |
|---|---|
| usize::from_i64(v: i64) -> usize | 从 i64 构造（截断/符号扩展） |
| usize::from_u64(v: u64) -> usize | 从 u64 构造 |
| usize::from_f64(v: f64) -> usize | 从 f64 向零截断 |
| usize::to_i64(self) -> i64 | 转换为 i64 |
| usize::to_u64(self) -> u64 | 转换为 u64 |
| usize::to_f64(self) -> f64 | 转换为 f64 |
| usize::to_string(self) -> String | 十进制字符串 |
| usize::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| usize::parse(s: &str) -> ?usize | 解析字符串，失败返回 none |
| usize::from_str(s: &str) -> Result<usize, str> | 解析字符串（Result 版） |
| usize::abs(self) -> usize | 绝对值（无符号类型恒等） |
| usize::neg(self) -> usize | 取负 |
| usize::pow(self, exp: u32) -> usize | 幂 |
| usize::checked_add(self, o: usize) -> ?usize | 加法溢出检测 |
| usize::checked_sub(self, o: usize) -> ?usize | 减法溢出检测 |
| usize::checked_mul(self, o: usize) -> ?usize | 乘法溢出检测 |
| usize::checked_div(self, o: usize) -> ?usize | 除法溢出/除零检测 |
| usize::checked_rem(self, o: usize) -> ?usize | 取模检测 |
| usize::checked_pow(self, exp: u32) -> ?usize | 幂溢出检测 |
| usize::saturating_add(self, o: usize) -> usize | 饱和加法 |
| usize::saturating_sub(self, o: usize) -> usize | 饱和减法 |
| usize::saturating_mul(self, o: usize) -> usize | 饱和乘法 |
| usize::wrapping_add(self, o: usize) -> usize | 回绕加法 |
| usize::wrapping_sub(self, o: usize) -> usize | 回绕减法 |
| usize::wrapping_mul(self, o: usize) -> usize | 回绕乘法 |
| usize::overflowing_add(self, o: usize) -> (usize, bool) | 回绕加法 + 溢出标志 |
| usize::midpoint(self, o: usize) -> usize | 中点（无溢出） |
| usize::bitand(self, o: usize) -> usize | 按位与 |
| usize::bitor(self, o: usize) -> usize | 按位或 |
| usize::bitxor(self, o: usize) -> usize | 按位异或 |
| usize::bitnot(self) -> usize | 按位取反 |
| usize::shl(self, n: u32) -> usize | 左移 |
| usize::shr(self, n: u32) -> usize | 右移（有符号算术/无符号逻辑） |
| usize::rotl(self, n: u32) -> usize | 循环左移 |
| usize::rotr(self, n: u32) -> usize | 循环右移 |
| usize::count_ones(self) -> u32 | 置位位数（popcount） |
| usize::count_zeros(self) -> u32 | 零位数 |
| usize::leading_zeros(self) -> u32 | 前导零位数 |
| usize::trailing_zeros(self) -> u32 | 末尾零位数 |
| usize::reverse_bits(self) -> usize | 反转所有位 |
| usize::swap_bytes(self) -> usize | 字节序反转 |
| usize::from_be(v: usize) -> usize | 从大端转换 |
| usize::from_le(v: usize) -> usize | 从小端转换 |
| usize::to_be(self) -> usize | 转大端 |
| usize::to_le(self) -> usize | 转小端 |
| usize::min(self, o: usize) -> usize | 最小值 |
| usize::max(self, o: usize) -> usize | 最大值 |
| usize::clamp(self, lo: usize, hi: usize) -> usize | 夹取 |
| usize::cmp(self, o: usize) -> Ordering | 三路比较 |
| usize::eq(self, o: usize) -> bool | 相等 |
| usize::ne(self, o: usize) -> bool | 不等 |
| usize::is_zero(self) -> bool | 是否为 0 |
| usize::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| usize::signum(self) -> usize | 符号函数 -1/0/1 |
| usize::gcd(self, o: usize) -> usize | 最大公约数 |
| usize::lcm(self, o: usize) -> usize | 最小公倍数 |
| usize::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| usize::next_power_of_two(self) -> usize | 向上取 2 的幂 |
| usize::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| usize::sqrt(self) -> usize | 整数平方根（向下取整） |
| usize::div_euclid(self, o: usize) -> usize | 欧几里得除法 |
| usize::rem_euclid(self, o: usize) -> usize | 欧几里得取模 |
| usize::MIN -> usize | 类型最小值常量 |
| usize::MAX -> usize | 类型最大值常量 |
| usize::BITS -> u32 | 位宽常量 |

| 签名（isize） | 说明 |
|---|---|
| isize::from_i64(v: i64) -> isize | 从 i64 构造（截断/符号扩展） |
| isize::from_u64(v: u64) -> isize | 从 u64 构造 |
| isize::from_f64(v: f64) -> isize | 从 f64 向零截断 |
| isize::to_i64(self) -> i64 | 转换为 i64 |
| isize::to_u64(self) -> u64 | 转换为 u64 |
| isize::to_f64(self) -> f64 | 转换为 f64 |
| isize::to_string(self) -> String | 十进制字符串 |
| isize::to_string_base(self, base: u32) -> String | 按进制转字符串（2..36） |
| isize::parse(s: &str) -> ?isize | 解析字符串，失败返回 none |
| isize::from_str(s: &str) -> Result<isize, str> | 解析字符串（Result 版） |
| isize::abs(self) -> isize | 绝对值（无符号类型恒等） |
| isize::neg(self) -> isize | 取负 |
| isize::pow(self, exp: u32) -> isize | 幂 |
| isize::checked_add(self, o: isize) -> ?isize | 加法溢出检测 |
| isize::checked_sub(self, o: isize) -> ?isize | 减法溢出检测 |
| isize::checked_mul(self, o: isize) -> ?isize | 乘法溢出检测 |
| isize::checked_div(self, o: isize) -> ?isize | 除法溢出/除零检测 |
| isize::checked_rem(self, o: isize) -> ?isize | 取模检测 |
| isize::checked_pow(self, exp: u32) -> ?isize | 幂溢出检测 |
| isize::saturating_add(self, o: isize) -> isize | 饱和加法 |
| isize::saturating_sub(self, o: isize) -> isize | 饱和减法 |
| isize::saturating_mul(self, o: isize) -> isize | 饱和乘法 |
| isize::wrapping_add(self, o: isize) -> isize | 回绕加法 |
| isize::wrapping_sub(self, o: isize) -> isize | 回绕减法 |
| isize::wrapping_mul(self, o: isize) -> isize | 回绕乘法 |
| isize::overflowing_add(self, o: isize) -> (isize, bool) | 回绕加法 + 溢出标志 |
| isize::midpoint(self, o: isize) -> isize | 中点（无溢出） |
| isize::bitand(self, o: isize) -> isize | 按位与 |
| isize::bitor(self, o: isize) -> isize | 按位或 |
| isize::bitxor(self, o: isize) -> isize | 按位异或 |
| isize::bitnot(self) -> isize | 按位取反 |
| isize::shl(self, n: u32) -> isize | 左移 |
| isize::shr(self, n: u32) -> isize | 右移（有符号算术/无符号逻辑） |
| isize::rotl(self, n: u32) -> isize | 循环左移 |
| isize::rotr(self, n: u32) -> isize | 循环右移 |
| isize::count_ones(self) -> u32 | 置位位数（popcount） |
| isize::count_zeros(self) -> u32 | 零位数 |
| isize::leading_zeros(self) -> u32 | 前导零位数 |
| isize::trailing_zeros(self) -> u32 | 末尾零位数 |
| isize::reverse_bits(self) -> isize | 反转所有位 |
| isize::swap_bytes(self) -> isize | 字节序反转 |
| isize::from_be(v: isize) -> isize | 从大端转换 |
| isize::from_le(v: isize) -> isize | 从小端转换 |
| isize::to_be(self) -> isize | 转大端 |
| isize::to_le(self) -> isize | 转小端 |
| isize::min(self, o: isize) -> isize | 最小值 |
| isize::max(self, o: isize) -> isize | 最大值 |
| isize::clamp(self, lo: isize, hi: isize) -> isize | 夹取 |
| isize::cmp(self, o: isize) -> Ordering | 三路比较 |
| isize::eq(self, o: isize) -> bool | 相等 |
| isize::ne(self, o: isize) -> bool | 不等 |
| isize::is_zero(self) -> bool | 是否为 0 |
| isize::is_negative(self) -> bool | 是否为负（无符号恒 false） |
| isize::signum(self) -> isize | 符号函数 -1/0/1 |
| isize::gcd(self, o: isize) -> isize | 最大公约数 |
| isize::lcm(self, o: isize) -> isize | 最小公倍数 |
| isize::is_power_of_two(self) -> bool | 是否为 2 的幂 |
| isize::next_power_of_two(self) -> isize | 向上取 2 的幂 |
| isize::ilog2(self) -> u32 | 以 2 为底的对数（向下取整） |
| isize::sqrt(self) -> isize | 整数平方根（向下取整） |
| isize::div_euclid(self, o: isize) -> isize | 欧几里得除法 |
| isize::rem_euclid(self, o: isize) -> isize | 欧几里得取模 |
| isize::MIN -> isize | 类型最小值常量 |
| isize::MAX -> isize | 类型最大值常量 |
| isize::BITS -> u32 | 位宽常量 |

| 签名（f32） | 说明 |
|---|---|
| f32::abs(self) -> f32 | 绝对值 |
| f32::neg(self) -> f32 | 取负 |
| f32::sqrt(self) -> f32 | 平方根 |
| f32::cbrt(self) -> f32 | 立方根 |
| f32::floor(self) -> f32 | 向下取整 |
| f32::ceil(self) -> f32 | 向上取整 |
| f32::round(self) -> f32 | 四舍五入 |
| f32::trunc(self) -> f32 | 向零取整 |
| f32::fract(self) -> f32 | 小数部分 |
| f32::signum(self) -> f32 | 符号函数 |
| f32::min(self, o: f32) -> f32 | 最小值 |
| f32::max(self, o: f32) -> f32 | 最大值 |
| f32::clamp(self, lo: f32, hi: f32) -> f32 | 夹取 |
| f32::pow(self, e: f32) -> f32 | 幂 |
| f32::powi(self, n: i32) -> f32 | 整数次幂 |
| f32::exp(self) -> f32 | e^x |
| f32::exp2(self) -> f32 | 2^x |
| f32::ln(self) -> f32 | 自然对数 |
| f32::log2(self) -> f32 | 以 2 为底对数 |
| f32::log10(self) -> f32 | 以 10 为底对数 |
| f32::log(self, base: f32) -> f32 | 任意底对数 |
| f32::sin(self) -> f32 | 正弦 |
| f32::cos(self) -> f32 | 余弦 |
| f32::tan(self) -> f32 | 正切 |
| f32::asin(self) -> f32 | 反正弦 |
| f32::acos(self) -> f32 | 反余弦 |
| f32::atan(self) -> f32 | 反正切 |
| f32::atan2(y: f32, x: f32) -> f32 | atan2 |
| f32::hypot(x: f32, y: f32) -> f32 | sqrt(x²+y²) |
| f32::sinh(self) -> f32 | 双曲正弦 |
| f32::cosh(self) -> f32 | 双曲余弦 |
| f32::tanh(self) -> f32 | 双曲正切 |
| f32::asinh(self) -> f32 | 反双曲正弦 |
| f32::acosh(self) -> f32 | 反双曲余弦 |
| f32::atanh(self) -> f32 | 反双曲正切 |
| f32::recip(self) -> f32 | 1/x |
| f32::to_degrees(self) -> f32 | 弧度转角度 |
| f32::to_radians(self) -> f32 | 角度转弧度 |
| f32::is_nan(self) -> bool | 是否 NaN |
| f32::is_infinite(self) -> bool | 是否无穷 |
| f32::is_finite(self) -> bool | 是否有限 |
| f32::is_normal(self) -> bool | 是否正规数 |
| f32::is_sign_positive(self) -> bool | 符号位正 |
| f32::is_sign_negative(self) -> bool | 符号位负 |
| f32::to_bits(self) -> u64 | 位模式转整数 |
| f32::from_bits(bits: u64) -> f32 | 整数位模式构造 |
| f32::to_string(self) -> String | 字符串 |
| f32::parse(s: &str) -> ?f32 | 解析 |
| f32::from_str(s: &str) -> Result<f32, str> | 解析（Result 版） |
| f32::NAN -> f32 | NaN 常量 |
| f32::INFINITY -> f32 | +∞ 常量 |
| f32::NEG_INFINITY -> f32 | -∞ 常量 |
| f32::EPSILON -> f32 | 机器 epsilon |
| f32::MIN -> f32 | 最小正规数 |
| f32::MAX -> f32 | 最大有限数 |

| 签名（f64） | 说明 |
|---|---|
| f64::abs(self) -> f64 | 绝对值 |
| f64::neg(self) -> f64 | 取负 |
| f64::sqrt(self) -> f64 | 平方根 |
| f64::cbrt(self) -> f64 | 立方根 |
| f64::floor(self) -> f64 | 向下取整 |
| f64::ceil(self) -> f64 | 向上取整 |
| f64::round(self) -> f64 | 四舍五入 |
| f64::trunc(self) -> f64 | 向零取整 |
| f64::fract(self) -> f64 | 小数部分 |
| f64::signum(self) -> f64 | 符号函数 |
| f64::min(self, o: f64) -> f64 | 最小值 |
| f64::max(self, o: f64) -> f64 | 最大值 |
| f64::clamp(self, lo: f64, hi: f64) -> f64 | 夹取 |
| f64::pow(self, e: f64) -> f64 | 幂 |
| f64::powi(self, n: i32) -> f64 | 整数次幂 |
| f64::exp(self) -> f64 | e^x |
| f64::exp2(self) -> f64 | 2^x |
| f64::ln(self) -> f64 | 自然对数 |
| f64::log2(self) -> f64 | 以 2 为底对数 |
| f64::log10(self) -> f64 | 以 10 为底对数 |
| f64::log(self, base: f64) -> f64 | 任意底对数 |
| f64::sin(self) -> f64 | 正弦 |
| f64::cos(self) -> f64 | 余弦 |
| f64::tan(self) -> f64 | 正切 |
| f64::asin(self) -> f64 | 反正弦 |
| f64::acos(self) -> f64 | 反余弦 |
| f64::atan(self) -> f64 | 反正切 |
| f64::atan2(y: f64, x: f64) -> f64 | atan2 |
| f64::hypot(x: f64, y: f64) -> f64 | sqrt(x²+y²) |
| f64::sinh(self) -> f64 | 双曲正弦 |
| f64::cosh(self) -> f64 | 双曲余弦 |
| f64::tanh(self) -> f64 | 双曲正切 |
| f64::asinh(self) -> f64 | 反双曲正弦 |
| f64::acosh(self) -> f64 | 反双曲余弦 |
| f64::atanh(self) -> f64 | 反双曲正切 |
| f64::recip(self) -> f64 | 1/x |
| f64::to_degrees(self) -> f64 | 弧度转角度 |
| f64::to_radians(self) -> f64 | 角度转弧度 |
| f64::is_nan(self) -> bool | 是否 NaN |
| f64::is_infinite(self) -> bool | 是否无穷 |
| f64::is_finite(self) -> bool | 是否有限 |
| f64::is_normal(self) -> bool | 是否正规数 |
| f64::is_sign_positive(self) -> bool | 符号位正 |
| f64::is_sign_negative(self) -> bool | 符号位负 |
| f64::to_bits(self) -> u64 | 位模式转整数 |
| f64::from_bits(bits: u64) -> f64 | 整数位模式构造 |
| f64::to_string(self) -> String | 字符串 |
| f64::parse(s: &str) -> ?f64 | 解析 |
| f64::from_str(s: &str) -> Result<f64, str> | 解析（Result 版） |
| f64::NAN -> f64 | NaN 常量 |
| f64::INFINITY -> f64 | +∞ 常量 |
| f64::NEG_INFINITY -> f64 | -∞ 常量 |
| f64::EPSILON -> f64 | 机器 epsilon |
| f64::MIN -> f64 | 最小正规数 |
| f64::MAX -> f64 | 最大有限数 |

| 签名（char） | 说明 |
|---|---|
| char::from_u32(v: u32) -> ?char | 从码点构造（非法返回 none） |
| char::to_u32(self) -> u32 | 码点 |
| char::eq(self, o: char) -> bool | 相等 |
| char::cmp(self, o: char) -> Ordering | 三路比较 |
| char::is_digit(self, radix: u32) -> bool | 是否为某进制数字 |
| char::is_alpha(self) -> bool | 是否字母 |
| char::is_alphanumeric(self) -> bool | 是否字母数字 |
| char::is_whitespace(self) -> bool | 是否空白 |
| char::is_uppercase(self) -> bool | 是否大写 |
| char::is_lowercase(self) -> bool | 是否小写 |
| char::to_uppercase(self) -> char | 大写 |
| char::to_lowercase(self) -> char | 小写 |
| char::to_string(self) -> String | 字符串 |
| char::escape_debug(self) -> String | 转义调试串 |
| char::escape_unicode(self) -> String | Unicode 转义 |

| 签名（bool） | 说明 |
|---|---|
| bool::to_int(self) -> i64 | true=1 false=0 |
| bool::to_string(self) -> String | "true"/"false" |
| bool::from_int(v: i64) -> bool | 0=false 非零=true |
| bool::not(self) -> bool | 逻辑非 |
| bool::and(self, o: bool) -> bool | 逻辑与 |
| bool::or(self, o: bool) -> bool | 逻辑或 |
| bool::xor(self, o: bool) -> bool | 逻辑异或 |
| bool::parse(s: &str) -> ?bool | 解析 |

| 签名（Ordering） | 说明 |
|---|---|
| Ordering::Less | 小于 |
| Ordering::Equal | 相等 |
| Ordering::Greater | 大于 |
| Ordering::is_eq(self) -> bool | 是否 Equal |
| Ordering::is_ne(self) -> bool | 是否非 Equal |
| Ordering::is_lt(self) -> bool | 是否 Less |
| Ordering::is_gt(self) -> bool | 是否 Greater |
| Ordering::reverse(self) -> Ordering | 反转 |
### 8.2 `std.text` —— 文本、字符串、正则、Unicode

`String` 是可增长的 UTF-8 字符串；`&str` 是字符串切片视图。

| 签名（String） | 说明 |
|---|---|
| String::new() -> String | 新建空串 |
| String::from(s: &str) -> String | 从切片构造 |
| String::with_capacity(n: usize) -> String | 预分配容量 |
| String::len(self) -> usize | 字节长度 |
| String::is_empty(self) -> bool | 是否为空 |
| String::capacity(self) -> usize | 容量（字节） |
| String::push(&mut self, c: char) | 追加字符 |
| String::push_str(&mut self, s: &str) | 追加切片 |
| String::pop(&mut self) -> ?char | 弹出末尾字符 |
| String::clear(&mut self) | 清空 |
| String::truncate(&mut self, n: usize) | 截断到 n 字节 |
| String::insert(&mut self, idx: usize, c: char) | 在 idx 插入字符 |
| String::insert_str(&mut self, idx: usize, s: &str) | 在 idx 插入串 |
| String::remove(&mut self, idx: usize) -> char | 移除 idx 处字符 |
| String::remove_range(&mut self, start: usize, end: usize) | 删除字节区间 |
| String::reserve(&mut self, n: usize) | 保留容量 |
| String::shrink_to_fit(&mut self) | 收缩到合适容量 |
| String::as_str(self) -> &str | 借用为切片 |
| String::as_bytes(self) -> &[u8] | 借用为字节切片 |
| String::as_mut_vec(&mut self) -> &mut Vec<u8> | 借用为可变字节向量 |
| String::clone(self) -> String | 克隆 |
| String::eq(self, o: &str) -> bool | 相等 |
| String::cmp(self, o: &str) -> Ordering | 字典序比较 |
| String::contains(self, pat: &str) -> bool | 是否包含 |
| String::starts_with(self, pat: &str) -> bool | 前缀 |
| String::ends_with(self, pat: &str) -> bool | 后缀 |
| String::find(self, pat: &str) -> ?usize | 查找首次出现 |
| String::rfind(self, pat: &str) -> ?usize | 查找末次出现 |
| String::find_many(self, pat: &str) -> Vec<usize> | 所有出现位置 |
| String::replace(&mut self, from: &str, to: &str) | 替换全部 |
| String::replacen(self, from: &str, to: &str, n: usize) -> String | 替换前 n 次 |
| String::replace_range(&mut self, range: Range, to: &str) | 替换区间 |
| String::trim(self) -> &str | 去两端空白 |
| String::trim_start(self) -> &str | 去左端空白 |
| String::trim_end(self) -> &str | 去右端空白 |
| String::trim_matches(self, pat: char) -> &str | 去两端指定字符 |
| String::trim_start_matches(self, pat: &str) -> &str | 去前缀串 |
| String::trim_end_matches(self, pat: &str) -> &str | 去后缀串 |
| String::to_uppercase(self) -> String | 转大写 |
| String::to_lowercase(self) -> String | 转小写 |
| String::to_titlecase(self) -> String | 转标题大小写 |
| String::chars(self) -> Chars | 字符迭代器 |
| String::char_indices(self) -> CharIndices | 字符+字节位置迭代 |
| String::bytes(self) -> Bytes | 字节迭代器 |
| String::split(self, pat: &str) -> Split | 按分隔串拆分 |
| String::split_whitespace(self) -> SplitWhitespace | 按空白拆分 |
| String::split_terminator(self, pat: &str) -> Split | 按终止符拆分 |
| String::rsplit(self, pat: &str) -> RSplit | 反向拆分 |
| String::lines(self) -> Lines | 按行迭代 |
| String::match_indices(self, pat: &str) -> MatchIndices | 匹配位置+子串 |
| String::matches(self, pat: &str) -> Matches | 匹配子串迭代 |
| String::get(self, idx: usize) -> ?char | 按下标取字符（字节位置） |
| String::get_range(self, start: usize, end: usize) -> ?&str | 取字节切片 |
| String::repeat(n: usize) -> String | 重复 n 次 |
| String::concat(parts: &[&str]) -> String | 拼接 |
| String::join(parts: &[&str], sep: &str) -> String | 用 sep 拼接 |
| String::from_utf8(bytes: Vec<u8>) -> Result<String, FromUtf8Error> | 从字节构造 |
| String::from_utf8_lossy(bytes: &[u8]) -> String | 损失式从字节构造 |
| String::from_char(c: char, n: usize) -> String | 重复字符 n 次 |
| String::is_ascii(self) -> bool | 是否纯 ASCII |
| String::eq_ignore_ascii_case(self, o: &str) -> bool | ASCII 忽略大小写比较 |
| String::to_ascii_uppercase(self) -> String | ASCII 大写 |
| String::to_ascii_lowercase(self) -> String | ASCII 小写 |
| String::escape_debug(self) -> String | 调试转义 |
| String::escape_default(self) -> String | 默认转义 |
| String::escape_unicode(self) -> String | Unicode 转义 |
| String::len_utf16(self) -> usize | UTF-16 码元长度 |
| String::encode_utf16(self) -> EncodeUtf16 | UTF-16 编码迭代 |
| String::parse_int(self, radix: u32) -> Result<i64, str> | 解析为整数 |
| String::parse_float(self) -> Result<f64, str> | 解析为浮点 |
| String::contains_char(self, c: char) -> bool | 是否含字符 |
| String::strip_prefix(self, prefix: &str) -> ?&str | 去前缀返回剩余 |
| String::strip_suffix(self, suffix: &str) -> ?&str | 去后缀返回剩余 |
| String::distance(self, o: &str) -> usize | 编辑距离（Levenshtein） |
| String::levenshtein(self, o: &str) -> usize | 同 distance |
| String::hamming(self, o: &str) -> Result<usize, str> | 汉明距离 |
| String::reverse(self) -> String | 字符反转 |
| String::pad_start(self, n: usize, c: char) -> String | 左端填充到 n 字符 |
| String::pad_end(self, n: usize, c: char) -> String | 右端填充到 n 字符 |
| String::center(self, n: usize, c: char) -> String | 居中填充 |
| String::count(self, pat: &str) -> usize | 计数出现次数 |
| String::to_vec(self) -> Vec<u8> | 转字节向量 |
| String::with_capacity_and_shrink(...) -> String | 组合构造 |

| 签名（StringBuilder） | 说明 |
|---|---|
| StringBuilder::new() -> StringBuilder | 新建 |
| StringBuilder::with_capacity(n: usize) -> StringBuilder | 预分配 |
| StringBuilder::push_str(&mut self, s: &str) | 追加串 |
| StringBuilder::push_char(&mut self, c: char) | 追加字符 |
| StringBuilder::push_int(&mut self, v: i64) | 追加整数 |
| StringBuilder::push_float(&mut self, v: f64) | 追加浮点 |
| StringBuilder::push_bool(&mut self, b: bool) | 追加布尔 |
| StringBuilder::build(self) -> String | 生成 String |
| StringBuilder::len(self) -> usize | 长度 |
| StringBuilder::is_empty(self) -> bool | 是否空 |
| StringBuilder::clear(&mut self) | 清空 |
| StringBuilder::capacity(self) -> usize | 容量 |
| StringBuilder::reserve(&mut self, n: usize) | 保留容量 |
| StringBuilder::as_str(self) -> &str | 当前内容切片 |

| 签名（Regex / Match / Captures） | 说明 |
|---|---|
| Regex::new(pattern: &str) -> Result<Regex, RegexError> | 编译正则 |
| Regex::is_match(self, text: &str) -> bool | 是否匹配 |
| Regex::find(self, text: &str) -> ?Match | 首次匹配 |
| Regex::find_iter(self, text: &str) -> MatchIter | 所有匹配迭代 |
| Regex::captures(self, text: &str) -> ?Captures | 捕获组 |
| Regex::captures_iter(self, text: &str) -> CapturesIter | 所有捕获 |
| Regex::replace(self, text: &str, rep: &str) -> String | 替换 |
| Regex::replacen(self, text: &str, rep: &str, n: usize) -> String | 替换前 n |
| Regex::replace_all(self, text: &str, rep: &str) -> String | 替换全部 |
| Regex::split(self, text: &str) -> Split | 按正则拆分 |
| Regex::as_str(self) -> &str | 原始模式 |
| Regex::size(self) -> usize | 编译后内存占用 |
| Match::as_str(self) -> &str | 匹配文本 |
| Match::start(self) -> usize | 起始字节位置 |
| Match::end(self) -> usize | 结束字节位置 |
| Captures::get(self, i: usize) -> ?Match | 第 i 个捕获组 |

| 签名（unicode 模块） | 说明 |
|---|---|
| unicode::len(text: &str) -> usize | 字符数（码点数） |
| unicode::is_numeric(c: char) -> bool | 是否数字 |
| unicode::is_alphabetic(c: char) -> bool | 是否字母 |
| unicode::is_whitespace(c: char) -> bool | 是否空白 |
| unicode::is_control(c: char) -> bool | 是否控制字符 |
| unicode::is_punctuation(c: char) -> bool | 是否标点 |
| unicode::is_symbol(c: char) -> bool | 是否符号 |
| unicode::is_mark(c: char) -> bool | 是否组合标记 |
| unicode::is_upper(c: char) -> bool | 是否大写 |
| unicode::is_lower(c: char) -> bool | 是否小写 |
| unicode::to_upper(c: char) -> char | 大写 |
| unicode::to_lower(c: char) -> char | 小写 |
| unicode::to_title(c: char) -> char | 标题大小写 |
| unicode::width(c: char) -> u8 | 显示宽度（1 或 2） |
| unicode::general_category(c: char) -> UnicodeCategory | Unicode 类别 |
| unicode::block(c: char) -> UnicodeBlock | 所在 Unicode 块 |
| unicode::name(c: char) -> String | 字符名 |
| unicode::script(c: char) -> UnicodeScript | 书写系统 |
| unicode::normalize_nfd(s: &str) -> String | NFD 归一化 |
| unicode::normalize_nfc(s: &str) -> String | NFC 归一化 |
| unicode::normalize_nfkd(s: &str) -> String | NFKD 归一化 |
| unicode::normalize_nfkc(s: &str) -> String | NFKC 归一化 |
| unicode::is_normalized(s: &str, form: NormalizationForm) -> bool | 是否已归一化 |
| unicode::graphemes(s: &str) -> GraphemeIter | 字素簇迭代 |
| unicode::words(s: &str) -> WordIter | 分词迭代 |
| unicode::sentences(s: &str) -> SentenceIter | 分句迭代 |
| unicode::emoji_presentation(c: char) -> bool | 是否 emoji 呈现 |
| unicode::join(s: &[&str], sep: &str) -> String | 拼接 |
| unicode::escape(s: &str) -> String | 转义为 ASCII |
| unicode::unescape(s: &str) -> Result<String, str> | 反转义 |

### 8.3 `std.collections` —— 容器与迭代器

所有容器泛型于 `T`；迭代器适配器 30+。

| 签名（Vec<T>） | 说明 |
|---|---|
| Vec::new() -> Vec<T> | 新建空向量 |
| Vec::with_capacity(n: usize) -> Vec<T> | 预分配 |
| Vec::from(v: &[T]) -> Vec<T> | 从切片构造 |
| Vec::with_len(n: usize) -> Vec<T> | 指定长度（未初始化） |
| Vec::len(self) -> usize | 长度 |
| Vec::is_empty(self) -> bool | 是否空 |
| Vec::capacity(self) -> usize | 容量 |
| Vec::push(&mut self, v: T) | 末尾追加 |
| Vec::pop(&mut self) -> ?T | 弹出末尾 |
| Vec::insert(&mut self, idx: usize, v: T) | 插入 |
| Vec::remove(&mut self, idx: usize) -> T | 移除并返回 |
| Vec::swap_remove(&mut self, idx: usize) -> T | 交换到末尾再弹出（O(1)） |
| Vec::clear(&mut self) | 清空 |
| Vec::truncate(&mut self, n: usize) | 截断到 n |
| Vec::reserve(&mut self, n: usize) | 保留容量 |
| Vec::shrink_to_fit(&mut self) | 收缩 |
| Vec::get(self, idx: usize) -> ?&T | 借用元素 |
| Vec::get_mut(self, idx: usize) -> ?&mut T | 可变借用 |
| Vec::first(self) -> ?&T | 首元素 |
| Vec::last(self) -> ?&T | 末元素 |
| Vec::first_mut(self) -> ?&mut T | 首元素可变 |
| Vec::last_mut(self) -> ?&mut T | 末元素可变 |
| Vec::as_slice(self) -> &[T] | 借用切片 |
| Vec::as_mut_slice(self) -> &mut [T] | 可变切片 |
| Vec::append(&mut self, other: &mut Vec<T>) | 追加另一向量 |
| Vec::split_off(&mut self, at: usize) -> Vec<T> | 从 at 切出 |
| Vec::drain(&mut self, range: Range) -> Drain<T> | 排空区间 |
| Vec::retain(&mut self, f: Fn(T) -> bool) | 保留满足条件者 |
| Vec::dedup(&mut self) | 去重相邻重复 |
| Vec::dedup_by(&mut self, f: Fn(T,T) -> bool) | 按谓词去重 |
| Vec::resize(&mut self, n: usize, v: T) | 调整长度（填充 v） |
| Vec::extend(&mut self, iter: Iter<T>) | 扩展迭代器 |
| Vec::contains(self, v: &T) -> bool | 包含判断 |
| Vec::starts_with(self, other: &[T]) -> bool | 前缀切片判断 |
| Vec::ends_with(self, other: &[T]) -> bool | 后缀切片判断 |
| Vec::sort(&mut self) | 升序排序 |
| Vec::sort_by(&mut self, f: Fn(T,T) -> Ordering) | 按比较函数排序 |
| Vec::sort_unstable(&mut self) | 不稳定排序（更快） |
| Vec::reverse(&mut self) | 反转 |
| Vec::binary_search(self, v: &T) -> Result<usize, usize> | 二分查找 |
| Vec::iter(self) -> Iter<T> | 迭代器 |
| Vec::iter_mut(self) -> IterMut<T> | 可变迭代器 |
| Vec::into_iter(self) -> IntoIter<T> | 消费迭代器 |
| Vec::chunks(self, n: usize) -> Chunks<T> | 定长块迭代 |
| Vec::windows(self, n: usize) -> Windows<T> | 滑动窗口 |
| Vec::join(self, sep: &str) -> String | 拼接（元素转串） |
| Vec::sum(self) -> T | 求和（数值型） |
| Vec::product(self) -> T | 求积 |
| Vec::min(self) -> ?T | 最小元素 |
| Vec::max(self) -> ?T | 最大元素 |
| Vec::clone(self) -> Vec<T> | 克隆 |
| Vec::eq(self, o: &[T]) -> bool | 切片相等 |
| Vec::as_ptr(self) -> *const T | 裸指针 |
| Vec::as_mut_ptr(self) -> *mut T | 可变裸指针 |
| Vec::leak(self) -> &mut [T] | 泄漏为静态切片 |

| 签名（Deque<T>） | 说明 |
|---|---|
| Deque::new() -> Deque<T> | 新建 |
| Deque::with_capacity(n: usize) -> Deque<T> | 预分配 |
| Deque::len(self) -> usize | 长度 |
| Deque::is_empty(self) -> bool | 是否空 |
| Deque::capacity(self) -> usize | 容量 |
| Deque::push_front(&mut self, v: T) | 队首入队 |
| Deque::push_back(&mut self, v: T) | 队尾入队 |
| Deque::pop_front(&mut self) -> ?T | 队首出队 |
| Deque::pop_back(&mut self) -> ?T | 队尾出队 |
| Deque::front(self) -> ?&T | 队首借用 |
| Deque::back(self) -> ?&T | 队尾借用 |
| Deque::get(self, idx: usize) -> ?&T | 按下标借用 |
| Deque::get_mut(self, idx: usize) -> ?&mut T | 按下标可变借用 |
| Deque::contains(self, v: &T) -> bool | 包含 |
| Deque::clear(&mut self) | 清空 |
| Deque::append(&mut self, other: &mut Deque<T>) | 拼接 |
| Deque::iter(self) -> Iter<T> | 迭代 |
| Deque::iter_mut(self) -> IterMut<T> | 可变迭代 |
| Deque::truncate(&mut self, n: usize) | 截断 |
| Deque::reserve(&mut self, n: usize) | 保留容量 |
| Deque::rotate_left(&mut self, n: usize) | 左旋转 |
| Deque::rotate_right(&mut self, n: usize) | 右旋转 |

| 签名（Map<K,V>） | 说明 |
|---|---|
| Map::new() -> Map<K, V> | 新建空表 |
| Map::with_capacity(n: usize) -> Map<K, V> | 预分配 |
| Map::len(self) -> usize | 条目数 |
| Map::is_empty(self) -> bool | 是否空 |
| Map::capacity(self) -> usize | 桶容量 |
| Map::insert(&mut self, k: K, v: V) -> ?V | 插入，返回旧值 |
| Map::get(self, k: &K) -> ?&V | 按键借用 |
| Map::get_mut(self, k: &K) -> ?&mut V | 按键可变借用 |
| Map::contains_key(self, k: &K) -> bool | 是否含键 |
| Map::remove(&mut self, k: &K) -> ?V | 按键删除并返回值 |
| Map::remove_entry(&mut self, k: &K) -> ?(K, V) | 按键删除并返回条目 |
| Map::clear(&mut self) | 清空 |
| Map::keys(self) -> Keys<K, V> | 键迭代 |
| Map::values(self) -> Values<K, V> | 值迭代 |
| Map::values_mut(self) -> ValuesMut<K, V> | 值可变迭代 |
| Map::iter(self) -> Iter<K, V> | 键值对迭代 |
| Map::iter_mut(self) -> IterMut<K, V> | 键值对可变迭代 |
| Map::entry(&mut self, k: K) -> Entry<K, V> | Entry API |
| Map::or_insert(&mut self, k: K, v: V) -> &mut V | 不存在则插入 |
| Map::or_insert_with(&mut self, k: K, f: Fn() -> V) -> &mut V | 不存在则用闭包插入 |
| Map::retain(&mut self, f: Fn(K,V) -> bool) | 保留满足条件 |
| Map::merge(&mut self, other: Map<K, V>) | 合并另一表 |
| Map::clone(self) -> Map<K, V> | 克隆 |
| Map::eq(self, o: &Map<K,V>) -> bool | 相等 |
| Map::len_hint(self) -> usize | 长度提示 |

| 签名（Set<T>） | 说明 |
|---|---|
| Set::new() -> Set<T> | 新建 |
| Set::with_capacity(n: usize) -> Set<T> | 预分配 |
| Set::len(self) -> usize | 元素数 |
| Set::is_empty(self) -> bool | 是否空 |
| Set::insert(&mut self, v: T) -> bool | 插入，返回是否新插入 |
| Set::remove(&mut self, v: &T) -> bool | 删除，返回是否存在 |
| Set::contains(self, v: &T) -> bool | 包含 |
| Set::clear(&mut self) | 清空 |
| Set::iter(self) -> Iter<T> | 迭代 |
| Set::union(self, o: &Set<T>) -> Union<T> | 并集 |
| Set::intersection(self, o: &Set<T>) -> Intersection<T> | 交集 |
| Set::difference(self, o: &Set<T>) -> Difference<T> | 差集 |
| Set::symmetric_difference(self, o: &Set<T>) -> SymDifference<T> | 对称差 |
| Set::is_subset(self, o: &Set<T>) -> bool | 是否子集 |
| Set::is_superset(self, o: &Set<T>) -> bool | 是否超集 |
| Set::is_disjoint(self, o: &Set<T>) -> bool | 是否不相交 |
| Set::clone(self) -> Set<T> | 克隆 |

| 签名（SortedMap<K,V>） | 说明 |
|---|---|
| SortedMap::new() -> SortedMap<K, V> | 新建红黑树映射 |
| SortedMap::len(self) -> usize | 条目数 |
| SortedMap::is_empty(self) -> bool | 是否空 |
| SortedMap::insert(&mut self, k: K, v: V) -> ?V | 插入 |
| SortedMap::get(self, k: &K) -> ?&V | 查找 |
| SortedMap::get_mut(self, k: &K) -> ?&mut V | 可变查找 |
| SortedMap::remove(&mut self, k: &K) -> ?V | 删除 |
| SortedMap::contains_key(self, k: &K) -> bool | 含键 |
| SortedMap::first_key(self) -> ?&K | 最小键 |
| SortedMap::last_key(self) -> ?&K | 最大键 |
| SortedMap::first_entry(self) -> ?(K, V) | 最小条目 |
| SortedMap::last_entry(self) -> ?(K, V) | 最大条目 |
| SortedMap::pop_first(&mut self) -> ?(K, V) | 弹出最小 |
| SortedMap::pop_last(&mut self) -> ?(K, V) | 弹出最大 |
| SortedMap::range(self, start: Bound<K>, end: Bound<K>) -> Range<K,V> | 范围迭代 |
| SortedMap::iter(self) -> Iter<K,V> | 有序迭代 |
| SortedMap::keys(self) -> Keys<K,V> | 有序键迭代 |
| SortedMap::values(self) -> Values<K,V> | 有序值迭代 |
| SortedMap::clear(&mut self) | 清空 |
| SortedMap::clone(self) -> SortedMap<K,V> | 克隆 |

| 签名（Iter<T> 适配器） | 说明 |
|---|---|
| Iter<T>::next(self) -> ?T | 取下一个 |
| Iter<T>::next_back(self) -> ?T | 反向取下一个（DoubleEnded） |
| Iter<T>::count(self) -> usize | 消耗并计数 |
| Iter<T>::last(self) -> ?T | 取最后一个 |
| Iter<T>::nth(self, n: usize) -> ?T | 第 n 个 |
| Iter<T>::step_by(self, n: usize) -> StepBy<T> | 步长 n |
| Iter<T>::chain<U>(self, other: U) -> Chain<T, U> | 连接两个迭代 |
| Iter<T>::zip<U>(self, other: U) -> Zip<T, U> | 拉链 |
| Iter<T>::map<B>(self, f: Fn(T) -> B) -> Map<T, B> | 映射 |
| Iter<T>::filter(self, f: Fn(T) -> bool) -> Filter<T> | 过滤 |
| Iter<T>::filter_map<B>(self, f: Fn(T) -> ?B) -> FilterMap<T,B> | 过滤+映射 |
| Iter<T>::enumerate(self) -> Enumerate<T> | 枚举 (索引, 值) |
| Iter<T>::peekable(self) -> Peekable<T> | 可窥视 |
| Iter<T>::skip(self, n: usize) -> Skip<T> | 跳过 n 个 |
| Iter<T>::take(self, n: usize) -> Take<T> | 取前 n 个 |
| Iter<T>::skip_while(self, f: Fn(T)->bool) -> SkipWhile<T> | 跳过满足前缀 |
| Iter<T>::take_while(self, f: Fn(T)->bool) -> TakeWhile<T> | 取满足前缀 |
| Iter<T>::flat_map<B, U>(self, f: Fn(T)->U) -> FlatMap<T,B,U> | 扁平化映射 |
| Iter<T>::flatten<B>(self) -> Flatten<T,B> | 扁平化嵌套 |
| Iter<T>::fuse(self) -> Fuse<T> | 熔断（首个 None 后不再调用 next） |
| Iter<T>::inspect(self, f: Fn(T)) -> Inspect<T> | 窥视副作用 |
| Iter<T>::collect<B>(self) -> B | 收集为容器 |
| Iter<T>::partition<B>(self, f: Fn(T)->bool) -> (B, B) | 分区 |
| Iter<T>::fold<B>(self, init: B, f: Fn(B,T)->B) -> B | 左折叠 |
| Iter<T>::reduce(self, f: Fn(T,T)->T) -> ?T | 归约 |
| Iter<T>::all(self, f: Fn(T)->bool) -> bool | 全部满足 |
| Iter<T>::any(self, f: Fn(T)->bool) -> bool | 任一满足 |
| Iter<T>::find(self, f: Fn(T)->bool) -> ?T | 查找首个 |
| Iter<T>::position(self, f: Fn(T)->bool) -> ?usize | 查找位置 |
| Iter<T>::max(self) -> ?T | 最大值 |
| Iter<T>::min(self) -> ?T | 最小值 |
| Iter<T>::max_by_key<B>(self, f: Fn(T)->B) -> ?T | 按键取最大 |
| Iter<T>::min_by_key<B>(self, f: Fn(T)->B) -> ?T | 按键取最小 |
| Iter<T>::sum<B>(self) -> B | 求和 |
| Iter<T>::product<B>(self) -> B | 求积 |
| Iter<T>::cmp(self, o: Iter<T>) -> Ordering | 字典序比较 |
| Iter<T>::eq(self, o: Iter<T>) -> bool | 相等比较 |
| Iter<T>::unzip<A, B>(self) -> (Vec<A>, Vec<B>) | 解包为两个容器 |
| Iter<T>::cycle(self) -> Cycle<T> | 循环（无限） |
| Iter<T>::chunked(self, n: usize) -> ChunkIter<T> | 按块迭代 |

| 签名（Range / Bound） | 说明 |
|---|---|
| Range::new(start: T, end: T) -> Range<T> | 半开区间 |
| Range::contains(self, v: T) -> bool | 包含判断 |
| Range::len(self) -> usize | 区间长度 |
| Bound::Included(v: T) -> Bound<T> | 包含下界 |
| Bound::Excluded(v: T) -> Bound<T> | 排除下界 |
| Bound::Unbounded -> Bound<T> | 无界 |

### 8.4 `std.math` —— 数学函数与常量

60+ 函数与 20+ 常量。

| 签名（math 函数） | 说明 |
|---|---|
| math::sqrt(x: f64) -> f64 | 平方根 |
| math::cbrt(x: f64) -> f64 | 立方根 |
| math::hypot(x: f64, y: f64) -> f64 | sqrt(x²+y²) |
| math::pow(x: f64, y: f64) -> f64 | 幂 |
| math::powi(x: f64, n: i32) -> f64 | 整数次幂 |
| math::exp(x: f64) -> f64 | e^x |
| math::exp2(x: f64) -> f64 | 2^x |
| math::ln(x: f64) -> f64 | 自然对数 |
| math::log2(x: f64) -> f64 | 以 2 为底 |
| math::log10(x: f64) -> f64 | 以 10 为底 |
| math::log(x: f64, base: f64) -> f64 | 任意底 |
| math::sin(x: f64) -> f64 | 正弦 |
| math::cos(x: f64) -> f64 | 余弦 |
| math::tan(x: f64) -> f64 | 正切 |
| math::asin(x: f64) -> f64 | 反正弦 |
| math::acos(x: f64) -> f64 | 反余弦 |
| math::atan(x: f64) -> f64 | 反正切 |
| math::atan2(y: f64, x: f64) -> f64 | atan2 |
| math::sinh(x: f64) -> f64 | 双曲正弦 |
| math::cosh(x: f64) -> f64 | 双曲余弦 |
| math::tanh(x: f64) -> f64 | 双曲正切 |
| math::asinh(x: f64) -> f64 | 反双曲正弦 |
| math::acosh(x: f64) -> f64 | 反双曲余弦 |
| math::atanh(x: f64) -> f64 | 反双曲正切 |
| math::floor(x: f64) -> f64 | 向下取整 |
| math::ceil(x: f64) -> f64 | 向上取整 |
| math::round(x: f64) -> f64 | 四舍五入 |
| math::trunc(x: f64) -> f64 | 向零取整 |
| math::abs(x: f64) -> f64 | 绝对值 |
| math::signum(x: f64) -> f64 | 符号 |
| math::copysign(x: f64, y: f64) -> f64 | 复制符号 |
| math::min(x: f64, y: f64) -> f64 | 最小 |
| math::max(x: f64, y: f64) -> f64 | 最大 |
| math::clamp(x: f64, lo: f64, hi: f64) -> f64 | 夹取 |
| math::fract(x: f64) -> f64 | 小数部分 |
| math::modf(x: f64) -> (f64, f64) | 整数+小数分解 |
| math::fmod(x: f64, y: f64) -> f64 | 浮点取模 |
| math::remainder(x: f64, y: f64) -> f64 | IEEE 余数 |
| math::next_after(x: f64, y: f64) -> f64 | 下一可表示浮点数 |
| math::next_up(x: f64) -> f64 | 下一可表示浮点数（向上） |
| math::next_down(x: f64) -> f64 | 下一可表示浮点数（向下） |
| math::is_nan(x: f64) -> bool | 是否 NaN |
| math::is_infinite(x: f64) -> bool | 是否无穷 |
| math::is_finite(x: f64) -> bool | 是否有限 |
| math::is_normal(x: f64) -> bool | 是否正规数 |
| math::lerp(a: f64, b: f64, t: f64) -> f64 | 线性插值 |
| math::deg_to_rad(d: f64) -> f64 | 角度转弧度 |
| math::rad_to_deg(r: f64) -> f64 | 弧度转角度 |
| math::gcd(a: i64, b: i64) -> i64 | 最大公约数 |
| math::lcm(a: i64, b: i64) -> i64 | 最小公倍数 |
| math::factorial(n: u64) -> u64 | 阶乘 |
| math::comb(n: u64, k: u64) -> u64 | 组合数 C(n,k) |
| math::perm(n: u64, k: u64) -> u64 | 排列数 P(n,k) |
| math::fibonacci(n: u64) -> u64 | 斐波那契 |
| math::isqrt(n: u64) -> u64 | 整数平方根 |
| math::ilog2(n: u64) -> u32 | 整数 log2 |
| math::abs_diff(a: i64, b: i64) -> u64 | 无符号绝对差 |
| math::mul_add(a: f64, b: f64, c: f64) -> f64 | a*b+c（融合） |
| math::sin_cos(x: f64) -> (f64, f64) | 同时求 sin 与 cos |
| math::erf(x: f64) -> f64 | 误差函数 |
| math::erfc(x: f64) -> f64 | 补误差函数 |
| math::tgamma(x: f64) -> f64 | Gamma 函数 |
| math::lgamma(x: f64) -> (f64, i32) | ln|Gamma| + 符号 |
| math::beta(x: f64, y: f64) -> f64 | Beta 函数 |
| math::sinc(x: f64) -> f64 | sinc 函数 |
| math::sigmoid(x: f64) -> f64 | 逻辑 S 形函数 |
| math::softmax(logits: &[f64]) -> Vec<f64> | softmax |
| math::clamp01(x: f64) -> f64 | 夹到 [0,1] |

| 签名（math 常量） | 说明 |
|---|---|
| math::PI -> f64 | π ≈ 3.141592653589793 |
| math::TAU -> f64 | τ = 2π |
| math::E -> f64 | 自然对数底 e |
| math::SQRT_2 -> f64 | √2 |
| math::FRAC_1_SQRT_2 -> f64 | 1/√2 |
| math::FRAC_PI_2 -> f64 | π/2 |
| math::FRAC_PI_4 -> f64 | π/4 |
| math::FRAC_1_PI -> f64 | 1/π |
| math::FRAC_2_PI -> f64 | 2/π |
| math::LN_2 -> f64 | ln 2 |
| math::LN_10 -> f64 | ln 10 |
| math::LOG2_E -> f64 | log₂e |
| math::LOG10_E -> f64 | log₁₀e |
| math::EPSILON -> f64 | 机器 ε |
| math::INFINITY -> f64 | +∞ |
| math::NEG_INFINITY -> f64 | -∞ |
| math::NAN -> f64 | NaN |
| math::MAX -> f64 | 最大有限数 |
| math::MIN -> f64 | 最小正规数 |
| math::GOLDEN_RATIO -> f64 | 黄金比例 φ |
| math::PHI -> f64 | 同 GOLDEN_RATIO |

### 8.5 `std.io` —— 输入输出、字节流、缓冲区

零拷贝、流式 IO；`Read` / `Write` 是 trait。

| 签名（io 模块） | 说明 |
|---|---|
| io::stdin() -> Stdin | 标准输入句柄 |
| io::stdout() -> Stdout | 标准输出句柄 |
| io::stderr() -> Stderr | 标准错误句柄 |
| io::print(s: &str) | 打印到 stdout（无换行） |
| io::println(s: &str) | 打印到 stdout（换行） |
| io::eprint(s: &str) | 打印到 stderr |
| io::eprintln(s: &str) | 打印到 stderr（换行） |
| io::flush() -> Result<(), IoError> | 刷新 stdout |
| io::read_to_string(r: &mut dyn Read) -> Result<String, IoError> | 读到字符串 |
| io::read_to_end(r: &mut dyn Read) -> Result<Vec<u8>, IoError> | 读到字节向量 |
| io::copy(r: &mut dyn Read, w: &mut dyn Write) -> Result<u64, IoError> | 拷贝流 |
| io::sink() -> Sink | 丢弃输出 |
| io::repeat(byte: u8) -> Repeat | 无限重复字节 |
| io::Cursor::new(data: Vec<u8>) -> Cursor | 字节游标 |
| BufReader::new(r: impl Read) -> BufReader | 带缓冲读取 |
| BufWriter::new(w: impl Write) -> BufWriter | 带缓冲写入 |
| BufReader::read_line(&mut self, buf: &mut String) -> Result<usize, IoError> | 读一行 |
| BufReader::read_until(&mut self, delim: u8, buf: &mut Vec<u8>) -> Result<usize, IoError> | 读到分隔符 |
| BufReader::peek(&mut self) -> Result<u8, IoError> | 窥视下一字节 |
| BufReader::buffer(self) -> &[u8] | 当前缓冲区切片 |
| BufWriter::flush(&mut self) -> Result<(), IoError> | 刷新缓冲区 |
| BufWriter::get_ref(self) -> &impl Write | 获取底层 writer |
| BufWriter::get_mut(&mut self) -> &mut impl Write | 可变获取底层 writer |
| Bytes::new(data: Vec<u8>) -> Bytes | 不可变字节块 |
| Bytes::len(self) -> usize | 长度 |
| Bytes::is_empty(self) -> bool | 是否空 |
| Bytes::slice(self, start: usize, end: usize) -> Bytes | 切片 |
| Bytes::as_ref(self) -> &[u8] | 借用 |
| Bytes::eq(self, o: &[u8]) -> bool | 相等 |
| BytesMut::new() -> BytesMut | 可变字节块 |
| BytesMut::with_capacity(n: usize) -> BytesMut | 预分配 |
| BytesMut::put(&mut self, data: &[u8]) | 追加字节 |
| BytesMut::put_u8(&mut self, v: u8) | 追加 u8 |
| BytesMut::put_u16(&mut self, v: u16) | 追加 u16（小端） |
| BytesMut::put_u32(&mut self, v: u32) | 追加 u32（小端） |
| BytesMut::put_u64(&mut self, v: u64) | 追加 u64（小端） |
| BytesMut::put_f64(&mut self, v: f64) | 追加 f64 |
| BytesMut::freeze(self) -> Bytes | 冻结为 Bytes |
| BytesMut::len(self) -> usize | 长度 |
| BytesMut::clear(&mut self) | 清空 |

| 签名（Read / Write trait） | 说明 |
|---|---|
| Read::read(&mut self, buf: &mut [u8]) -> Result<usize, IoError> | 读入缓冲区 |
| Read::read_exact(&mut self, buf: &mut [u8]) -> Result<(), IoError> | 读满缓冲区 |
| Read::read_to_end(&mut self) -> Result<Vec<u8>, IoError> | 读到 EOF |
| Read::read_to_string(&mut self) -> Result<String, IoError> | 读到字符串 |
| Read::bytes(self) -> ByteIter<Self> | 字节迭代 |
| Read::chain<R: Read>(self, next: R) -> Chain<Self, R> | 连接两个流 |
| Read::take(self, limit: u64) -> Take<Self> | 限制读字节数 |
| Write::write(&mut self, buf: &[u8]) -> Result<usize, IoError> | 写入 |
| Write::write_all(&mut self, buf: &[u8]) -> Result<(), IoError> | 写满 |
| Write::write_fmt(&mut self, args: fmt::Arguments) -> Result<(), IoError> | 格式化写入 |
| Write::flush(&mut self) -> Result<(), IoError> | 刷新 |
| Write::by_ref(&mut self) -> &mut Self | 可变借用（不消耗所有权） |
| Seek::seek(&mut self, pos: SeekFrom) -> Result<u64, IoError> | 寻址 |
| Seek::stream_position(&mut self) -> Result<u64, IoError> | 当前位置 |
| Seek::rewind(&mut self) -> Result<(), IoError> | 回到开头 |
| Seek::stream_len(&mut self) -> Result<u64, IoError> | 流长度 |
| SeekFrom::Start(n: u64) -> SeekFrom | 从开头 |
| SeekFrom::Current(n: i64) -> SeekFrom | 从当前 |
| SeekFrom::End(n: i64) -> SeekFrom | 从末尾 |

### 8.6 `std.fs` —— 文件系统

跨平台文件系统操作；路径用 `std.path::Path`。

| 签名（fs 模块） | 说明 |
|---|---|
| fs::read(path: &str) -> Result<Vec<u8>, IoError> | 读整个文件 |
| fs::read_to_string(path: &str) -> Result<String, IoError> | 读整个文件为字符串 |
| fs::write(path: &str, data: &[u8]) -> Result<(), IoError> | 写入整个文件 |
| fs::write_string(path: &str, s: &str) -> Result<(), IoError> | 写入字符串 |
| fs::open(path: &str) -> Result<File, IoError> | 打开只读文件 |
| fs::create(path: &str) -> Result<File, IoError> | 创建/截断文件 |
| fs::create_dir(path: &str) -> Result<(), IoError> | 创建单级目录 |
| fs::create_dir_all(path: &str) -> Result<(), IoError> | 递归创建目录 |
| fs::remove_file(path: &str) -> Result<(), IoError> | 删除文件 |
| fs::remove_dir(path: &str) -> Result<(), IoError> | 删除空目录 |
| fs::remove_dir_all(path: &str) -> Result<(), IoError> | 递归删除目录 |
| fs::rename(from: &str, to: &str) -> Result<(), IoError> | 重命名/移动 |
| fs::copy(from: &str, to: &str) -> Result<u64, IoError> | 拷贝文件，返回字节数 |
| fs::metadata(path: &str) -> Result<Metadata, IoError> | 文件元数据 |
| fs::symlink_metadata(path: &str) -> Result<Metadata, IoError> | 符号链接元数据（不跟随） |
| fs::exists(path: &str) -> bool | 是否存在 |
| fs::is_file(path: &str) -> bool | 是否文件 |
| fs::is_dir(path: &str) -> bool | 是否目录 |
| fs::is_symlink(path: &str) -> bool | 是否符号链接 |
| fs::canonicalize(path: &str) -> Result<String, IoError> | 规范化为绝对路径 |
| fs::read_dir(path: &str) -> Result<ReadDir, IoError> | 列目录 |
| fs::read_link(path: &str) -> Result<String, IoError> | 读符号链接目标 |
| fs::hard_link(src: &str, dst: &str) -> Result<(), IoError> | 硬链接 |
| fs::soft_link(src: &str, dst: &str) -> Result<(), IoError> | 软链接 |
| fs::set_permissions(path: &str, perm: Permissions) -> Result<(), IoError> | 设置权限 |
| fs::set_modified(path: &str, time: SystemTime) -> Result<(), IoError> | 设置修改时间 |
| fs::set_accessed(path: &str, time: SystemTime) -> Result<(), IoError> | 设置访问时间 |
| fs::copy_dir_all(from: &str, to: &str) -> Result<u64, IoError> | 递归拷贝目录 |
| fs::tempdir() -> Result<TempDir, IoError> | 新建临时目录 |
| fs::tempfile() -> Result<File, IoError> | 新建临时文件 |
| fs::symlink_metadata_no_follow(...) -> Result<Metadata, IoError> | 不跟随符号链接 |
| fs::drive_list() -> Vec<String> | 列出盘符（Windows） |
| fs::current_exe() -> Result<String, IoError> | 当前可执行文件路径 |
| fs::current_dir() -> Result<String, IoError> | 当前工作目录 |
| fs::set_current_dir(path: &str) -> Result<(), IoError> | 切换工作目录 |
| File::read(&mut self, buf: &mut [u8]) -> Result<usize, IoError> | 读 |
| File::write(&mut self, buf: &[u8]) -> Result<usize, IoError> | 写 |
| File::read_to_end(&mut self) -> Result<Vec<u8>, IoError> | 读到末尾 |
| File::seek(&mut self, pos: SeekFrom) -> Result<u64, IoError> | 寻址 |
| File::sync_all(&self) -> Result<(), IoError> | 刷盘 |
| File::sync_data(&self) -> Result<(), IoError> | 刷数据（不含元数据） |
| File::set_len(&self, size: u64) -> Result<(), IoError> | 截断/扩展 |
| File::metadata(&self) -> Result<Metadata, IoError> | 元数据 |
| File::try_clone(&self) -> Result<File, IoError> | 克隆句柄 |
| File::set_permissions(&self, perm: Permissions) -> Result<(), IoError> | 设置权限 |
| Metadata::len(self) -> u64 | 文件大小 |
| Metadata::is_file(self) -> bool | 是否文件 |
| Metadata::is_dir(self) -> bool | 是否目录 |
| Metadata::is_symlink(self) -> bool | 是否符号链接 |
| Metadata::permissions(self) -> Permissions | 权限 |
| Metadata::modified(self) -> Result<SystemTime, IoError> | 修改时间 |
| Metadata::accessed(self) -> Result<SystemTime, IoError> | 访问时间 |
| Metadata::created(self) -> Result<SystemTime, IoError> | 创建时间 |
| Permissions::readonly(self) -> bool | 是否只读 |
| Permissions::set_readonly(&mut self, readonly: bool) | 设置只读 |
| Permissions::mode(self) -> u32 | Unix 权限位 |
| DirEntry::file_name(self) -> String | 条目名 |
| DirEntry::path(self) -> String | 完整路径 |
| DirEntry::metadata(self) -> Result<Metadata, IoError> | 元数据 |
| DirEntry::file_type(self) -> Result<FileType, IoError> | 类型 |
### 8.7 `std.time` —— 时间、日期、计时器

Duration 是时间段；Instant 是单调时钟；SystemTime 是墙钟；Date/DateTime 是日历时间。

| 签名（time 模块） | 说明 |
|---|---|
| Duration::ZERO -> Duration | 零时长 |
| Duration::from_nanos(n: u64) -> Duration | 从纳秒构造 |
| Duration::from_micros(n: u64) -> Duration | 从微秒构造 |
| Duration::from_millis(n: u64) -> Duration | 从毫秒构造 |
| Duration::from_secs(n: u64) -> Duration | 从秒构造 |
| Duration::from_secs_f64(n: f64) -> Duration | 从浮点秒构造 |
| Duration::as_nanos(self) -> u128 | 总纳秒 |
| Duration::as_micros(self) -> u128 | 总微秒 |
| Duration::as_millis(self) -> u128 | 总毫秒 |
| Duration::as_secs(self) -> u64 | 总秒 |
| Duration::as_secs_f64(self) -> f64 | 浮点秒 |
| Duration::add(self, o: Duration) -> Duration | 相加 |
| Duration::sub(self, o: Duration) -> Duration | 相减 |
| Duration::mul(self, n: f64) -> Duration | 缩放 |
| Duration::div(self, o: Duration) -> f64 | 比值 |
| Duration::cmp(self, o: Duration) -> Ordering | 比较 |
| Duration::is_zero(self) -> bool | 是否零 |
| Duration::format(self, fmt: &str) -> String | 格式化 |
| Instant::now() -> Instant | 当前单调时钟时刻 |
| Instant::elapsed(self) -> Duration | 距 now 的时长 |
| Instant::duration_since(self, earlier: Instant) -> Duration | 时间差 |
| Instant::checked_add(self, d: Duration) -> ?Instant | 安全加法 |
| Instant::cmp(self, o: Instant) -> Ordering | 比较 |
| SystemTime::now() -> SystemTime | 当前墙钟 |
| SystemTime::duration_since_epoch(self) -> Duration | 距 Unix epoch |
| SystemTime::from_unix_secs(secs: u64) -> SystemTime | 从 Unix 秒构造 |
| SystemTime::to_unix_secs(self) -> u64 | 转 Unix 秒 |
| SystemTime::to_date(self) -> DateTime | 转日历时间 |
| DateTime::now_local() -> DateTime | 当前本地日历时间 |
| DateTime::now_utc() -> DateTime | 当前 UTC 日历时间 |
| DateTime::new(y: i32, m: u32, d: u32, h: u32, mi: u32, s: u32) -> DateTime | 构造 |
| DateTime::year(self) -> i32 | 年 |
| DateTime::month(self) -> u32 | 月 |
| DateTime::day(self) -> u32 | 日 |
| DateTime::hour(self) -> u32 | 时 |
| DateTime::minute(self) -> u32 | 分 |
| DateTime::second(self) -> u32 | 秒 |
| DateTime::weekday(self) -> Weekday | 星期几 |
| DateTime::ordinal(self) -> u32 | 一年中的第几天 |
| DateTime::format(self, fmt: &str) -> String | strftime 格式化 |
| DateTime::parse(s: &str, fmt: &str) -> Result<DateTime, ParseError> | 解析 |
| DateTime::to_utc(self) -> DateTime | 转 UTC |
| DateTime::to_local(self) -> DateTime | 转本地 |
| DateTime::add_days(self, n: i64) -> DateTime | 加天数 |
| DateTime::sub_days(self, o: DateTime) -> i64 | 天数差 |
| Date::from_ymd(y: i32, m: u32, d: u32) -> Date | 构造日期 |
| Date::today() -> Date | 今天 |
| Date::format(self, fmt: &str) -> String | 格式化 |
| Date::cmp(self, o: Date) -> Ordering | 比较 |
| Weekday::Monday -> Weekday | 周一 |
| Weekday::Tuesday -> Weekday | 周二 |
| Weekday::Wednesday -> Weekday | 周三 |
| Weekday::Thursday -> Weekday | 周四 |
| Weekday::Friday -> Weekday | 周五 |
| Weekday::Saturday -> Weekday | 周六 |
| Weekday::Sunday -> Weekday | 周日 |
| Weekday::num_days_from_monday(self) -> u32 | 距周一天数 |
| Timer::after(d: Duration) -> chan () | 延时通道 |
| Timer::interval(d: Duration) -> chan () | 周期通道 |
| time::sleep(d: Duration) | 当前 task 睡眠 |
| time::timestamp() -> u64 | Unix 秒戳 |
| time::timestamp_millis() -> u64 | Unix 毫秒戳 |

### 8.8 `std.async` —— task / chan / select / 等待组

M:N 协程调度；channel 是 task 间唯一安全通信方式。

| 签名（async 模块） | 说明 |
|---|---|
| task::spawn<F, R>(f: Fn() -> R) -> JoinHandle<R> | 派生协程 |
| task::spawn_async<F, R>(f: Fn() -> Future<R>) -> JoinHandle<R> | 派生 async 协程 |
| task::yield_now() | 让出 CPU |
| task::current_id() -> TaskId | 当前 task ID |
| task::parallel<T, R>(items: &[T], f: Fn(T) -> R) -> Vec<R> | 并行 map |
| task::join_all<R>(handles: Vec<JoinHandle<R>>) -> Vec<R> | 等待全部 |
| task::select<R>(futures: &mut [Future<R>]) -> (R, usize) | 任意完成 |
| JoinHandle::join(self) -> R | 等待结果 |
| JoinHandle::cancel(self) | 取消 |
| JoinHandle::is_finished(self) -> bool | 是否完成 |
| chan::new<T>(cap: usize) -> chan T | 创建带缓冲通道 |
| chan::unbounded<T>() -> chan T | 创建无缓冲通道 |
| chan<T>::send(self, v: T) | 发送（阻塞至接收） |
| chan<T>::recv(self) -> T | 接收（阻塞至有值） |
| chan<T>::try_send(self, v: T) -> Result<(), T> | 尝试发送 |
| chan<T>::try_recv(self) -> Result<T, TryRecvError> | 尝试接收 |
| chan<T>::close(self) | 关闭 |
| chan<T>::is_closed(self) -> bool | 是否关闭 |
| chan<T>::len(self) -> usize | 当前缓冲长度 |
| chan<T>::cap(self) -> usize | 缓冲容量 |
| chan<T>::iter(self) -> ChanIter<T> | 迭代器 |
| select::new() -> Select | 构造 select 语句 |
| Select::add_recv<T>(self, ch: &chan T) -> usize | 注册接收分支 |
| Select::add_send<T>(self, ch: &chan T, v: T) -> usize | 注册发送分支 |
| Select::add_default(self) | 注册默认分支 |
| Select::wait(self) -> usize | 等待任一就绪，返回分支索引 |
| WaitGroup::new() -> WaitGroup | 新建等待组 |
| WaitGroup::add(self, n: u32) | 计数加 n |
| WaitGroup::done(self) | 计数减 1 |
| WaitGroup::wait(self) | 等待归零 |
| Future::poll(self, waker: Waker) -> Poll<T> | 轮询 Future |
| Waker::wake(self) | 唤醒任务 |
| async::sleep(d: Duration) -> Future<()> | 睡眠 Future |
| async::timeout<T>(d: Duration, fut: Future<T>) -> Result<T, TimeoutError> | 超时包装 |
| async::race<T>(a: Future<T>, b: Future<T>) -> Future<T> | 竞速 |
| async::join<T, U>(a: Future<T>, b: Future<U>) -> Future<(T, U)> | 同时等待 |
| async::spawn_local<F, R>(f: F) -> JoinHandle<R> | 当前线程局部派生 |

### 8.9 `std.net` —— 网络编程

TCP/UDP/HTTP；SocketAddr/IpAddr 地址类型。

| 签名（net 模块） | 说明 |
|---|---|
| net::TcpListener::bind(addr: &str) -> Result<TcpListener, NetError> | 绑定监听 |
| TcpListener::accept(self) -> Result<(TcpStream, SocketAddr), NetError> | 接受连接 |
| TcpListener::incoming(self) -> Incoming | 迭代接受连接 |
| TcpListener::local_addr(self) -> Result<SocketAddr, NetError> | 本地地址 |
| TcpListener::set_nonblocking(&mut self, nb: bool) | 设置非阻塞 |
| TcpListener::set_ttl(&mut self, ttl: u32) | 设置 TTL |
| net::TcpStream::connect(addr: &str) -> Result<TcpStream, NetError> | 连接 |
| TcpStream::peer_addr(self) -> Result<SocketAddr, NetError> | 对端地址 |
| TcpStream::local_addr(self) -> Result<SocketAddr, NetError> | 本地地址 |
| TcpStream::read(&mut self, buf: &mut [u8]) -> Result<usize, NetError> | 读 |
| TcpStream::write(&mut self, buf: &[u8]) -> Result<usize, NetError> | 写 |
| TcpStream::flush(&mut self) -> Result<(), NetError> | 刷新 |
| TcpStream::shutdown(&self, how: Shutdown) -> Result<(), NetError> | 关闭读/写/两端 |
| TcpStream::set_nodelay(&mut self, nodelay: bool) | 禁用 Nagle |
| TcpStream::set_ttl(&mut self, ttl: u32) | TTL |
| TcpStream::set_read_timeout(&mut self, d: Duration) | 读超时 |
| TcpStream::set_write_timeout(&mut self, d: Duration) | 写超时 |
| net::UdpSocket::bind(addr: &str) -> Result<UdpSocket, NetError> | 绑定 UDP |
| UdpSocket::send_to(&mut self, buf: &[u8], addr: &str) -> Result<usize, NetError> | 发送到 |
| UdpSocket::recv_from(&mut self, buf: &mut [u8]) -> Result<(usize, SocketAddr), NetError> | 接收 |
| UdpSocket::connect(&mut self, addr: &str) -> Result<(), NetError> | 连接（只收发固定对端） |
| UdpSocket::send(&mut self, buf: &[u8]) -> Result<usize, NetError> | 发送到已连接对端 |
| UdpSocket::recv(&mut self, buf: &[u8]) -> Result<usize, NetError> | 从已连接对端接收 |
| UdpSocket::set_broadcast(&mut self, b: bool) | 广播开关 |
| UdpSocket::set_read_timeout(&mut self, d: Duration) | 读超时 |
| SocketAddr::parse(s: &str) -> Result<SocketAddr, NetError> | 解析地址 |
| SocketAddr::ip(self) -> IpAddr | IP 部分 |
| SocketAddr::port(self) -> u16 | 端口 |
| SocketAddr::is_ipv4(self) -> bool | 是否 IPv4 |
| SocketAddr::is_ipv6(self) -> bool | 是否 IPv6 |
| SocketAddr::to_string(self) -> String | 字符串表示 |
| IpAddr::v4(a: u8, b: u8, c: u8, d: u8) -> IpAddr | IPv4 构造 |
| IpAddr::v6(...) -> IpAddr | IPv6 构造 |
| IpAddr::parse(s: &str) -> Result<IpAddr, NetError> | 解析 |
| IpAddr::is_loopback(self) -> bool | 环回地址 |
| IpAddr::is_private(self) -> bool | 私有地址 |
| IpAddr::is_multicast(self) -> bool | 组播地址 |
| IpAddr::to_string(self) -> String | 字符串 |
| net::resolve(host: &str, port: u16) -> Result<Vec<SocketAddr>, NetError> | DNS 解析 |
| net::get_hostname() -> Result<String, NetError> | 主机名 |
| net::get_host_by_name(host: &str) -> Result<Vec<IpAddr>, NetError> | 域名查询 |
| net::HttpClient::new() -> HttpClient | HTTP 客户端 |
| HttpClient::get(self, url: &str) -> Result<HttpResponse, NetError> | GET |
| HttpClient::post(self, url: &str, body: &[u8]) -> Result<HttpResponse, NetError> | POST |
| HttpClient::put(self, url: &str, body: &[u8]) -> Result<HttpResponse, NetError> | PUT |
| HttpClient::delete(self, url: &str) -> Result<HttpResponse, NetError> | DELETE |
| HttpClient::request(self, method: &str, url: &str) -> HttpRequest | 构造请求 |
| HttpClient::set_timeout(&mut self, d: Duration) | 超时 |
| HttpClient::set_header(&mut self, k: &str, v: &str) | 默认请求头 |
| HttpRequest::header(&mut self, k: &str, v: &str) | 设置请求头 |
| HttpRequest::body(&mut self, body: &[u8]) | 设置体 |
| HttpRequest::send(self) -> Result<HttpResponse, NetError> | 发送 |
| HttpResponse::status(self) -> u16 | 状态码 |
| HttpResponse::status_text(self) -> String | 状态文本 |
| HttpResponse::header(self, k: &str) -> ?String | 响应头 |
| HttpResponse::headers(self) -> Map<String, String> | 全部响应头 |
| HttpResponse::body(self) -> Vec<u8> | 响应体 |
| HttpResponse::body_string(self) -> Result<String, NetError> | 响应体字符串 |
| HttpResponse::json<T>(self) -> Result<T, JsonError> | 解析 JSON 体 |
| HttpServer::bind(addr: &str) -> HttpServer | 启动 HTTP 服务 |
| HttpServer::route(&mut self, method: &str, path: &str, handler: Fn(HttpRequest) -> HttpResponse) | 注册路由 |
| HttpServer::listen_and_serve(self) -> Result<(), NetError> | 开始服务 |
| Url::parse(s: &str) -> Result<Url, UrlError> | 解析 URL |
| Url::scheme(self) -> &str | 协议 |
| Url::host(self) -> ?&str | 主机 |
| Url::port(self) -> ?u16 | 端口 |
| Url::path(self) -> &str | 路径 |
| Url::query(self) -> &str | 查询串 |
| Url::fragment(self) -> ?&str | 片段 |
| Url::to_string(self) -> String | 序列化 |

### 8.10 `std.json` —— JSON 解析与序列化

动态 Value；也支持结构体到 JSON 的 derive。

| 签名（json 模块） | 说明 |
|---|---|
| json::parse(s: &str) -> Result<Value, JsonError> | 解析为 Value |
| json::stringify(v: &Value) -> String | 序列化为紧凑串 |
| json::stringify_pretty(v: &Value, indent: usize) -> String | 美化输出 |
| json::from_str<T>(s: &str) -> Result<T, JsonError> | 反序列化为 T |
| json::to_string<T>(v: &T) -> Result<String, JsonError> | 序列化为 T |
| Value::Null -> Value | null |
| Value::Bool(b: bool) -> Value | 布尔 |
| Value::Int(i: i64) -> Value | 整数 |
| Value::Float(f: f64) -> Value | 浮点 |
| Value::String(s: String) -> Value | 字符串 |
| Value::Array(arr: Vec<Value>) -> Value | 数组 |
| Value::Object(map: Map<String, Value>) -> Value | 对象 |
| Value::type(self) -> JsonType | 值类型 |
| Value::is_null(self) -> bool | 是否 null |
| Value::is_bool(self) -> bool | 是否布尔 |
| Value::is_int(self) -> bool | 是否整数 |
| Value::is_float(self) -> bool | 是否浮点 |
| Value::is_string(self) -> bool | 是否字符串 |
| Value::is_array(self) -> bool | 是否数组 |
| Value::is_object(self) -> bool | 是否对象 |
| Value::as_bool(self) -> ?bool | 转布尔 |
| Value::as_int(self) -> ?i64 | 转整数 |
| Value::as_float(self) -> ?f64 | 转浮点 |
| Value::as_str(self) -> ?&str | 转字符串 |
| Value::as_array(self) -> ?&Vec<Value> | 转数组 |
| Value::as_object(self) -> ?&Map<String, Value> | 转对象 |
| Value::get(self, k: &str) -> ?&Value | 对象按键取值 |
| Value::get_at(self, i: usize) -> ?&Value | 数组按下标取值 |
| Value::set(&mut self, k: &str, v: Value) | 对象按键赋值 |
| Value::push(&mut self, v: Value) | 数组追加 |
| Value::len(self) -> ?usize | 长度（数组/对象） |
| Value::contains_key(self, k: &str) -> bool | 对象含键 |
| Value::remove(&mut self, k: &str) -> ?Value | 对象删键 |
| Value::eq(self, o: &Value) -> bool | 相等 |
| Value::pointer(self, ptr: &str) -> ?&Value | JSON Pointer 查询 |
| Value::pointer_mut(self, ptr: &str) -> ?&mut Value | JSON Pointer 可变查询 |
| JsonType::Null | null 类型 |
| JsonType::Bool | 布尔类型 |
| JsonType::Int | 整数类型 |
| JsonType::Float | 浮点类型 |
| JsonType::String | 字符串类型 |
| JsonType::Array | 数组类型 |
| JsonType::Object | 对象类型 |

### 8.11 `std.xml` —— XML 解析

| 签名（xml 模块） | 说明 |
|---|---|
| xml::parse(s: &str) -> Result<Document, XmlError> | 解析文档 |
| Document::root(self) -> Node | 根节点 |
| Document::to_string(self) -> String | 序列化 |
| Node::element(tag: &str) -> Node | 构造元素节点 |
| Node::text(content: &str) -> Node | 构造文本节点 |
| Node::tag(self) -> ?&str | 标签名 |
| Node::text(self) -> &str | 文本内容 |
| Node::attr(self, k: &str) -> ?&str | 属性 |
| Node::set_attr(&mut self, k: &str, v: &str) | 设置属性 |
| Node::children(self) -> Vec<Node> | 子节点 |
| Node::child(self, i: usize) -> ?Node | 第 i 个子节点 |
| Node::parent(self) -> ?Node | 父节点 |
| Node::append(&mut self, child: Node) | 追加子节点 |
| Node::remove(&mut self, child: Node) | 移除子节点 |
| Node::select(self, query: &str) -> Vec<Node> | XPath/CSS 选择 |
| Node::select_first(self, query: &str) -> ?Node | 首个匹配 |
| Node::is_element(self) -> bool | 是否元素 |
| Node::is_text(self) -> bool | 是否文本 |
| Node::is_comment(self) -> bool | 是否注释 |
| Node::line(self) -> usize | 源文件行号 |

### 8.12 `std.base64` —— Base64 编解码

| 签名（base64 模块） | 说明 |
|---|---|
| base64::encode(data: &[u8]) -> String | 标准 Base64 编码 |
| base64::decode(s: &str) -> Result<Vec<u8>, Base64Error> | 标准 Base64 解码 |
| base64::encode_url(data: &[u8]) -> String | URL 安全 Base64 |
| base64::decode_url(s: &str) -> Result<Vec<u8>, Base64Error> | URL 安全 Base64 解码 |
| base64::encode_no_pad(data: &[u8]) -> String | 无填充编码 |
| base64::decode_no_pad(s: &str) -> Result<Vec<u8>, Base64Error> | 无填充解码 |
| base64::encode_as_str(data: &[u8]) -> &str | 编码为借用字符串 |

### 8.13 `std.random` —— 随机数生成

| 签名（random 模块） | 说明 |
|---|---|
| random::thread_rng() -> ThreadRng | 线程局部随机源 |
| random::seed_from(seed: u64) -> StdRng | 固定种子 RNG |
| random::random<T: Uniform>() -> T | 全局随机值 |
| random::random_range<T: Uniform>(lo: T, hi: T) -> T | 区间均匀分布 |
| random::random_bool(p: f64) -> bool | 概率布尔 |
| random::choose<T>(items: &[T]) -> ?&T | 随机选一个 |
| random::shuffle<T>(items: &mut [T]) | 随机洗牌 |
| random::sample<T, W>(items: &[T], weights: &[W], n: usize) -> Vec<T> | 加权采样 |
| ThreadRng::next_u64(&mut self) -> u64 | 下一个 u64 |
| ThreadRng::next_f64(&mut self) -> f64 | [0,1) 浮点 |
| ThreadRng::fill_bytes(&mut self, buf: &mut [u8]) | 填充字节 |
| StdRng::next_u64(&mut self) -> u64 | 下一个 u64 |
| StdRng::next_f64(&mut self) -> f64 | [0,1) 浮点 |
| StdRng::fill_bytes(&mut self, buf: &mut [u8]) | 填充字节 |
| random::normal(mean: f64, std_dev: f64) -> f64 | 正态分布 |
| random::exponential(lambda: f64) -> f64 | 指数分布 |
| random::uniform(lo: f64, hi: f64) -> f64 | 浮点均匀分布 |
| random::uuid_v4() -> Uuid | 随机 UUID v4 |
| random::secure_u64() -> u64 | 加密安全随机 |
| random::secure_bytes(buf: &mut [u8]) | 加密安全随机字节 |

### 8.14 `std.test` —— 单元测试框架

| 签名（test 模块） | 说明 |
|---|---|
| test::assert(cond: bool) | 断言 |
| test::assert_eq<T: Eq>(a: T, b: T) | 相等断言 |
| test::assert_ne<T: Eq>(a: T, b: T) | 不等断言 |
| test::assert_almost_eq(a: f64, b: f64, eps: f64) | 浮点近似相等 |
| test::assert_true(b: bool) | 为真 |
| test::assert_false(b: bool) | 为假 |
| test::assert_none<T>(opt: ?T) | 为 none |
| test::assert_some<T>(opt: ?T) -> T | 为 some 并取值 |
| test::assert_ok<T, E>(res: Result<T,E>) -> T | 为 ok 并取值 |
| test::assert_err<T, E>(res: Result<T,E>) -> E | 为 err 并取值 |
| test::assert_panics(f: Fn()) | 断言 panic |
| test::assert_that<T>(v: T) -> Assertion<T> | 链式断言 |
| Assertion<T>::equals(self, expected: T) | 等于 |
| Assertion<T>::not_equals(self, expected: T) | 不等于 |
| Assertion<T>::is_some(self) -> Assertion<T> | 是 some |
| Assertion<T>::contains(self, part: &str) | 字符串包含 |
| Assertion<T>::starts_with(self, part: &str) | 前缀 |
| Assertion<T>::ends_with(self, part: &str) | 后缀 |
| Assertion<T>::greater_than(self, expected: T) | 大于 |
| Assertion<T>::less_than(self, expected: T) | 小于 |
| test::bench<F>(name: &str, f: Fn(&mut Bencher)) | 微基准 |
| Bencher::iter(&mut self, f: Fn()) | 迭代计次 |
| Bencher::bytes(&mut self, n: u64) | 报告吞吐字节数 |
| test::set_up(f: Fn()) | 注册测试前钩子 |
| test::tear_down(f: Fn()) | 注册测试后钩子 |
| test::ignore(reason: &str) | 忽略当前测试 |
| test::only() | 只跑当前测试 |

### 8.15 `std.cli` —— 命令行参数解析

| 签名（cli 模块） | 说明 |
|---|---|
| cli::args() -> Vec<String> | 原始参数列表 |
| cli::arg(i: usize) -> ?String | 第 i 个参数 |
| cli::name() -> String | 程序名 |
| cli::Parser::new(program: &str) -> Parser | 新建解析器 |
| Parser::about(&mut self, desc: &str) | 设置描述 |
| Parser::version(&mut self, v: &str) | 设置版本 |
| Parser::arg(&mut self, name: &str) -> Arg | 添加位置参数 |
| Parser::option(&mut self, short: char, long: &str) -> Arg | 添加选项 |
| Parser::flag(&mut self, short: char, long: &str) -> Arg | 添加布尔开关 |
| Parser::subcommand(&mut self, name: &str) -> Parser | 添加子命令 |
| Parser::parse(&mut self) -> Result<ArgMatches, CliError> | 解析 |
| Arg::help(&mut self, desc: &str) | 帮助文本 |
| Arg::required(&mut self) | 必填 |
| Arg::default_value(&mut self, v: &str) | 默认值 |
| Arg::takes_value(&mut self) | 接受值 |
| Arg::multiple(&mut self) | 接受多个值 |
| Arg::possible_values(&mut self, values: &[&str]) | 枚举值 |
| Arg::value_name(&mut self, name: &str) | 值名 |
| ArgMatches::value_of(self, name: &str) -> ?String | 取选项值 |
| ArgMatches::value_of_t<T>(self, name: &str) -> Result<T, CliError> | 取并转换值 |
| ArgMatches::values_of(self, name: &str) -> Vec<String> | 取多值 |
| ArgMatches::is_present(self, name: &str) -> bool | 开关是否出现 |
| ArgMatches::subcommand_name(self) -> ?String | 子命令名 |
| ArgMatches::subcommand_matches(self, name: &str) -> ?ArgMatches | 子命令匹配 |
| cli::print_help() | 打印帮助 |
| cli::print_version() | 打印版本 |
| cli::exit(code: i32) | 退出进程 |
### 8.16 `std.mem` —— 内存操作

| 签名（mem 模块） | 说明 |
|---|---|
| mem::size_of<T>() -> usize | 类型大小 |
| mem::align_of<T>() -> usize | 类型对齐 |
| mem::size_of_val(v: &T) -> usize | 值大小 |
| mem::align_of_val(v: &T) -> usize | 值对齐 |
| mem::drop<T>(v: T) | 显式析构 |
| mem::swap<T>(a: &mut T, b: &mut T) | 交换 |
| mem::replace<T>(dst: &mut T, src: T) -> T | 替换并返回旧值 |
| mem::take<T: Default>(dst: &mut T) -> T | 取出并替换为默认值 |
| mem::forget<T>(v: T) | 忘记析构（泄漏） |
| mem::transmute<T, U>(v: T) -> U | 位级重解释（unsafe） |
| mem::transmute_copy<T, U>(v: &T) -> U | 拷贝并重解释 |
| mem::zeroed<T>() -> T | 全零初始化 |
| mem::uninitialized<T>() -> T | 未初始化（unsafe） |
| mem::copy(dst: &mut [u8], src: &[u8]) | 字节拷贝 |
| mem::copy_nonoverlapping(dst: *mut u8, src: *const u8, n: usize) | 非重叠拷贝 |
| mem::cmp(a: &[u8], b: &[u8]) -> Ordering | 字节比较 |
| mem::eq(a: &[u8], b: &[u8]) -> bool | 字节相等 |
| mem::hash(bytes: &[u8]) -> u64 | 快速哈希 |
| mem::align_up(n: usize, align: usize) -> usize | 向上对齐 |
| mem::align_down(n: usize, align: usize) -> usize | 向下对齐 |
| mem::offset_of<T>(field: &str) -> usize | 字段偏移 |
| mem::variant_count<T>() -> usize | 枚举变体数 |
| mem::needs_drop<T>() -> bool | 类型是否需要析构 |

### 8.17 `std.ptr` —— 裸指针

| 签名（ptr 模块） | 说明 |
|---|---|
| ptr::null<T>() -> *const T | 空指针 |
| ptr::null_mut<T>() -> *mut T | 空可变指针 |
| ptr::read<T>(src: *const T) -> T | 读取（不移动） |
| ptr::read_mut<T>(src: *mut T) -> T | 读取可变 |
| ptr::write<T>(dst: *mut T, src: T) | 写入（不析构旧值） |
| ptr::copy<T>(dst: *mut T, src: *const T, count: usize) | 拷贝（可重叠） |
| ptr::copy_nonoverlapping<T>(dst: *mut T, src: *const T, count: usize) | 拷贝（不重叠） |
| ptr::drop_in_place<T>(dst: *mut T) | 就地析构 |
| ptr::eq<T>(a: *const T, b: *const T) -> bool | 指针相等 |
| ptr::addr_of<T>(expr: T) -> *const T | 取地址 |
| ptr::addr_of_mut<T>(expr: T) -> *mut T | 取可变地址 |
| ptr::offset<T>(p: *const T, count: isize) -> *const T | 偏移 |
| ptr::add<T>(p: *const T, count: usize) -> *const T | 加偏移 |
| ptr::sub<T>(p: *const T, count: usize) -> *const T | 减偏移 |
| ptr::is_null<T>(p: *const T) -> bool | 是否空 |
| ptr::as_ref<T>(p: *const T) -> ?&T | 转为借用 |
| ptr::as_mut<T>(p: *mut T) -> ?&mut T | 转为可变借用 |
| ptr::slice_from_raw_parts<T>(data: *const T, len: usize) -> *const [T] | 构造切片指针 |
| ptr::valid<T>(p: *const T) -> bool | 指针是否有效 |

### 8.18 `std.sync` —— 同步原语

Mutex / RwLock / Atomic / Once / Barrier / Condvar。

| 签名（sync 模块） | 说明 |
|---|---|
| sync::Mutex::new<T>(v: T) -> Mutex<T> | 新建互斥锁 |
| Mutex::lock(&self) -> MutexGuard<T> | 加锁（阻塞） |
| Mutex::try_lock(&self) -> ?MutexGuard<T> | 尝试加锁 |
| Mutex::is_locked(&self) -> bool | 是否已锁 |
| Mutex::into_inner(self) -> T | 消费锁取内部值 |
| Mutex::get_mut(&mut self) -> &mut T | 可变借用（无锁） |
| MutexGuard::deref(&self) -> &T | 解借用 |
| MutexGuard::deref_mut(&mut self) -> &mut T | 可变解借用 |
| MutexGuard::unlock(self) | 主动解锁 |
| sync::RwLock::new<T>(v: T) -> RwLock<T> | 新建读写锁 |
| RwLock::read(&self) -> RwLockReadGuard<T> | 读锁 |
| RwLock::write(&self) -> RwLockWriteGuard<T> | 写锁 |
| RwLock::try_read(&self) -> ?RwLockReadGuard<T> | 尝试读 |
| RwLock::try_write(&self) -> ?RwLockWriteGuard<T> | 尝试写 |
| RwLock::into_inner(self) -> T | 消费 |
| sync::AtomicBool::new(v: bool) -> AtomicBool | 新建原子布尔 |
| AtomicBool::load(&self, order: Ordering) -> bool | 读 |
| AtomicBool::store(&self, v: bool, order: Ordering) | 写 |
| AtomicBool::swap(&self, v: bool, order: Ordering) -> bool | 交换 |
| AtomicBool::compare_exchange(&self, expected: bool, new: bool, order: Ordering) -> Result<bool, bool> | CAS |
| AtomicBool::fetch_and(&self, v: bool, order: Ordering) -> bool | 原子与 |
| AtomicBool::fetch_or(&self, v: bool, order: Ordering) -> bool | 原子或 |
| AtomicBool::fetch_xor(&self, v: bool, order: Ordering) -> bool | 原子异或 |
| AtomicBool::get_mut(&mut self) -> &mut bool | 可变借用 |
| AtomicBool::into_inner(self) -> bool | 消费 |
| sync::AtomicUsize::new(v: usize) -> AtomicUsize | 新建原子 usize |
| AtomicUsize::load(&self, order: Ordering) -> usize | 读 |
| AtomicUsize::store(&self, v: usize, order: Ordering) | 写 |
| AtomicUsize::swap(&self, v: usize, order: Ordering) -> usize | 交换 |
| AtomicUsize::compare_exchange(&self, e: usize, n: usize, order: Ordering) -> Result<usize, usize> | CAS |
| AtomicUsize::fetch_add(&self, v: usize, order: Ordering) -> usize | 原子加 |
| AtomicUsize::fetch_sub(&self, v: usize, order: Ordering) -> usize | 原子减 |
| AtomicUsize::fetch_and(&self, v: usize, order: Ordering) -> usize | 原子与 |
| AtomicUsize::fetch_or(&self, v: usize, order: Ordering) -> usize | 原子或 |
| AtomicUsize::fetch_xor(&self, v: usize, order: Ordering) -> usize | 原子异或 |
| AtomicUsize::fetch_max(&self, v: usize, order: Ordering) -> usize | 原子最大 |
| AtomicUsize::fetch_min(&self, v: usize, order: Ordering) -> usize | 原子最小 |
| AtomicUsize::get_mut(&mut self) -> &mut usize | 可变借用 |
| AtomicUsize::into_inner(self) -> usize | 消费 |
| sync::AtomicI64::new(v: i64) -> AtomicI64 | 新建原子 i64 |
| AtomicI64::load(&self, order: Ordering) -> i64 | 读 |
| AtomicI64::store(&self, v: i64, order: Ordering) | 写 |
| AtomicI64::swap(&self, v: i64, order: Ordering) -> i64 | 交换 |
| AtomicI64::compare_exchange(&self, e: i64, n: i64, order: Ordering) -> Result<i64, i64> | CAS |
| AtomicI64::fetch_add(&self, v: i64, order: Ordering) -> i64 | 原子加 |
| AtomicI64::fetch_sub(&self, v: i64, order: Ordering) -> i64 | 原子减 |
| AtomicI64::get_mut(&mut self) -> &mut i64 | 可变借用 |
| AtomicI64::into_inner(self) -> i64 | 消费 |
| Ordering::Relaxed | 松散序 |
| Ordering::Acquire | 获取 |
| Ordering::Release | 释放 |
| Ordering::AcqRel | 获取释放 |
| Ordering::SeqCst | 顺序一致 |
| sync::Once::new() -> Once | 新建一次性初始化 |
| Once::call_once(&self, f: FnOnce()) | 只执行一次 |
| Once::is_completed(&self) -> bool | 是否已完成 |
| sync::Barrier::new(n: usize) -> Barrier | 新建屏障 |
| Barrier::wait(&self) -> BarrierWaitResult | 等待 |
| Barrier::arrive(&self) -> usize | 到达 |
| Barrier::reset(&self) | 重置 |
| BarrierWaitResult::is_leader(self) -> bool | 是否 leader |
| sync::Condvar::new() -> Condvar | 新建条件变量 |
| Condvar::wait(&self, lock: MutexGuard<T>) -> MutexGuard<T> | 等待 |
| Condvar::wait_timeout(&self, lock: MutexGuard<T>, d: Duration) -> (MutexGuard<T>, WaitTimeoutResult) | 超时等待 |
| Condvar::notify_one(&self) | 唤醒一个 |
| Condvar::notify_all(&self) | 唤醒全部 |
| WaitTimeoutResult::timed_out(self) -> bool | 是否超时 |

### 8.19 `std.thread` —— OS 线程

| 签名（thread 模块） | 说明 |
|---|---|
| thread::spawn<F, R>(f: Fn() -> R) -> JoinThread<R> | 派生 OS 线程 |
| thread::sleep(d: Duration) | 睡眠 |
| thread::yield_now() | 让出 |
| thread::current() -> Thread | 当前线程 |
| thread::id() -> ThreadId | 当前线程 ID |
| thread::name() -> ?String | 线程名 |
| thread::set_name(name: &str) | 设置线程名 |
| thread::available_parallelism() -> usize | 可用并行数 |
| thread::stack_size() -> usize | 栈大小 |
| thread::Builder::new() -> ThreadBuilder | 构造器 |
| ThreadBuilder::name(&mut self, name: &str) | 设置名 |
| ThreadBuilder::stack_size(&mut self, n: usize) | 设置栈大小 |
| ThreadBuilder::spawn<F, R>(&mut self, f: Fn() -> R) -> Result<JoinThread<R>, IoError> | 派生 |
| JoinThread::join(self) -> Result<R, Box<dyn Any>> | 等待结束 |
| JoinThread::is_finished(self) -> bool | 是否结束 |
| Thread::id(self) -> ThreadId | ID |
| Thread::name(self) -> ?String | 名 |
| Thread::park() | 挂起 |
| Thread::park_timeout(d: Duration) | 超时挂起 |
| Thread::unpark(thread: Thread) | 唤醒 |

### 8.20 `std.env` —— 环境变量与进程信息

| 签名（env 模块） | 说明 |
|---|---|
| env::var(key: &str) -> Result<String, EnvError> | 读环境变量 |
| env::var_os(key: &str) -> ?String | 读环境变量（无错误） |
| env::set_var(key: &str, val: &str) -> Result<(), EnvError> | 设环境变量 |
| env::remove_var(key: &str) -> Result<(), EnvError> | 删环境变量 |
| env::vars() -> Vec<(String, String)> | 全部环境变量 |
| env::args() -> Vec<String> | 命令行参数 |
| env::args_os() -> Vec<String> | 原始参数 |
| env::current_dir() -> Result<String, IoError> | 当前目录 |
| env::set_current_dir(path: &str) -> Result<(), IoError> | 切换目录 |
| env::home_dir() -> ?String | 用户主目录 |
| env::temp_dir() -> String | 临时目录 |
| env::current_exe() -> Result<String, IoError> | 当前可执行路径 |
| env::split_paths(path: &str) -> Vec<String> | 拆分 PATH |
| env::join_paths(paths: &[&str]) -> Result<String, EnvError> | 合并 PATH |
| env::consts::OS -> &str | 操作系统名 |
| env::consts::ARCH -> &str | CPU 架构 |
| env::consts::FAMILY -> &str | OS 家族 |
| env::consts::EXE_SUFFIX -> &str | 可执行后缀 |
| env::consts::EXE_EXTENSION -> &str | 可执行扩展名 |
| env::consts::DLL_EXTENSION -> &str | 动态库扩展名 |
| env::consts::DLL_PREFIX -> &str | 动态库前缀 |
| env::consts::LINE_SEP -> &str | 行分隔符 |
| env::consts::PATH_SEP -> &str | 路径分隔符 |
| env::consts::DIR_SEP -> &str | 目录分隔符 |
| env::var_optional(key: &str) -> ?String | 读环境变量 |

### 8.21 `std.process` —— 子进程

| 签名（process 模块） | 说明 |
|---|---|
| process::Command::new(prog: &str) -> Command | 构造命令 |
| Command::arg(&mut self, arg: &str) -> &mut Command | 加参数 |
| Command::args(&mut self, args: &[&str]) -> &mut Command | 加多个参数 |
| Command::env(&mut self, key: &str, val: &str) -> &mut Command | 设环境变量 |
| Command::env_remove(&mut self, key: &str) -> &mut Command | 删环境变量 |
| Command::current_dir(&mut self, dir: &str) -> &mut Command | 设工作目录 |
| Command::stdin(&mut self, cfg: Stdio) -> &mut Command | 标准输入配置 |
| Command::stdout(&mut self, cfg: Stdio) -> &mut Command | 标准输出配置 |
| Command::stderr(&mut self, cfg: Stdio) -> &mut Command | 标准错误配置 |
| Command::spawn(&mut self) -> Result<Child, IoError> | 启动子进程 |
| Command::output(&mut self) -> Result<Output, IoError> | 执行并收集输出 |
| Command::status(&mut self) -> Result<ExitStatus, IoError> | 执行并取状态 |
| Child::wait(&mut self) -> Result<ExitStatus, IoError> | 等待结束 |
| Child::try_wait(&mut self) -> Result<?ExitStatus, IoError> | 非阻塞等待 |
| Child::kill(&mut self) -> Result<(), IoError> | 终止 |
| Child::id(&self) -> u32 | 进程 ID |
| Child::stdin(&mut self) -> &mut ?ChildStdin | 标准输入句柄 |
| Child::stdout(&mut self) -> &mut ?ChildStdout | 标准输出句柄 |
| Child::stderr(&mut self) -> &mut ?ChildStderr | 标准错误句柄 |
| Output::status(self) -> ExitStatus | 退出状态 |
| Output::stdout(self) -> Vec<u8> | 标准输出 |
| Output::stderr(self) -> Vec<u8> | 标准错误 |
| ExitStatus::success(self) -> bool | 是否成功 |
| ExitStatus::code(self) -> ?i32 | 退出码 |
| Stdio::inherit() -> Stdio | 继承父进程 |
| Stdio::piped() -> Stdio | 管道 |
| Stdio::null() -> Stdio | 丢弃 |
| Stdio::make_path(p: &str) -> Stdio | 重定向到文件 |
| process::exit(code: i32) -> ! | 退出进程 |
| process::abort() -> ! | 异常终止 |

### 8.22 `std.path` —— 路径操作

| 签名（path 模块） | 说明 |
|---|---|
| path::Path::new(s: &str) -> Path | 从字符串构造 |
| Path::as_str(self) -> &str | 字符串表示 |
| Path::to_string(self) -> String | 字符串 |
| Path::is_absolute(self) -> bool | 是否绝对 |
| Path::is_relative(self) -> bool | 是否相对 |
| Path::has_root(self) -> bool | 是否有根 |
| Path::has_parent(self) -> bool | 是否有父 |
| Path::parent(self) -> ?Path | 父目录 |
| Path::file_name(self) -> ?&str | 文件名 |
| Path::extension(self) -> ?&str | 扩展名 |
| Path::file_stem(self) -> ?&str | 文件名（去扩展） |
| Path::with_file_name(self, name: &str) -> Path | 替换文件名 |
| Path::with_extension(self, ext: &str) -> Path | 替换扩展名 |
| Path::join(self, other: &Path) -> Path | 拼接 |
| Path::push(&mut self, other: &Path) | 原地拼接 |
| Path::pop(&mut self) -> bool | 弹掉最后一段 |
| Path::starts_with(self, base: &Path) -> bool | 前缀判断 |
| Path::ends_with(self, base: &Path) -> bool | 后缀判断 |
| Path::components(self) -> Components | 组件迭代 |
| Path::ancestors(self) -> Ancestors | 祖先迭代 |
| Path::canonicalize(self) -> Result<Path, IoError> | 规范化为绝对路径 |
| Path::exists(self) -> bool | 是否存在 |
| Path::is_file(self) -> bool | 是否文件 |
| Path::is_dir(self) -> bool | 是否目录 |
| Path::read_link(self) -> Result<Path, IoError> | 读符号链接 |
| Path::read_dir(self) -> Result<ReadDir, IoError> | 列目录 |
| Path::strip_prefix(self, base: &Path) -> Result<Path, PathError> | 去前缀 |
| Path::to_absolute(self) -> Result<Path, IoError> | 转绝对路径 |
| path::is_sep(c: char) -> bool | 是否路径分隔符 |
| path::sep() -> char | 平台分隔符 |
| path::is_delimiter(c: char) -> bool | 是否 PATH 分隔符 |
| path::delimiter() -> char | PATH 分隔符 |
| path::absolute(path: &str) -> Result<Path, IoError> | 绝对化 |
| path::relative(from: &str, to: &str) -> Path | 计算相对路径 |
| path::normalize(path: &str) -> Path | 规范化（去 . ..） |
| path::ext(path: &str) -> ?&str | 取扩展名 |
| path::name(path: &str) -> ?&str | 取文件名 |
| path::dir(path: &str) -> Path | 取目录 |

### 8.23 `std.log` —— 日志

| 签名（log 模块） | 说明 |
|---|---|
| log::error!(msg) | 错误级别日志 |
| log::warn!(msg) | 警告级别日志 |
| log::info!(msg) | 信息级别日志 |
| log::debug!(msg) | 调试级别日志 |
| log::trace!(msg) | 跟踪级别日志 |
| log::set_max_level(level: Level) | 设置最大级别 |
| log::max_level() -> Level | 获取最大级别 |
| log::logger() -> Logger | 获取当前 logger |
| log::set_logger(logger: Logger) | 设置 logger |
| Logger::log(&self, record: Record) | 记录日志 |
| Logger::enabled(&self, level: Level) -> bool | 是否启用 |
| Record::new(level: Level, target: &str, msg: &str) -> Record | 构造记录 |
| Record::level(self) -> Level | 级别 |
| Record::target(self) -> &str | 目标 |
| Record::msg(self) -> &str | 消息 |
| Record::module_path(self) -> &str | 模块路径 |
| Record::file(self) -> &str | 文件 |
| Record::line(self) -> u32 | 行号 |
| Level::Error | 错误 |
| Level::Warn | 警告 |
| Level::Info | 信息 |
| Level::Debug | 调试 |
| Level::Trace | 跟踪 |

### 8.24 `std.hash` —— 哈希

| 签名（hash 模块） | 说明 |
|---|---|
| hash::Hash::hash<T: Hashable>(v: T) -> u64 | 计算哈希 |
| hash::Hasher::new() -> Hasher | 新建流式哈希器 |
| Hasher::write(&mut self, bytes: &[u8]) | 写入字节 |
| Hasher::write_u8(&mut self, v: u8) | 写入 u8 |
| Hasher::write_u64(&mut self, v: u64) | 写入 u64 |
| Hasher::write_str(&mut self, s: &str) | 写入字符串 |
| Hasher::finish(self) -> u64 | 完成并取哈希 |
| hash::DefaultHasher::new() -> DefaultHasher | 默认哈希器（SipHash） |
| hash::BuildHasher::build_hasher(&self) -> Hasher | 构造哈希器 |
| hash::Hashable::hash(&self, hasher: &mut Hasher) | trait 方法 |
| hash::eq(a: u64, b: u64) -> bool | 哈希相等 |
| hash::combine(a: u64, b: u64) -> u64 | 合并哈希 |
| hash::brown::new() -> BrownHasher | Brown 哈希器 |
| hash::fx::new() -> FxHasher | Fx 哈希器 |
| hash::ahash::new() -> AHasher | AHash 哈希器 |

### 8.25 `std.crypto` —— 加密哈希与 HMAC

| 签名（crypto 模块） | 说明 |
|---|---|
| crypto::md5(data: &[u8]) -> [u8; 16] | MD5 摘要 |
| crypto::md5_hex(data: &[u8]) -> String | MD5 十六进制 |
| crypto::sha1(data: &[u8]) -> [u8; 20] | SHA-1 摘要 |
| crypto::sha1_hex(data: &[u8]) -> String | SHA-1 十六进制 |
| crypto::sha256(data: &[u8]) -> [u8; 32] | SHA-256 摘要 |
| crypto::sha256_hex(data: &[u8]) -> String | SHA-256 十六进制 |
| crypto::sha512(data: &[u8]) -> [u8; 64] | SHA-512 摘要 |
| crypto::sha512_hex(data: &[u8]) -> String | SHA-512 十六进制 |
| crypto::sha3_256(data: &[u8]) -> [u8; 32] | SHA3-256 摘要 |
| crypto::hmac_sha256(key: &[u8], data: &[u8]) -> [u8; 32] | HMAC-SHA256 |
| crypto::hmac_sha256_hex(key: &[u8], data: &[u8]) -> String | HMAC-SHA256 十六进制 |
| crypto::pbkdf2_hmac_sha256(password: &[u8], salt: &[u8], iters: u32, dklen: usize) -> Vec<u8> | PBKDF2 |
| crypto::constant_time_eq(a: &[u8], b: &[u8]) -> bool | 常量时间比较 |
| crypto::SecureRandom::bytes(buf: &mut [u8]) | 加密安全随机字节 |
| crypto::SecureRandom::u64() -> u64 | 加密安全随机 u64 |
| crypto::SecureRandom::uuid_v4() -> Uuid | 加密安全 UUID |
| crypto::b64_encode(data: &[u8]) -> String | Base64 编码 |
| crypto::b64_decode(s: &str) -> Result<Vec<u8>, CryptoError> | Base64 解码 |
| crypto::crc32(data: &[u8]) -> u32 | CRC32 |
| crypto::crc32c(data: &[u8]) -> u32 | CRC32C |
| crypto::adler32(data: &[u8]) -> u32 | Adler32 |
| crypto::blake2b(data: &[u8]) -> [u8; 64] | BLAKE2b 摘要 |
| crypto::blake2s(data: &[u8]) -> [u8; 32] | BLAKE2s 摘要 |

### 8.26 `std.encoding` —— 文本编码

| 签名（encoding 模块） | 说明 |
|---|---|
| encoding::utf8::decode(bytes: &[u8]) -> Result<String, EncodingError> | UTF-8 解码 |
| encoding::utf8::encode(s: &str) -> Vec<u8> | UTF-8 编码 |
| encoding::utf8::valid(bytes: &[u8]) -> bool | 是否合法 UTF-8 |
| encoding::utf8::validate(bytes: &[u8]) -> Result<(), EncodingError> | 校验 |
| encoding::utf16::decode_le(bytes: &[u8]) -> Result<String, EncodingError> | UTF-16 LE 解码 |
| encoding::utf16::decode_be(bytes: &[u8]) -> Result<String, EncodingError> | UTF-16 BE 解码 |
| encoding::utf16::encode_le(s: &str) -> Vec<u8> | UTF-16 LE 编码 |
| encoding::utf16::encode_be(s: &str) -> Vec<u8> | UTF-16 BE 编码 |
| encoding::ascii::decode(bytes: &[u8]) -> Result<String, EncodingError> | ASCII 解码 |
| encoding::ascii::encode(s: &str) -> Result<Vec<u8>, EncodingError> | ASCII 编码 |
| encoding::ascii::valid(bytes: &[u8]) -> bool | 是否纯 ASCII |
| encoding::latin1::decode(bytes: &[u8]) -> String | Latin-1 解码 |
| encoding::latin1::encode(s: &str) -> Result<Vec<u8>, EncodingError> | Latin-1 编码 |
| encoding::gbk::decode(bytes: &[u8]) -> Result<String, EncodingError> | GBK 解码 |
| encoding::gbk::encode(s: &str) -> Result<Vec<u8>, EncodingError> | GBK 编码 |
| encoding::big5::decode(bytes: &[u8]) -> Result<String, EncodingError> | Big5 解码 |
| encoding::big5::encode(s: &str) -> Result<Vec<u8>, EncodingError> | Big5 编码 |
| encoding::detect(bytes: &[u8]) -> ?&str | 自动检测编码 |
| encoding::convert(s: &str, from: &str, to: &str) -> Result<Vec<u8>, EncodingError> | 编码转换 |

### 8.27 `std.fmt` —— 格式化

| 签名（fmt 模块） | 说明 |
|---|---|
| fmt::format(s: &str, args: &[Value]) -> String | 格式化字符串 |
| fmt::format_int(n: i64, width: usize, fill: char, align: Align) -> String | 整数格式化 |
| fmt::format_float(n: f64, precision: usize) -> String | 浮点格式化 |
| fmt::format_hex(n: u64, width: usize, uppercase: bool) -> String | 十六进制格式化 |
| fmt::format_binary(n: u64, width: usize) -> String | 二进制格式化 |
| fmt::format_octal(n: u64, width: usize) -> String | 八进制格式化 |
| fmt::pad_left(s: &str, width: usize, fill: char) -> String | 左填充 |
| fmt::pad_right(s: &str, width: usize, fill: char) -> String | 右填充 |
| fmt::pad_center(s: &str, width: usize, fill: char) -> String | 居中填充 |
| fmt::truncate(s: &str, width: usize, ellipsis: &str) -> String | 截断 |
| fmt::debug(v: &T) -> String | 调试格式 |
| fmt::display(v: &T) -> String | 展示格式 |
| fmt::Alternate | 交替格式 |
| fmt::Align::Left | 左对齐 |
| fmt::Align::Right | 右对齐 |
| fmt::Align::Center | 居中 |
| fmt::Arguments::new(s: &str, args: &[Value]) -> Arguments | 构造参数 |
| fmt::write(f: &mut dyn Write, args: Arguments) -> Result<(), IoError> | 写入流 |
| fmt::format_args(s: &str, args: &[Value]) -> String | 格式化参数 |
| fmt::to_string<T: Display>(v: &T) -> String | 转字符串 |

### 8.28 `std.csv` —— CSV

| 签名（csv 模块） | 说明 |
|---|---|
| csv::Reader::new(r: impl Read) -> Reader | 新建读取器 |
| Reader::read(&mut self) -> Result<?Record, CsvError> | 读一行 |
| Reader::records(self) -> RecordIter | 迭代记录 |
| Reader::headers(&self) -> &[String] | 表头 |
| Reader::set_delimiter(&mut self, d: u8) | 设分隔符 |
| Reader::has_headers(&mut self, h: bool) | 是否有表头 |
| csv::Writer::new(w: impl Write) -> Writer | 新建写入器 |
| Writer::write(&mut self, record: &[&str]) -> Result<(), CsvError> | 写一行 |
| Writer::write_record(&mut self, record: Record) -> Result<(), CsvError> | 写记录 |
| Writer::flush(&mut self) -> Result<(), CsvError> | 刷新 |
| Writer::write_header(&mut self, headers: &[&str]) -> Result<(), CsvError> | 写表头 |
| Record::new() -> Record | 新建记录 |
| Record::get(self, i: usize) -> ?&str | 按列取 |
| Record::len(self) -> usize | 列数 |
| Record::iter(self) -> Iter<&str> | 列迭代 |
| Record::push(&mut self, field: &str) | 追加列 |
| csv::parse(s: &str) -> Result<Vec<Record>, CsvError> | 解析整个字符串 |
| csv::to_string(records: &[Record]) -> Result<String, CsvError> | 序列化为字符串 |
| csv::from_str(s: &str) -> Result<Vec<Record>, CsvError> | 从字符串解析 |
| csv::dialect::default() -> Dialect | 默认方言 |
| csv::dialect::excel() -> Dialect | Excel 方言 |

### 8.29 `std.linalg` —— 线性代数

Vec2 / Vec3 / Vec4 / Mat3 / Mat4 / Quat / Ray / Plane / AABB。

| 签名（Vec2） | 说明 |
|---|---|
| linalg::Vec2::new(x: f64, y: f64) -> Vec2 | 构造 |
| Vec2::zero() -> Vec2 | 零向量 |
| Vec2::one() -> Vec2 | 单位向量 |
| Vec2::x_axis() -> Vec2 | X 轴 |
| Vec2::y_axis() -> Vec2 | Y 轴 |
| Vec2::add(self, o: Vec2) -> Vec2 | 加 |
| Vec2::sub(self, o: Vec2) -> Vec2 | 减 |
| Vec2::mul(self, s: f64) -> Vec2 | 数乘 |
| Vec2::div(self, s: f64) -> Vec2 | 数除 |
| Vec2::dot(self, o: Vec2) -> f64 | 点积 |
| Vec2::length(self) -> f64 | 长度 |
| Vec2::length_sq(self) -> f64 | 长度平方 |
| Vec2::normalize(self) -> Vec2 | 归一化 |
| Vec2::distance(self, o: Vec2) -> f64 | 距离 |
| Vec2::lerp(self, o: Vec2, t: f64) -> Vec2 | 线性插值 |
| Vec2::neg(self) -> Vec2 | 取负 |
| Vec2::eq(self, o: Vec2) -> bool | 相等 |
| Vec2::to_vec3(self, z: f64) -> Vec3 | 转 Vec3 |

| 签名（Vec3） | 说明 |
|---|---|
| linalg::Vec3::new(x: f64, y: f64, z: f64) -> Vec3 | 构造 |
| Vec3::zero() -> Vec3 | 零向量 |
| Vec3::one() -> Vec3 | 单位向量 |
| Vec3::x_axis() -> Vec3 | X 轴 |
| Vec3::y_axis() -> Vec3 | Y 轴 |
| Vec3::z_axis() -> Vec3 | Z 轴 |
| Vec3::add(self, o: Vec3) -> Vec3 | 加 |
| Vec3::sub(self, o: Vec3) -> Vec3 | 减 |
| Vec3::mul(self, s: f64) -> Vec3 | 数乘 |
| Vec3::div(self, s: f64) -> Vec3 | 数除 |
| Vec3::dot(self, o: Vec3) -> f64 | 点积 |
| Vec3::cross(self, o: Vec3) -> Vec3 | 叉积 |
| Vec3::length(self) -> f64 | 长度 |
| Vec3::length_sq(self) -> f64 | 长度平方 |
| Vec3::normalize(self) -> Vec3 | 归一化 |
| Vec3::distance(self, o: Vec3) -> f64 | 距离 |
| Vec3::lerp(self, o: Vec3, t: f64) -> Vec3 | 线性插值 |
| Vec3::neg(self) -> Vec3 | 取负 |
| Vec3::reflect(self, normal: Vec3) -> Vec3 | 反射 |
| Vec3::refract(self, normal: Vec3, eta: f64) -> Vec3 | 折射 |
| Vec3::eq(self, o: Vec3) -> bool | 相等 |
| Vec3::to_vec2(self) -> Vec2 | 转 Vec2 |
| Vec3::to_vec4(self, w: f64) -> Vec4 | 转 Vec4 |

| 签名（Vec4） | 说明 |
|---|---|
| linalg::Vec4::new(x: f64, y: f64, z: f64, w: f64) -> Vec4 | 构造 |
| Vec4::zero() -> Vec4 | 零向量 |
| Vec4::one() -> Vec4 | 单位向量 |
| Vec4::add(self, o: Vec4) -> Vec4 | 加 |
| Vec4::sub(self, o: Vec4) -> Vec4 | 减 |
| Vec4::mul(self, s: f64) -> Vec4 | 数乘 |
| Vec4::div(self, s: f64) -> Vec4 | 数除 |
| Vec4::dot(self, o: Vec4) -> f64 | 点积 |
| Vec4::length(self) -> f64 | 长度 |
| Vec4::normalize(self) -> Vec4 | 归一化 |
| Vec4::lerp(self, o: Vec4, t: f64) -> Vec4 | 线性插值 |
| Vec4::to_vec3(self) -> Vec3 | 转 Vec3 |

| 签名（Mat4） | 说明 |
|---|---|
| linalg::Mat4::new(m: [[f64; 4]; 4]) -> Mat4 | 构造 |
| Mat4::identity() -> Mat4 | 单位矩阵 |
| Mat4::zero() -> Mat4 | 零矩阵 |
| Mat4::translate(v: Vec3) -> Mat4 | 平移矩阵 |
| Mat4::scale(v: Vec3) -> Mat4 | 缩放矩阵 |
| Mat4::rotate_x(angle: f64) -> Mat4 | 绕 X 旋转 |
| Mat4::rotate_y(angle: f64) -> Mat4 | 绕 Y 旋转 |
| Mat4::rotate_z(angle: f64) -> Mat4 | 绕 Z 旋转 |
| Mat4::look_at(eye: Vec3, center: Vec3, up: Vec3) -> Mat4 | 观察矩阵 |
| Mat4::perspective(fov: f64, aspect: f64, near: f64, far: f64) -> Mat4 | 透视投影 |
| Mat4::ortho(left: f64, right: f64, bottom: f64, top: f64, near: f64, far: f64) -> Mat4 | 正交投影 |
| Mat4::mul(self, o: Mat4) -> Mat4 | 矩阵乘 |
| Mat4::apply_vec4(self, v: Vec4) -> Vec4 | 应用于 Vec4 |
| Mat4::apply_vec3(self, v: Vec3) -> Vec3 | 应用于 Vec3 |
| Mat4::inverse(self) -> ?Mat4 | 逆矩阵 |
| Mat4::transpose(self) -> Mat4 | 转置 |
| Mat4::determinant(self) -> f64 | 行列式 |
| Mat4::eq(self, o: Mat4) -> bool | 相等 |

| 签名（Mat3） | 说明 |
|---|---|
| linalg::Mat3::new(m: [[f64; 3]; 3]) -> Mat3 | 构造 |
| Mat3::identity() -> Mat3 | 单位矩阵 |
| Mat3::from_quat(q: Quat) -> Mat3 | 从四元数构造 |
| Mat3::mul(self, o: Mat3) -> Mat3 | 矩阵乘 |
| Mat3::apply_vec3(self, v: Vec3) -> Vec3 | 应用 |
| Mat3::inverse(self) -> ?Mat3 | 逆矩阵 |
| Mat3::transpose(self) -> Mat3 | 转置 |
| Mat3::determinant(self) -> f64 | 行列式 |

| 签名（Quat） | 说明 |
|---|---|
| linalg::Quat::new(x: f64, y: f64, z: f64, w: f64) -> Quat | 构造 |
| Quat::identity() -> Quat | 单位四元数 |
| Quat::from_axis_angle(axis: Vec3, angle: f64) -> Quat | 轴角构造 |
| Quat::from_euler(pitch: f64, yaw: f64, roll: f64) -> Quat | 欧拉角构造 |
| Quat::mul(self, o: Quat) -> Quat | 四元数乘 |
| Quat::rotate_vec3(self, v: Vec3) -> Vec3 | 旋转向量 |
| Quat::inverse(self) -> Quat | 逆四元数 |
| Quat::conjugate(self) -> Quat | 共轭 |
| Quat::normalize(self) -> Quat | 归一化 |
| Quat::slerp(self, o: Quat, t: f64) -> Quat | 球面线性插值 |
| Quat::length(self) -> f64 | 长度 |

| 签名（几何类型） | 说明 |
|---|---|
| linalg::Ray::new(origin: Vec3, dir: Vec3) -> Ray | 构造 |
| Ray::at(self, t: f64) -> Vec3 | 取 t 处点 |
| linalg::Plane::new(normal: Vec3, d: f64) -> Plane | 构造 |
| Plane::signed_distance(self, p: Vec3) -> f64 | 有符号距离 |
| Plane::project_point(self, p: Vec3) -> Vec3 | 投影 |
| linalg::AABB::new(min: Vec3, max: Vec3) -> AABB | 构造 |
| AABB::contains_point(self, p: Vec3) -> bool | 包含点 |
| AABB::intersects_aabb(self, o: AABB) -> bool | 相交判断 |
| AABB::expand(self, v: Vec3) -> AABB | 扩展 |
| AABB::center(self) -> Vec3 | 中心 |
| AABB::size(self) -> Vec3 | 尺寸 |
| AABB::union(self, o: AABB) -> AABB | 并集 |
| linalg::Vec2::dot(self, o: Vec2) -> f64 | 点积（重复保险） |
| linalg::Vec3::reflect(self, normal: Vec3) -> Vec3 | 反射 |

### 8.30 `std.stats` —— 统计

| 签名（stats 模块） | 说明 |
|---|---|
| stats::mean(data: &[f64]) -> f64 | 均值 |
| stats::median(data: &[f64]) -> f64 | 中位数 |
| stats::mode(data: &[f64]) -> Vec<f64> | 众数 |
| stats::variance(data: &[f64]) -> f64 | 方差 |
| stats::std_dev(data: &[f64]) -> f64 | 标准差 |
| stats::min(data: &[f64]) -> f64 | 最小值 |
| stats::max(data: &[f64]) -> f64 | 最大值 |
| stats::range(data: &[f64]) -> f64 | 极差 |
| stats::sum(data: &[f64]) -> f64 | 求和 |
| stats::product(data: &[f64]) -> f64 | 求积 |
| stats::percentile(data: &[f64], p: f64) -> f64 | 百分位数 |
| stats::quartiles(data: &[f64]) -> (f64, f64, f64) | 四分位数 |
| stats::correlation(x: &[f64], y: &[f64]) -> f64 | 皮尔逊相关系数 |
| stats::covariance(x: &[f64], y: &[f64]) -> f64 | 协方差 |
| stats::linear_regression(x: &[f64], y: &[f64]) -> (f64, f64) | 线性回归 (斜率, 截距) |
| stats::histogram(data: &[f64], bins: usize) -> Vec<(f64, usize)> | 直方图 |
| stats::z_score(data: &[f64], v: f64) -> f64 | Z 分数 |
| stats::normalize(data: &[f64]) -> Vec<f64> | 归一化到 [0,1] |
| stats::standardize(data: &[f64]) -> Vec<f64> | 标准化（均值0方差1） |
| stats::summary(data: &[f64]) -> Summary | 统计摘要 |
| Summary::mean(self) -> f64 | 均值 |
| Summary::median(self) -> f64 | 中位数 |
| Summary::min(self) -> f64 | 最小 |
| Summary::max(self) -> f64 | 最大 |
| Summary::std_dev(self) -> f64 | 标准差 |

### 8.31 `std.num` —— 数值扩展

Complex / Rational / BigInt / BigFloat。

| 签名（num 模块） | 说明 |
|---|---|
| num::Complex::new(re: f64, im: f64) -> Complex | 构造 |
| Complex::zero() -> Complex | 零 |
| Complex::one() -> Complex | 一 |
| Complex::i() -> Complex | 虚数单位 |
| Complex::add(self, o: Complex) -> Complex | 加 |
| Complex::sub(self, o: Complex) -> Complex | 减 |
| Complex::mul(self, o: Complex) -> Complex | 乘 |
| Complex::div(self, o: Complex) -> Complex | 除 |
| Complex::conjugate(self) -> Complex | 共轭 |
| Complex::abs(self) -> f64 | 模长 |
| Complex::arg(self) -> f64 | 幅角 |
| Complex::sqrt(self) -> Complex | 平方根 |
| Complex::exp(self) -> Complex | 指数 |
| Complex::ln(self) -> Complex | 对数 |
| Complex::sin(self) -> Complex | 正弦 |
| Complex::cos(self) -> Complex | 余弦 |
| num::Rational::new(num: i64, den: i64) -> Rational | 构造 |
| Rational::from_int(v: i64) -> Rational | 从整数 |
| Rational::add(self, o: Rational) -> Rational | 加 |
| Rational::sub(self, o: Rational) -> Rational | 减 |
| Rational::mul(self, o: Rational) -> Rational | 乘 |
| Rational::div(self, o: Rational) -> Rational | 除 |
| Rational::to_f64(self) -> f64 | 转浮点 |
| Rational::reduce(self) -> Rational | 约分 |
| Rational::eq(self, o: Rational) -> bool | 相等 |
| num::BigInt::zero() -> BigInt | 零 |
| num::BigInt::one() -> BigInt | 一 |
| num::BigInt::from_i64(v: i64) -> BigInt | 从 i64 |
| num::BigInt::parse(s: &str) -> Result<BigInt, NumError> | 解析 |
| BigInt::add(self, o: BigInt) -> BigInt | 加 |
| BigInt::sub(self, o: BigInt) -> BigInt | 减 |
| BigInt::mul(self, o: BigInt) -> BigInt | 乘 |
| BigInt::div(self, o: BigInt) -> BigInt | 除 |
| BigInt::rem(self, o: BigInt) -> BigInt | 取模 |
| BigInt::pow(self, exp: u32) -> BigInt | 幂 |
| BigInt::abs(self) -> BigInt | 绝对值 |
| BigInt::neg(self) -> BigInt | 取负 |
| BigInt::cmp(self, o: BigInt) -> Ordering | 比较 |
| BigInt::to_string(self) -> String | 字符串 |
| BigInt::to_i64(self) -> Result<i64, NumError> | 转 i64 |
| BigInt::bitand(self, o: BigInt) -> BigInt | 按位与 |
| BigInt::bitor(self, o: BigInt) -> BigInt | 按位或 |
| BigInt::bitxor(self, o: BigInt) -> BigInt | 按位异或 |
| num::BigFloat::zero() -> BigFloat | 零 |
| num::BigFloat::parse(s: &str) -> Result<BigFloat, NumError> | 解析 |
| BigFloat::add(self, o: BigFloat) -> BigFloat | 加 |
| BigFloat::sub(self, o: BigFloat) -> BigFloat | 减 |
| BigFloat::mul(self, o: BigFloat) -> BigFloat | 乘 |
| BigFloat::div(self, o: BigFloat) -> BigFloat | 除 |
| BigFloat::sqrt(self) -> BigFloat | 平方根 |
| BigFloat::to_f64(self) -> f64 | 转 f64 |
| BigFloat::to_string(self) -> String | 字符串 |

### 8.32 `std.bytes` —— 字节缓冲区

| 签名（bytes 模块） | 说明 |
|---|---|
| bytes::ByteBuf::new() -> ByteBuf | 新建 |
| bytes::ByteBuf::with_capacity(n: usize) -> ByteBuf | 预分配 |
| bytes::ByteBuf::from(data: &[u8]) -> ByteBuf | 从字节切片构造 |
| ByteBuf::len(self) -> usize | 长度 |
| ByteBuf::is_empty(self) -> bool | 是否空 |
| ByteBuf::capacity(self) -> usize | 容量 |
| ByteBuf::clear(&mut self) | 清空 |
| ByteBuf::reserve(&mut self, n: usize) | 保留容量 |
| ByteBuf::shrink_to_fit(&mut self) | 收缩 |
| ByteBuf::put(&mut self, data: &[u8]) | 追加字节 |
| ByteBuf::put_u8(&mut self, v: u8) | 追加 u8 |
| ByteBuf::put_u16_le(&mut self, v: u16) | 追加 u16 小端 |
| ByteBuf::put_u16_be(&mut self, v: u16) | 追加 u16 大端 |
| ByteBuf::put_u32_le(&mut self, v: u32) | 追加 u32 小端 |
| ByteBuf::put_u32_be(&mut self, v: u32) | 追加 u32 大端 |
| ByteBuf::put_u64_le(&mut self, v: u64) | 追加 u64 小端 |
| ByteBuf::put_u64_be(&mut self, v: u64) | 追加 u64 大端 |
| ByteBuf::put_f32_le(&mut self, v: f32) | 追加 f32 小端 |
| ByteBuf::put_f64_le(&mut self, v: f64) | 追加 f64 小端 |
| ByteBuf::put_str(&mut self, s: &str) | 追加字符串 |
| ByteBuf::get_u8(&self, off: usize) -> Result<u8, BytesError> | 读 u8 |
| ByteBuf::get_u16_le(&self, off: usize) -> Result<u16, BytesError> | 读 u16 小端 |
| ByteBuf::get_u32_le(&self, off: usize) -> Result<u32, BytesError> | 读 u32 小端 |
| ByteBuf::get_u64_le(&self, off: usize) -> Result<u64, BytesError> | 读 u64 小端 |
| ByteBuf::get_f64_le(&self, off: usize) -> Result<f64, BytesError> | 读 f64 小端 |
| ByteBuf::slice(&self, start: usize, end: usize) -> &[u8] | 切片 |
| ByteBuf::as_bytes(&self) -> &[u8] | 字节切片 |
| ByteBuf::as_mut_bytes(&mut self) -> &mut [u8] | 可变字节切片 |
| ByteBuf::clone(self) -> ByteBuf | 克隆 |
| ByteBuf::eq(self, o: &[u8]) -> bool | 相等 |
| ByteBuf::hex(&self) -> String | 十六进制字符串 |
| ByteBuf::from_hex(s: &str) -> Result<ByteBuf, BytesError> | 从十六进制构造 |

### 8.33 `std.bit` —— 位操作

| 签名（bit 模块） | 说明 |
|---|---|
| bit::count_ones(v: u64) -> u32 | 置位位数 |
| bit::count_zeros(v: u64) -> u32 | 零位数 |
| bit::leading_zeros(v: u64) -> u32 | 前导零 |
| bit::trailing_zeros(v: u64) -> u32 | 末尾零 |
| bit::reverse_bits(v: u64) -> u64 | 反转位 |
| bit::rotate_left(v: u64, n: u32) -> u64 | 循环左移 |
| bit::rotate_right(v: u64, n: u32) -> u64 | 循环右移 |
| bit::swap_bytes(v: u64) -> u64 | 字节交换 |
| bit::from_be(v: u64) -> u64 | 从大端 |
| bit::from_le(v: u64) -> u64 | 从小端 |
| bit::to_be(v: u64) -> u64 | 转大端 |
| bit::to_le(v: u64) -> u64 | 转小端 |
| bit::is_power_of_two(v: u64) -> bool | 是否 2 的幂 |
| bit::next_power_of_two(v: u64) -> u64 | 下一 2 的幂 |
| bit::ilog2(v: u64) -> u32 | 整数 log2 |
| bit::sqrt(v: u64) -> u64 | 整数平方根 |
| bit::extract(v: u64, start: u32, len: u32) -> u64 | 提取位域 |
| bit::insert(v: u64, field: u64, start: u32, len: u32) -> u64 | 插入位域 |
| bit::set_bit(v: u64, n: u32) -> u64 | 置位 |
| bit::clear_bit(v: u64, n: u32) -> u64 | 清位 |
| bit::toggle_bit(v: u64, n: u32) -> u64 | 翻位 |
| bit::get_bit(v: u64, n: u32) -> bool | 取位 |

### 8.34 `std.arch` —— CPU 特性与 SIMD

| 签名（arch 模块） | 说明 |
|---|---|
| arch::cpu_arch() -> &str | CPU 架构名 |
| arch::os() -> &str | 操作系统名 |
| arch::endian() -> Endian | 字节序 |
| arch::is_x86_64() -> bool | 是否 x86_64 |
| arch::is_arm64() -> bool | 是否 ARM64 |
| arch::is_wasm32() -> bool | 是否 WASM |
| arch::has_sse2() -> bool | 是否支持 SSE2 |
| arch::has_sse42() -> bool | 是否支持 SSE4.2 |
| arch::has_avx() -> bool | 是否支持 AVX |
| arch::has_avx2() -> bool | 是否支持 AVX2 |
| arch::has_neon() -> bool | 是否支持 NEON |
| arch::has_fma() -> bool | 是否支持 FMA |
| arch::cache_line_size() -> usize | 缓存行大小 |
| arch::num_cpus() -> usize | CPU 核数 |
| arch::page_size() -> usize | 内存页大小 |
| arch::prefetch(addr: *const u8) | 预取指令 |
| arch::black_box<T>(v: T) -> T | 编译器黑盒（防止优化） |
| arch::black_box_ref<T>(v: &T) -> &T | 黑盒引用 |
| arch::u64x2::new(a: u64, b: u64) -> u64x2 | 128 位向量 |
| u64x2::add(self, o: u64x2) -> u64x2 | 向量加 |
| u64x2::mul(self, o: u64x2) -> u64x2 | 向量乘 |
| u64x2::extract(self, i: usize) -> u64 | 提取元素 |
| arch::f64x2::new(a: f64, b: f64) -> f64x2 | 浮点向量 |
| f64x2::add(self, o: f64x2) -> f64x2 | 向量加 |
| f64x2::mul(self, o: f64x2) -> f64x2 | 向量乘 |
| f64x2::sqrt(self) -> f64x2 | 向量平方根 |
| f64x2::sum(self) -> f64 | 求和 |
| arch::Endian::Little | 小端 |
| arch::Endian::Big | 大端 |

### 8.35 `std.event` —— 事件循环

| 签名（event 模块） | 说明 |
|---|---|
| event::EventLoop::new() -> EventLoop | 新建事件循环 |
| EventLoop::register(&mut self, fd: RawFd, interest: Interest) -> Result<Token, EventError> | 注册 fd |
| EventLoop::reregister(&mut self, token: Token, interest: Interest) -> Result<(), EventError> | 重新注册 |
| EventLoop::deregister(&mut self, token: Token) -> Result<(), EventError> | 注销 |
| EventLoop::poll(&mut self, timeout: ?Duration) -> Result<Vec<Event>, EventError> | 等待事件 |
| EventLoop::run(&mut self, handler: Fn(Event)) -> Result<(), EventError> | 运行循环 |
| EventLoop::stop(&mut self) | 停止 |
| Interest::readable() -> Interest | 可读兴趣 |
| Interest::writable() -> Interest | 可写兴趣 |
| Interest::both() -> Interest | 读写兴趣 |
| Event::token(self) -> Token | 事件 token |
| Event::is_readable(self) -> bool | 可读 |
| Event::is_writable(self) -> bool | 可写 |
| Token::new(v: usize) -> Token | 构造 token |
| Token::value(self) -> usize | token 值 |

### 8.36 `std.future` —— Future

| 签名（future 模块） | 说明 |
|---|---|
| future::Future::poll(self, cx: Context) -> Poll<T> | 轮询 |
| future::ready(v: T) -> Future<T> | 立即就绪 Future |
| future::pending<T>() -> Future<T> | 永远挂起 Future |
| future::join(a: Future<T>, b: Future<U>) -> Future<(T, U)> | 同时等待 |
| future::select(a: Future<T>, b: Future<T>) -> Future<(T, usize)> | 竞速 |
| future::join_all(futures: Vec<Future<T>>) -> Future<Vec<T>> | 等待全部 |
| future::select_all(futures: Vec<Future<T>>) -> Future<(T, usize, Vec<Future<T>>)> | 等待任一 |
| future::then<F, U>(self, f: Fn(T) -> Future<U>) -> Future<U> | 链式组合 |
| future::map<F, U>(self, f: Fn(T) -> U) -> Future<U> | 映射 |
| Context::waker(self) -> Waker | 获取 waker |
| Poll::Ready(T) | 就绪 |
| Poll::Pending | 挂起 |
| Waker::wake(self) | 唤醒 |
| Waker::clone(self) -> Waker | 克隆 |

### 8.37 `std.stream` —— 流

| 签名（stream 模块） | 说明 |
|---|---|
| stream::Stream::poll_next(self, cx: Context) -> Poll<?T> | 轮询下一个 |
| stream::iter<I: Iterator>(iter: I) -> Stream<I> | 从迭代器构造流 |
| stream::once(v: T) -> Stream<T> | 单元素流 |
| stream::empty<T>() -> Stream<T> | 空流 |
| stream::pending<T>() -> Stream<T> | 永远挂起流 |
| Stream::map<F, U>(self, f: Fn(T) -> U) -> Stream<U> | 映射 |
| Stream::filter(self, f: Fn(T) -> bool) -> Stream<T> | 过滤 |
| Stream::then<F, U>(self, f: Fn(T) -> Future<U>) -> Stream<U> | 异步映射 |
| Stream::chain<U: Stream<Item=T>>(self, other: U) -> Stream<T> | 连接 |
| Stream::take(self, n: usize) -> Stream<T> | 取前 n |
| Stream::skip(self, n: usize) -> Stream<T> | 跳过前 n |
| Stream::collect<U>(self) -> Future<U> | 收集 |
| Stream::fold<U>(self, init: U, f: Fn(U, T) -> U) -> Future<U> | 折叠 |
| Stream::next(self) -> Future<?T> | 取下一个 |
| Stream::for_each<F>(self, f: Fn(T)) -> Future<()> | 遍历 |

### 8.38 `std.error` —— 错误类型

| 签名（error 模块） | 说明 |
|---|---|
| error::Error::new(msg: &str) -> Error | 新建错误 |
| Error::msg(self) -> &str | 错误消息 |
| Error::source(self) -> ?&Error | 错误链根因 |
| Error::kind(self) -> ErrorKind | 错误类别 |
| Error::to_string(self) -> String | 字符串 |
| Error::chain(self) -> ErrorChain | 错误链迭代 |
| ErrorKind::Io | IO 错误 |
| ErrorKind::NotFound | 未找到 |
| ErrorKind::PermissionDenied | 权限拒绝 |
| ErrorKind::AlreadyExists | 已存在 |
| ErrorKind::InvalidInput | 非法输入 |
| ErrorKind::TimedOut | 超时 |
| ErrorKind::Interrupted | 中断 |
| ErrorKind::Other | 其他 |
| ErrorChain::next(self) -> ?&Error | 链下一个 |

### 8.39 `std.reflect` —— 反射

| 签名（reflect 模块） | 说明 |
|---|---|
| reflect::TypeInfo::of<T>() -> TypeInfo | 获取类型信息 |
| TypeInfo::name(self) -> &str | 类型名 |
| TypeInfo::size(self) -> usize | 大小 |
| TypeInfo::align(self) -> usize | 对齐 |
| TypeInfo::is_struct(self) -> bool | 是否结构体 |
| TypeInfo::is_enum(self) -> bool | 是否枚举 |
| TypeInfo::fields(self) -> &[FieldInfo] | 字段列表 |
| TypeInfo::variants(self) -> &[VariantInfo] | 变体列表 |
| TypeInfo::methods(self) -> &[MethodInfo] | 方法列表 |
| TypeInfo::type_id(self) -> TypeId | 类型 ID |
| FieldInfo::name(self) -> &str | 字段名 |
| FieldInfo::ty(self) -> TypeInfo | 字段类型 |
| FieldInfo::offset(self) -> usize | 字段偏移 |
| VariantInfo::name(self) -> &str | 变体名 |
| VariantInfo::fields(self) -> &[FieldInfo] | 变体字段 |
| MethodInfo::name(self) -> &str | 方法名 |
| MethodInfo::params(self) -> &[TypeInfo] | 参数类型 |
| MethodInfo::return_type(self) -> TypeInfo | 返回类型 |
| reflect::type_name<T>() -> &str | 类型名 |
| reflect::type_id<T>() -> TypeId | 类型 ID |

### 8.40 `std.any` —— Any

| 签名（any 模块） | 说明 |
|---|---|
| any::Any::type_id(self) -> TypeId | 类型 ID |
| Any::is<T: Any>(self) -> bool | 是否某类型 |
| Any::downcast_ref<T: Any>(self) -> ?&T | 向下借用 |
| Any::downcast_mut<T: Any>(self) -> ?&mut T | 向下可变借用 |
| Any::downcast<T: Any>(self) -> ?T | 向下移动 |
| any::Any::new<T: Any>(v: T) -> Box<dyn Any> | 装箱为 Any |
| any::is_send(v: &dyn Any) -> bool | 是否 Send |
| any::is_sync(v: &dyn Any) -> bool | 是否 Sync |

### 8.41 `std.borrow` —— 借用

| 签名（borrow 模块） | 说明 |
|---|---|
| borrow::Borrow::borrow(&self) -> &T | trait 借用 |
| borrow::BorrowMut::borrow_mut(&mut self) -> &mut T | 可变借用 |
| borrow::Cow::Borrowed(v: &T) -> Cow<T> | 借用态 |
| borrow::Cow::Owned(v: T) -> Cow<T> | 拥有态 |
| Cow::is_borrowed(self) -> bool | 是否借用态 |
| Cow::is_owned(self) -> bool | 是否拥有态 |
| Cow::to_mut(&mut self) -> &mut T | 克隆并可变借用 |
| Cow::into_owned(self) -> T | 转为拥有 |

### 8.42 `std.cell` —— 内部可变性

| 签名（cell 模块） | 说明 |
|---|---|
| cell::Cell::new(v: T) -> Cell<T> | 新建 |
| Cell::get(&self) -> T | 读（需 Copy） |
| Cell::set(&self, v: T) | 写 |
| Cell::replace(&self, v: T) -> T | 替换并返回旧值 |
| Cell::into_inner(self) -> T | 消费取内部值 |
| Cell::as_ptr(&self) -> *mut T | 裸指针 |
| cell::RefCell::new(v: T) -> RefCell<T> | 新建 |
| RefCell::borrow(&self) -> Ref<T> | 不可变借用 |
| RefCell::borrow_mut(&self) -> RefMut<T> | 可变借用 |
| RefCell::try_borrow(&self) -> ?Ref<T> | 尝试借用 |
| RefCell::try_borrow_mut(&self) -> ?RefMut<T> | 尝试可变借用 |
| RefCell::is_borrowed(&self) -> bool | 是否已借 |
| RefCell::is_borrowed_mut(&self) -> bool | 是否已可变借 |
| RefCell::into_inner(self) -> T | 消费 |
| Ref::deref(&self) -> &T | 解借用 |
| RefMut::deref(&self) -> &T | 解借用 |
| RefMut::deref_mut(&mut self) -> &mut T | 可变解借用 |

### 8.43 `std.ops` —— 运算符 trait

| 签名（ops 模块） | 说明 |
|---|---|
| ops::Add::add(self, o: T) -> T | + |
| ops::Sub::sub(self, o: T) -> T | - |
| ops::Mul::mul(self, o: T) -> T | * |
| ops::Div::div(self, o: T) -> T | / |
| ops::Rem::rem(self, o: T) -> T | % |
| ops::Neg::neg(self) -> T | 单目 - |
| ops::Not::not(self) -> T | 单目 ! |
| ops::BitAnd::bitand(self, o: T) -> T | & |
| ops::BitOr::bitor(self, o: T) -> T | | |
| ops::BitXor::bitxor(self, o: T) -> T | ^ |
| ops::Shl::shl(self, n: u32) -> T | << |
| ops::Shr::shr(self, n: u32) -> T | >> |
| ops::Index::index(self, idx: I) -> &T | [] |
| ops::IndexMut::index_mut(self, idx: I) -> &mut T | [] 写 |
| ops::Deref::deref(self) -> &T | 解引用 |
| ops::DerefMut::deref_mut(self) -> &mut T | 可变解引用 |
| ops::Fn::call(self, args: Args) -> R | () |
| ops::FnOnce::call_once(self, args: Args) -> R | () 消费 |
| ops::FnMut::call_mut(&mut self, args: Args) -> R | () 可变 |

### 8.44 `std.toml` —— TOML

| 签名（toml 模块） | 说明 |
|---|---|
| toml::parse(s: &str) -> Result<Value, TomlError> | 解析 TOML |
| toml::stringify(v: &Value) -> String | 序列化 TOML |
| Value::Table(map: Map<String, Value>) -> Value | 表 |
| Value::Array(arr: Vec<Value>) -> Value | 数组 |
| Value::String(s: String) -> Value | 字符串 |
| Value::Integer(i: i64) -> Value | 整数 |
| Value::Float(f: f64) -> Value | 浮点 |
| Value::Boolean(b: bool) -> Value | 布尔 |
| Value::get(self, k: &str) -> ?&Value | 按键取值 |
| Value::get_path(self, path: &str) -> ?&Value | 点路径取值 |
| Value::as_table(self) -> ?&Map<String, Value> | 转表 |
| Value::as_array(self) -> ?&Vec<Value> | 转数组 |
| Value::as_str(self) -> ?&str | 转字符串 |
| Value::as_int(self) -> ?i64 | 转整数 |
| Value::as_float(self) -> ?f64 | 转浮点 |
| Value::as_bool(self) -> ?bool | 转布尔 |
| Value::type(self) -> TomlType | 类型 |
| Value::set(&mut self, k: &str, v: Value) | 按键赋值 |
| Value::eq(self, o: &Value) -> bool | 相等 |

### 8.45 `std.ini` —— INI

| 签名（ini 模块） | 说明 |
|---|---|
| ini::parse(s: &str) -> Result<Ini, IniError> | 解析 INI |
| ini::stringify(v: &Ini) -> String | 序列化 |
| Ini::new() -> Ini | 新建 |
| Ini::get(self, section: &str, key: &str) -> ?&str | 取键值 |
| Ini::set(&mut self, section: &str, key: &str, val: &str) | 设键值 |
| Ini::section(self, name: &str) -> ?&Map<String, String> | 取节 |
| Ini::sections(self) -> Vec<String> | 节列表 |
| Ini::keys(self, section: &str) -> Vec<String> | 节内键列表 |
| Ini::remove_section(&mut self, section: &str) | 删节 |
| Ini::remove_key(&mut self, section: &str, key: &str) | 删键 |

### 8.46 `std.glob` —— 通配符

| 签名（glob 模块） | 说明 |
|---|---|
| glob::Pattern::new(pat: &str) -> Result<Pattern, GlobError> | 编译模式 |
| Pattern::matches(self, s: &str) -> bool | 匹配字符串 |
| Pattern::matches_path(self, path: &str) -> bool | 匹配路径 |
| glob::glob(pat: &str) -> Result<GlobIter, GlobError> | 按模式匹配文件 |
| GlobIter::next(&mut self) -> ?String | 下一个匹配文件 |
| glob::wildmatch(pat: &str, s: &str) -> bool | shell 风格通配 |
| glob::escape(s: &str) -> String | 转义特殊字符 |
| glob::is_pattern(s: &str) -> bool | 是否含通配符 |

### 8.47 `std.bench` —— 微基准

| 签名（bench 模块） | 说明 |
|---|---|
| bench::Bencher::new() -> Bencher | 新建基准器 |
| Bencher::iter(&mut self, f: Fn()) | 迭代计次 |
| Bencher::iter_batched<F, G>(&mut self, setup: Fn(), routine: Fn(G)) | 分批迭代 |
| Bencher::bytes(&mut self, n: u64) | 报告吞吐字节数 |
| Bencher::items(&mut self, n: u64) | 报告吞吐条目数 |
| bench::black_box<T>(v: T) -> T | 黑盒防优化 |
| bench::iterations() -> u64 | 当前迭代次数 |
| bench::elapsed() -> Duration | 已耗时 |
| bench::summary(bencher: &Bencher) -> BenchResult | 取结果 |
| BenchResult::mean(self) -> Duration | 平均耗时 |
| BenchResult::median(self) -> Duration | 中位耗时 |
| BenchResult::min(self) -> Duration | 最小耗时 |
| BenchResult::max(self) -> Duration | 最大耗时 |
| BenchResult::std_dev(self) -> Duration | 标准差 |
| BenchResult::throughput(self) -> ?Throughput | 吞吐 |

### 8.48 `std.profiler` —— 性能分析

| 签名（profiler 模块） | 说明 |
|---|---|
| profiler::start(name: &str) | 开始计时段 |
| profiler::end(name: &str) | 结束计时段 |
| profiler::scope(name: &str) -> ProfilerGuard | 作用域计时 |
| profiler::report() -> Report | 生成报告 |
| profiler::reset() | 重置统计 |
| profiler::enable(on: bool) | 开关 |
| Report::sections(self) -> &[Section] | 段列表 |
| Report::total(self) -> Duration | 总耗时 |
| Report::to_string(self) -> String | 字符串报告 |
| Section::name(self) -> &str | 段名 |
| Section::count(self) -> u64 | 调用次数 |
| Section::total(self) -> Duration | 总耗时 |
| Section::mean(self) -> Duration | 平均耗时 |
| ProfilerGuard::drop(self) | 守卫析构（自动结束） |

### 8.49 `std.heap` —— 堆分配器

| 签名（heap 模块） | 说明 |
|---|---|
| heap::alloc(layout: Layout) -> *mut u8 | 分配 |
| heap::alloc_zeroed(layout: Layout) -> *mut u8 | 零分配 |
| heap::realloc(ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 | 重分配 |
| heap::dealloc(ptr: *mut u8, layout: Layout) | 释放 |
| heap::usable_size(layout: Layout) -> usize | 可用大小 |
| heap::stats() -> HeapStats | 堆统计 |
| HeapStats::allocated(self) -> usize | 已分配字节 |
| HeapStats::deallocated(self) -> usize | 已释放字节 |
| HeapStats::peak(self) -> usize | 峰值 |
| HeapStats::live_objects(self) -> usize | 存活对象数 |

### 8.50 `std.ver` —— 版本号

| 签名（ver 模块） | 说明 |
|---|---|
| ver::Version::new(major: u64, minor: u64, patch: u64) -> Version | 构造 |
| ver::Version::parse(s: &str) -> Result<Version, VerError> | 解析 SemVer |
| Version::to_string(self) -> String | 字符串 |
| Version::major(self) -> u64 | 主版本 |
| Version::minor(self) -> u64 | 次版本 |
| Version::patch(self) -> u64 | 补丁版本 |
| Version::cmp(self, o: Version) -> Ordering | 比较 |
| Version::compatible(self, o: Version) -> bool | SemVer 兼容 |
| Version::satisfies(self, req: &str) -> bool | 是否满足要求 |
| ver::Req::parse(s: &str) -> Result<Req, VerError> | 解析版本要求 |
| Req::matches(self, v: Version) -> bool | 是否匹配 |
### 8.51 `std.color` —— 颜色

| 签名（color 模块） | 说明 |
|---|---|
| color::RGB::new(r: u8, g: u8, b: u8) -> RGB | 构造 RGB |
| RGB::new_alpha(r: u8, g: u8, b: u8, a: u8) -> RGBA | 构造 RGBA |
| RGB::red(self) -> u8 | 红通道 |
| RGB::green(self) -> u8 | 绿通道 |
| RGB::blue(self) -> u8 | 蓝通道 |
| RGB::to_hsv(self) -> HSV | 转 HSV |
| RGB::to_hsl(self) -> HSL | 转 HSL |
| RGB::to_hex(self) -> String | 十六进制串 |
| RGB::from_hex(s: &str) -> ?RGB | 从十六进制构造 |
| RGB::lerp(self, o: RGB, t: f64) -> RGB | 插值 |
| RGB::mix(self, o: RGB) -> RGB | 混合 |
| RGB::blend(self, o: RGB, mode: BlendMode) -> RGB | 按混合模式混合 |
| RGB::invert(self) -> RGB | 反色 |
| RGB::grayscale(self) -> RGB | 灰度 |
| HSV::new(h: f64, s: f64, v: f64) -> HSV | 构造 HSV |
| HSV::to_rgb(self) -> RGB | 转 RGB |
| HSL::new(h: f64, s: f64, l: f64) -> HSL | 构造 HSL |
| HSL::to_rgb(self) -> RGB | 转 RGB |
| color::named(name: &str) -> ?RGB | 命名色查询 |
| color::palette::viridian() -> Vec<RGB> | Viridian 调色板 |
| color::palette::cool() -> Vec<RGB> | 冷色调色板 |
| color::gradient(a: RGB, b: RGB, n: usize) -> Vec<RGB> | 渐变 |
| BlendMode::Normal | 正常混合 |
| BlendMode::Multiply | 正片叠底 |
| BlendMode::Screen | 滤色 |
| BlendMode::Overlay | 叠加 |

### 8.52 `std.image` —— 图像

| 签名（image 模块） | 说明 |
|---|---|
| image::Image::new(w: u32, h: u32) -> Image | 新建图像 |
| Image::from_pixels(w: u32, h: u32, pixels: &[RGB]) -> Image | 从像素构造 |
| Image::load(path: &str) -> Result<Image, ImageError> | 从文件加载 |
| Image::save(&self, path: &str) -> Result<(), ImageError> | 保存到文件 |
| Image::width(self) -> u32 | 宽度 |
| Image::height(self) -> u32 | 高度 |
| Image::pixel(self, x: u32, y: u32) -> RGB | 取像素 |
| Image::put_pixel(&mut self, x: u32, y: u32, c: RGB) | 写像素 |
| Image::resize(&mut self, w: u32, h: u32, filter: Filter) -> Image | 缩放 |
| Image::crop(&self, x: u32, y: u32, w: u32, h: u32) -> Image | 裁剪 |
| Image::flip_h(&self) -> Image | 水平翻转 |
| Image::flip_v(&self) -> Image | 垂直翻转 |
| Image::rotate(&self, deg: f64) -> Image | 旋转 |
| Image::blur(&self, sigma: f64) -> Image | 高斯模糊 |
| Image::grayscale(&self) -> Image | 灰度化 |
| Image::invert(&self) -> Image | 反色 |
| Image::to_bytes(self) -> Vec<u8> | 转字节 |
| Image::from_bytes(w: u32, h: u32, data: &[u8]) -> Image | 从字节构造 |
| Filter::Nearest | 最近邻插值 |
| Filter::Linear | 双线性插值 |
| Filter::Cubic | 双三次插值 |

### 8.53 `std.audio` —— 音频

| 签名（audio 模块） | 说明 |
|---|---|
| audio::SampleRate::new(hz: u32) -> SampleRate | 采样率 |
| audio::Buffer::new(samples: &[f32], rate: SampleRate) -> Buffer | 音频缓冲 |
| Buffer::len(self) -> usize | 采样数 |
| Buffer::duration(self) -> Duration | 时长 |
| Buffer::sample_at(self, i: usize) -> f32 | 取采样 |
| audio::Player::new() -> Player | 新建播放器 |
| Player::play(&mut self, buf: &Buffer) -> Result<(), AudioError> | 播放 |
| Player::pause(&mut self) | 暂停 |
| Player::stop(&mut self) | 停止 |
| Player::set_volume(&mut self, v: f32) | 音量 |
| Player::is_playing(self) -> bool | 是否播放中 |
| audio::Mixer::new() -> Mixer | 混音器 |
| Mixer::add(&mut self, buf: &Buffer, gain: f32) | 加声道 |
| Mixer::mix(&mut self) -> Buffer | 混音输出 |
| audio::decode_wav(data: &[u8]) -> Result<Buffer, AudioError> | WAV 解码 |
| audio::decode_mp3(data: &[u8]) -> Result<Buffer, AudioError> | MP3 解码 |
| audio::encode_wav(buf: &Buffer) -> Result<Vec<u8>, AudioError> | WAV 编码 |
| audio::record(secs: Duration) -> Result<Buffer, AudioError> | 录音 |

### 8.54 `std.clipboard` / `std.prefs` / `std.keychain`

| 签名（clipboard/prefs/keychain） | 说明 |
|---|---|
| clipboard::read() -> Result<String, ClipError> | 读剪贴板文本 |
| clipboard::write(text: &str) -> Result<(), ClipError> | 写剪贴板文本 |
| clipboard::read_image() -> Result<Image, ClipError> | 读剪贴板图像 |
| clipboard::write_image(img: &Image) -> Result<(), ClipError> | 写剪贴板图像 |
| prefs::new(namespace: &str) -> Prefs | 新建偏好存储 |
| Prefs::get(self, key: &str) -> ?String | 读值 |
| Prefs::set(&mut self, key: &str, val: &str) | 写值 |
| Prefs::remove(&mut self, key: &str) | 删值 |
| Prefs::get_int(self, key: &str) -> ?i64 | 读整数 |
| Prefs::set_int(&mut self, key: &str, val: i64) | 写整数 |
| Prefs::get_bool(self, key: &str) -> ?bool | 读布尔 |
| Prefs::set_bool(&mut self, key: &str, val: bool) | 写布尔 |
| Prefs::clear(&mut self) | 清空 |
| keychain::set(service: &str, account: &str, secret: &str) -> Result<(), KeyError> | 写密钥 |
| keychain::get(service: &str, account: &str) -> Result<String, KeyError> | 读密钥 |
| keychain::delete(service: &str, account: &str) -> Result<(), KeyError> | 删密钥 |

### 8.55 `std.db` —— 嵌入式数据库

| 签名（db 模块） | 说明 |
|---|---|
| db::Sqlite::open(path: &str) -> Result<Sqlite, DbError> | 打开数据库 |
| Sqlite::close(&mut self) -> Result<(), DbError> | 关闭 |
| Sqlite::exec(&mut self, sql: &str) -> Result<u64, DbError> | 执行 SQL |
| Sqlite::query(&self, sql: &str) -> Result<Rows, DbError> | 查询 |
| Sqlite::prepare(&self, sql: &str) -> Result<Stmt, DbError> | 预编译 |
| Stmt::bind_int(&mut self, i: usize, v: i64) -> Result<(), DbError> | 绑定整数 |
| Stmt::bind_text(&mut self, i: usize, v: &str) -> Result<(), DbError> | 绑定文本 |
| Stmt::bind_null(&mut self, i: usize) -> Result<(), DbError> | 绑定 NULL |
| Stmt::step(&mut self) -> Result<?Row, DbError> | 步进 |
| Stmt::finalize(&mut self) -> Result<(), DbError> | 释放语句 |
| Row::get_int(self, i: usize) -> i64 | 取整数列 |
| Row::get_text(self, i: usize) -> String | 取文本列 |
| Row::get_blob(self, i: usize) -> Vec<u8> | 取二进制列 |
| Row::is_null(self, i: usize) -> bool | 列是否 NULL |
| Rows::next(&mut self) -> ?Row | 下一行 |
| Sqlite::transaction<F, T>(&mut self, f: F) -> Result<T, DbError> | 事务 |
| Sqlite::last_insert_rowid(&self) -> i64 | 最后插入行 ID |
| Sqlite::changes(&self) -> u64 | 受影响行数 |

### 8.56 `std.qrcode` / `std.term` / `std.tui`

| 签名（qrcode/term/tui） | 说明 |
|---|---|
| qrcode::encode(text: &str, ecl: EcLevel) -> Result<QrCode, QrError> | 编码二维码 |
| QrCode::size(self) -> usize | 矩阵尺寸 |
| QrCode::module(self, x: usize, y: usize) -> bool | 模块是否为黑 |
| QrCode::to_image(&self, scale: usize) -> Image | 转图像 |
| QrCode::to_terminal(&self) -> String | 终端字符画 |
| EcLevel::L | 低纠错 |
| EcLevel::M | 中纠错 |
| EcLevel::Q | 较高纠错 |
| EcLevel::H | 高纠错 |
| term::size() -> (u16, u16) | 终端尺寸 |
| term::clear() | 清屏 |
| term::move_to(x: u16, y: u16) | 移动光标 |
| term::hide_cursor() | 隐藏光标 |
| term::show_cursor() | 显示光标 |
| term::color(fg: Color, bg: Color) | 设置颜色 |
| term::reset() | 重置样式 |
| term::read_line() -> Result<String, TermError> | 读一行 |
| term::read_char() -> Result<char, TermError> | 读一个字符 |
| tui::App::new() -> TuiApp | 新建 TUI 应用 |
| TuiApp::run<F>(&mut self, f: F) -> Result<(), TuiError> | 运行事件循环 |
| TuiApp::draw<F>(&mut self, f: Fn(&mut Frame)) | 绘制回调 |
| Frame::rect(self) -> Rect | 帧区域 |
| Rect::new(x: u16, y: u16, w: u16, h: u16) -> Rect | 构造矩形 |

### 8.57 `std.progress` / `std.prompt` / `std.shell`

| 签名（progress/prompt/shell） | 说明 |
|---|---|
| progress::Bar::new(total: u64) -> Bar | 新建进度条 |
| Bar::set(&mut self, n: u64) | 设置进度 |
| Bar::tick(&mut self) | 推进一格 |
| Bar::set_message(&mut self, msg: &str) | 设置消息 |
| Bar::finish(&mut self) | 完成 |
| progress::Multi::new() -> MultiProgress | 多进度条 |
| Multi::add(&mut self, bar: Bar) -> Bar | 加进度条 |
| prompt::text(msg: &str) -> Result<String, PromptError> | 文本输入 |
| prompt::password(msg: &str) -> Result<String, PromptError> | 密码输入 |
| prompt::confirm(msg: &str, default: bool) -> Result<bool, PromptError> | 确认 |
| prompt::select(msg: &str, options: &[&str]) -> Result<usize, PromptError> | 选择 |
| prompt::multi_select(msg: &str, options: &[&str]) -> Result<Vec<usize>, PromptError> | 多选 |
| shell::exec(cmd: &str) -> Result<Output, ShellError> | 执行命令 |
| shell::which(cmd: &str) -> ?String | 查找命令路径 |
| shell::env(cmd: &str, args: &[&str], envs: &[(&str, &str)]) -> Result<Output, ShellError> | 带环境变量执行 |

### 8.58 `std.ffi` / `std.cinterop` / `std.jni`

| 签名（ffi/cinterop/jni） | 说明 |
|---|---|
| ffi::Library::open(path: &str) -> Result<Library, FfiError> | 打开动态库 |
| Library::get<T>(&self, sym: &str) -> Result<extern fn T, FfiError> | 取符号 |
| Library::close(&mut self) -> Result<(), FfiError> | 关闭 |
| ffi::CString::new(s: &str) -> Result<CString, FfiError> | 构造 C 字符串 |
| CString::as_ptr(&self) -> *const u8 | 裸指针 |
| CString::from_c(ptr: *const u8) -> String | 从 C 指针构造 |
| ffi::CStr::from_ptr(ptr: *const u8) -> &CStr | 借用 C 串 |
| CStr::to_string(&self) -> String | 转 Maxx 字符串 |
| ffi::OSString::new(s: &str) -> OSString | 构造 OS 串 |
| cinterop::import(path: &str) -> Result<CIface, CinteropError> | 导入 C 头文件 |
| CIface::functions(self) -> Vec<CFunc> | C 函数列表 |
| CIface::types(self) -> Vec<CType> | C 类型列表 |
| jni::attach_jvm() -> Result<Jvm, JniError> | 附加 JVM |
| jni::find_class(env: &Env, name: &str) -> Result<Class, JniError> | 查找类 |
| Env::call_method(&mut self, obj: JObj, name: &str, sig: &str, args: &[JVal]) -> Result<JVal, JniError> | 调用方法 |
| Env::new_string(env: &Env, s: &str) -> Result<JString, JniError> | 新建 Java 串 |
| Env::get_string(env: &Env, s: JString) -> Result<String, JniError> | 读 Java 串 |

### 8.59 `std.web` / `std.dom` / `std.fetch` / `std.websocket`

| 签名（web/dom/fetch/websocket） | 说明 |
|---|---|
| web::window() -> Window | 全局窗口对象 |
| web::document() -> Document | 文档对象 |
| Window::alert(msg: &str) | 弹窗 |
| Window::confirm(msg: &str) -> bool | 确认框 |
| Window::location() -> Location | 当前 URL |
| Window::set_timeout<F>(ms: u32, f: F) | 延时回调 |
| Window::set_interval<F>(ms: u32, f: F) -> IntervalId | 周期回调 |
| Window::clear_interval(id: IntervalId) | 清除周期回调 |
| Document::get_element_by_id(&self, id: &str) -> ?Element | 按 ID 取元素 |
| Document::query_selector(&self, sel: &str) -> ?Element | CSS 选择器 |
| Document::create_element(&self, tag: &str) -> Element | 创建元素 |
| Document::create_text_node(&self, text: &str) -> Node | 创建文本节点 |
| Element::set_attribute(&self, k: &str, v: &str) | 设属性 |
| Element::get_attribute(&self, k: &str) -> ?String | 取属性 |
| Element::append_child(&self, child: &Node) | 追加子节点 |
| Element::add_event_listener(&self, ev: &str, f: Fn(Event)) | 注册事件 |
| Element::text_content(&self) -> String | 文本内容 |
| Element::set_text_content(&self, s: &str) | 设文本内容 |
| Element::class_list(&self) -> ClassList | 类列表 |
| ClassList::add(&mut self, c: &str) | 加类 |
| ClassList::remove(&mut self, c: &str) | 删类 |
| fetch::get(url: &str) -> Future<Response> | GET 请求 |
| fetch::post(url: &str, body: &[u8]) -> Future<Response> | POST 请求 |
| Response::status(self) -> u16 | 状态码 |
| Response::text(self) -> Future<String> | 文本体 |
| Response::json(self) -> Future<JsonValue> | JSON 体 |
| websocket::connect(url: &str) -> Future<WebSocket> | 连接 WebSocket |
| WebSocket::send(&self, msg: &str) -> Result<(), WsError> | 发送文本 |
| WebSocket::recv(&self) -> Future<String> | 接收 |
| WebSocket::close(&self) -> Result<(), WsError> | 关闭 |

### 8.60 `std.android` / `std.ios` / `std.sensor` / `std.location`

| 签名（android/ios/sensor/location） | 说明 |
|---|---|
| android::context() -> AndroidContext | 全局 Context |
| AndroidContext::package_name() -> String | 包名 |
| AndroidContext::version_code() -> i64 | 版本号 |
| AndroidContext::version_name() -> String | 版本名 |
| AndroidContext::toast(msg: &str, dur: Duration) | Toast 提示 |
| AndroidContext::request_permission(perm: &str) -> Future<bool> | 申请权限 |
| AndroidContext::has_permission(perm: &str) -> bool | 是否有权限 |
| ios::application() -> IosApp | 全局 UIApplication |
| IosApp::open_url(url: &str) -> bool | 打开 URL |
| IosApp::version() -> String | 版本 |
| sensor::accelerometer() -> Accelerometer | 加速度计 |
| Accelerometer::read(&mut self) -> Result<Vec3, SensorError> | 读加速度 |
| sensor::gyroscope() -> Gyroscope | 陀螺仪 |
| Gyroscope::read(&mut self) -> Result<Vec3, SensorError> | 读角速度 |
| sensor::magnetometer() -> Magnetometer | 磁力计 |
| Magnetometer::read(&mut self) -> Result<Vec3, SensorError> | 读磁场 |
| sensor::proximity() -> ProximitySensor | 距离传感器 |
| ProximitySensor::is_near(&self) -> bool | 是否靠近 |
| location::request_permission() -> Future<bool> | 申请定位权限 |
| location::current() -> Result<Location, LocError> | 当前位置 |
| Location::latitude(self) -> f64 | 纬度 |
| Location::longitude(self) -> f64 | 经度 |
| Location::altitude(self) -> f64 | 海拔 |
| Location::accuracy(self) -> f64 | 精度 |

### 8.61 `std.notification` / `std.camera` / `std.gallery` / `std.share`

| 签名（notification/camera/gallery/share/haptics） | 说明 |
|---|---|
| notification::request_permission() -> Future<bool> | 申请通知权限 |
| notification::show(title: &str, body: &str) -> Result<(), NotifError> | 发通知 |
| notification::schedule(title: &str, body: &str, at: DateTime) -> Result<(), NotifError> | 定时通知 |
| camera::request_permission() -> Future<bool> | 申请相机权限 |
| camera::take_picture() -> Future<Result<Image, CamError>> | 拍照 |
| camera::record_video(dur: Duration) -> Future<Result<Video, CamError>> | 录像 |
| gallery::pick_image() -> Future<Result<Image, GalError>> | 从相册选图 |
| gallery::pick_video() -> Future<Result<Video, GalError>> | 从相册选视频 |
| gallery::save_image(img: &Image) -> Result<(), GalError> | 保存图到相册 |
| share::text(text: &str) -> Result<(), ShareError> | 分享文本 |
| share::file(path: &str) -> Result<(), ShareError> | 分享文件 |
| share::image(img: &Image) -> Result<(), ShareError> | 分享图 |
| haptics::impact(style: ImpactStyle) | 触感反馈 |
| haptics::notification(kind: NotificationKind) | 通知触感 |
| haptics::selection() | 选择触感 |

### 8.62 `std.tls` / `std.ssl` / `std.cert`

| 签名（tls/ssl/cert） | 说明 |
|---|---|
| tls::Connector::new() -> TlsConnector | 新建 TLS 连接器 |
| TlsConnector::connect(host: &str, addr: SocketAddr) -> Result<TlsStream, TlsError> | 连接 |
| TlsStream::read(&mut self, buf: &mut [u8]) -> Result<usize, IoError> | 读 |
| TlsStream::write(&mut self, buf: &[u8]) -> Result<usize, IoError> | 写 |
| TlsStream::flush(&mut self) -> Result<(), IoError> | 刷新 |
| TlsStream::peer_certificate(&self) -> Result<Cert, TlsError> | 对端证书 |
| TlsConnector::set_root_certs(&mut self, certs: &[Cert]) | 设置根证书 |
| TlsConnector::danger_accept_invalid_certs(&mut self, on: bool) | 接受非法证书（危险） |
| ssl::Library::init() -> Result<SslCtx, SslError> | 初始化 SSL |
| SslCtx::new(method: SslMethod) -> Result<SslCtx, SslError> | 新建上下文 |
| SslCtx::use_certificate_file(&mut self, path: &str) -> Result<(), SslError> | 加载证书 |
| SslCtx::use_private_key_file(&mut self, path: &str) -> Result<(), SslError> | 加载私钥 |
| cert::from_pem(data: &[u8]) -> Result<Cert, CertError> | 从 PEM 构造 |
| cert::from_der(data: &[u8]) -> Result<Cert, CertError> | 从 DER 构造 |
| Cert::subject(self) -> String | 主题 |
| Cert::issuer(self) -> String | 签发者 |
| Cert::not_before(self) -> DateTime | 生效时间 |
| Cert::not_after(self) -> DateTime | 过期时间 |
| Cert::fingerprint(self) -> Vec<u8> | 指纹 |
| Cert::to_pem(self) -> Vec<u8> | 转 PEM |

### 8.63 `std.config` / `std.cron` / `std.schedule`

| 签名（config/cron/schedule） | 说明 |
|---|---|
| config::load(path: &str) -> Result<Config, ConfigError> | 加载配置文件 |
| Config::get(self, key: &str) -> ?Value | 按键取值 |
| Config::get_str(self, key: &str) -> ?String | 取字符串 |
| Config::get_int(self, key: &str) -> ?i64 | 取整数 |
| Config::get_bool(self, key: &str) -> ?bool | 取布尔 |
| Config::set(&mut self, key: &str, val: Value) | 设值 |
| Config::merge(&mut self, other: Config) | 合并 |
| Config::save(&self, path: &str) -> Result<(), ConfigError> | 保存 |
| cron::parse(expr: &str) -> Result<Cron, CronError> | 解析 cron 表达式 |
| Cron::matches(self, time: DateTime) -> bool | 是否匹配时刻 |
| Cron::next(self, after: DateTime) -> ?DateTime | 下次触发 |
| Cron::iter(self, after: DateTime) -> CronIter | 迭代触发时刻 |
| schedule::Job::new(expr: Cron, task: TaskFn) -> Job | 新建定时任务 |
| schedule::Scheduler::new() -> Scheduler | 新建调度器 |
| Scheduler::add(&mut self, job: Job) -> JobId | 加任务 |
| Scheduler::remove(&mut self, id: JobId) | 删任务 |
| Scheduler::run(&mut self) -> Result<(), SchedError> | 运行 |
| Scheduler::stop(&mut self) | 停止 |

### 8.64 `std.compress` / `std.tar` / `std.gzip` / `std.zstd`

| 签名（compress/tar/gzip/zstd） | 说明 |
|---|---|
| compress::gzip(data: &[u8], level: u32) -> Result<Vec<u8>, CmpError> | gzip 压缩 |
| compress::gunzip(data: &[u8]) -> Result<Vec<u8>, CmpError> | gzip 解压 |
| compress::zstd(data: &[u8], level: u32) -> Result<Vec<u8>, CmpError> | zstd 压缩 |
| compress::unzstd(data: &[u8]) -> Result<Vec<u8>, CmpError> | zstd 解压 |
| compress::brotli(data: &[u8]) -> Result<Vec<u8>, CmpError> | brotli 压缩 |
| compress::unbrotli(data: &[u8]) -> Result<Vec<u8>, CmpError> | brotli 解压 |
| compress::lz4(data: &[u8]) -> Result<Vec<u8>, CmpError> | LZ4 压缩 |
| compress::unlz4(data: &[u8]) -> Result<Vec<u8>, CmpError> | LZ4 解压 |
| tar::create(path: &str, files: &[&str]) -> Result<(), TarError> | 创建 tar |
| tar::extract(path: &str, dest: &str) -> Result<(), TarError> | 解包 tar |
| tar::list(path: &str) -> Result<Vec<String>, TarError> | 列出条目 |
| gzip::compress_file(src: &str, dst: &str) -> Result<(), CmpError> | 压缩文件 |
| gzip::decompress_file(src: &str, dst: &str) -> Result<(), CmpError> | 解压文件 |
| zstd::compress_dict(data: &[u8], dict: &[u8]) -> Result<Vec<u8>, CmpError> | 字典压缩 |
| zstd::decompress_dict(data: &[u8], dict: &[u8]) -> Result<Vec<u8>, CmpError> | 字典解压 |

### 8.65 `std.graph` / `std.bitset` / `std.trie`

| 签名（graph/bitset/trie） | 说明 |
|---|---|
| graph::Graph::new() -> Graph<T, E> | 新建图 |
| Graph::add_vertex(&mut self, v: T) -> VertexId | 加顶点 |
| Graph::add_edge(&mut self, from: VertexId, to: VertexId, e: E) | 加边 |
| Graph::remove_vertex(&mut self, id: VertexId) | 删顶点 |
| Graph::neighbors(self, id: VertexId) -> Vec<VertexId> | 邻接顶点 |
| Graph::len(self) -> usize | 顶点数 |
| Graph::is_empty(self) -> bool | 是否空 |
| graph::dfs(g: &Graph, start: VertexId) -> Vec<VertexId> | DFS 遍历 |
| graph::bfs(g: &Graph, start: VertexId) -> Vec<VertexId> | BFS 遍历 |
| graph::dijkstra(g: &Graph, start: VertexId) -> Map<VertexId, u64> | Dijkstra 最短路径 |
| graph::toposort(g: &Graph) -> Result<Vec<VertexId>, GraphError> | 拓扑排序 |
| graph::union_find::new(n: usize) -> UnionFind | 新建并查集 |
| UnionFind::find(&mut self, x: usize) -> usize | 查找根 |
| UnionFind::union(&mut self, a: usize, b: usize) | 合并 |
| bitset::BitSet::new() -> BitSet | 新建位集 |
| BitSet::set(&mut self, i: usize) | 置位 |
| BitSet::clear(&mut self, i: usize) | 清位 |
| BitSet::toggle(&mut self, i: usize) | 翻位 |
| BitSet::get(&self, i: usize) -> bool | 取位 |
| BitSet::count(self) -> usize | 置位数 |
| trie::Trie::new() -> Trie | 新建前缀树 |
| Trie::insert(&mut self, s: &str) | 插入 |
| Trie::contains(self, s: &str) -> bool | 是否包含 |
| Trie::prefix(self, s: &str) -> Vec<String> | 前缀搜索 |

### 8.66 `std.priority` / `std.binaryheap` / `std.semaphore`

| 签名（priority/binaryheap/semaphore） | 说明 |
|---|---|
| priority::BinaryHeap::new() -> BinaryHeap<T> | 新建二叉堆 |
| BinaryHeap::push(&mut self, v: T) | 入堆 |
| BinaryHeap::pop(&mut self) -> ?T | 出堆 |
| BinaryHeap::peek(&self) -> ?&T | 看堆顶 |
| BinaryHeap::len(self) -> usize | 大小 |
| BinaryHeap::is_empty(self) -> bool | 是否空 |
| BinaryHeap::clear(&mut self) | 清空 |
| BinaryHeap::into_vec(self) -> Vec<T> | 转向量 |
| BinaryHeap::from_vec(v: Vec<T>) -> BinaryHeap<T> | 从向量构造 |
| semaphore::Semaphore::new(n: usize) -> Semaphore | 新建信号量 |
| Semaphore::acquire(&self) -> Result<(), SyncError> | 获取 |
| Semaphore::try_acquire(&self) -> bool | 尝试获取 |
| Semaphore::release(&self) | 释放 |
| Semaphore::available_permits(&self) -> usize | 可用许可数 |

### 8.67 `std.easing` / `std.bezier` / `std.spline`

| 签名（easing/bezier/spline） | 说明 |
|---|---|
| easing::linear(t: f64) -> f64 | 线性 |
| easing::ease_in_quad(t: f64) -> f64 | 二次缓入 |
| easing::ease_out_quad(t: f64) -> f64 | 二次缓出 |
| easing::ease_in_out_quad(t: f64) -> f64 | 二次缓入缓出 |
| easing::ease_in_cubic(t: f64) -> f64 | 三次缓入 |
| easing::ease_out_cubic(t: f64) -> f64 | 三次缓出 |
| easing::ease_in_out_cubic(t: f64) -> f64 | 三次缓入缓出 |
| easing::ease_in_back(t: f64) -> f64 | 回退缓入 |
| easing::ease_out_back(t: f64) -> f64 | 回退缓出 |
| easing::ease_out_bounce(t: f64) -> f64 | 反弹缓出 |
| easing::ease_out_elastic(t: f64) -> f64 | 弹性缓出 |
| bezier::Cubic::new(p0: Vec2, p1: Vec2, p2: Vec2, p3: Vec2) -> Cubic | 三次贝塞尔 |
| Cubic::point(self, t: f64) -> Vec2 | 取 t 处点 |
| Cubic::derivative(self, t: f64) -> Vec2 | 取 t 处导数 |
| Cubic::length(self) -> f64 | 近似长度 |
| spline::CatmullRom::new(points: &[Vec2]) -> CatmullRom | Catmull-Rom 样条 |
| CatmullRom::point(self, t: f64) -> Vec2 | 取 t 处点 |
| CatmullRom::sample(self, n: usize) -> Vec<Vec2> | 均匀采样 |

### 8.68 `std.llm` / `std.agent` / `std.rag`

| 签名（llm/agent/rag） | 说明 |
|---|---|
| llm::Client::new(endpoint: &str, key: &str) -> LlmClient | 新建客户端 |
| LlmClient::chat(&mut self, model: &str, msgs: &[Message]) -> Future<String> | 对话 |
| LlmClient::stream(&mut self, model: &str, msgs: &[Message]) -> Stream<String> | 流式对话 |
| Message::user(content: &str) -> Message | 用户消息 |
| Message::assistant(content: &str) -> Message | 助手消息 |
| Message::system(content: &str) -> Message | 系统消息 |
| llm::tokenizer::load(name: &str) -> Result<Tokenizer, LlmError> | 加载分词器 |
| Tokenizer::encode(self, text: &str) -> Vec<u32> | 编码 |
| Tokenizer::decode(self, tokens: &[u32]) -> String | 解码 |
| agent::Agent::new(llm: LlmClient, tools: &[Tool]) -> Agent | 新建智能体 |
| Agent::run(&mut self, prompt: &str) -> Future<String> | 运行 |
| Tool::new(name: &str, desc: &str, func: ToolFn) -> Tool | 新建工具 |
| rag::VectorStore::new(dim: usize) -> VectorStore | 新建向量库 |
| VectorStore::add(&mut self, id: &str, vec: &[f32], doc: &str) | 加文档 |
| VectorStore::query(self, vec: &[f32], k: usize) -> Vec<(String, f64)> | 相似度查询 |
| VectorStore::save(&self, path: &str) -> Result<(), RagError> | 保存 |
| VectorStore::load(path: &str) -> Result<VectorStore, RagError> | 加载 |
| rag::embed(model: &str, text: &str) -> Future<Vec<f32>> | 文本向量化 |

### 8.69 `std.rc` / `std.arc` / `std.arena` / `std.bump` / `std.gc`

| 签名（rc/arc/arena/bump/gc） | 说明 |
|---|---|
| rc::Rc::new<T>(v: T) -> Rc<T> | 新建引用计数指针 |
| Rc::clone(&self) -> Rc<T> | 克隆（引用 +1） |
| Rc::strong_count(&self) -> usize | 强引用数 |
| Rc::weak_count(&self) -> usize | 弱引用数 |
| Rc::downgrade(&self) -> Weak<T> | 取弱引用 |
| Weak::upgrade(&self) -> ?Rc<T> | 弱引用升级 |
| arc::Arc::new<T>(v: T) -> Arc<T> | 新建原子引用计数 |
| Arc::clone(&self) -> Arc<T> | 原子克隆 |
| Arc::strong_count(&self) -> usize | 强引用数 |
| Arc::downgrade(&self) -> WeakArc<T> | 取弱引用 |
| arena::Arena::new() -> Arena<T> | 新建 arena 分配器 |
| Arena::alloc(&mut self, v: T) -> &mut T | 分配 |
| Arena::clear(&mut self) | 清空 |
| arena::Arena::len(self) -> usize | 存活对象数 |
| bump::Bump::new() -> Bump | 新建 bump 分配器 |
| Bump::alloc<T>(&mut self, v: T) -> &mut T | 分配 |
| Bump::reset(&mut self) | 重置 |
| gc::collect() | 触发一次循环 GC |
| gc::threshold() -> usize | 当前回收阈值 |
| gc::set_threshold(n: usize) | 设回收阈值 |
| gc::stats() -> GcStats | GC 统计 |
| GcStats::collections(self) -> u64 | 回收次数 |
| GcStats::collected(self) -> u64 | 回收对象数 |

### 8.70 `std.fuzz` / `std.property` / `std.mock` / `std.snapshot`

| 签名（fuzz/property/mock/snapshot） | 说明 |
|---|---|
| fuzz::run<F>(name: &str, f: Fn(&[u8])) -> Result<(), FuzzError> | 运行模糊测试 |
| fuzz::minimize<F>(data: &[u8], f: Fn(&[u8]) -> bool) -> Vec<u8> | 最小化失败用例 |
| property::test<F>(name: &str, f: Fn()) -> Result<(), PropError> | 属性测试 |
| property::for_all<F>(gen: Gen<T>, f: Fn(T) -> bool) | 对所有生成值断言 |
| property::Gen::int(lo: i64, hi: i64) -> Gen<i64> | 整数生成器 |
| property::Gen::str(max_len: usize) -> Gen<String> | 字符串生成器 |
| property::Gen::bool() -> Gen<bool> | 布尔生成器 |
| property::Gen::choose<T>(items: &[T]) -> Gen<T> | 元素生成器 |
| property::Gen::map<F, T, U>(gen: Gen<T>, f: Fn(T) -> U) -> Gen<U> | 映射生成器 |
| property::Gen::bind<F, T, U>(gen: Gen<T>, f: Fn(T) -> Gen<U>) -> Gen<U> | 绑定生成器 |
| mock::Mock::new() -> Mock<T> | 新建 mock |
| Mock::expect<F>(&mut self, name: &str, f: Fn()) | 期望调用 |
| Mock::verify(&self) -> Result<(), MockError> | 验证调用 |
| Mock::times(&mut self, n: u32) | 期望次数 |
| Mock::return_value<T>(&mut self, name: &str, v: T) | 返回值 |
| snapshot::assert(value: &T, name: &str) -> Result<(), SnapError> | 快照断言 |
| snapshot::save(value: &T, name: &str) | 保存快照 |

### 8.71 `std.abi` / `std.link` / `std.loader`

| 签名（abi/link/loader） | 说明 |
|---|---|
| abi::Abi::C | C ABI |
| abi::Abi::System | 系统 ABI |
| abi::Abi::Fastcall | fastcall |
| abi::Abi::Thiscall | thiscall |
| link::LinkKind::Static | 静态链接 |
| link::LinkKind::Dynamic | 动态链接 |
| link::LinkKind::Framework | macOS framework |
| link::link_lib(name: &str, kind: LinkKind) | 链接系统库 |
| link::link_framework(name: &str) | 链接 framework |
| link::link_args(args: &str) | 传链接参数 |
| loader::Library::load(path: &str) -> Result<Library, LoadError> | 加载动态库 |
| Library::sym<T>(&self, name: &str) -> Result<*const T, LoadError> | 取符号 |
| Library::unload(&mut self) -> Result<(), LoadError> | 卸载 |
| loader::loaded_libs() -> Vec<String> | 已加载库列表 |
| loader::resolve(path: &str) -> Result<String, LoadError> | 解析库路径 |

### 8.72 `std.either` / `std.validated` / `std.result` more

| 签名（either/validated/result） | 说明 |
|---|---|
| either::Either::Left(v: L) -> Either<L, R> | 左值 |
| either::Either::Right(v: R) -> Either<L, R> | 右值 |
| Either::is_left(self) -> bool | 是否左 |
| Either::is_right(self) -> bool | 是否右 |
| Either::left(self) -> ?L | 取左值 |
| Either::right(self) -> ?R | 取右值 |
| Either::map<F, T>(self, f: Fn(L) -> T) -> Either<T, R> | 映射左 |
| Either::map_right<F, T>(self, f: Fn(R) -> T) -> Either<L, T> | 映射右 |
| validated::Validated::valid(v: T) -> Validated<T, E> | 有效值 |
| Validated::invalid(e: E) -> Validated<T, E> | 无效值 |
| Validated::is_valid(self) -> bool | 是否有效 |
| Validated::errors(self) -> Vec<E> | 错误列表 |
| Validated::and_then<F, U>(self, f: Fn(T) -> Validated<U, E>) -> Validated<U, E> | 绑定 |
| Validated::product<F, U>(self, other: Validated<U, E>) -> Validated<(T, U), E> | 收集错误 |
| result::Result::ok(self) -> ?T | 取 Ok 值 |
| result::Result::err(self) -> ?E | 取 Err 值 |
| Result::unwrap(self) -> T | 解包（panic） |
| Result::unwrap_or(self, default: T) -> T | 默认解包 |
| Result::unwrap_or_else<F>(self, f: Fn(E) -> T) -> T | 闭包默认解包 |
| Result::expect(self, msg: &str) -> T | 带消息解包 |
| Result::map<F, U>(self, f: Fn(T) -> U) -> Result<U, E> | 映射 |
| Result::map_err<F, U>(self, f: Fn(E) -> U) -> Result<T, U> | 映射错误 |
| Result::and_then<F, U>(self, f: Fn(T) -> Result<U, E>) -> Result<U, E> | 绑定 |
| Result::or_else<F, U>(self, f: Fn(E) -> Result<T, U>) -> Result<T, U> | 错误绑定 |
| Result::transpose(self) -> ?Result<T, E> | 转置 |
| Result::flatten(self) -> Result<T, E> | 展平 |
| Result::ok_or<E>(opt: ?T, err: E) -> Result<T, E> | 从可选构造 |

### 8.73 `std.option` / `std.default` / `std.convert`

| 签名（option/default/convert） | 说明 |
|---|---|
| option::Option::some(v: T) -> ?T | 有值 |
| option::Option::none<T>() -> ?T | 空 |
| ?T::is_some(self) -> bool | 是否有值 |
| ?T::is_none(self) -> bool | 是否空 |
| ?T::unwrap(self) -> T | 解包（panic） |
| ?T::unwrap_or(self, default: T) -> T | 默认解包 |
| ?T::unwrap_or_else<F>(self, f: Fn() -> T) -> T | 闭包默认解包 |
| ?T::expect(self, msg: &str) -> T | 带消息解包 |
| ?T::map<F, U>(self, f: Fn(T) -> U) -> ?U | 映射 |
| ?T::and_then<F, U>(self, f: Fn(T) -> ?U) -> ?U | 绑定 |
| ?T::or_else<F>(self, f: Fn() -> ?T) -> ?T | 空时回退 |
| ?T::ok_or<E>(self, err: E) -> Result<T, E> | 转结果 |
| ?T::ok_or_else<F, E>(self, f: Fn() -> E) -> Result<T, E> | 闭包转结果 |
| ?T::transpose<E>(self) -> ?Result<T, E> | 转置 |
| ?T::flatten(self) -> ?T | 展平 |
| ?T::as_ref(self) -> ?&T | 借用 |
| ?T::as_mut(self) -> ?&mut T | 可变借用 |
| ?T::cloned(self) -> ?T | 克隆 |
| default::Default::default<T: Default>() -> T | 默认值 |
| default::is_default<T: Default + Eq>(v: &T) -> bool | 是否默认值 |
| convert::From<T>::from(v: T) -> U | From trait |
| convert::Into<U>::into(self) -> U | Into trait |
| convert::TryFrom<T>::try_from(v: T) -> Result<U, TryFromError> | TryFrom trait |
| convert::TryInto<U>::try_into(self) -> Result<U, TryFromError> | TryInto trait |
| convert::AsRef<T>::as_ref(&self) -> &T | AsRef trait |
| convert::AsMut<T>::as_mut(&mut self) -> &mut T | AsMut trait |
| convert::ToOwned::to_owned(&self) -> T | ToOwned trait |

### 8.74 `std.io` 扩展 / `std.fs` 扩展 / `std.path` 扩展

| 签名（io/fs/path 扩展） | 说明 |
|---|---|
| io::copy_n(r: &mut dyn Read, w: &mut dyn Write, n: u64) -> Result<u64, IoError> | 拷贝 n 字节 |
| io::read_to_end_with_capacity(r: &mut dyn Read, cap: usize) -> Result<Vec<u8>, IoError> | 带容量读取 |
| io::write_all_fmt(w: &mut dyn Write, s: &str, args: &[Value]) -> Result<(), IoError> | 格式化写入 |
| io::sink() -> Sink | 丢弃输出 |
| io::sink_mut() -> Sink | 丢弃可变输出 |
| io::repeat(byte: u8) -> Repeat | 重复字节流 |
| io::cursor::new(data: Vec<u8>) -> Cursor | 新建游标 |
| Cursor::position(self) -> u64 | 当前位置 |
| Cursor::set_position(&mut self, pos: u64) | 设置位置 |
| fs::copy_dir(from: &str, to: &str) -> Result<u64, IoError> | 递归拷贝目录 |
| fs::remove_dir_all(path: &str) -> Result<(), IoError> | 递归删除 |
| fs::hard_link(src: &str, dst: &str) -> Result<(), IoError> | 硬链接 |
| fs::soft_link(src: &str, dst: &str) -> Result<(), IoError> | 软链接 |
| fs::read_link(path: &str) -> Result<Path, IoError> | 读软链接 |
| fs::canonicalize(path: &str) -> Result<Path, IoError> | 规范化 |
| fs::metadata(path: &str) -> Result<Metadata, IoError> | 元数据 |
| fs::symlink_metadata(path: &str) -> Result<Metadata, IoError> | 不跟随软链元数据 |
| fs::walkdir(path: &str) -> WalkDir | 递归遍历 |
| WalkDir::next(&mut self) -> ?DirEntry | 下一项 |
| WalkDir::max_depth(&mut self, n: usize) | 最大深度 |
| path::absolute(path: &str) -> Result<Path, IoError> | 绝对化 |
| path::relative(from: &str, to: &str) -> Path | 计算相对路径 |
| path::is_absolute(path: &str) -> bool | 是否绝对 |
| path::is_relative(path: &str) -> bool | 是否相对 |
| path::extension(path: &str) -> ?&str | 扩展名 |
| path::file_name(path: &str) -> ?&str | 文件名 |
| path::parent(path: &str) -> ?Path | 父目录 |

### 8.75 `std.net` 扩展 / `std.http` 扩展

| 签名（net/http 扩展） | 说明 |
|---|---|
| net::TcpListener::bind(addr: &str) -> Result<TcpListener, NetError> | 绑定 |
| TcpListener::accept(&mut self) -> Result<(TcpStream, SocketAddr), NetError> | 接受连接 |
| TcpListener::incoming(self) -> IncomingIter | 迭代连接 |
| TcpStream::connect(addr: &str) -> Result<TcpStream, NetError> | 连接 |
| TcpStream::peer_addr(self) -> Result<SocketAddr, NetError> | 对端地址 |
| TcpStream::local_addr(self) -> Result<SocketAddr, NetError> | 本地地址 |
| TcpStream::set_nodelay(&mut self, on: bool) -> Result<(), NetError> | 禁用 Nagle |
| TcpStream::set_ttl(&mut self, ttl: u32) -> Result<(), NetError> | 设 TTL |
| TcpStream::shutdown(&self, how: Shutdown) -> Result<(), NetError> | 关闭 |
| net::UdpSocket::bind(addr: &str) -> Result<UdpSocket, NetError> | 绑定 UDP |
| UdpSocket::send_to(&mut self, buf: &[u8], addr: &str) -> Result<usize, NetError> | 发送到 |
| UdpSocket::recv_from(&mut self, buf: &mut [u8]) -> Result<(usize, SocketAddr), NetError> | 接收 |
| UdpSocket::set_broadcast(&mut self, on: bool) -> Result<(), NetError> | 广播开关 |
| SocketAddr::parse(s: &str) -> Result<SocketAddr, NetError> | 解析地址 |
| SocketAddr::ip(self) -> IpAddr | IP 部分 |
| SocketAddr::port(self) -> u16 | 端口 |
| IpAddr::v4(a: u8, b: u8, c: u8, d: u8) -> IpAddr | IPv4 构造 |
| IpAddr::v6(s: &str) -> IpAddr | IPv6 构造 |
| IpAddr::is_loopback(self) -> bool | 环回地址 |
| IpAddr::is_private(self) -> bool | 私有地址 |
| http::Request::new(method: Method, url: &str) -> HttpRequest | 新建请求 |
| HttpRequest::header(&mut self, k: &str, v: &str) | 设请求头 |
| HttpRequest::body(&mut self, body: Vec<u8>) | 设体 |
| HttpRequest::send(self) -> Result<HttpResponse, NetError> | 发送 |
| HttpResponse::status(self) -> u16 | 状态码 |
| HttpResponse::headers(self) -> Map<String, String> | 响应头 |
| HttpResponse::body(self) -> Vec<u8> | 响应体 |
| HttpResponse::text(self) -> String | 文本体 |
| HttpResponse::json<T: Deserialize>(self) -> Result<T, JsonError> | JSON 体 |
| http::get(url: &str) -> Result<HttpResponse, NetError> | 快捷 GET |
| http::post(url: &str, body: &[u8]) -> Result<HttpResponse, NetError> | 快捷 POST |
| http::server::Server::new(addr: &str) -> HttpServer | 新建服务 |
| HttpServer::route(&mut self, method: Method, path: &str, handler: HandlerFn) | 注册路由 |
| HttpServer::listen(self) -> Result<(), NetError> | 监听 |

### 8.76 `std.math` 扩展 / `std.prim` 扩展

| 签名（math 扩展） | 说明 |
|---|---|
| math::erfc_inv(x: f64) -> f64 | 逆补误差函数 |
| math::beta_regularized(a: f64, b: f64, x: f64) -> f64 | 正则 Beta 函数 |
| math::gamma_regularized(a: f64, x: f64) -> f64 | 正则 Gamma 函数 |
| math::bessel_j0(x: f64) -> f64 | 第一类零阶贝塞尔 |
| math::bessel_j1(x: f64) -> f64 | 第一类一阶贝塞尔 |
| math::bessel_y0(x: f64) -> f64 | 第二类零阶贝塞尔 |
| math::bessel_y1(x: f64) -> f64 | 第二类一阶贝塞尔 |
| math::legendre(n: u32, x: f64) -> f64 | 勒让德多项式 |
| math::factorial(n: u64) -> u128 | 阶乘（128 位） |
| math::gamma(x: f64) -> f64 | Gamma 函数 |
| math::ln_gamma(x: f64) -> f64 | ln|Gamma| |
| math::digamma(x: f64) -> f64 | 双伽马函数 |
| math::trigamma(x: f64) -> f64 | 三伽马函数 |
| math::sinc(x: f64) -> f64 | sinc 函数 |
| math::logistic(x: f64) -> f64 | 逻辑函数 |
| math::logit(x: f64) -> f64 | logit 函数 |
| math::gaussian(x: f64, mu: f64, sigma: f64) -> f64 | 高斯分布 |
| math::erf(x: f64) -> f64 | 误差函数 |
| math::erfc(x: f64) -> f64 | 补误差函数 |
| math::modf(x: f64) -> (f64, f64) | 分解整数小数 |
| math::fmod(x: f64, y: f64) -> f64 | 浮点取模 |
| math::remainder(x: f64, y: f64) -> f64 | IEEE 余数 |
| math::next_after(x: f64, y: f64) -> f64 | 下一浮点数 |
| math::next_up(x: f64) -> f64 | 下一浮点数（向上） |
| math::next_down(x: f64) -> f64 | 下一浮点数（向下） |
| math::copysign(x: f64, y: f64) -> f64 | 复制符号 |
| math::sign(x: f64) -> f64 | 符号 |
| math::fract(x: f64) -> f64 | 小数部分 |
| math::trunc(x: f64) -> f64 | 向零取整 |
| math::round(x: f64) -> f64 | 四舍五入 |
| math::floor(x: f64) -> f64 | 向下取整 |
| math::ceil(x: f64) -> f64 | 向上取整 |
| math::abs(x: f64) -> f64 | 绝对值 |
| math::pow(x: f64, y: f64) -> f64 | 幂 |
| math::sqrt(x: f64) -> f64 | 平方根 |
| math::cbrt(x: f64) -> f64 | 立方根 |
| math::exp(x: f64) -> f64 | e^x |
| math::exp2(x: f64) -> f64 | 2^x |
| math::ln(x: f64) -> f64 | 自然对数 |
| math::log2(x: f64) -> f64 | log2 |
| math::log10(x: f64) -> f64 | log10 |
| math::sin(x: f64) -> f64 | 正弦 |
| math::cos(x: f64) -> f64 | 余弦 |
| math::tan(x: f64) -> f64 | 正切 |
| math::asin(x: f64) -> f64 | 反正弦 |
| math::acos(x: f64) -> f64 | 反余弦 |
| math::atan(x: f64) -> f64 | 反正切 |
| math::atan2(y: f64, x: f64) -> f64 | atan2 |
| math::sinh(x: f64) -> f64 | 双曲正弦 |
| math::cosh(x: f64) -> f64 | 双曲余弦 |
| math::tanh(x: f64) -> f64 | 双曲正切 |
| math::asinh(x: f64) -> f64 | 反双曲正弦 |
| math::acosh(x: f64) -> f64 | 反双曲余弦 |
| math::atanh(x: f64) -> f64 | 反双曲正切 |
| math::hypot(x: f64, y: f64) -> f64 | sqrt(x²+y²) |
| math::clamp(x: f64, lo: f64, hi: f64) -> f64 | 夹取 |
| math::max(x: f64, y: f64) -> f64 | 最大 |
| math::min(x: f64, y: f64) -> f64 | 最小 |
| math::lerp(a: f64, b: f64, t: f64) -> f64 | 线性插值 |
| math::deg_to_rad(d: f64) -> f64 | 角度转弧度 |
| math::rad_to_deg(r: f64) -> f64 | 弧度转角度 |
| math::gcd(a: i64, b: i64) -> i64 | 最大公约数 |
| math::lcm(a: i64, b: i64) -> i64 | 最小公倍数 |
| math::isqrt(n: u64) -> u64 | 整数平方根 |
| math::ilog2(n: u64) -> u32 | 整数 log2 |

---

## 8. 四层文件格式规范（`.max` / `.mxx` / `.smx` / `.zip`）

> **设计决策溯源**：本章的四层划分呼应"万物一理"（§0.5）——每一层只做一件事，层与层之间的转换完全透明。也呼应"透明无隐"（§0.4）——你拿到一个 `.mxx`，就知道它是原生库；拿到一个 `.smx`，就知道它是 zip 分发包；不会有"这个文件到底是源码还是库"的歧义。

### 8.1 `.max` 源文件格式

- UTF-8 文本，LF 换行，无 BOM。
- 模块即文件：`~ std.io` 对应 `std/io.max` 或 `std/io/mod.max`。
- 一行一语句；4 空格缩进分块；行尾 `;` 可选。
- 人类可读可编辑。
- 编码规范：首行可为 `//! 模块文档`；其余文档注释用 `///`。

### 8.2 `.mxx` 共享库格式（类比 C 的 `.so`/`.dll`）

由 `maxxc build foo.max` 产出 `foo.mxx`。它是一个二进制容器，包含：

| 段 | 内容 |
|---|---|
| **机器码段** | 按目标平台 ABI（x86_64-linux / arm64-android / arm64-ios / wasm32）编译的原生码 |
| **导出符号表** | 该库 `pub` 出的函数/类型/常量的符号名与地址 |
| **导入符号表** | 该库依赖的外部符号（来自其他 `.mxx` 或运行时） |
| **类型元数据** | 泛型实例化信息、vtable、反射表、布局信息 |
| **GC 绑定** | GC 指针表、析构函数表、Finalizer 注册 |
| **依赖表** | 依赖的其他 `.mxx` 的名字与版本 |

**动态加载机制**：运行时通过 `dlopen`（Linux）/ `LoadLibrary`（Windows）/ `dlopen`（macOS）等价接口加载 `.mxx`，按导入符号表解析依赖，按导出符号表对外提供服务。

**链接语义**：编译期 `~ mylib::foo` 会查 `mylib.mxx` 的导出符号表，把调用点链接到该符号；运行时由加载器完成实际地址绑定。

**与 C `.so` 的区别**：`.mxx` 自带类型元数据与 GC 绑定，跨语言 ABI 不兼容（仅 Maxx 内部使用）。它不是为了给 C 调用而设计的。

### 8.3 `.smx` 分发包格式（类比 Python whl）

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

**安装**：`maxx install mypkg` 拉取 `.smx`，解压到 `.maxx/vendor/mypkg-1.0.0/`，得到 `lib/<target>/mylib.mxx` 与 `include/mypkg/*.max`。
**依赖解析**：SemVer 版本范围；`maxx build` 自动链接 vendor 目录。

### 8.4 `.zip` 项目归档格式

- 整个项目目录的 zip 归档（源码 `.max` + 已安装 `.smx` 依赖 + README + examples/）。
- 安装：`unzip myapp.zip && cd myapp && maxx run main.max`。
- 这是给最终用户/开发者的整包发布格式，不是包管理器的格式。

### 8.5 三层转换流程

```
.max  ──maxxc build──▶  .mxx  ──maxx pack──▶  .smx  ──maxx archive──▶  .zip
源码（人写）           共享库（机器码+元数据）    分发包（whl 式 zip）      项目归档（整包）
```

---

## 9. 内存模型与垃圾回收

> **设计决策溯源**：本章的"引用计数 + 分代循环回收"呼应"诚实即高效"（§0.7）——引用计数在每次赋值/ drop 时明确记账，不偷偷扫描；移动端对时延敏感，"诚实"的引用计数比全停顿 GC 更合适。

### 9.1 栈与堆

- **栈**：局部值类型（struct / 枚举 / 数字 / char / 元组）、`[T; N]` 定长数组、借用指针。
- **堆**：`Box<T>`、`Vec<T>`、`String`、`Map<K,V>`、ADT 中的堆字段、`Rc<T>` / `Arc<T>`。
- 值类型默认栈分配；`Box<T>` 显式堆分配。

### 9.2 引用计数

- 所有堆对象头部有一个 `refcount` 字段。
- 拷贝 `Box` / `Rc<T>` / `Arc<T>` 即 `refcount += 1`。
- drop（离开作用域或显式 `drop`）时 `refcount -= 1`。
- 归零即释放对象，调用析构函数。
- `Arc<T>` 的 `refcount` 是原子操作（跨线程安全）；`Rc<T>` 是非原子（单线程，更快）。

### 9.3 循环引用回收

- 引用计数无法回收循环引用（A 引用 B，B 引用 A，refcount 都不归零）。
- Maxx 用**分代循环 GC** 周期性扫描堆，检测循环并断开。
- 引导阶段：使用 Boehm GC 作为分代循环回收的实现。
- 自举后：自实现的分代扫描器，与引用计数协同。
- `Weak<T>` / `WeakArc<T>` 是不参与 refcount 的弱引用，用于手动打破循环。

### 9.4 析构时机

- **确定性 drop**：作用域结束时自动调用析构函数。
- 析构函数通过 `impl Drop for T` 定义：`@ drop(&mut self)`。
- 无 finalizer 魔法；析构就是普通函数调用。

### 9.5 借用检查（简化版）

- 无 Rust 那种生命周期标注。
- 编译器在函数级作用域内强制：**同一时刻，一个值要么有一个 `&mut`，要么有任意多个 `&`**。
- 跨函数边界的借用通过匿名生命周期自动推导。
- 没有 double-free，没有 use-after-free。

---

## 10. 跨平台运行时架构

> **设计决策溯源**：本章的"同源"设计呼应"人即度量"（§0.3）——开发者写一份 `.max`，就能跑在桌面、移动端、Web 上，不需要为每个平台学一套新工具链。

### 10.1 桌面端（Windows / macOS / Linux）

- AOT 编译为原生可执行文件，静态链接运行时。
- 运行时核心：GC、调度器、IO 层（抽象 POSIX / WinAPI）。
- `.mxx` 即平台原生动态库，通过 `dlopen` / `LoadLibrary` 加载。

### 10.2 Android

- `.mxx` 即 `.so` 等价物，通过 JNI 包装在 APK 中加载。
- 运行时嵌入 APK，不依赖外部安装。
- 也支持 Termux 直接编译运行。
- 调度器抽象 Android Looper。

### 10.3 iOS

- `.mxx` 打包进 `.a` 静态库，嵌入 Xcode 工程。
- 运行时静态链接，不做动态加载（iOS 限制）。
- IO 层抽象 iOS 系统调用。

### 10.4 Web（WASM）

- 编译为 WASM，在浏览器中运行。
- 运行时核心裁剪（GC、调度器）；IO 层抽象浏览器 API。
- `.mxx` 即 WASM 模块。

### 10.5 运行时核心组件

| 组件 | 职责 |
|---|---|
| GC | 引用计数 + 分代循环回收 |
| 调度器 | M:N task 调度到 OS 线程池 |
| 模块加载器 | `dlopen` / `LoadLibrary` 加载 `.mxx`，符号解析 |
| IO 层 | 抽象 POSIX / WinAPI / Android Looper / iOS / 浏览器 |
| 异常处理 | panic 捕获与堆栈打印（不展开） |
| 类型元数据 | 反射、泛型实例化、布局查询 |

### 10.6 调度器设计

- M:N 模型：M 个 task 映射到 N 个 OS 线程。
- 每个 OS 线程有一个 run queue。
- `task f(args...)` 派生协程，放入当前线程的 run queue。
- `chan T` 的 `send` / `recv` 是阻塞语义，但只阻塞当前 task，不阻塞 OS 线程。
- `select` 语句在多个 channel 上等待，任一就绪即返回。

---

## 11. 错误处理模型

> **设计决策溯源**：本章的 `Result<T,E>` + `?` 传播呼应"诚实即高效"（§0.7）——错误就是普通返回值，不需要异常表和展开表，运行时代码不需要为"可能的欺骗"付费。

### 11.1 无异常栈展开

- Maxx **没有**异常机制。没有 `try/catch`，没有异常表，没有栈展开。
- 错误一律用 `Result<T,E>` 显式返回。
- `panic!` 是不可恢复错误，直接终止 task / 进程，不展开栈。

### 11.2 `Result<T,E>` 与 `?` 传播

```maxx
@ safe_div(a: f64, b: f64) -> Result<f64, str>:
    if b == 0.0:
        ret err("div by zero")
    ret ok(a / b)

@ use_div() -> Result<int, str>:
    let r = try safe_div(10.0, 2.0)?   // 出错则提前 return err
    ret ok(int(r))
```

- `?` 运算符：如果左侧是 `ok(v)`，解包为 `v`；如果是 `err(e)`，提前 `return err(e)`。
- `try` 关键字标记一个 `Result` 表达式参与 `?` 传播。
- 错误类型 `E` 必须实现 `Error` trait（可转字符串、可链式根因）。

### 11.3 panic 语义

- `panic!("msg")` 立即终止当前 task；若是 main task，则打印堆栈并以非零状态退出进程。
- panic **不展开**栈；没有 `catch`。
- 标准库所有"可能失败但不该 panic"的 API 都返回 `Result`。
- `panic!` 用于"不可恢复、编程错误"：越界、`unwrap()` on `none`、整数除零（运行期）、断言失败。

### 11.4 错误链

- `Error` trait 有 `source()` 方法，返回根因错误。
- `?` 传播时自动包装错误（通过 `From` trait），形成错误链。
- 打印错误时自动打印整条链。

---

## 12. 语法对照附录（Maxx vs Python vs Go vs Rust）

> 本章用同一段代码在四种语言里的写法，直观展示 Maxx 的设计选择。

### 12.1 结构体与方法

**Maxx**：

```maxx
# Point:
    x: f64
    y: f64

@ Point::dist(self: Point, o: Point) -> f64:
    ret sqrt((self.x - o.x)^2 + (self.y - o.y)^2)
```

**Python**：

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def dist(self, o):
        return ((self.x - o.x)**2 + (self.y - o.y)**2)**0.5
```

**Go**：

```go
type Point struct { X, Y float64 }
func (p Point) Dist(o Point) float64 {
    return math.Sqrt((p.X-o.X)*(p.X-o.X) + (p.Y-o.Y)*(p.Y-o.Y))
}
```

**Rust**：

```rust
struct Point { x: f64, y: f64 }
impl Point {
    fn dist(&self, o: &Point) -> f64 {
        ((self.x - o.x).powi(2) + (self.y - o.y).powi(2)).sqrt()
    }
}
```

### 12.2 ADT 与模式匹配

**Maxx**：

```maxx
# Shape:
    Circle(r: f64)
    Rect(w: f64, h: f64)
    Dot

@ area(s: Shape) -> f64:
    match s:
        Circle(r):   ret 3.14159265 * r * r
        Rect(w, h):  ret w * h
        Dot:         ret 0.0
```

**Python**（无 ADT，用 class + isinstance）：

```python
class Circle: ...
class Rect: ...
class Dot: ...
def area(s):
    if isinstance(s, Circle): return 3.14159265 * s.r * s.r
    elif isinstance(s, Rect): return s.w * s.h
    elif isinstance(s, Dot): return 0.0
```

**Go**（无 ADT，用 interface + type switch）：

```go
type Shape interface{}
func area(s Shape) float64 {
    switch v := s.(type) {
    case Circle: return 3.14159265 * v.r * v.r
    case Rect:   return v.w * v.h
    case Dot:    return 0.0
    }
    return 0
}
```

**Rust**：

```rust
enum Shape { Circle(f64), Rect(f64, f64), Dot }
fn area(s: Shape) -> f64 {
    match s {
        Shape::Circle(r) => 3.14159265 * r * r,
        Shape::Rect(w, h) => w * h,
        Shape::Dot => 0.0,
    }
}
```

### 12.3 错误处理

**Maxx**：

```maxx
@ safe_div(a: f64, b: f64) -> Result<f64, str>:
    if b == 0.0:
        ret err("div by zero")
    ret ok(a / b)

@ use_div() -> Result<int, str>:
    let r = try safe_div(10.0, 2.0)?
    ret ok(int(r))
```

**Python**（异常）：

```python
def safe_div(a, b):
    if b == 0: raise ValueError("div by zero")
    return a / b
def use_div():
    try:
        r = safe_div(10.0, 2.0)
        return int(r)
    except ValueError as e:
        raise
```

**Go**（显式 if err != nil）：

```go
func safeDiv(a, b float64) (float64, error) {
    if b == 0 { return 0, errors.New("div by zero") }
    return a / b, nil
}
func useDiv() (int, error) {
    r, err := safeDiv(10.0, 2.0)
    if err != nil { return 0, err }
    return int(r), nil
}
```

**Rust**：

```rust
fn safe_div(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 { return Err("div by zero".into()) }
    Ok(a / b)
}
fn use_div() -> Result<i64, String> {
    let r = safe_div(10.0, 2.0)?;
    Ok(r as i64)
}
```

### 12.4 并发

**Maxx**：

```maxx
@ worker(id: int, out: chan str):
    out.send("hello #" + str(id))

@ main() -> int:
    let ch = chan str
    task worker(1, ch)
    task worker(2, ch)
    io.println(ch.recv())
    io.println(ch.recv())
    ret 0
```

**Go**：

```go
func worker(id int, out chan string) {
    out <- fmt.Sprintf("hello #%d", id)
}
func main() {
    ch := make(chan string)
    go worker(1, ch)
    go worker(2, ch)
    fmt.Println(<-ch)
    fmt.Println(<-ch)
}
```

**Rust**（tokio）：

```rust
async fn worker(id: i64, out: mpsc::Sender<String>) {
    out.send(format!("hello #{}", id)).await.unwrap();
}
#[tokio::main]
async fn main() {
    let (tx, mut rx) = mpsc::channel(2);
    tokio::spawn(worker(1, tx.clone()));
    tokio::spawn(worker(2, tx));
    println!("{}", rx.recv().await.unwrap());
    println!("{}", rx.recv().await.unwrap());
}
```

### 12.5 对比总结

| 特性 | Maxx | Python | Go | Rust |
|---|---|---|---|---|
| ADT + match | 原生 | 无 | 无（type switch） | 原生 |
| 错误处理 | Result + ? | 异常 | if err != nil | Result + ? |
| 空值 | ?T 编译期 | None 运行时 | nil 运行时 | Option<T> |
| 并发 | task + chan | 线程+GIL | goroutine+chan | async/await |
| 内存 | RC + 分代 GC | GC 全停顿 | GC 全停顿 | 借用检查 |
| 块结构 | 缩进 | 缩进 | 花括号 | 花括号 |
| 类型推断 | 局部推断 | 动态 | 局部推断 | 局部推断 |
| 数字隐式转换 | 绝不 | 随意 | 无 | 无 |

---

## 14. 二进制分发哲学（Binary Distribution Philosophy）

> **设计决策溯源**：本章是"诚实即高效"（§0.7）在分发策略上的直接落地。用户拿到的应该是**工具**，不是源代码阅读体验。二进制不分发源码、可复现构建、签名校验——这三件事合在一起，就是"诚实"的分发：你拿到的就是你要跑的那个东西，没有隐藏的编译步骤，没有"先装个解释器"的暗门。

### 14.1 只分发机器码二进制，不分发源码

**Maxx 编译器本体（`maxxc`）的分发策略是：只分发预编译的原生二进制，不分发源码。**

这与 Rust（分发 `rustc` 源码 + 预编译二进制）、Go（分发 `go` 源码 + 预编译二进制）、Python（只分发 CPython 源码）都不同。

**为什么？**

1. **用户要的是工具，不是源代码阅读体验。** 99% 的 Maxx 用户想用的是"写 `.max` 文件，跑起来"，而不是"读 `maxxc` 的源码"。把编译器源码混进发行版，只会增加下载体积、增加安全审计负担、增加"版本不一致"的风险。
2. **二进制即真相。** 你跑的就是你下载的那个文件，没有"先编译编译器再编译我的代码"的两步黑箱。`./maxxc build main.max` 一条命令完成，不需要先 `python3 bootstrap.py`。
3. **安全供应链更短。** 只分发一个二进制，意味着供应链只有一条链：源码 → CI 构建 → 签名 → 分发。不需要担心用户在自己机器上编译编译器时被供应链攻击植入恶意代码。

**例外**：Maxx 的**标准库**（`std/*.max`）和**示例程序**是开源的，随 `.smx` 分发包一起发布。这部分用户确实需要读源码（理解 API、学习示例）。但编译器本体是黑盒二进制。

### 14.2 可复现构建（Reproducible Build）承诺

虽然我们只分发二进制，但我们承诺：**任何人都可以独立复现这个二进制**。

- **构建环境冻结**：CI 容器的 Dockerfile 公开（虽然不在主分发里，但在单独的 `build/` 仓库里）。
- **依赖锁文件**：所有编译依赖（gcc 版本、glibc 版本、Boehm GC 版本）都有精确的 hash 锁定。
- **构建命令公开**：`maxxc` 团队发布的每个版本都附带完整的构建脚本。
- **校验和公开**：每个分发的二进制都附带 SHA-256 校验和，任何人可以自己编译一个，对比 hash 是否一致。

```bash
# 验证可复现构建
$ wget https://releases.maxx-lang.org/v1.0.0/maxxc-x86_64-linux
$ wget https://releases.maxx-lang.org/v1.0.0/maxxc-x86_64-linux.sha256
$ sha256sum -c maxxc-x86_64-linux.sha256
maxxc-x86_64-linux: OK

# 或者：自己从构建脚本编译
$ git clone https://github.com/maxx-lang/build-toolchain.git
$ cd build-toolchain && docker build .
$ sha256sum ./output/maxxc
# 应该和官方发布的 SHA-256 一致
```

### 14.3 签名与校验

每个分发的二进制都用 Maxx 项目的 GPG 密钥签名：

```bash
# 下载二进制和签名
$ wget https://releases.maxx-lang.org/v1.0.0/maxxc-x86_64-linux
$ wget https://releases.maxx-lang.org/v1.0.0/maxxc-x86_64-linux.sig

# 验证签名
$ gpg --verify maxxc-x86_64-linux.sig maxxc-x86_64-linux
gpg: Good signature from "Maxx Language Project <release@maxx-lang.org>"
```

- **公钥**：公开在 `keys.maxx-lang.org` 和主流密钥服务器上。
- **密钥轮转**：每年轮转一次签名密钥，旧密钥签名的旧版本仍可验证。
- **吊销**：如果密钥泄露，立即发布吊销公告，旧版本标记为不受信任。

### 14.4 与其他语言分发模式的对比

| 语言 | 编译器分发 | 运行时分发 | 可复现构建 |
|---|---|---|---|
| Python | CPython 源码（需要自己编译或用发行版的） | 解释器随源码一起 | 无 |
| Go | `go` 二进制（预编译 + 源码） | 静态链接进二进制 | 有 |
| Rust | `rustc` 二进制（rustup 下载） | 静态链接进二进制 | 有 |
| Java | JDK 二进制（Oracle/OpenJDK） | JVM 随 JDK 一起 | 有 |
| **Maxx** | **`maxxc` 二进制（只分发二进制，不分发源码）** | **静态链接进用户程序** | **有（构建脚本公开，hash 可复现）** |

### 14.5 为什么不分发源码？

这是一个有争议的选择。我们的理由：

1. **简化用户体验**：用户不需要 `git clone && ./configure && make && make install`。
2. **缩短供应链**：一个二进制 vs 一个编译工具链。
3. **安全审计更容易**：你只需要审计一个二进制的 hash，不需要审计"编译过程中被注入了什么"。
4. **商业友好**：如果你想做 Maxx 的商业发行版，不分发源码是必要的（虽然标准库仍然开源）。

**但我们不反对任何人自己编译。** 构建脚本和 Dockerfile 是公开的，你想自己编译就自己编译——只是我们不为"自己编译"这个路径提供一等支持。

---

> **本规范文档结束。** Maxx v1.0——人写得少，机器做得多，但一切透明。
