cmake_minimum_required(VERSION 3.22.1)
project(maxx_runtime)

# Maxx Android 运行时 CMake 构建脚本
# 用 NDK 把 maxx_jni.cpp + 运行时 C 代码编译为 arm64-v8a / armeabi-v7a 的 .so

add_library(maxx_runtime SHARED
    src/mainCpp/maxx_jni.cpp
    # 引导阶段：把宿主 runtime_minimal.c 拷到这里一起编译
    ../../runtime/minimal_runtime.c
)

find_library(log-lib log)

target_link_libraries(maxx_runtime
    ${log-lib}
    android
)

# 编译目标：arm64-v8a（现代 Android 手机）+ armeabi-v7a（老设备）
# ABI filters 在 build.gradle 中配置
