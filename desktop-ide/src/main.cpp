/**
 * Maxx Desktop IDE - 主入口
 * 
 * 基于 ImGui + GLFW 的跨平台代码编辑器。
 * 深色主题，毛玻璃风格，对接 Maxx 编译器。
 */

#include <iostream>
#include <string>
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"
#include <GLFW/glfw3.h>

// 模块
#include "editor.h"
#include "console.h"
#include "file_tree.h"
#include "compiler_runner.h"

static void glfw_error_callback(int error, const char* description) {
    fprintf(stderr, "GLFW Error %d: %s\n", error, description);
}

int main(int, char**) {
    // 初始化 GLFW
    glfwSetErrorCallback(glfw_error_callback);
    if (!glfwInit()) return 1;

    // OpenGL 3.0
    const char* glsl_version = "#version 130";
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);

    // 创建窗口
    GLFWwindow* window = glfwCreateWindow(1280, 800, "Maxx IDE", nullptr, nullptr);
    if (window == nullptr) { glfwTerminate(); return 1; }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    // 初始化 ImGui
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO(); (void)io;
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;

    // 深色主题
    ImGui::StyleColorsDark();

    // 毛玻璃风格样式
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding = 12.0f;
    style.FrameRounding = 8.0f;
    style.GrabRounding = 8.0f;
    style.WindowBorderSize = 0.0f;

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init(glsl_version);

    // 初始化模块
    MaxxEditor editor;
    MaxxConsole console;
    MaxxFileTree fileTree;
    MaxxCompilerRunner compiler;

    // 默认示例代码
    editor.setCode(R"(
@ main() -> int:
    io.println("Hello, Maxx!")
    let x = 42
    io.println(str(x))
    ret 0
)");

    // 主循环
    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        // 全屏窗口
        ImGui::SetNextWindowPos(ImVec2(0, 0));
        ImGui::SetNextWindowSize(io.DisplaySize);
        ImGui::Begin("Maxx IDE", nullptr,
            ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize |
            ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoBringToFrontOnFocus);

        // 顶部菜单栏
        if (ImGui::BeginMainMenuBar()) {
            if (ImGui::BeginMenu("文件")) {
                if (ImGui::MenuItem("新建", "Ctrl+N")) {}
                if (ImGui::MenuItem("打开", "Ctrl+O")) {}
                if (ImGui::MenuItem("保存", "Ctrl+S")) {}
                ImGui::EndMenu();
            }
            if (ImGui::BeginMenu("编译")) {
                if (ImGui::MenuItem("运行", "F5")) {
                    std::string output = compiler.run(editor.getCode());
                    console.append(output);
                }
                ImGui::EndMenu();
            }
            if (ImGui::BeginMenu("设置")) {
                ImGui::EndMenu();
            }
            ImGui::EndMainMenuBar();
        }

        // 左侧文件树
        ImGui::BeginChild("FileTree", ImVec2(200, 0), true);
        fileTree.render();
        ImGui::EndChild();

        ImGui::SameLine();

        // 中间代码编辑器
        ImGui::BeginChild("Editor", ImVec2(0, ImGui::GetContentRegionAvail().y * 0.7f), true);
        editor.render();
        ImGui::EndChild();

        // 底部控制台
        ImGui::BeginChild("Console", ImVec2(0, 0), true);
        console.render();
        ImGui::EndChild();

        ImGui::End();

        // 渲染
        ImGui::Render();
        int display_w, display_h;
        glfwGetFramebufferSize(window, &display_w, &display_h);
        glViewport(0, 0, display_w, display_h);
        glClearColor(0.07f, 0.08f, 0.11f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        glfwSwapBuffers(window);
    }

    // 清理
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();

    return 0;
}
