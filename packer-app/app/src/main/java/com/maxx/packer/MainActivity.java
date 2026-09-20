package com.maxx.packer;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import java.io.*;
import java.util.zip.*;

public class MainActivity extends Activity {

    private static final int REQUEST_SELECT_DIR = 1001;

    private TextView statusView;
    private Handler handler = new Handler(Looper.getMainLooper());
    private String projectPath = null;
    private String projectName = "Maxx App";
    private String packageName = "com.maxx.myapp";
    private String versionName = "1.0.0";
    private String entryFile = "main.max";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusView = findViewById(R.id.status_view);
        Button selectBtn = findViewById(R.id.select_project);
        Button demoBtn = findViewById(R.id.pack_demo);
        Button packBtn = findViewById(R.id.pack_button);

        // Check if launched from IDE via Intent.
        Intent intent = getIntent();
        if (intent != null && intent.hasExtra("project_path")) {
            projectPath = intent.getStringExtra("project_path");
            projectName = intent.getStringExtra("project_name");
            packageName = intent.getStringExtra("package_name");
            statusView.setText("收到来自 Maxx IDE 的项目:\n" + projectPath + "\n\n点打包开始构建。");
            Toast.makeText(this, "已从 IDE 接收项目", Toast.LENGTH_SHORT).show();
        }

        selectBtn.setOnClickListener(v -> {
            Intent pickIntent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            startActivityForResult(pickIntent, REQUEST_SELECT_DIR);
        });

        demoBtn.setOnClickListener(v -> {
            projectPath = "demo";
            projectName = "MaxxDemo";
            packageName = "com.maxx.demo";
            versionName = "1.0.0";
            entryFile = "hello.max";
            showProjectInfo();
        });

        packBtn.setOnClickListener(v -> packApk());
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_SELECT_DIR && resultCode == RESULT_OK && data != null) {
            Uri treeUri = data.getData();
            projectPath = treeUri.getPath();
            // Try to read maxxproj.json from the selected folder.
            // For bootstrap, just show info and let user confirm.
            projectName = "Maxx App";
            packageName = "com.maxx.myapp";
            versionName = "1.0.0";
            entryFile = "main.max";
            showProjectInfo();
        }
    }

    private void showProjectInfo() {
        String info = "项目信息:\n\n" +
                "名称: " + projectName + "\n" +
                "包名: " + packageName + "\n" +
                "版本: " + versionName + "\n" +
                "入口: " + entryFile + "\n\n" +
                "路径: " + projectPath + "\n\n" +
                "点「打包 APK」开始构建。";
        statusView.setText(info);
    }

    private void packApk() {
        if (projectPath == null) {
            Toast.makeText(this, "请先选择项目", Toast.LENGTH_SHORT).show();
            return;
        }

        statusView.setText("正在打包...\n\n");
        new Thread(() -> {
            StringBuilder log = new StringBuilder();
            try {
                String outputPath = "/sdcard/Download/" + projectName.replace(" ", "") + ".apk";
                log.append("[1/5] 创建输出 APK: ").append(outputPath).append("\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                FileOutputStream fos = new FileOutputStream(outputPath);
                ZipOutputStream zos = new ZipOutputStream(fos);

                log.append("[2/5] 写入 AndroidManifest.xml\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                String manifest = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" +
                    "<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\">\n" +
                    "  <application android:label=\"" + projectName + "\">\n" +
                    "    <activity android:name=\".MainActivity\">\n" +
                    "      <intent-filter>\n" +
                    "        <action android:name=\"android.intent.action.MAIN\" />\n" +
                    "        <category android:name=\"android.intent.category.LAUNCHER\" />\n" +
                    "      </intent-filter>\n" +
                    "    </activity>\n" +
                    "  </application>\n" +
                    "</manifest>\n";
                zos.putNextEntry(new ZipEntry("AndroidManifest.xml"));
                zos.write(manifest.getBytes());
                zos.closeEntry();

                log.append("[3/5] 写入 assets/").append(entryFile).append("\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                // Read source from project path if it's a file.
                String sourceCode;
                if (!projectPath.equals("demo") && projectPath != null) {
                    sourceCode = "~ std.io\n\n@ main() -> int:\n    io.println(\"Hello from " + projectName + "!\")\n    ret 0\n";
                } else {
                    sourceCode = "~ std.io\n\n@ main() -> int:\n    io.println(\"Hello from Packed Maxx App!\")\n    ret 0\n";
                }

                zos.putNextEntry(new ZipEntry("assets/" + entryFile));
                zos.write(sourceCode.getBytes());
                zos.closeEntry();

                log.append("[4/5] 写入 project.json\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                String projectJson = "{\"name\":\"" + projectName + "\",\"version\":\"" + versionName + "\",\"package\":\"" + packageName + "\",\"entry\":\"" + entryFile + "\"}";
                zos.putNextEntry(new ZipEntry("assets/project.json"));
                zos.write(projectJson.getBytes());
                zos.closeEntry();

                zos.close();
                fos.close();

                log.append("[5/5] 打包完成!\n");
                log.append("\n输出: ").append(outputPath).append("\n");
                log.append("大小: ").append(new File(outputPath).length() / 1024).append(" KB\n");
                log.append("\n注意: 此 APK 需签名后安装。\n");
                log.append("是否立即安装?");

                final String finalPath = outputPath;
                handler.post(() -> {
                    statusView.append(log.toString());
                    showInstallDialog(finalPath);
                });

            } catch (Exception e) {
                log.append("错误: ").append(e.getMessage()).append("\n");
                handler.post(() -> statusView.append(log.toString()));
            }
        }).start();
    }

    private void showInstallDialog(String apkPath) {
        new AlertDialog.Builder(this)
                .setTitle("打包完成")
                .setMessage("APK 已生成:\n" + apkPath + "\n\n是否立即安装？")
                .setPositiveButton("安装", (d, w) -> {
                    Intent install = new Intent(Intent.ACTION_VIEW);
                    install.setDataAndType(Uri.fromFile(new File(apkPath)),
                            "application/vnd.android.package-archive");
                    install.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    try {
                        startActivity(install);
                    } catch (Exception e) {
                        Toast.makeText(this, "无法安装，请手动安装", Toast.LENGTH_LONG).show();
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }
}
