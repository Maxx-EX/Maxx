#!/usr/bin/env bash
# Maxx Android 构建脚本
# 在装有 Android NDK 的 Linux/macOS 机器上运行
# 产出 APK：android-bridge/app/build/outputs/apk/debug/app-debug.apk

set -e

if [ -z "$ANDROID_NDK_HOME" ]; then
    echo "ERROR: 请先设置 ANDROID_NDK_HOME 环境变量"
    echo "  export ANDROID_NDK_HOME=/path/to/android-ndk-r26"
    exit 1
fi

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "=== Step 1: 用桌面 maxxc 把 .max 编译为 arm64-android 目标的 .mxx ==="
for f in std/*.max examples/*.max; do
    out="build/mxx/$(basename "$f" .max).mxx"
    mkdir -p "$(dirname "$out")"
    ./bin/maxxc build "$f" -o "$out" --target arm64-android
done

echo "=== Step 2: 把 .mxx 拷贝到 Android 工程 assets ==="
mkdir -p android-bridge/app/src/main/assets/mxx
cp build/mxx/*.mxx android-bridge/app/src/main/assets/mxx/

echo "=== Step 3: 用 Gradle 构建 APK ==="
cd android-bridge
./gradlew assembleDebug

echo ""
echo "=== 完成 ==="
echo "APK 位置: $(pwd)/app/build/outputs/apk/debug/app-debug.apk"
echo "安装: adb install -r app/build/outputs/apk/debug/app-debug.apk"
