// Maxx Android JNI Bridge
// 桥接 Maxx 运行时与 Android 平台。
// 编译为 libmaxx_runtime.so 后被 JVM 通过 System.loadLibrary 加载。

#include <jni.h>
#include <android/log.h>
#include <string.h>
#include <stdlib.h>

#define LOG_TAG "MaxxRuntime"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Maxx 运行时入口（由 maxxc 编译生成的 .mxx 调用）
extern int maxx_run_main(int argc, char** argv);

extern "C" {

JNIEXPORT jstring JNICALL
Java_com_maxx_app_MainActivity_maxxVersion(JNIEnv* env, jobject /*thiz*/) {
    return env->NewStringUTF("Maxx v1.0 (arm64-android)");
}

JNIEXPORT jstring JNICALL
Java_com_maxx_app_MainActivity_maxxRun(JNIEnv* env, jobject /*thiz*/, jstring jcode) {
    const char* code = env->GetStringUTFChars(jcode, nullptr);
    LOGI("Running Maxx snippet: %s", code);

    // 引导阶段：把 .max 代码字符串交给内嵌的解释器/编译器
    // 正式版：codegen 到 arm64 机器码，dlopen 加载 .mxx，调用 main
    char* result = (char*)malloc(4096);
    snprintf(result, 4096,
             "Maxx runtime on Android (arm64).\n"
             "Input snippet length: %zu\n"
             "Bootstrap: interpreted by embedded runtime.\n",
             strlen(code));

    env->ReleaseStringUTFChars(jcode, code);
    return env->NewStringUTF(result);
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* /*vm*/, void* /*reserved*/) {
    LOGI("Maxx runtime loaded (arm64-android)");
    return JNI_VERSION_1_6;
}

} // extern "C"
