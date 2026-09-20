package com.maxx.app;

import android.app.Activity;
import android.os.Bundle;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;

public class SyntaxRefActivity extends Activity {

    private String[] categories = {
        "基础语法", "关键字", "类型", "控制流", "标准库"
    };

    private String[] contents = {
        // 基础语法
        "=== 基础语法 ===\n\n" +
        "@ 函数定义\n" +
        "  @ main() -> int:\n" +
        "      ret 0\n\n" +
        "# 结构体/类型定义\n" +
        "  # Point:\n" +
        "      x: f64\n" +
        "      y: f64\n\n" +
        "~ 导入模块\n" +
        "  ~ std.io\n" +
        "  ~ std.math::sqrt\n\n" +
        ":: 命名空间访问\n" +
        "  io.println(\"hi\")\n" +
        "  Point::new(3.0, 4.0)\n\n" +
        "=> Lambda\n" +
        "  let add = |a, b| -> a + b\n\n" +
        "// 单行注释\n" +
        "/* 多行注释 */\n",

        // 关键字
        "=== 关键字 ===\n\n" +
        "控制流:\n" +
        "  if / elif / else\n" +
        "  for / in / while\n" +
        "  match / case\n" +
        "  ret / break / continue\n\n" +
        "定义:\n" +
        "  @ (函数)\n" +
        "  # (类型/结构体)\n" +
        "  ~ (导入)\n" +
        "  let (不可变绑定)\n" +
        "  var (可变绑定)\n\n" +
        "类型系统:\n" +
        "  ?T (可选类型)\n" +
        "  Result<T, E> (错误处理)\n" +
        "  Vec<T> (动态数组)\n" +
        "  Map<K, V> (字典)\n" +
        "  fn (函数类型)\n" +
        "  chan (通道)\n\n" +
        "并发:\n" +
        "  task (协程)\n" +
        "  chan (通道)\n\n" +
        "其他:\n" +
        "  true / false\n" +
        "  null (不推荐，用 ?T)\n" +
        "  self (方法接收者)\n",

        // 类型
        "=== 类型系统 ===\n\n" +
        "标量类型:\n" +
        "  int / i64    64位整数\n" +
        "  i32 / i16 / i8  小整数\n" +
        "  u64 / u32    无符号整数\n" +
        "  f64 / f32    浮点数\n" +
        "  bool         布尔值\n" +
        "  str          字符串\n\n" +
        "复合类型:\n" +
        "  ?T           可选类型\n" +
        "  Result<T,E>  结果类型\n" +
        "  Vec<T>       动态数组\n" +
        "  Map<K,V>     字典\n" +
        "  Set<T>       集合\n" +
        "  Tuple(A,B)    元组\n" +
        "  fn(...) -> T 函数类型\n\n" +
        "用户定义:\n" +
        "  # Point:     结构体\n" +
        "  # Shape:     ADT 枚举\n" +
        "      Circle: f64\n" +
        "      Rect: f64, f64\n" +
        "      Dot:\n\n" +
        "类型标注:\n" +
        "  let x: int = 42\n" +
        "  fn add(a: int, b: int) -> int\n" +
        "  var name: str = \"Maxx\"\n",

        // 控制流
        "=== 控制流 ===\n\n" +
        "if / elif / else:\n" +
        "  if x > 0:\n" +
        "      io.println(\"pos\")\n" +
        "  elif x < 0:\n" +
        "      io.println(\"neg\")\n" +
        "  else:\n" +
        "      io.println(\"zero\")\n\n" +
        "for 循环:\n" +
        "  for i in 1..=10:\n" +
        "      io.println(i)\n\n" +
        "  for item in vec:\n" +
        "      io.println(item)\n\n" +
        "while 循环:\n" +
        "  var n = 10\n" +
        "  while n > 0:\n" +
        "      n -= 1\n\n" +
        "match 模式匹配:\n" +
        "  match shape:\n" +
        "      Circle(r) =>\n" +
        "          ret 3.14 * r * r\n" +
        "      Rect(w, h) =>\n" +
        "          ret w * h\n" +
        "      Dot =>\n" +
        "          ret 0.0\n\n" +
        "Range 语法:\n" +
        "  1..10    1到9 (左闭右开)\n" +
        "  1..=10   1到10 (全闭)\n",

        // 标准库
        "=== 标准库速查 ===\n\n" +
        "std.io:\n" +
        "  io.println(s)     打印+换行\n" +
        "  io.print(s)       打印\n" +
        "  read_line()       读一行\n" +
        "  read_file(path)   读文件\n" +
        "  write_file(p, c)  写文件\n\n" +
        "std.math:\n" +
        "  sqrt(x)           平方根\n" +
        "  sin(x) / cos(x)   三角函数\n" +
        "  tan(x)            正切\n" +
        "  log(x) / log10(x) 对数\n" +
        "  exp(x)            e^x\n" +
        "  pow(x, y)         x^y\n" +
        "  floor(x)          向下取整\n" +
        "  ceil(x)           向上取整\n" +
        "  abs(x)            绝对值\n" +
        "  min(a, b) / max(a, b)\n\n" +
        "std.time:\n" +
        "  now()             当前时间戳\n" +
        "  sleep(secs)       休眠\n\n" +
        "std.str:\n" +
        "  str(v)            转字符串\n" +
        "  s.len()           长度\n" +
        "  s.concat(t)      拼接\n" +
        "  s.contains(t)     包含\n" +
        "  s.starts_with(t)  前缀\n" +
        "  s.ends_with(t)    后缀\n" +
        "  s.split(d)        分割\n" +
        "  s.trim()          去空格\n\n" +
        "std.vec:\n" +
        "  Vec::new()        新建\n" +
        "  v.push(x)         末尾添加\n" +
        "  v.pop()           末尾弹出\n" +
        "  v.len()           长度\n" +
        "  v[i]              索引访问\n\n" +
        "std.map:\n" +
        "  Map::new()        新建\n" +
        "  m.insert(k, v)   插入\n" +
        "  m.get(k)          获取 (返回?T)\n" +
        "  m.remove(k)       删除\n" +
        "  m.len()           长度\n"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_syntax_ref);

        Button backButton = findViewById(R.id.back_button);
        ListView categoryList = findViewById(R.id.category_list);
        TextView contentView = findViewById(R.id.content_view);

        backButton.setOnClickListener(v -> finish());

        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
                android.R.layout.simple_list_item_1, categories);
        categoryList.setAdapter(adapter);

        categoryList.setOnItemClickListener((parent, view, position, id) -> {
            contentView.setText(contents[position]);
        });

        // Show first category by default.
        contentView.setText(contents[0]);
    }
}
