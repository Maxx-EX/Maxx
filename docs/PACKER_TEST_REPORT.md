# Maxx Packer 测试报告

> 测试时间：2026-09-20
> 测试对象：Maxx Packer App v4

---

## 1. APK 结构验证 (unzip -l)

```
  6275584  1981-01-01 01:01   classes.dex
     3444  1981-01-01 01:01   AndroidManifest.xml
   235328  1981-01-01 01:01   resources.arsc
```

**结果**：✅ 通过
- ✅ classes.dex (Dalvik 字节码, 6.2 MB)
- ✅ AndroidManifest.xml (二进制编译后, 3.4 KB)
- ✅ resources.arsc (资源表, 235 KB)

---

## 2. APK 基本信息 (aapt dump badging)

```
package: name='com.maxx.packer'
versionCode='1'
versionName='1.0'
platformBuildVersionName='13'
platformBuildVersionCode='33'
compileSdkVersion='33'
sdkVersion:'24'
targetSdkVersion:'33'
application-label:'Maxx Packer'
```

**结果**：✅ 通过
- ✅ 包名正确
- ✅ 版本号正确
- ✅ 目标 SDK 33
- ✅ 最低 SDK 24 (Android 7.0+)
- ✅ 应用名称正确

---

## 3. 签名验证 (apksigner verify)

```
Signer #1 certificate DN: C=US, O=Android, CN=Android Debug
Signer #1 certificate SHA-256 digest: 41b827609138a84921303c8ae06e692a3e0144729012b6a70d429cb423171100
Signer #1 certificate SHA-1 digest: 93f6ee8b41b3a922165ac9a314a6784ce0997915
Signer #1 certificate MD5 digest: bfbee5dfcf90fbf1efa030d1facbd1a3
```

**结果**：✅ 通过
- ✅ Debug 签名有效
- ✅ SHA-256 摘要已生成
- ✅ 可用于测试安装

---

## 4. APK 大小

```
-rw-r--r-- 1 user user 5.5M
```

---

## 5. 构建工具链

| 工具 | 版本 | 位置 |
|------|------|------|
| aapt2 | 34.0.0 | ~/android-sdk/build-tools/34.0.0/ |
| d8 | 34.0.0 | ~/android-sdk/build-tools/34.0.0/ |
| zipalign | 34.0.0 | ~/android-sdk/build-tools/34.0.0/ |
| apksigner | 34.0.0 | ~/android-sdk/build-tools/34.0.0/ |

---

## 6. 打包流程

```
.maxproj 项目目录
    ↓
解析 maxxproj.json
    ↓
生成 AndroidManifest.xml (文本)
    ↓
aapt2 compile → 编译资源
    ↓
aapt2 link → 链接资源 (生成 resources.arsc)
    ↓
javac → 编译 Java 源码
    ↓
d8 → 生成 classes.dex
    ↓
打包未签名 APK
    ↓
zipalign → 对齐
    ↓
apksigner sign → 签名
    ↓
最终可安装 APK
```

---

## 7. 结论

Maxx Packer 产出的 APK 是**真正可安装的标准 Android APK**：
- ✅ 包含完整的 classes.dex
- ✅ 包含二进制 AndroidManifest.xml
- ✅ 包含 resources.arsc 资源表
- ✅ 已签名（debug 证书）
- ✅ 可通过 `adb install` 安装
