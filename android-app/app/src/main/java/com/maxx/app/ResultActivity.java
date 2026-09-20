package com.maxx.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class ResultActivity extends Activity {

    private TextView outputView;
    private String output;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        setContentView(R.layout.activity_result);

        output = getIntent().getStringExtra("output");
        if (output == null) output = "(no output)";

        outputView = findViewById(R.id.output_view);
        Button backButton = findViewById(R.id.back_button);

        outputView.setText(output + "\n\n[Process completed - tap to go back]");

        // Tap output to go back.
        outputView.setOnClickListener(v -> finish());

        backButton.setOnClickListener(v -> finish());

        // Check if program requested input (contains "INPUT_REQUEST:").
        if (output.contains("INPUT_REQUEST:")) {
            showInputDialog();
        }
    }

    private void showInputDialog() {
        // Extract prompt from output.
        String prompt = "Enter input:";
        int idx = output.indexOf("INPUT_REQUEST:");
        if (idx >= 0) {
            int end = output.indexOf("\n", idx);
            if (end < 0) end = output.length();
            prompt = output.substring(idx + 14, end).trim();
        }

        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setHint(prompt);

        new AlertDialog.Builder(this)
                .setTitle("Program needs input")
                .setView(input)
                .setPositiveButton("Send", (d, w) -> {
                    String userInput = input.getText().toString();
                    // Send input back to main activity (simplified: show toast).
                    Toast.makeText(this, "Input: " + userInput, Toast.LENGTH_LONG).show();
                    outputView.append("\n> " + userInput + "\n");
                })
                .setNegativeButton("Cancel", null)
                .show();
    }
}
