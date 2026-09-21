# Maxx 语法规范 — EBNF 完整定义

> 本文用 EBNF 列出 Maxx 的全部语法规则。
> 版本：v1.0
> 缩进：4 空格（禁用 Tab）

---

## 1. 程序结构

```ebnf
program          = import*, toplevel*
import           = "~", path, ("as", ident)?
toplevel         = function_decl | type_decl | const_decl | module_doc
module_doc       = "//!" , { char }
```

## 2. 声明

### 2.1 函数

```ebnf
function_decl    = "pub"?, "@", ident, param_list, ("->", type)?, block
param_list       = "(", [ param, { ",", param } ], ")"
param            = ident, ":", type, ("=", expr)?
block            = indent, statement*, dedent
```

### 2.2 类型

```ebnf
type_decl        = "pub"?, "#", ident, type_params?, type_body
type_params      = "<", ident, { ",", ident }, ">"
type_body         = indent, field*, variant*, dedent
field            = ident, ":", type
variant          = ident, "(", type, { ",", type }, ")"
```

### 2.3 常量与变量

```ebnf
const_decl       = "pub"?, "const", ident, ":", type, "=", expr
var_decl         = "let", ("mut")?, ident, ":", type, "=", expr
```

## 3. 表达式

```ebnf
expr             = assign | logic_or
assign           = unary, ("=" | "+=" | "-=" | "*=" | "/="), expr

logic_or         = logic_and, ("||", logic_and)*
logic_and        = equality, ("&&", equality)*
equality         = comparison, ("==" | "!="), comparison
comparison       = term, ("<" | ">" | "<=" | ">="), term
term             = factor, ("+" | "-"), factor
factor           = unary, ("*" | "/" | "%"), unary
unary            = ("!" | "-" | "~"), postfix
postfix          = primary, (".", ident | "[" expr "]" | "(" args ")")*
primary          = literal | ident | "(", expr ")" | lambda
```

### 3.1 字面量

```ebnf
literal          = int_lit | float_lit | str_lit | bool_lit | null_lit | array_lit | map_lit
int_lit          = digit, { digit }
float_lit        = digit, ".", digit, { digit }
str_lit          = '"', { char_escape }, '"' | 'f"', { char_escape }, '"'
bool_lit         = "true" | "false"
null_lit         = "none"
array_lit        = "[", expr, { ",", expr }, "]"
map_lit          = "{", expr, ":", expr, { ",", expr, ":", expr }, "}"
```

### 3.2 函数字面量

```ebnf
lambda           = "fn", "(", param_list, ")", "->", type, block
```

## 4. 语句

```ebnf
statement        = var_decl | expr_stmt | if_stmt | while_stmt | for_stmt
                | return_stmt | break_stmt | continue_stmt | match_stmt | block

if_stmt          = "if", expr, block, ("elif", expr, block)*, ("else", block)?
while_stmt       = "while", expr, block
for_stmt         = "for", ident, "in", expr, block
return_stmt      = "ret", expr?
break_stmt       = "break"
continue_stmt    = "continue"
expr_stmt        = expr
```

### 4.1 Match 语句

```ebnf
match_stmt       = "match", expr, ":", indent, arm+, dedent
arm              = pattern, ":", block
pattern          = literal | ident | "_" | ident, "(" pattern, { ",", pattern }, ")"
```

## 5. 类型系统

```ebnf
type             = prim_type | generic_type | fn_type | ref_type | tuple_type

prim_type        = "int" | "i64" | "f64" | "bool" | "str" | "char" | "void"
generic_type     = ident, "<", type, { ",", type }, ">"
fn_type          = "fn", "(", type, { ",", type }, ")", "->", type
ref_type         = "?", type
tuple_type       = "(", type, { ",", type }, ")"
```

## 6. 关键字（完整列表）

```
let    mut    ret    if     elif   else   while  for
in     match  break  continue fn    true   false  none
some   ok     err    pub     ~     @      #      ?
```

共 **20 个关键字**。

## 7. 运算符优先级（从高到低）

| 优先级 | 运算符 | 说明 |
|---|---|---|
| 1（最高）| `()` `[]` `.` | 调用、下标、字段 |
| 2 | `!` `-` `~` | 一元 |
| 3 | `*` `/` `%` | 乘除 |
| 4 | `+` `-` | 加减 |
| 5 | `<` `>` `<=` `>=` | 比较 |
| 6 | `==` `!=` | 相等 |
| 7 | `&&` | 逻辑与 |
| 8（最低）| `||` | 逻辑或 |

## 8. 模块系统

```ebnf
import           = "~", path, ("as", ident)?
path             = ident, (".", ident)*
```

## 9. 并发

```ebnf
task_spawn       = "task", block
chan_send        = ident, "<-", expr
chan_recv        = "<-", ident
```

## 10. 错误处理

```ebnf
option_some      = "some", "(", expr, ")"
option_none      = "none"
result_ok        = "ok", "(", expr, ")"
result_err       = "err", "(", expr, ")"
try_op           = expr, "?"
```

## 11. 注释

```ebnf
comment          = "//", { char }
doc_comment      = "///", { char }
module_doc       = "//!", { char }
block_comment    = "/*", { char }, "*/"
```

## 12. 完整示例

```maxx
// 这是一个注释
/// 这是函数文档
~ std.io
~ std.collections::Vec

# Point:
    x: f64
    y: f64

@ main() -> ():
    let mut v = Vec<int>::new()
    v.push(1)
    v.push(2)
    io.println("Hello, Maxx!")
    ret
```
