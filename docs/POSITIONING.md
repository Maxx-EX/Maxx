# Maxx 语言定位：三位一体

> Maxx 是一门**通用系统级语言**，同时覆盖前端、脚本、系统三个领域。
> 一个语言，一套语法，编译到所有平台。

---

## 定位一：前端语言（代替 HTML + CSS + JS）

### 问题
前端三件套（HTML/CSS/JS）割裂：结构、样式、逻辑分离在三个文件里。
Maxx 用**声明式 UI + 响应式状态**，一个文件搞定整个页面。

### 示例：计数器网页
```maxx
// counter.maxx —— 整个网页就这一个文件
@ main() -> int:
    let count = state(0)
    
    page(
        title = "Counter",
        style = {
            font_family = "system-ui",
            max_width = "400px",
            margin = "0 auto",
            padding = "2rem",
        },
        body = div(
            children = [
                h1(text = "Counter Demo"),
                p(text = "Count: " + str(count)),
                button(
                    text = "+1",
                    onclick = |e| => count.value = count.value + 1,
                    style = { padding = "8px 16px", background = "#2196F3", color = "white" }
                )
            ]
        )
    )
```

### 编译输出
```bash
maxxc build counter.maxx --target web
# 输出: counter.html (自包含，含 WASM + CSS + JS)
```

### 对比
| 技术栈 | 文件数 | 语法割裂 | 状态管理 |
|--------|--------|----------|----------|
| HTML+CSS+JS | 3+ | 是 | 手动 DOM |
| React/TSX | 1+ | 样式仍需 CSS | useState |
| **Maxx** | **1** | **否** | **state() 内置** |

### 编译目标
- WebAssembly (WASM)：高性能，浏览器原生
- JavaScript (ES2020)：兼容旧浏览器
- 输出单文件 HTML：直接双击打开

---

## 定位二：嵌入式脚本语言（代替 Lua / Python / Bash）

### 问题
- Lua：语法奇怪，标准库弱
- Python：启动慢，嵌入复杂
- Bash：错误处理差，跨平台差

### Maxx 嵌入方案
```c
// C 代码嵌入 Maxx 脚本引擎
#include "maxx.h"

int main() {
    mx_State* L = mx_open();
    
    // 加载并运行脚本
    mx_dofile(L, "plugin.maxx");
    
    // 调用脚本里的函数
    mx_getglobal(L, "on_update");
    mx_pushnumber(L, delta_time);
    mx_pcall(L, 1, 0);
    
    mx_close(L);
    return 0;
}
```

### 示例：游戏插件脚本
```maxx
// plugin.maxx —— 游戏 NPC 行为
@ on_update(dt: f64):
    if player.near:
        say("Hello, traveler!")
        move_toward(player)
    
    if player.hp < 10:
        give_item("health_potion")

@ on_pickup(item: str):
    if item == "sword":
        player.attack = player.attack + 10
```

### 示例：自动化脚本（代替 Bash）
```maxx
// deploy.maxx —— 一键部署
@ main() -> int:
    let files = fs.list("./dist")
    for f in files:
        if f.ends_with(".js"):
            fs.upload(f, "ftp://server.com/www/")
    
    log.info("部署完成: " + str(len(files)) + " 个文件")
    ret 0
```

### 对比
| 语言 | 嵌入体积 | 启动速度 | 类型安全 | 跨平台 |
|------|----------|----------|----------|--------|
| Lua | ~100KB | 极快 | 无 | ✅ |
| Python | ~10MB | 慢 | 无 | ✅ |
| **Maxx** | **~200KB** | **极快** | **有** | **✅** |

---

## 定位三：系统级语言（代替 C / Rust）

### 问题
- C：无类型安全，无所有权，容易出内存 bug
- Rust：学习曲线陡峭，编译慢

### Maxx 系统级特性
- **手动内存 + GC 可选**：启动期手动，运行期 GC
- **无运行时**：内核/固件场景，零依赖
- **直接系统调用**：`sys.open()`, `sys.mmap()`
- **编译到裸机**：ARM/RISC-V，无 OS

### 示例：系统组件
```maxx
// kernel/driver.maxx —— 简单字符设备驱动
# Device:
    fd: int
    name: str

@ init(name: str) -> Device:
    let fd = sys.open("/dev/maxx", O_RDWR)
    ret Device(fd=fd, name=name)

@ read(self: Device, buf: Vec[u8]) -> int:
    ret sys.read(self.fd, buf.ptr, buf.cap)

@ write(self: Device, data: str) -> int:
    ret sys.write(self.fd, data.ptr, data.len)

@ main() -> int:
    let dev = init("sensor")
    dev.write("hello from kernel!")
    ret 0
```

### 编译目标
| 目标 | 场景 | 依赖 |
|------|------|------|
| `--target bare-arm` | 单片机/固件 | 零 |
| `--target linux` | Linux 用户态 | libc |
| `--target android` | Android NDK | libc |
| `--target web` | 浏览器 | WASM |

---

## 跨平台编译路线

```
                    Maxx 源码 (.maxx)
                          │
           ┌───────────────┼───────────────┐
           │               │               │
     前端编译器        脚本编译器        系统编译器
     (WASM/JS)       (嵌入引擎)        (裸机/系统调用)
           │               │               │
        浏览器          C 嵌入 API      ARM/RISC-V
        桌面           游戏引擎        Linux/Android
```

## 设计原则
1. **零开销抽象**：高级特性不增加运行时开销
2. **渐进式类型**：可以写动态脚本，也可以写严格类型
3. **一套语法**：前端、脚本、系统，语法统一
4. **编译优先**：AOT 编译，不是解释执行
5. **诚实**：能跑的才说是特性，规划的标注清楚
