#!/bin/bash
# Build Maxx Packer APK
set -e
cd "$(dirname "$0")"
export ANDROID_HOME=~/android-sdk
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
~/gradle-8.5/bin/gradle assembleDebug --no-daemon 2>&1 | tail -15
APK=app/build/outputs/apk/debug/app-debug.apk
if [ -f "$APK" ]; then
    ls -lh "$APK"
    echo "Packer APK built successfully."
fi
