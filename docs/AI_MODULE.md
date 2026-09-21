# Maxx AI 标准库 (std.ai)

> 用 Maxx 写 AI 应用：张量操作、神经网络、推理。

## 设计理念
- 轻量级：嵌入式 AI，不依赖 PyTorch
- 编译期优化：常量折叠、图优化
- 跨平台：手机、嵌入式、桌面、Web

## 核心 API

### 张量 (Tensor)
```maxx
# Tensor:
    data: Vec[f64]
    shape: Vec[int]
    dtype: str

@ tensor(shape: Vec[int], data: Vec[f64]) -> Tensor:
@ zeros(shape: Vec[int]) -> Tensor:
@ ones(shape: Vec[int]) -> Tensor:
@ rand(shape: Vec[int]) -> Tensor:
@ matmul(a: Tensor, b: Tensor) -> Tensor:
@ add(a: Tensor, b: Tensor) -> Tensor:
@ relu(x: Tensor) -> Tensor:
@ softmax(x: Tensor) -> Tensor:
```

### 神经网络层
```maxx
# Linear:
    weight: Tensor
    bias: Tensor

@ linear(in_dim: int, out_dim: int) -> Linear:
@ forward(l: Linear, x: Tensor) -> Tensor:

# Conv2d:
@ conv2d(in_ch: int, out_ch: int, kernel: int) -> Conv2d:

# LSTM:
@ lstm(input_dim: int, hidden_dim: int) -> LSTM:
```

### 模型
```maxx
# Model:
    layers: Vec[Tensor]

@ load_model(path: str) -> Model:
@ save_model(model: Model, path: str):
@ predict(model: Model, input: Tensor) -> Tensor:
```

## 示例：手写数字识别
```maxx
~ std.ai

@ main() -> int:
    // 加载预训练模型
    let model = ai.load_model("mnist.onnx")
    
    // 准备输入 (28x28 图像)
    let input = ai.zeros([1, 1, 28, 28])
    input = ai.set(input, [0, 0, 14, 14], 1.0)
    
    // 推理
    let output = ai.predict(model, input)
    
    // 找最大值
    let pred = ai.argmax(output)
    io.println("预测结果: " + str(pred))
    
    ret 0
```

## 示例：简单聊天机器人
```maxx
~ std.ai

@ main() -> int:
    // 加载小模型
    let model = ai.load_model("chatbot.onnx")
    
    loop:
        let input = io.read_line()
        if input == "exit": break
        
        let tokens = ai.tokenize(input)
        let output = ai.generate(model, tokens, max_len=50)
        io.println(ai.detokenize(output))
    
    ret 0
```

## 推理引擎
- **CPU 推理**：x86/ARM，SIMD 优化
- **GPU 推理**：OpenGL ES / Vulkan (手机)
- **NPU 推理**：Android NNAPI (规划中)
- **Web 推理**：WebAssembly + WebGPU

## 平台支持
| 平台 | 推理后端 | 状态 |
|------|----------|------|
| Linux x86_64 | CPU (AVX2) | ✅ |
| Linux ARM64 | CPU (NEON) | ✅ |
| Android | CPU + NNAPI | ⏳ 规划中 |
| Web | WASM | ⏳ 规划中 |
| macOS | Core ML | ⏳ 规划中 |
