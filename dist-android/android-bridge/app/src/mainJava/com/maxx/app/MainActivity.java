package com.maxx.app;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends AppCompatActivity {

    static {
        // 加载 Maxx 运行时 .so
        System.loadLibrary("maxx_runtime");
    }

    public native String maxxVersion();
    public native String maxxRun(String code);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        TextView tv = new TextView(this);
        tv.setTextSize(16f);

        String version = maxxVersion();
        String result = maxxRun("~ std.io\n@ main(): io.println(\"hello from maxx on android\")");

        tv.setText(version + "\n\n" + result);
        setContentView(tv);
    }
}
