package com.roborabbit.assistant;

import android.app.Notification;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.util.Log;

import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class RoborabbitNotificationListener extends NotificationListenerService {
    private static final String TAG = "RoborabbitNotif";
    private static final String SERVER_URL = "https://ssh.scempyy.me/api/notifications/phone/push";
    private static final String LOCAL_URL = "http://192.168.1.22:7777/api/notifications/phone/push";

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null) return;
        Notification notif = sbn.getNotification();
        if (notif == null) return;

        // Skip persistent / ongoing service notifications
        if ((notif.flags & Notification.FLAG_ONGOING_EVENT) != 0) return;

        final String pkg = sbn.getPackageName() != null ? sbn.getPackageName() : "unknown";
        // Ignore self or system noise
        if (pkg.contains("roborabbit") || pkg.equals("android")) return;

        Bundle extras = notif.extras;
        String rawTitle = "";
        String rawText = "";

        if (extras != null) {
            CharSequence t = extras.getCharSequence(Notification.EXTRA_TITLE);
            CharSequence c = extras.getCharSequence(Notification.EXTRA_TEXT);
            CharSequence b = extras.getCharSequence(Notification.EXTRA_BIG_TEXT);
            if (t != null) rawTitle = t.toString().trim();
            if (c != null) rawText = c.toString().trim();
            else if (b != null) rawText = b.toString().trim();
        }

        if (rawTitle.isEmpty() && rawText.isEmpty()) {
            if (notif.tickerText != null) {
                rawText = notif.tickerText.toString().trim();
            }
        }

        if (rawTitle.isEmpty() && rawText.isEmpty()) return;

        final String appName = resolveAppName(pkg);
        final String title = rawTitle.isEmpty() ? appName : rawTitle;
        final String content = rawText.isEmpty() ? "New notification" : rawText;

        new Thread(new Runnable() {
            @Override
            public void run() {
                sendNotificationPayload(pkg, appName, title, content);
            }
        }).start();
    }

    private void sendNotificationPayload(String pkg, String appName, String title, String content) {
        try {
            JSONObject json = new JSONObject();
            json.put("package_name", pkg);
            json.put("app_name", appName);
            json.put("title", title);
            json.put("content", content);

            byte[] bytes = json.toString().getBytes("UTF-8");

            // Try GLOBAL_URL first, fallback to LOCAL_URL
            if (!postBytes(SERVER_URL, bytes)) {
                postBytes(LOCAL_URL, bytes);
            }
        } catch (Exception e) {
            Log.e(TAG, "Notification push failed: " + e.getMessage());
        }
    }

    private boolean postBytes(String endpoint, byte[] data) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(endpoint);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(2500);
            conn.setReadTimeout(2500);

            OutputStream os = conn.getOutputStream();
            os.write(data);
            os.flush();
            os.close();

            int code = conn.getResponseCode();
            return code >= 200 && code < 300;
        } catch (Exception e) {
            return false;
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    private String resolveAppName(String pkg) {
        if (pkg.contains("whatsapp")) return "WhatsApp";
        if (pkg.contains("android.gm") || pkg.contains("gmail")) return "Gmail";
        if (pkg.contains("calendar")) return "Calendar";
        if (pkg.contains("telegram")) return "Telegram";
        if (pkg.contains("instagram")) return "Instagram";
        if (pkg.contains("discord")) return "Discord";
        if (pkg.contains("slack")) return "Slack";
        if (pkg.contains("messaging") || pkg.contains("sms") || pkg.contains("mms")) return "Messages";
        if (pkg.contains("dialer") || pkg.contains("phone")) return "Phone Call";
        if (pkg.contains("youtube")) return "YouTube";
        if (pkg.contains("twitter") || pkg.contains("x.android")) return "X";

        String[] parts = pkg.split("\\.");
        if (parts.length > 0) {
            String p = parts[parts.length - 1];
            if (p.length() > 0) {
                return Character.toUpperCase(p.charAt(0)) + p.substring(1);
            }
        }
        return "Phone App";
    }
}
