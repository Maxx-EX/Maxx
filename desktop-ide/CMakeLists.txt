cmake_minimum_required(VERSION 3.14)
project(MaxxIDE LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ImGui + GLFW + OpenGL
find_package(glfw3 REQUIRED)
find_package(OpenGL REQUIRED)

# ImGui sources
set(IMGUI_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/imgui)

add_executable(maxx-ide
    src/main.cpp
    src/editor.cpp
    src/console.cpp
    src/file_tree.cpp
    src/compiler_runner.cpp
    ${IMGUI_DIR}/imgui.cpp
    ${IMGUI_DIR}/imgui_draw.cpp
    ${IMGUI_DIR}/imgui_tables.cpp
    ${IMGUI_DIR}/imgui_widgets.cpp
    ${IMGUI_DIR}/backends/imgui_impl_glfw.cpp
    ${IMGUI_DIR}/backends/imgui_impl_opengl3.cpp
)

target_include_directories(maxx-ide PRIVATE
    src
    ${IMGUI_DIR}
    ${IMGUI_DIR}/backends
)

target_link_libraries(maxx-ide PRIVATE
    glfw
    OpenGL::GL
)

# 深色主题默认
target_compile_definitions(maxx-ide PRIVATE
    IMGUI_IMPL_OPENGL_LOADER_GLAD
)
