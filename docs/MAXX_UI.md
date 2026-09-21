# Maxx UI 框架设计（声明式）

> 用 Maxx 代码写 UI，编译到 Android / iOS / Web / 桌面。

## 设计理念
- 声明式 UI：描述"UI 长什么样"，不描述"怎么画"
- 编译时布局：布局在编译期计算，不是运行时
- 响应式：状态变化自动刷新 UI
- 跨平台：一套代码，多平台渲染

## 基本语法

### 组件树
```maxx
@ main() -> int:
    App:
        title = "My App"
        body = Column:
            spacing = 16
            padding = 16
            
            Text:
                text = "Hello, Maxx!"
                font_size = 24
                color = "#2196F3"
            
            Button:
                text = "Click me"
                on_click = |e| => io.println("clicked!")
            
            TextField:
                hint = "Enter your name"
                on_change = |v| => name = v
```

### 布局组件
- `Row` / `Column`：水平/垂直排列
- `Stack`：层叠布局
- `Spacer`：弹性空间
- `Padding`：内边距
- `Expanded`：弹性填充

### 状态管理
```maxx
@ main() -> int:
    let count = state(0)
    
    App:
        Column:
            Text:
                text = "Count: " + str(count)
            
            Button:
                text = "+1"
                on_click = |e| => count.value = count.value + 1
```

### 导航
```maxx
@ main() -> int:
    Navigator:
        routes = {
            "/": HomePage,
            "/settings": SettingsPage,
            "/profile/:id": ProfilePage,
        }
        initial_route = "/"
```

## 编译目标

### Android
- 输出：APK
- 渲染：原生 View (via JNI)
- 布局：Compose-like 编译到 ViewGroup

### Web (WASM)
- 输出：.html + .wasm
- 渲染：DOM (via web_sys)
- 样式：CSS-in-Maxx 编译到 CSS

### Linux 桌面
- 输出：可执行文件
- 渲染：GTK / Qt (规划中)

### iOS
- 输出：.app
- 渲染：SwiftUI (规划中)

## 示例：计数器 App
```maxx
@ main() -> int:
    let count = state(0)
    
    MaterialApp:
        title = "Counter"
        home = Scaffold:
            app_bar = AppBar:
                title = "Counter Demo"
            
            body = Center:
                child = Column:
                    main_axis = center
                    children = [
                        Text:
                            text = "Count:"
                            style = h2
                        Text:
                            text = str(count)
                            style = h1
                            color = "#2196F3"
                    ]
            
            floating_action_button = FloatingActionButton:
                icon = "+"
                on_pressed = |e| => count.value = count.value + 1
```

## .maxproj 项目格式

```
my-app/
├── maxxproj.json    # 项目配置
├── src/
│   └── main.max     # 入口
├── assets/
│   ├── icon.png
│   └── fonts/
└── build/           # 编译输出
```

### maxxproj.json
```json
{
    "name": "My App",
    "version": "1.0.0",
    "package": "com.example.myapp",
    "entry": "src/main.max",
    "targets": ["android", "web", "linux"],
    "icon": "assets/icon.png"
}
```

## 跨平台编译路线

| 阶段 | 目标 | 状态 |
|------|------|------|
| v1.0 | Linux 桌面 | ✅ 已支持 |
| v2.0 | Android APK | ✅ 已支持 |
| v3.0 | Web (WASM) | ⏳ 规划中 |
| v4.0 | Windows | ⏳ 规划中 |
| v5.0 | macOS | ⏳ 规划中 |
| v6.0 | iOS | ⏳ 规划中 |
