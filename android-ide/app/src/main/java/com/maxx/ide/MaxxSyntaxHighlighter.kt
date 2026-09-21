package com.maxx.ide

import android.graphics.Color
import android.text.Editable
import android.text.Spannable
import android.text.TextWatcher
import android.text.style.ForegroundColorSpan
import android.widget.EditText

/**
 * Maxx 语法高亮工具
 * 
 * 支持 Maxx 关键字、类型、字符串、注释、数字的语法高亮。
 * 护眼低饱和配色。
 */
class MaxxSyntaxHighlighter(private val editText: EditText) : TextWatcher {
    
    // 配色方案（护眼低饱和）
    private val colorKeyword = Color.parseColor("#2b6cb0")    // 关键字：深蓝
    private val colorType = Color.parseColor("#0d9488")      // 类型：青色
    private val colorString = Color.parseColor("#c53030")   // 字符串：红
    private val colorComment = Color.parseColor("#718096")  // 注释：灰
    private val colorNumber = Color.parseColor("#2f855a")   // 数字：绿
    private val colorFunction = Color.parseColor("#805ad5") // 函数：紫
    private val colorPunct = Color.parseColor("#d97706")    // 标点：橙
    
    // Maxx 关键字
    private val keywords = setOf(
        "if", "elif", "else", "for", "while", "loop", "match", "ret",
        "let", "var", "task", "chan", "true", "false", "none", "some",
        "ok", "err", "try", "break", "continue", "fn", "trait", "impl",
        "is", "as", "in", "of"
    )
    
    // Maxx 类型
    private val types = setOf(
        "int", "i64", "i32", "i16", "i8",
        "u64", "u32", "u16", "u8",
        "f64", "f32",
        "bool", "str", "char",
        "Vec", "Map", "Set", "Option", "Result"
    )
    
    override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
    
    override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
    
    override fun afterTextChanged(s: Editable?) {
        s ?: return
        highlight(s)
    }
    
    /**
     * 执行语法高亮
     */
    private fun highlight(text: Editable) {
        // 清除之前的样式
        text.getSpans(0, text.length, ForegroundColorSpan::class.java).forEach {
            text.removeSpan(it)
        }
        
        val content = text.toString()
        val lines = content.lines()
        var offset = 0
        
        for (line in lines) {
            highlightLine(text, line, offset)
            offset += line.length + 1 // +1 for newline
        }
    }
    
    /**
     * 高亮单行
     */
    private fun highlightLine(text: Editable, line: String, offset: Int) {
        // 注释高亮
        val commentIndex = line.indexOf("//")
        if (commentIndex >= 0) {
            text.setSpan(
                ForegroundColorSpan(colorComment),
                offset + commentIndex,
                offset + line.length,
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            return
        }
        
        // 简单分词高亮
        val tokens = Regex("""(\w+|"[^"]*"|\d+\.?\d*|[^\w\s])""").findAll(line)
        for (token in tokens) {
            val value = token.value
            val start = offset + token.range.first
            val end = offset + token.range.last + 1
            
            when {
                // 字符串
                value.startsWith("\"") -> {
                    text.setSpan(ForegroundColorSpan(colorString), start, end, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
                // 数字
                value.matches(Regex("""\d+\.?\d*""")) -> {
                    text.setSpan(ForegroundColorSpan(colorNumber), start, end, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
                // 关键字
                keywords.contains(value) -> {
                    text.setSpan(ForegroundColorSpan(colorKeyword), start, end, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
                // 类型
                types.contains(value) -> {
                    text.setSpan(ForegroundColorSpan(colorType), start, end, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
                // 标点符号
                value.matches(Regex("""[{}()\[\];,.:]+""")) -> {
                    text.setSpan(ForegroundColorSpan(colorPunct), start, end, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
            }
        }
    }
}
