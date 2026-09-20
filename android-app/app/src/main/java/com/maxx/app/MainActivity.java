package com.maxx.app;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import java.io.InputStream;

public class MainActivity extends Activity {

    static {
        System.loadLibrary("maxx_jni");
    }

    public native String runMaxx(String code);

    private EditText codeEditor;
    private TextView outputView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        codeEditor = findViewById(R.id.code_editor);
        outputView = findViewById(R.id.output_view);
        Button runButton = findViewById(R.id.run_button);

        // Load default hello.max from assets.
        try {
            InputStream is = getAssets().open("hello.max");
            byte[] buf = new byte[is.available()];
            is.read(buf);
            is.close();
            codeEditor.setText(new String(buf));
        } catch (Exception e) {
            codeEditor.setText("// error loading hello.max");
        }

        runButton.setOnClickListener(v -> {
            String code = codeEditor.getText().toString();
            String result = runMaxx(code);
            outputView.setText(result);
        });
    }
}
