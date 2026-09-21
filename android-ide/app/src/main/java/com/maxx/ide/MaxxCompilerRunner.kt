package com.maxx.ide

import android.content.Context
import android.util.Log
import java.io.*

/**
 * Maxx 编译器运行器
 * 
 * 负责执行 Maxx 编译器二进制，捕获 stdout/stderr 输出。
 * 引导阶段使用内嵌的简单解释器，后续可替换为真实编译器。
 */
class MaxxCompilerRunner(private val context: Context) {
    
    companion object {
        private const val TAG = "MaxxCompilerRunner"
        private const val COMPILER_ASSET = "maxxc"
    }
    
    /**
     * 编译并运行 Maxx 代码
     * @param code Maxx 源代码字符串
     * @return 运行结果（stdout + stderr）
     */
    fun run(code: String): String {
        return try {
            // 写入临时文件
            val tempFile = File(context.cacheDir, "temp.max")
            tempFile.writeText(code)
            
            // 彩蛋检测：hi！Maxx
            if (code.contains("hi！Maxx")) {
                return "Maxx: simple by design, efficient by choice, transparent by default."
            }
            
            // 引导阶段：简单解释器模式
            // 识别 io.println("...") 并输出
            val output = StringBuilder()
            val lines = code.lines()
            
            for (line in lines) {
                val trimmed = line.trim()
                
                // 匹配 io.println("...")
                val printlnMatch = Regex("""io\.println\("(.*)"\)""").find(trimmed)
                if (printlnMatch != null) {
                    output.appendLine(printlnMatch.groupValues[1])
                    continue
                }
                
                // 匹配 io.println(variable)
                val varMatch = Regex("""io\.println\((\w+)\)""").find(trimmed)
                if (varMatch != null) {
                    val varName = varMatch.groupValues[1]
                    output.appendLine("[variable: $varName]")
                    continue
                }
            }
            
            // 如果没有识别到任何输出，提示成功
            if (output.isEmpty()) {
                output.appendLine("[编译成功，无输出]")
            }
            
            output.toString()
        } catch (e: Exception) {
            Log.e(TAG, "运行失败", e)
            "错误: ${e.message}"
        }
    }
    
    /**
     * 从 assets 复制编译器到私有目录
     */
    fun extractCompiler(): File {
        val outFile = File(context.filesDir, COMPILER_ASSET)
        if (!outFile.exists()) {
            context.assets.open(COMPILER_ASSET).use { input ->
                FileOutputStream(outFile).use { output ->
                    input.copyTo(output)
                }
            }
            outFile.setExecutable(true)
        }
        return outFile
    }
}
