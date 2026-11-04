package com.roborabbit.assistant;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.ServiceInfo;
import android.net.Uri;
import android.os.BatteryManager;
import android.os.Build;
import android.os.IBinder;
import android.os.Vibrator;
import android.os.VibrationEffect;
import android.speech.tts.TextToSpeech;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;

public class RoborabbitService extends Service {
    private static final String TAG = "RoborabbitService";
    private static final String CHANNEL_ID = "roborabbit_service_channel";
    private static final String SERVER_URL = "https://ssh.scempyy.me";
    private static final String FALLBACK_URL = "http://192.168.1.22:7777";

    private boolean isRunning = false;
    private Thread workerThread;
    private TextToSpeech tts;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        Notification notification = buildForegroundNotification();
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                startForeground(1001, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE);
            } else {
                startForeground(1001, notification);
            }
        } catch (Throwable e) {
            try {
                startForeground(1001, notification);
            } catch (Throwable ignored) {}
        }

        // Initialize Android TextToSpeech
        try {
            tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
                @Override
                public void onInit(int status) {
                    if (status == TextToSpeech.SUCCESS && tts != null) {
                        tts.setLanguage(Locale.US);
                    }
                }
            });
        } catch (Exception ignored) {}
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!isRunning) {
            isRunning = true;
            startPollingLoop();
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        isRunning = false;
        if (workerThread != null) {
            workerThread.interrupt();
        }
        if (tts != null) {
            try { tts.shutdown(); } catch (Exception ignored) {}
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void startPollingLoop() {
        workerThread = new Thread(new Runnable() {
            @Override
            public void run() {
                int loopCount = 0;
                while (isRunning) {
                    try {
                        // 1. Poll Server for commands
                        pollServerCommands();

                        // 2. Report Battery every 30 seconds
                        if (loopCount % 15 == 0) {
                            reportBatteryTelemetry();
                        }

                        loopCount++;
                        Thread.sleep(2000);
                    } catch (InterruptedException e) {
                        break;
                    } catch (Exception e) {
                        Log.w(TAG, "Polling loop warning: " + e.getMessage());
                        try { Thread.sleep(3000); } catch (InterruptedException ignored) { break; }
                    }
                }
            }
        });
        workerThread.start();
    }

    private void pollServerCommands() {
        HttpURLConnection conn = null;
        String[] bases = {SERVER_URL, FALLBACK_URL};
        for (String base : bases) {
            try {
                URL url = new URL(base + "/api/phone/poll");
                conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(2500);
                conn.setReadTimeout(2500);

                if (conn.getResponseCode() == 200) {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        sb.append(line);
                    }
                    reader.close();

                    JSONObject res = new JSONObject(sb.toString());
                    if (res.has("commands")) {
                        JSONArray cmds = res.getJSONArray("commands");
                        for (int i = 0; i < cmds.length(); i++) {
                            JSONObject c = cmds.getJSONObject(i);
                            executeCommand(c);
                        }
                    }
                    return;
                }
            } catch (Exception ignored) {
            } finally {
                if (conn != null) { conn.disconnect(); conn = null; }
            }
        }
    }

    private void executeCommand(JSONObject cmd) {
        try {
            String action = cmd.optString("action", "").toLowerCase();
            if ("open_url".equals(action)) {
                String targetUrl = cmd.optString("url", "https://google.com");
                Intent viewIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(targetUrl));
                viewIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(viewIntent);
            } else if ("open_app".equals(action) || "launch_app".equals(action)) {
                String appName = cmd.optString("app", "").toLowerCase();
                String targetPkg = cmd.optString("package", "");
                if (targetPkg.isEmpty()) {
                    if (appName.contains("whatsapp")) targetPkg = "com.whatsapp";
                    else if (appName.contains("insta")) targetPkg = "com.instagram.android";
                    else if (appName.contains("youtube")) targetPkg = "com.google.android.youtube";
                    else if (appName.contains("spotify")) targetPkg = "com.spotify.music";
                    else if (appName.contains("gmail") || appName.contains("mail")) targetPkg = "com.google.android.gm";
                    else if (appName.contains("telegram")) targetPkg = "org.telegram.messenger";
                    else if (appName.contains("map")) targetPkg = "com.google.android.apps.maps";
                    else if (appName.contains("camera")) {
                        Intent cam = new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
                        cam.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(cam);
                        return;
                    }
                }
                if (!targetPkg.isEmpty()) {
                    Intent launchIntent = getPackageManager().getLaunchIntentForPackage(targetPkg);
                    if (launchIntent != null) {
                        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(launchIntent);
                        return;
                    }
                }
                String fallbackUrl = cmd.optString("url", "https://google.com");
                Intent viewIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(fallbackUrl));
                viewIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(viewIntent);
            } else if ("speak".equals(action)) {
                String text = cmd.optString("text", "All systems operational.");
                if (tts != null) {
                    tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "robo_tts");
                }
            } else if ("vibrate".equals(action)) {
                Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
                if (v != null) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        v.vibrate(VibrationEffect.createOneShot(800, VibrationEffect.DEFAULT_AMPLITUDE));
                    } else {
                        v.vibrate(800);
                    }
                }
            } else if ("locate".equals(action) || "ring".equals(action)) {
                Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
                if (v != null) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        v.vibrate(VibrationEffect.createWaveform(new long[]{0, 400, 200, 400, 200, 800}, -1));
                    } else {
                        v.vibrate(1500);
                    }
                }
                if (tts != null) {
                    tts.speak("RoboRabbit device location beacon active. Phone online, sir.", TextToSpeech.QUEUE_FLUSH, null, "robo_beacon");
                }
            } else if ("dial".equals(action) || "call".equals(action)) {
                String phone = cmd.optString("phone", cmd.optString("number", ""));
                Intent dialIntent = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + phone));
                dialIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(dialIntent);
            } else if ("sms".equals(action)) {
                String phone = cmd.optString("phone", cmd.optString("number", ""));
                String body = cmd.optString("message", cmd.optString("body", ""));
                Intent smsIntent = new Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:" + phone));
                smsIntent.putExtra("sms_body", body);
                smsIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(smsIntent);
            } else if ("clipboard".equals(action) || "copy".equals(action)) {
                String text = cmd.optString("text", "");
                android.content.ClipboardManager cm = (android.content.ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                if (cm != null) {
                    android.content.ClipData clip = android.content.ClipData.newPlainText("Roborabbit Clip", text);
                    cm.setPrimaryClip(clip);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Execute command error: " + e.getMessage());
        }
    }

    private void reportBatteryTelemetry() {
        HttpURLConnection conn = null;
        try {
            IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
            Intent b = registerReceiver(null, ifilter);
            int level = -1;
            boolean charging = false;
            if (b != null) {
                level = b.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                int status = b.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
                charging = (status == BatteryManager.BATTERY_STATUS_CHARGING ||
                            status == BatteryManager.BATTERY_STATUS_FULL);
            }

            JSONObject json = new JSONObject();
            json.put("battery", level + "%" + (charging ? " (Charging)" : ""));
            json.put("model", Build.MODEL);

            byte[] bytes = json.toString().getBytes("UTF-8");

            String[] bases = {SERVER_URL, FALLBACK_URL};
            for (String base : bases) {
                try {
                    URL url = new URL(base + "/api/phone/telemetry");
                    conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setDoOutput(true);
                    conn.setConnectTimeout(2500);
                    conn.setReadTimeout(2500);

                    OutputStream os = conn.getOutputStream();
                    os.write(bytes);
                    os.flush();
                    os.close();
                    if (conn.getResponseCode() == 200) {
                        return;
                    }
                } catch (Exception ignored) {
                } finally {
                    if (conn != null) { conn.disconnect(); conn = null; }
                }
            }
        } catch (Exception ignored) {
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "Roborabbit Background Agent",
                    NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Maintains continuous neural link with Laptop 2 Server");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    private Notification buildForegroundNotification() {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this, 0, notificationIntent,
                Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0
        );

        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }

        builder.setContentTitle("Roborabbit Cyber Command")
                .setContentText("Persistent link active // Wireless Debugging NOT required")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pendingIntent)
                .setOngoing(true);

        return builder.build();
    }
}
