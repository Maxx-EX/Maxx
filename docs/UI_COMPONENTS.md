# Maxx UI 组件库

> 声明式 UI 组件，编译到 Android / Web / 桌面。

## 基础组件

### Text（文本）
```maxx
Text:
    text = "Hello"
    font_size = 24
    font_weight = "bold"  // normal / bold / 100-900
    color = "#212529"
    align = "center"  // left / center / right
```

### Button（按钮）
```maxx
Button:
    text = "Click me"
    on_click = |e| => io.println("clicked")
    style = {
        background = "#2196F3"
        color = "white"
        padding = "8px 16px"
        border_radius = "8px"
    }
```

### TextField（输入框）
```maxx
TextField:
    hint = "Enter your name"
    value = name
    on_change = |v| => name = v
    keyboard_type = "text"  // text / number / email / password
```

### Image（图片）
```maxx
Image:
    src = "https://example.com/logo.png"
    width = 100
    height = 100
    fit = "cover"  // contain / cover / fill
```

## 布局组件

### Row / Column（行/列）
```maxx
Row:
    spacing = 8
    children = [
        Text: text = "A"
        Text: text = "B"
    ]

Column:
    spacing = 16
    padding = 16
    children = [...]
```

### Stack（层叠）
```maxx
Stack:
    children = [
        Image: src = "bg.jpg"
        Text: text = "Overlay"
    ]
```

### Expanded（弹性填充）
```maxx
Row:
    children = [
        Expanded:
            child = Text: text = "flexible"
        Text: text = "fixed"
    ]
```

## 导航组件

### Navigator（导航器）
```maxx
Navigator:
    initial_route = "/"
    routes = {
        "/": HomePage,
        "/settings": SettingsPage,
        "/profile/:id": ProfilePage,
    }
```

### AppBar（顶部栏）
```maxx
AppBar:
    title = "My App"
    actions = [
        IconButton: icon = "search"
        IconButton: icon = "settings"
    ]
```

## 反馈组件

### Dialog（弹窗）
```maxx
if show_dialog:
    Dialog:
        title = "Confirm"
        content = "Are you sure?"
        actions = [
            Button: text = "Cancel"
            Button: text = "OK"
        ]
```

### Snackbar（轻提示）
```maxx
Snackbar:
    message = "Saved!"
    duration = 2000  // ms
```

### Loading（加载）
```maxx
Loading:
    visible = is_loading
    size = "large"  // small / medium / large
```

## 数据展示

### ListView（列表）
```maxx
ListView:
    items = users
    item_builder = |user| => ListTile:
        title = user.name
        subtitle = user.email
        on_tap = |e| => open_profile(user)
```

### Card（卡片）
```maxx
Card:
    elevation = 4
    child = Column:
        children = [
            Image: src = "cover.jpg"
            Padding:
                child = Text: text = "Title"
        ]
```

## 完整示例：登录页
```maxx
@ main() -> int:
    let username = state("")
    let password = state("")
    let loading = state(false)
    
    Scaffold:
        app_bar = AppBar: title = "Login"
        body = Padding:
            padding = 32
            child = Column:
                spacing = 16
                main_axis = center
                
                Text:
                    text = "Welcome back!"
                    font_size = 28
                    font_weight = "bold"
                
                TextField:
                    hint = "Username"
                    value = username
                
                TextField:
                    hint = "Password"
                    keyboard_type = "password"
                    value = password
                
                Button:
                    text = if loading.value then "Loading..." else "Login"
                    on_click = |e| => {
                        loading.value = true
                        api.login(username.value, password.value)
                        loading.value = false
                    }
```

## 编译目标

| 组件 | Android | Web | Linux |
|------|---------|-----|-------|
| Text | ✅ | ✅ | ✅ |
| Button | ✅ | ✅ | ✅ |
| TextField | ✅ | ✅ | ✅ |
| Row/Column | ✅ | ✅ | ✅ |
| Navigator | ✅ | ✅ | ⏳ |
| Dialog | ✅ | ✅ | ⏳ |
| ListView | ✅ | ✅ | ⏳ |
| Image | ✅ | ✅ | ⏳ |
