cmake_minimum_required(VERSION 3.22.1)
project(maxx_jni)

add_library(maxx_jni SHARED
    maxx_jni.cpp
)

find_library(log-lib log)

target_link_libraries(maxx_jni
    ${log-lib}
)
