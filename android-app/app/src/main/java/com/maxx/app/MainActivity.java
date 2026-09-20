package com.maxx.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.text.style.ForegroundColorSpan;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class MainActivity extends Activity {

    static {
        System.loadLibrary("maxx_jni");
    }

    public native String runMaxx(String code);

    private EditText codeEditor;
    private TextView lineNumbers;
    private TextView saveStatus;
    private Button runButton, menuButton;
    private Handler saveHandler = new Handler(Looper.getMainLooper());
    private Runnable saveRunnable;

    private static final String[] CONTROL = {"if", "elif", "else", "for", "while", "match", "ret", "let", "var", "task", "chan"};

    private static final String[][] EXAMPLES = {
        {"HelloWorld", "~ std.io\n\n@ main() -> int:\n    io.println(\"Hello from Maxx!\")\n    ret 0\n"},
        {"Fibonacci", "~ std.io\n\n@ fib(n: int) -> int:\n    if n <= 1:\n        ret n\n    ret fib(n - 1) + fib(n - 2)\n\n@ main() -> int:\n    io.println(\"fib(10) = \" + str(fib(10)))\n    ret 0\n"},
        {"Struct", "~ std.io\n\n# Point:\n    x: f64\n    y: f64\n\n@ Point::dist(self: Point) -> f64:\n    ret sqrt(self.x * self.x + self.y * self.y)\n\n@ main() -> int:\n    var p = Point{x: 3.0, y: 4.0}\n    io.println(\"dist = \" + str(p.dist()))\n    ret 0\n"},
        {"Collections", "~ std.io\n\n@ main() -> int:\n    var total = 0\n    for i in 1..=100:\n        total += i\n    io.println(\"sum(1..100) = \" + str(total))\n    ret 0\n"},
        {"Math", "~ std.io\n\n@ main() -> int:\n    io.println(\"sqrt(16) = \" + str(sqrt(16.0)))\n    io.println(\"2^10 = \" + str(pow(2.0, 10.0)))\n    io.println(\"floor(3.7) = \" + str(floor(3.7)))\n    ret 0\n"}
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
        setContentView(R.layout.activity_main);

        codeEditor = findViewById(R.id.code_editor);
        lineNumbers = findViewById(R.id.line_numbers);
        saveStatus = findViewById(R.id.save_status);
        runButton = findViewById(R.id.run_button);
        menuButton = findViewById(R.id.menu_button);

        loadCode();

        codeEditor.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            public void onTextChanged(CharSequence s, int a, int b, int c) {}
            public void afterTextChanged(Editable s) {
                updateLineNumbers();
                scheduleAutoSave();
                applySyntaxHighlight(s);
            }
        });

        runButton.setOnClickListener(v -> runCode());
        menuButton.setOnClickListener(v -> showMenu());

        setupToolbar();
    }

    private void loadCode() {
        File f = new File(getFilesDir(), "current.max");
        if (f.exists()) {
            try {
                FileInputStream fis = new FileInputStream(f);
                byte[] buf = new byte[(int) f.length()];
                fis.read(buf);
                fis.close();
                codeEditor.setText(new String(buf));
            } catch (Exception e) { loadDefaultCode(); }
        } else {
            loadDefaultCode();
        }
    }

    private void loadDefaultCode() {
        try {
            InputStream is = getAssets().open("hello.max");
            byte[] buf = new byte[is.available()];
            is.read(buf);
            is.close();
            codeEditor.setText(new String(buf));
        } catch (Exception e) {
            codeEditor.setText("// Hello Maxx!\n@ main() -> int:\n    io.println(\"Hi\")\n    ret 0\n");
        }
    }

    private void updateLineNumbers() {
        String text = codeEditor.getText().toString();
        int lines = text.isEmpty() ? 1 : text.split("\n").length;
        StringBuilder sb = new StringBuilder();
        for (int i = 1; i <= lines; i++) sb.append(i).append("\n");
        lineNumbers.setText(sb.toString());
    }

    private void scheduleAutoSave() {
        saveStatus.setText("修改中...");
        if (saveRunnable != null) saveHandler.removeCallbacks(saveRunnable);
        saveRunnable = () -> {
            try {
                FileOutputStream fos = new FileOutputStream(new File(getFilesDir(), "current.max"));
                fos.write(codeEditor.getText().toString().getBytes());
                fos.close();
                String time = new SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(new Date());
                saveStatus.setText("自动保存于 " + time);
            } catch (Exception e) { saveStatus.setText("保存失败"); }
        };
        saveHandler.postDelayed(saveRunnable, 3000);
    }

    private void applySyntaxHighlight(Editable s) {
        String text = s.toString();
        highlightPattern(s, text, "\"[^\"]*\"", 0xFF6A9955);
        highlightPattern(s, text, "//[^\n]*", 0xFF808080);
        for (String kw : CONTROL) highlightWord(s, text, kw, 0xFF569CD6);
        highlightPattern(s, text, "\\b[0-9]+\\.?[0-9]*\\b", 0xFFB5CEA8);
    }

    private void highlightPattern(Editable s, String text, String regex, int color) {
        java.util.regex.Pattern p = java.util.regex.Pattern.compile(regex);
        java.util.regex.Matcher m = p.matcher(text);
        while (m.find()) {
            s.setSpan(new ForegroundColorSpan(color), m.start(), m.end(),
                    android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
    }

    private void highlightWord(Editable s, String text, String word, int color) {
        java.util.regex.Pattern p = java.util.regex.Pattern.compile("\\b" + word + "\\b");
        java.util.regex.Matcher m = p.matcher(text);
        while (m.find()) {
            s.setSpan(new ForegroundColorSpan(color), m.start(), m.end(),
                    android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
    }

    private void runCode() {
        String code = codeEditor.getText().toString();
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setView(R.layout.dialog_compiling)
                .setCancelable(false)
                .create();
        dialog.show();

        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            dialog.dismiss();
            String result = runMaxx(code);
            try {
                FileOutputStream fos = new FileOutputStream(new File(getFilesDir(), "history.log"), true);
                fos.write(("=== " + new Date() + " ===\n" + result + "\n\n").getBytes());
                fos.close();
            } catch (Exception e) {}
            Intent intent = new Intent(this, ResultActivity.class);
            intent.putExtra("output", result);
            startActivity(intent);
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
        }, 1500);
    }

    private void showMenu() {
        String[] items = {"缩进", "打开", "另存为", "清空", "HelloWorld 示例", "示例库", "运行历史", "语法参考", "打包为 APK", "关于"};
        new AlertDialog.Builder(this)
                .setTitle("菜单")
                .setItems(items, (d, w) -> {
                    switch (w) {
                        case 0: codeEditor.getText().insert(codeEditor.getSelectionStart(), "    "); break;
                        case 1: Toast.makeText(this, "打开文件 (SAF)", Toast.LENGTH_SHORT).show(); break;
                        case 2: Toast.makeText(this, "另存为 (SAF)", Toast.LENGTH_SHORT).show(); break;
                        case 3: codeEditor.setText(""); break;
                        case 4: loadExample(0); break;
                        case 5: showExamples(); break;
                        case 6: showHistory(); break;
                        case 7: startActivity(new Intent(this, SyntaxRefActivity.class)); break;
                        case 8: packAsApk(); break;
                        case 9: showAbout(); break;
                    }
                })
                .show();
    }

    private void packAsApk() {
        // Save current code first.
        try {
            FileOutputStream fos = new FileOutputStream(new File(getFilesDir(), "current.max"));
            fos.write(codeEditor.getText().toString().getBytes());
            fos.close();
        } catch (Exception e) {}

        String projectPath = new File(getFilesDir(), "current.max").getAbsolutePath();
        try {
            Intent intent = new Intent();
            intent.setClassName("com.maxx.packer", "com.maxx.packer.MainActivity");
            intent.putExtra("project_path", projectPath);
            intent.putExtra("project_name", "MaxxApp");
            intent.putExtra("package_name", "com.maxx.myapp");
            startActivity(intent);
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "请先安装 Maxx Packer", Toast.LENGTH_LONG).show();
        }
    }

    private void showHistory() {
        try {
            File f = new File(getFilesDir(), "history.log");
            if (!f.exists()) {
                Toast.makeText(this, "暂无运行历史", Toast.LENGTH_SHORT).show();
                return;
            }
            FileInputStream fis = new FileInputStream(f);
            byte[] buf = new byte[(int) f.length()];
            fis.read(buf);
            fis.close();
            String content = new String(buf);
            // Show last 2000 chars.
            if (content.length() > 2000) content = content.substring(content.length() - 2000);
            new AlertDialog.Builder(this)
                    .setTitle("运行历史")
                    .setMessage(content)
                    .setPositiveButton("OK", null)
                    .show();
        } catch (Exception e) {
            Toast.makeText(this, "读取历史失败", Toast.LENGTH_SHORT).show();
        }
    }

    private void showExamples() {
        String[] names = new String[EXAMPLES.length];
        for (int i = 0; i < EXAMPLES.length; i++) names[i] = EXAMPLES[i][0];
        new AlertDialog.Builder(this)
                .setTitle("示例库")
                .setItems(names, (d, w) -> loadExample(w))
                .show();
    }

    private void loadExample(int idx) {
        codeEditor.setText(EXAMPLES[idx][1]);
        Toast.makeText(this, "已加载: " + EXAMPLES[idx][0], Toast.LENGTH_SHORT).show();
    }

    private void showAbout() {
        new AlertDialog.Builder(this)
                .setTitle("关于 Maxx")
                .setMessage("Maxx 编译器 v1.0\n\n简单 · 高效 · 原创\n\nLevel 1 引导版本\n支持: 结构体 / ADT / match / Result\n跨平台: Android / Linux / macOS / Windows")
                .setPositiveButton("OK", null)
                .show();
    }

    private void setupToolbar() {
        String[] row1 = {"Tab", "{", "}", "\"", "\"", ";", "(", ")", "[", "]"};
        String[] row2 = {"=", "\\", "&", ",", "=>", "::", "ret", "let", "if", "for"};
        LinearLayout r1 = findViewById(R.id.toolbar_row1);
        LinearLayout r2 = findViewById(R.id.toolbar_row2);
        for (String s : row1) addToolbarButton(r1, s);
        for (String s : row2) addToolbarButton(r2, s);
    }

    private void addToolbarButton(LinearLayout parent, String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextSize(11);
        b.setTextColor(Color.WHITE);
        b.setBackgroundResource(R.drawable.bg_tool_btn);
        b.setPadding(24, 0, 24, 0);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.MATCH_PARENT);
        lp.setMargins(4, 4, 4, 4);
        b.setLayoutParams(lp);
        b.setOnClickListener(v -> {
            String insert = label.equals("Tab") ? "    " : label;
            codeEditor.getText().insert(codeEditor.getSelectionStart(), insert);
            codeEditor.requestFocus();
        });
        parent.addView(b);
    }
}
