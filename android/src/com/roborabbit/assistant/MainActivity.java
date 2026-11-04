package com.roborabbit.assistant;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final String GLOBAL_URL = "https://ssh.scempyy.me";
    private static final String LOCAL_URL = "http://192.168.1.22:7777";

    private WebView webView;
    private LinearLayout loadingLayout;
    private TextView loadingStatusText;
    private ProgressBar progressBar;
    private Button btnRetry;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Dark cyber status bar and navigation
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Window window = getWindow();
            window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
            window.setStatusBarColor(0xFF03070B);
            window.setNavigationBarColor(0xFF03070B);
        }

        setContentView(R.layout.activity_main);

        // Start background 24/7 service
        startRoborabbitService();

        // Request runtime permissions for audio / mic if needed
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{
                        Manifest.permission.RECORD_AUDIO,
                        "android.permission.POST_NOTIFICATIONS"
                }, 101);
            }
        }

        webView = findViewById(R.id.webView);
        loadingLayout = findViewById(R.id.loadingLayout);
        loadingStatusText = findViewById(R.id.loadingStatusText);
        progressBar = findViewById(R.id.progressBar);
        btnRetry = findViewById(R.id.btnRetry);

        setupWebView();
        loadRoborabbit();

        if (btnRetry != null) {
            btnRetry.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    btnRetry.setVisibility(View.GONE);
                    progressBar.setVisibility(View.VISIBLE);
                    loadingStatusText.setText("RECONNECTING TO ROBORABBIT...");
                    loadRoborabbit();
                }
            });
        }
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);
        settings.setUserAgentString(settings.getUserAgentString() + " RoborabbitMobile/1.0 Vivo-V2437");

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                // Automatically grant microphone permissions for Web Speech / Voice Engine
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        request.grant(request.getResources());
                    }
                });
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (loadingLayout != null) loadingLayout.setVisibility(View.GONE);
                if (webView != null) webView.setVisibility(View.VISIBLE);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request != null && request.isForMainFrame()) {
                    String failingUrl = request.getUrl().toString();
                    if (failingUrl.startsWith(GLOBAL_URL)) {
                        if (loadingStatusText != null) loadingStatusText.setText("CONNECTING TO DIRECT HOMELAB NODE...");
                        webView.loadUrl(LOCAL_URL);
                    } else {
                        if (progressBar != null) progressBar.setVisibility(View.GONE);
                        if (btnRetry != null) btnRetry.setVisibility(View.VISIBLE);
                        if (loadingStatusText != null) loadingStatusText.setText("CONNECTION OFFLINE. CHECK INTERNET.");
                    }
                }
            }
        });
    }

    private void loadRoborabbit() {
        // Load global URL so it functions anywhere on cellular, 5G, or any Wi-Fi
        webView.loadUrl(GLOBAL_URL);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private void startRoborabbitService() {
        try {
            Intent s = new Intent(this, RoborabbitService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(s);
            } else {
                startService(s);
            }
        } catch (Throwable e) {
            e.printStackTrace();
        }
    }
}
