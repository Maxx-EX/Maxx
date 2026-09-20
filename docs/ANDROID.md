# Maxx Android 开发套件（MADK）专章

> 本文档是 Maxx v1.0 规范的 Android 平台专章，与 `SPEC.md` 配套阅读。
> Android 是 Maxx 的**首要目标平台**——不是"顺便支持"，而是"手机上闭环开发"。

---

## 1. 设计目标

Maxx 在 Android 上的目标不是"能跑"，而是**手机上闭环开发**：

- **写代码**：在手机上用触控键盘写 `.max` 源文件。
- **编译**：在手机上直接编译为 `.mxx` 共享库。
- **运行**：在手机上直接运行，看到输出。
- **调库**：在手机上直接调用标准库和第三方 `.smx` 包。

这意味着：
- `maxxc` 编译器本身必须能在 arm64 Android 上原生运行。
- 标准库必须有 Android 原生实现（不是 Java 层再包一层）。
- 编辑器和 REPL 是一等公民，不是附加品。

---

## 2. On-device 编辑器 / REPL 设计

### 2.1 编辑器 UI 草案

```
┌─────────────────────────────────┐
│  ← back    main.max    ☰ menu   │  ← 顶部栏：返回、文件名、菜单
├─────────────────────────────────┤
│  1  ~ std.io                    │
│  2  ~ std.math::sqrt            │
│  3                              │
│  4  # Point:                    │
│  5      x: f64                  │  ← 代码区：4 空格缩进高亮
│  6      y: f64                  │
│  7                              │
│  8  @ Point::dist(self, o)      │
│  9      ret sqrt(...)           │
│ 10                              │
│ 11  @ main() -> int:            │
│ 12      let p = Point{...}      │
│ 13      io.println("dist = " +  │  ← 光标行：底部建议栏弹出
│       ┌─────────────────┐      │
│       │ io.println(str)  │      │  ← 自动补全建议
│       │ io.print(s)      │      │
│       │ io.flush()       │      │
│       └─────────────────┘      │
├─────────────────────────────────┤
│  ▶ run   ⌨️  </>  📁  🔍  🐛   │  ← 底部工具栏
└─────────────────────────────────┘
```

**关键交互设计**：

- **触控键盘**：自定义键盘，顶部一行快捷键（`@ # ~ :: => |> ? .`），减少触摸层级。
- **语法高亮**：`@` 函数名橙色、`#` 类型名蓝色、`~` 导入绿色、关键字紫色、字符串绿色、注释灰色。
- **自动缩进**：换行后自动补 4 空格；`:` 结尾的行换行后自动多缩进一层。
- **错误浮层**：编译错误显示在对应行下方的红色浮层，点击跳转到错误位置。
- **实时 lint**：边写边检查未使用变量、类型不匹配，黄色波浪线提示。
- **括号匹配**：光标停在括号上时，高亮配对的另一半。
- **选择模式**：长按进入选择模式，出现剪切/复制/粘贴浮动工具条。

### 2.2 REPL 交互设计

```
maxx> ~ std.io
maxx> ~ std.math::sqrt
maxx> let x = 3.0
x: f64 = 3.0
maxx> let y = 4.0
y: f64 = 4.0
maxx> sqrt(x*x + y*y)
5.0
maxx> # Point:
.....   x: f64
.....   y: f64
@ Point: 已定义
maxx> @ Point::dist(self: Point, o: Point) -> f64:
.....   ret sqrt((self.x-o.x)^2 + (self.y-o.y)^2)
@ Point::dist: 已定义
maxx> let p = Point{x: 3.0, y: 4.0}
p: Point = Point { x: 3.0, y: 4.0 }
maxx> let q = Point{x: 0.0, y: 0.0}
q: Point = Point { x: 0.0, y: 0.0 }
maxx> p.dist(q)
5.0
maxx> :exit
```

**REPL 规则**：

- 提示符 `maxx> `。
- 逐行求值，立即显示类型和值。
- 多行块：以 `#` / `@` / `if` / `for` 等块关键字开头时，提示符变为 `..... `（缩进跟随），连续空行结束块。
- 历史：上下箭头翻历史，Ctrl+R 搜索历史。
- 自动补全：Tab 补全标识符和方法。
- 特殊命令：`:help`、`:quit`、`:reset`、`:load file.max`、`:save file.max`。

---

## 3. 两种运行形态

### 3.1 Termux 环境

```bash
$ pkg install clang
$ pkg install make
$ git clone https://github.com/maxx-lang/maxx.git
$ cd maxx
$ ./bootstrap.sh
$ maxxc run examples/hello.max
Hello, Maxx!
```

- **直接在 Termux 里跑**，不需要 Android Studio。
- `maxxc` 编译为 arm64 原生二进制，直接调用 Termux 的 clang 后端。
- 标准库 `.smx` 预编译为 arm64-android 目标，`pkg install maxx-std` 即可安装。
- 适合：高级用户、Termux 重度用户、服务器开发者。

### 3.2 独立 App（MADK App）

```
MADK App
├── app/
│   ├── build.gradle
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/maxx/madk/
│       │   ├── MainActivity.java
│       │   ├── EditorActivity.java
│       │   └── ReplActivity.java
│       ├── cpp/
│       │   ├── CMakeLists.txt
│       │   ├── maxx_runtime.cpp    # JNI 桥
│       │   └── libmaxx_runtime.so  # 预编译运行时
│       └── assets/
│           ├── std/                # 标准库 .max 源文件
│           │   ├── core.max
│           │   ├── prim.max
│           │   └── ...
│           ├── lib/arm64-android/ # 标准库 .mxx
│           │   └── libstd.mxx
│           └── examples/
│               ├── hello.max
│               └── gui.max
```

- **独立 App**：不需要 Termux，从 Play Store 安装即可用。
- 内嵌 `libmaxx_runtime.so`（Maxx 运行时：GC、调度器、IO）。
- `assets/std/` 放标准库 `.max` 源文件和预编译 `.mxx`。
- 用户的 `.max` 源文件存在应用私有目录，编译后 `.mxx` 也存在那里。
- 适合：普通用户、学生、手机开发者。

---

## 4. `.mxx` ↔ `.so` 对应关系

在 Android 上，`.mxx` **直接就是 ART 可 `dlopen` 的 `.so` 格式扩展**。

### 4.1 二进制布局

```
libmylib.mxx  (= libmylib.so + Maxx 元数据)
├── ELF 头
├── .text          # 机器码段（ARM64 指令）
├── .data          # 全局数据
├── .rodata        # 只读数据
├── .dynsym        # 动态符号表（导出/导入）
├── .dynstr        # 动态字符串表
├── .hash          # 符号哈希表
├── .plt           # 过程链接表
├── .got           # 全局偏移表
├── .maxx_meta     # Maxx 类型元数据（新增段）
│   ├── 泛型实例化信息
│   ├── vtable 表
│   ├── 反射表
│   └── 布局信息
├── .maxx_gc       # Maxx GC 绑定（新增段）
│   ├── GC 指针表
│   ├── 析构函数表
│   └── Finalizer 注册
└── .maxx_deps     # Maxx 依赖表（新增段）
    └── 依赖的 .mxx 名字与版本
```

### 4.2 JNI 注册

`.mxx` 导出符号用 JNI 命名约定注册：

```c
// Maxx 编译器自动生成的 JNI 桥代码
JNIEXPORT jstring JNICALL
Java_com_maxx_madk_NativeBridge_callMaxx(
    JNIEnv *env, jobject thiz, jstring j_code) {

    const char *code = (*env)->GetStringUTFChars(env, j_code, NULL);
    char *result = maxx_eval(code);  // 调用 Maxx 运行时求值
    (*env)->ReleaseStringUTFChars(env, j_code, code);
    return (*env)->NewStringUTF(env, result);
}
```

### 4.3 Java/Kotlin 端调用

```kotlin
// Kotlin 端
class NativeBridge {
    external fun callMaxx(code: String): String

    companion object {
        init {
            System.loadLibrary("maxx_runtime")  // 加载 Maxx 运行时
        }
    }
}

// 在 Activity 里调用
val bridge = NativeBridge()
val output = bridge.callMaxx("""
    ~ std.io
    @ main() -> int:
        io.println("Hello from Maxx!")
        ret 0
""")
textView.text = output
```

---

## 5. Android 内存模型

### 5.1 堆隔离边界

```
┌─────────────────────────────────┐
│  ART 堆（Java/Kotlin 对象）     │  ← Java 对象在这里
├─────────────────────────────────┤
│  Maxx 堆（C/C++ 堆）            │  ← Maxx 对象在这里
│  ┌─────────────────────────┐   │
│  │ Maxx GC 管理             │   │
│  │ (RC + 分代循环回收)      │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

- **Maxx 堆自己 GC**，不碰 ART 堆。
- **JNI 调用时做值拷贝**：Java String → JNI 拷贝为 C 字符串 → Maxx String；Maxx String → JNI 拷贝为 Java String。
- **不能跨 GC 持有 jobject 裸指针**——jobject 是 ART 堆上的句柄，Maxx GC 不知道它，必须用 `NewGlobalRef` 把它钉住。

### 5.2 JNI 引用规则

```maxx
// 错误：跨 GC 持有 jobject 裸指针
@ bad_callback(env: JNIEnv, obj: jobject):
    // obj 是 ART 堆上的句柄，Maxx GC 不知道它
    // 如果 ART GC 移动了 obj，这个指针就悬空了
    call_java_method(env, obj, ...)  // 可能 crash

// 正确：用 NewGlobalRef 钉住
@ good_callback(env: JNIEnv, obj: jobject):
    let global_ref = env.NewGlobalRef(obj)  // 钉住
    defer env.DeleteGlobalRef(global_ref)   // 用完释放
    call_java_method(env, global_ref, ...)
```

### 5.3 内存预算

| 指标 | 预算 |
|---|---|
| Maxx 堆初始大小 | 16 MB |
| Maxx 堆最大大小 | 50 MB |
| GC pause（单次） | < 16 ms（60fps 不掉帧） |
| 冷启动时间 | < 500 ms |
| 常驻内存（空闲） | < 30 MB |

---

## 6. Android 线程模型

### 6.1 task → pthread 映射

```
Maxx task  ──映射──▶  pthread
                        │
                        └── 跑在 Android Looper 的 HandlerThread 上
```

- Maxx 的 `task` 直接映射到 pthread，不碰 ART 的 JVMTI。
- 调度器跑在一个专用的 HandlerThread 上，不阻塞主线程（UI 线程）。
- UI 更新必须 post 到主线程：

```maxx
@ update_ui(text: str):
    // 不能直接在 Maxx task 里更新 UI
    // 必须 post 到 Android 主线程
    android::run_on_ui_thread(fn():
        text_view.setText(text)
    )
```

### 6.2 线程优先级

| 线程 | Android 优先级 | 用途 |
|---|---|---|
| 主线程 | ANDROID_PRIORITY_DISPLAY | UI 渲染 |
| Maxx 调度线程 | ANDROID_PRIORITY_DEFAULT | task 调度 |
| Maxx IO 线程 | ANDROID_PRIORITY_BACKGROUND | 磁盘/网络 IO |
| Maxx GC 线程 | ANDROID_PRIORITY_LOWEST | 后台 GC |

---

## 7. 与 Java/Kotlin 互操作 ABI

### 7.1 C ABI 桥

Maxx 导出函数用 C ABI 命名约定：

```c
// Maxx 编译器自动生成的导出符号
JNIEXPORT jstring JNICALL
Java_com_maxx_madk_NativeBridge_callMaxx(JNIEnv *env, jobject thiz, jstring j_code);

JNIEXPORT jint JNICALL
Java_com_maxx_madk_NativeBridge_runFile(JNIEnv *env, jobject thiz, jstring j_path);

JNIEXPORT void JNICALL
Java_com_maxx_madk_NativeBridge_evaluateAsync(JNIEnv *env, jobject thiz, jstring j_code, jobject j_callback);
```

### 7.2 数据类型映射

| Maxx 类型 | Java 类型 | JNI 类型 |
|---|---|---|
| `i64` | `long` | `jlong` |
| `f64` | `double` | `jdouble` |
| `bool` | `boolean` | `jboolean` |
| `str` | `String` | `jstring` |
| `Vec<u8>` | `byte[]` | `jbyteArray` |
| `?T` | `@Nullable T` | `jobject`（可空） |
| `Result<T,E>` | `Result<T, E>` | 自定义类 |

### 7.3 异常映射

- Maxx `panic!` → Java 端抛出 `MaxxPanicException`。
- Maxx `Result::err(e)` → Java 端返回 `Result.err(e.toString())`。
- JNI 异常检查：每次 JNI 调用后检查 `ExceptionCheck`，有异常就转回 Maxx `err`。

---

## 8. Maxx Android 开发套件（MADK）

### 8.1 套件内容

| 组件 | 说明 |
|---|---|
| `maxxc` 二进制 | arm64 原生编译器（约 5 MB） |
| `std/*.max` | 标准库源文件（约 2 MB） |
| `lib/<target>/*.mxx` | 预编译标准库共享库（约 10 MB） |
| 编辑器 APK | 代码编辑器 + REPL（约 15 MB） |
| `libmaxx_runtime.so` | Maxx 运行时（GC + 调度器 + IO，约 5 MB） |
| 示例 `.max` 程序 | hello / gui / concurrency / ffi（约 1 MB） |
| 文档 HTML | 离线文档（约 5 MB） |

**总大小**：约 43 MB（单个 APK）。

### 8.2 安装方式

- **Google Play**：搜索 "Maxx MADK" 安装。
- **直接安装**：下载 `.apk`，允许"未知来源"安装。
- **Termux**：`pkg install maxx`（不含编辑器，只有命令行工具）。

### 8.3 目录结构

```
/data/data/com.maxx.madk/
├── files/
│   ├── projects/           # 用户项目
│   │   └── myapp/
│   │       ├── mod.max
│   │       ├── maxx.toml
│   │       └── src/
│   ├── cache/              # 编译缓存
│   └── vendor/              # 安装的 .smx 依赖
├── assets/                  # 只读资源
│   ├── std/                 # 标准库源文件
│   ├── lib/                 # 预编译 .mxx
│   ├── examples/            # 示例
│   └── docs/                # 离线文档
└── lib/
    └── arm64-v8a/
        ├── libmaxx_runtime.so
        └── libnative_bridge.so
```

---

## 9. 性能预算

| 指标 | 预算 | 测量方法 |
|---|---|---|
| 冷启动（App 启动到 REPL 可用） | < 500 ms | `adb shell am start -W` |
| REPL 求值（简单表达式） | < 10 ms | 内部计时 |
| 编译（100 行 `.max`） | < 200 ms | 内部计时 |
| GC pause（单次） | < 16 ms | 不影响 60fps |
| 内存占用（空闲 REPL） | < 30 MB | ` dumpsys meminfo` |
| 内存占用（跑复杂程序） | < 50 MB | `dumpsys meminfo` |
| 标准库 `.mxx` 加载 | < 100 ms | `dlopen` 计时 |

---

## 10. 与 Android 系统 API 互操作

### 10.1 传感器

```maxx
~ std.sensor

@ main() -> int:
    let accel = sensor::accelerometer()
    loop:
        let v = accel.read()?
        io.println(f"x={v.x:.2f} y={v.y:.2f} z={v.z:.2f}")
        time::sleep(100ms)
    ret 0
```

### 10.2 位置

```maxx
~ std.location

@ main() -> int:
    location::request_permission()?
    let loc = location::current()?
    io.println(f"lat={loc.latitude()} lon={loc.longitude()}")
    ret 0
```

### 10.3 通知

```maxx
~ std.notification

@ main() -> int:
    notification::request_permission()?
    notification::show("Maxx", "Hello from Android!")
    ret 0
```

### 10.4 相机

```maxx
~ std.camera

@ main() -> int:
    camera::request_permission()?
    let img = camera::take_picture()?
    io.println(f"Photo taken: {img.width()}x{img.height()}")
    ret 0
```

---

> **Maxx 之道在 Android 上的体现**：人写得少（手机上触控键盘写代码），机器做得多（自动编译、自动 GC、自动调度），但一切透明（JNI 边界清晰、GC 堆隔离、内存预算明确）。
