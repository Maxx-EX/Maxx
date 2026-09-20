# Maxx for Android (arm64-android)

这是 Maxx 语言的 **Android 目标分发包**。

## 包内容
```
dist-android/
├── bin/
│   └── maxxc                 # 桌面交叉编译器（x86_64 Linux），用于把 .max 编译为 arm64-android 目标的 .mxx
├── std/*.max                 # 标准库源文件
├── examples/*.max            # 示例
├── docs/
│   ├── SPEC.md               # 语言规范（第 11 章详述 Android 运行时）
│   └── BOOTSTRAP.md
├── android-bridge/
│   └── app/src/
│       ├── mainCpp/
│       │   ├── maxx_jni.cpp     # JNI 桥接代码
│       │   └── CMakeLists.txt   # NDK 构建脚本
│       └── mainJava/com/maxx/app/
│           └── MainActivity.java # Android 入口 Activity
└── build-scripts/
    └── build_android.sh      # 一键构建脚本
```

## 在 Android 上运行 Maxx 的原理

1. **桌面交叉编译**：`maxxc build foo.max --target arm64-android` 产出 `foo.mxx`
   - `.mxx` 是 Maxx 自己的原生共享库格式（类似 `.so`）
   - 内含 arm64 机器码 + 导出符号表 + 类型元数据 + GC 绑定
2. **打包进 APK**：`.mxx` 放到 `assets/mxx/`，APK 安装时释放到应用私有目录
3. **运行时加载**：JNI 桥接代码在 `JNI_OnLoad` 时调用 `dlopen` 加载 `.mxx`
4. **Java ↔ Maxx 互操作**：Java 调 `maxxRun(code)`，桥接代码把字符串交给 Maxx 解释器/编译器执行

## 构建 APK（需要 NDK）

```bash
# 1. 安装 Android NDK r26+
export ANDROID_NDK_HOME=/path/to/android-ndk-r26

# 2. 运行构建脚本
chmod +x build-scripts/build_android.sh
./build-scripts/build_android.sh

# 3. 安装到手机
adb install -r android-bridge/app/build/outputs/apk/debug/app-debug.apk
```

## 为什么这里没有预编译的 .so

当前 sandbox 环境没有 Android NDK，无法直接产出 arm64-v8a 的 `.so` 二进制。
包内提供了：
- 完整的 JNI 桥接 C++ 源码
- CMake 构建脚本
- Gradle 工程骨架
- 一键构建 shell 脚本

在装有 NDK 的机器上跑一次 `build_android.sh` 即可得到 APK。

## Termux 直接运行

如果你用 Termux 终端模拟器：
```bash
pkg install python clang
cd dist-android
python compiler/maxxc.py run examples/hello.max   # 直接在 Termux 里跑
```

## 支持的 ABI
- `arm64-v8a`（Android 5.0+，绝大多数现代手机）
- `armeabi-v7a`（Android 4.1+，老设备）
- 预留 `x86_64`（Android 模拟器）

## 对应规范
详见 `docs/SPEC.md` 第 11 章「跨平台运行时架构」中的 Android 小节。
