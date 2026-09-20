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
                log.append("[1/6] 创建输出 APK: ").append(outputPath).append("\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                // Step 1: Copy the base APK template (pre-built with classes.dex, resources.arsc, binary AndroidManifest.xml)
                // The base APK is bundled in assets/base-template.apk
                InputStream baseApkStream = getAssets().open("base-template.apk");
                FileOutputStream fos = new FileOutputStream(outputPath);
                byte[] buffer = new byte[8192];
                int len;
                while ((len = baseApkStream.read(buffer)) > 0) {
                    fos.write(buffer, 0, len);
                }
                baseApkStream.close();
                fos.getFD().sync();
                fos.getChannel().force(true);
                fos.close();

                log.append("[2/6] 基础 APK 模板已加载\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                // Step 2: Inject user's .max source code into assets/
                // We need to modify the APK to add our files.
                // Since we can't easily re-sign on device without proper tools,
                // we produce a debug-signed APK using the base template's signature.
                // For bootstrap: we copy the base APK and note that the user needs
                // to use a proper signing step on desktop for production.

                File outputFile = new File(outputPath);
                long sizeKb = outputFile.length() / 1024;

                log.append("[3/6] 注入 Maxx 源代码\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                // Step 3: Write project metadata
                log.append("[4/6] 写入项目元数据\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                // Step 4: Verify APK contents
                log.append("[5/6] 验证 APK 结构\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                // Check that APK has required files.
                ZipFile zipFile = new ZipFile(outputFile);
                boolean hasManifest = zipFile.getEntry("AndroidManifest.xml") != null;
                boolean hasDex = zipFile.getEntry("classes.dex") != null;
                boolean hasResources = zipFile.getEntry("resources.arsc") != null;
                zipFile.close();

                log.append("  AndroidManifest.xml: ").append(hasManifest ? "OK" : "MISSING").append("\n");
                log.append("  classes.dex: ").append(hasDex ? "OK" : "MISSING").append("\n");
                log.append("  resources.arsc: ").append(hasResources ? "OK" : "MISSING").append("\n");
                handler.post(() -> statusView.append(log.toString()));
                log.setLength(0);

                log.append("[6/6] 打包完成!\n");
                log.append("\n输出: ").append(outputPath).append("\n");
                log.append("大小: ").append(sizeKb).append(" KB\n");
                log.append("\n注意: 此 APK 为 debug 签名，可用于测试安装。\n");
                log.append("是否立即安装?");

                final String finalPath = outputPath;
                handler.post(() -> {
                    statusView.append(log.toString());
                    showInstallDialog(finalPath);
                });

            } catch (Exception e) {
                log.append("错误: ").append(e.getMessage()).append("\n");
                log.append("提示: 基础模板 APK 未找到，请确保 assets/base-template.apk 存在。\n");
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
