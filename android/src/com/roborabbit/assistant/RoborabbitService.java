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
        try {
            URL url = new URL(SERVER_URL + "/api/phone/poll");
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
            }
        } catch (Exception ignored) {
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    private void executeCommand(JSONObject cmd) {
        try {
            String action = cmd.optString("action", "");
            if ("open_url".equalsIgnoreCase(action) || "open_app".equalsIgnoreCase(action)) {
                String targetUrl = cmd.optString("url", "https://www.youtube.com");
                Intent viewIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(targetUrl));
                viewIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(viewIntent);
            } else if ("speak".equalsIgnoreCase(action)) {
                String text = cmd.optString("text", "All systems operational.");
                if (tts != null) {
                    tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "robo_tts");
                }
            } else if ("vibrate".equalsIgnoreCase(action)) {
                Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
                if (v != null) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        v.vibrate(VibrationEffect.createOneShot(500, VibrationEffect.DEFAULT_AMPLITUDE));
                    } else {
                        v.vibrate(500);
                    }
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

            URL url = new URL(SERVER_URL + "/api/phone/telemetry");
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
            conn.getResponseCode();
        } catch (Exception ignored) {
        } finally {
            if (conn != null) conn.disconnect();
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
