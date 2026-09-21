# Maxx UI — 声明式 UI 框架

> 用 Maxx 自身语法描述 Android App 界面。文件后缀 `.maxui`（本质就是 `.max`）。
> 设计哲学：**简而有力**——只用 `Column / Row / Stack` + `Text / Button / TextField` 就能写出 90% 的 App。

---

## 1. 设计目标

Maxx UI 不是 Flutter，也不是 Compose。它的核心取舍：

| | Flutter | Jetpack Compose | Maxx UI |
|---|---|---|---|
| Widget tree diff | 有 | 有 | **无**（命令式重建） |
| 声明式 | 是 | 是 | 是 |
| 状态驱动 | StatefulWidget | remember / mutableState | **`State<T>` 单一类型** |
| 布局 | Row/Column/Stack + Expanded | Row/Column/Box | **完全一致** |
| 编译目标 | Dart VM | Kotlin JVM | **原生 Android View** |
| 学习曲线 | 陡 | 陡 | **平（只有 8 个组件）** |

**为什么没有 widget tree diff？**
因为手机端 App 的状态更新频率远低于 60fps（用户点一下、输一行字）。每次状态变化直接重建整棵 View 树，开销在 Android View 层完全可以接受。省掉 diff 算法，就省掉了 80% 的复杂度。

---

## 2. 核心类型

### 2.1 组件基类

所有 UI 组件都是 `# View` 的变体：

```maxx
~ maxx.ui

# View:
    // 标记为"组件类型"，具体字段由各组件自己定义
```

### 2.2 布局容器

```maxx
# Column:
    children: Vec<View>
    spacing: int          // 子元素间距（dp）
    padding: EdgeInsets   // 内边距
    align: Align          // 交叉轴对齐

# Row:
    children: Vec<View>
    spacing: int
    padding: EdgeInsets
    align: Align

# Stack:
    children: Vec<View>   // 叠放，第一个在最底
    padding: EdgeInsets
```

### 2.3 基础组件

```maxx
# Text:
    content: str
    size: int             // sp
    color: Color
    bold: bool

# Button:
    label: str
    on_click: fn() -> ()
    enabled: bool

# TextField:
    hint: str
    value: str
    on_change: fn(str) -> ()

# Image:
    src: str              // 资源名或文件路径
    width: int
    height: int

# Spacer:
    weight: int           // 弹性占位（类似 Flutter Expanded）
```

### 2.4 样式类型

```maxx
# Color:
    r: int
    g: int
    b: int
    a: int

# EdgeInsets:
    left: int
    top: int
    right: int
    bottom: int

# Size:
    w: int
    h: int

# Align:
    Start
    Center
    End
    Stretch
```

---

## 3. State — 状态管理

`State<T>` 是 Maxx UI 的唯一状态原语。没有 remember、no setState、no Provider。

```maxx
// 构造：State(初始值)
let count = State<int>(0)

// 读：.get()
count.get()

// 写：.set(v) —— 触发整棵树重建
count.set(count.get() + 1)

// 派生：.watch(fn) —— 状态变化时回调
count.watch(fn(v: int):
    io.println(f"count changed to {v}")
)
```

**工作机制：**
1. 用户点击 Button → 调用 `on_click`
2. `on_click` 里调用 `state.set(new_val)`
3. UI 运行时收到"状态变更"事件
4. 重新调用 `home_view()` 函数，得到新的 View 树
5. 把新树 diff 成 Android View 的最小更新（只更新文本、可见性，不重建整个 Activity）

> **简化说明：** 引导阶段（Level 1）直接全量重建；Level 2+ 引入增量更新。

---

## 4. 完整示例：Counter

```maxx
~ maxx.ui
~ std.io

@ counter_app() -> App:
    let count = State<int>(0)

    ret App{
        name = "Counter",
        home = Column{
            children = [
                Text{
                    content = "Count: " + str(count.get()),
                    size = 32,
                    color = Color{r: 0, g: 0, b: 0, a: 255},
                    bold = true,
                },
                Row{
                    children = [
                        Button{
                            label = "-",
                            on_click = fn(): count.set(count.get() - 1),
                        },
                        Button{
                            label = "+",
                            on_click = fn(): count.set(count.get() + 1),
                        },
                    ],
                    spacing = 16,
                },
                Button{
                    label = "Reset",
                    on_click = fn(): count.set(0),
                },
            ],
            spacing = 24,
            padding = EdgeInsets::all(24),
            align = Align::Center,
        }
    }

@ main() -> ():
    run_app(counter_app())
```

---

## 5. 布局规则

### 5.1 主轴与交叉轴

- `Row`：主轴水平，交叉轴垂直
- `Column`：主轴垂直，交叉轴水平
- `Stack`：重叠，无主轴概念

### 5.2 弹性空间

`Spacer{weight: n}` 占满剩余空间：

```maxx
Column{
    children = [
        Text{content = "Top", ...},
        Spacer{weight = 1},     // 把下面的推到底部
        Text{content = "Bottom", ...},
    ],
}
```

### 5.3 嵌套

容器可以任意嵌套：

```maxx
Row{
    children = [
        Column{children = [Text{...}, Text{...}], spacing = 8},
        Spacer{weight = 1},
        Button{label = "OK", on_click = fn(): ()},
    ],
    spacing = 16,
}
```

---

## 6. 路由

```maxx
# Route:
    path: str
    builder: fn() -> View

@ main() -> ():
    let router = Router{
        routes = {
            "/": home_view,
            "/about": about_view,
            "/counter": counter_view,
        }
    }
    run_app(router)
```

导航：

```maxx
navigate("/about")          // 跳转
navigate_back()             // 返回
```

---

## 7. App 类型

```maxx
# App:
    name: str
    home: View
    theme: Theme
```

`Theme` 定义全局颜色：

```maxx
# Theme:
    primary: Color
    background: Color
    text_color: Color
```

---

## 8. 如何被 Maxx Android App 加载

Maxx Android App 内置一个轻量解释器：

```
.maxui 文件
    │
    ▼  (maxx.ui loader)
解析 View 树
    │
    ▼
翻译成 Android View：
    Column  → LinearLayout(VERTICAL)
    Row     → LinearLayout(HORIZONTAL)
    Stack   → FrameLayout
    Text    → TextView
    Button  → Button
    TextField → EditText
    Spacer  → Space(weight)
    │
    ▼
setContentView(android_view)
```

**事件绑定：**
- `Button.on_click` → `view.setOnClickListener { ... }`
- `TextField.on_change` → `view.addTextChangedListener { ... }`
- `State.set()` → 标记 Activity 为"脏"，下一帧重建

**性能：**
- 首次加载：解析 + 翻译，约 50ms
- 状态更新：重建 View 树（约 16ms / 帧）
- 目标：60fps 流畅

---

## 9. 与 Flutter / Compose 的对比

| 特性 | Flutter | Compose | Maxx UI |
|---|---|---|---|
| 组件数量（核心） | ~50 | ~30 | **8** |
| 状态管理 | setState / Provider / Riverpod | remember / mutableState | **State<T> 一种** |
| 布局系统 | Flex + Expanded | Row/Column + weight | **Row/Column + Spacer** |
| 动画 | 完整动画系统 | Animatable | **Level 2+ 再加** |
| 主题 | ThemeData | MaterialTheme | **Theme{primary, bg, text}** |
| 导航 | Navigator | NavController | **Router{routes}** |
| 学习时间 | 1 周 | 3 天 | **1 小时** |

**设计取舍：**
- 没有动画：先把骨架跑起来，动画 Level 2+ 再加
- 没有列表懒加载：引导阶段直接全部渲染，列表超过 1000 项再优化
- 没有自定义绘制：用现成的 Android View，Level 2+ 加 Canvas

---

## 10. 设计哲学呼应

Maxx UI 是 Maxx 六条哲学在 UI 层的体现：

1. **简而有力** — 8 个组件覆盖 90% 场景
2. **人即度量** — 读 `.maxui` 就像读界面草图
3. **透明无隐** — 没有隐藏的 widget diff，没有 remember 魔法
4. **万物一理** — State<T> 就是唯一状态原语
5. **涌现之美** — Row/Column/Stack 组合出任意布局
6. **诚实即高效** — 直接翻译到 Android View，不绕过系统

---

## 11. 文件后缀

- UI 源文件：`.maxui`（本质就是 `.max`，只是文件名后缀标记用途）
- 编译产物：`.smx`（和普通 Maxx 项目一样）
- 最终分发包：`.apk`（Android）/ `.zip`（源码）

---

## 12. 下一步（Level 2+）

- [ ] 动画：`Animated{to: ..., duration: ms}`
- [ ] 列表：`ListView{children: Vec<View>, on_scroll: fn(int)}`
- [ ] 自定义绘制：`Canvas{draw: fn(Canvas) -> ()}`
- [ ] 手势：`on_tap / on_drag / on_long_press`
- [ ] 主题切换：`theme.dark / theme.light`

引导阶段先交付：**Column / Row / Stack / Text / Button / TextField / Spacer / Image** 8 个组件 + State<T> + Router。
