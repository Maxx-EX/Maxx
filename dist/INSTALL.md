# Maxx 安装指南

## Linux

### 一键安装
```bash
curl -sSL https://raw.githubusercontent.com/Maxx-EX/Maxx/main/maxx-install | bash
```

### 从源码安装
```bash
git clone https://github.com/Maxx-EX/Maxx.git
cd Maxx
bash install.sh
```

### 验证
```bash
maxx version
maxx repl
```

## Android (APK)

### 下载
- 下载 `maxx-android-app-v10.apk`
- 允许安装未知来源应用
- 安装 APK

### 使用
- 打开 Maxx IDE
- 编辑 .max 文件
- 点击运行

## Termux

### 一键安装
```bash
curl -sSL https://raw.githubusercontent.com/Maxx-EX/Maxx/main/maxx-install | bash
```

### 验证
```bash
maxx version
```

## Windows（规划中）

- 提供 `.exe` 安装包
- 支持 MSYS2 / WSL

## macOS（规划中）

- 提供 `.pkg` 安装包
- 支持 Homebrew

## Web（规划中）

- WASM 运行时
- 浏览器直接运行
