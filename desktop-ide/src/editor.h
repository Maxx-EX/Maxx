#pragma once
#include <string>
#include "imgui.h"

/**
 * Maxx 代码编辑器
 * 
 * 支持语法高亮、行号、自动缩进。
 */
class MaxxEditor {
public:
    MaxxEditor();
    ~MaxxEditor() = default;

    void render();
    void setCode(const std::string& code);
    std::string getCode() const;

private:
    char buffer[1024 * 16] = {};  // 16KB 编辑缓冲区
    int bufferSize = 0;

    void renderLineNumbers();
    void applySyntaxHighlighting();
};
