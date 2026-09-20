package com.maxx.app;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.Button;
import android.widget.ScrollView;
import android.widget.TextView;

public class ResultActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        setContentView(R.layout.activity_result);

        String output = getIntent().getStringExtra("output");
        if (output == null) output = "(no output)";

        TextView outputView = findViewById(R.id.output_view);
        Button backButton = findViewById(R.id.back_button);

        outputView.setText(output + "\n\n[Process completed - press Enter]");
        backButton.setOnClickListener(v -> finish());
    }
}
