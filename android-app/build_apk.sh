#!/bin/bash
# Build Maxx Android APK
set -e

cd "$(dirname "$0")"

export ANDROID_HOME=~/android-sdk
export ANDROID_SDK_ROOT=~/android-sdk
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

echo "=== Building Maxx Android APK ==="
echo "ANDROID_HOME=$ANDROID_HOME"
echo "JAVA_HOME=$JAVA_HOME"
echo ""

# Use the local Gradle installation.
GRADLE=~/gradle-8.5/bin/gradle

echo "=== Running Gradle assembleDebug ==="
$GRADLE assembleDebug --no-daemon 2>&1

echo ""
echo "=== Build complete ==="
APK=app/build/outputs/apk/debug/app-debug.apk
if [ -f "$APK" ]; then
    ls -lh "$APK"
    echo "APK built successfully: $APK"
else
    echo "ERROR: APK not found at $APK"
    exit 1
fi
