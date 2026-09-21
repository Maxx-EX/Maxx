# Maxx Web 框架设计 (std.web / std.http)

> 目标：类似 Node.js / Express 的 Web 开发能力。

## 设计理念
- 轻量级：零依赖，纯标准库实现
- 异步：基于 task/chan 的异步请求处理
- 中间件：洋葱模型
- 路由：声明式路由定义

## std.http 核心 API

### 服务器
```maxx
@ main() -> int:
    let app = http.new_server(8080)
    
    app.get("/", |req| => http.response(200, "Hello, Maxx!"))
    app.get("/api/:name", |req| => {
        let name = req.param("name")
        return http.response(200, "Hello " + name)
    })
    
    app.post("/api/echo", |req| => {
        return http.response(200, req.body)
    })
    
    app.use(logger_middleware)
    app.use(cors_middleware)
    
    app.start()
    ret 0
```

### 请求对象 (Request)
```maxx
# Request:
    method: str
    path: str
    headers: Map[str, str]
    body: str
    params: Map[str, str]
    query: Map[str, str]
```

### 响应对象 (Response)
```maxx
@ http.response(status: int, body: str) -> Response:
@ http.json(data: str) -> Response:
@ http.redirect(url: str) -> Response:
```

### 中间件
```maxx
# 日志中间件
fn logger(req: Request, next: fn() -> Response) -> Response:
    io.println(req.method + " " + req.path)
    let res = next()
    return res
```

## std.web 高级封装

```maxx
@ main() -> int:
    let app = web.app()
    
    app.route("/").index(|req| => "Home")
    app.route("/about").get(|req| => "About")
    
    // 静态文件
    app.static("/static", "./public")
    
    // API 分组
    let api = app.group("/api")
    api.get("/users", |req| => json([...]))
    api.post("/users", |req| => json({...}))
    
    app.listen(3000)
    ret 0
```

## 平台支持
| 平台 | 状态 |
|------|------|
| Linux | ✅ 支持 (epoll) |
| macOS | ✅ 支持 (kqueue) |
| Windows | ⏳ 规划中 (IOCP) |
| Android | ✅ 支持 (bionic) |
| Web (WASI) | ⏳ 规划中 |
