// State
let currentSessionId = localStorage.getItem("roborabbit_session_id") || "";
let targetScope = "auto"; // auto, laptop1, laptop2, phone
let isStreaming = false;

// Audio & Voice State
let isAutoSpeak = localStorage.getItem("roborabbit_autospeak") !== "false";
let selectedVoice = localStorage.getItem("roborabbit_voice") || "en-GB-RyanNeural";
let selectedRate = localStorage.getItem("roborabbit_rate") || "+0%";
let currentAudio = null;
let activeSpeakBtn = null;
let speechRecognizer = null;
let isRecognizing = false;

// Wake Word & Hands-Free Conversation State
let isWakeWordEnabled = localStorage.getItem("roborabbit_wakeword") !== "false";
let isConversationMode = false;
let isAudioSpeaking = false;
let conversationExpiryTimer = null;
let recognizerRestartTimeout = null;
let silenceTimer = null;
let audioCtx = null;

// Elements
const messagesContainer = document.getElementById("messages-container");
const welcomeCard = document.getElementById("welcome-card");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send");
const btnMic = document.getElementById("btn-mic");
const sessionsContainer = document.getElementById("sessions-container");
const btnNewChat = document.getElementById("btn-new-chat");

// Wake Word Elements
const btnToggleWakeword = document.getElementById("btn-toggle-wakeword");
const wakewordIndicator = document.getElementById("wakeword-indicator");
const listeningIndicator = document.getElementById("listening-indicator");
const listeningStatusText = document.getElementById("listening-status-text");
const btnCancelListening = document.getElementById("btn-cancel-listening");

// Voice Mode Elements
const btnToggleVoice = document.getElementById("btn-toggle-voice");
const voiceIndicatorPing = document.getElementById("voice-indicator-ping");
const voiceIndicatorDot = document.getElementById("voice-indicator-dot");
const voiceStatusText = document.getElementById("voice-status-text");
const jarvisVisualizer = document.getElementById("jarvis-visualizer");

// Device Badges
const laptop1StatsText = document.getElementById("laptop1-stats-text");
const laptop1StatusDot = document.getElementById("laptop1-status-dot");
const badgeLaptop1 = document.getElementById("badge-laptop1");
const btnWakeLaptop1 = document.getElementById("btn-wake-laptop1");

const laptop2StatsText = document.getElementById("laptop2-stats-text");

const phoneStatsText = document.getElementById("phone-stats-text");
const phoneStatusDot = document.getElementById("phone-status-dot");
const badgePhone = document.getElementById("badge-phone");
const btnConnectPhoneModal = document.getElementById("btn-connect-phone-modal");
const btnRefreshStatus = document.getElementById("btn-refresh-status");

// Arc Reactor
const arcReactorCore = document.getElementById("arc-reactor-core");

// HUD Manager Ribbon Elements
const btnHudBriefing = document.getElementById("btn-hud-briefing");
const btnHudCalendar = document.getElementById("btn-hud-calendar");
const btnHudAlarms = document.getElementById("btn-hud-alarms");
const btnHudEmails = document.getElementById("btn-hud-emails");
const btnHudPhone = document.getElementById("btn-hud-phone");
const btnHudNews = document.getElementById("btn-hud-news");
const hudNewsTicker = document.getElementById("hud-news-ticker");
const hudNewsHeadline = document.getElementById("hud-news-headline");

// Badges
const badgeCalendarCount = document.getElementById("badge-calendar-count");
const badgeAlarmsCount = document.getElementById("badge-alarms-count");
const badgeEmailsCount = document.getElementById("badge-emails-count");
const badgePhoneNotifsCount = document.getElementById("badge-phone-notifs-count");

// Manager Modals
const modalBriefing = document.getElementById("modal-briefing");
const modalCalendar = document.getElementById("modal-calendar");
const modalAlarms = document.getElementById("modal-alarms");
const modalEmails = document.getElementById("modal-emails");
const modalPhoneHub = document.getElementById("modal-phone-hub");
const modalNews = document.getElementById("modal-news");
const alarmTriggerOverlay = document.getElementById("alarm-trigger-overlay");

// Phone Modal Legacy
const phoneModal = document.getElementById("phone-modal");
const btnClosePhone = document.getElementById("btn-close-phone");
const btnCancelPhone = document.getElementById("btn-cancel-phone");
const btnSubmitPhone = document.getElementById("btn-submit-phone");
const phoneIpInput = document.getElementById("phone-ip-input");
const phonePortInput = document.getElementById("phone-port-input");

// Scope Buttons
const scopeAuto = document.getElementById("scope-auto");
const scopeLaptop1 = document.getElementById("scope-laptop1");
const scopeLaptop2 = document.getElementById("scope-laptop2");
const scopePhone = document.getElementById("scope-phone");
const providerIndicator = document.getElementById("ai-provider-indicator");

// Settings Modal
const settingsModal = document.getElementById("settings-modal");
const btnOpenSettings = document.getElementById("btn-open-settings");
const btnCloseSettings = document.getElementById("btn-close-settings");
const btnCancelSettings = document.getElementById("btn-cancel-settings");
const btnSaveSettings = document.getElementById("btn-save-settings");
const cfgProvider = document.getElementById("cfg-provider");
const cfgApiKey = document.getElementById("cfg-api-key");
const cfgModel = document.getElementById("cfg-model");
const cfgBaseUrl = document.getElementById("cfg-base-url");
const apiKeyStatus = document.getElementById("api-key-status");

const cfgTtsVoice = document.getElementById("cfg-tts-voice");
const cfgTtsRate = document.getElementById("cfg-tts-rate");
const cfgTtsAutoSpeak = document.getElementById("cfg-tts-autospeak");
const btnTestVoice = document.getElementById("btn-test-voice");
const testVoiceStatus = document.getElementById("test-voice-status");

document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  marked.setOptions({
    highlight: function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true
  });

  updateVoiceUI();
  updateWakeWordUI();
  initSession();
  loadSessions();
  pollDeviceStatus();
  setInterval(pollDeviceStatus, 10000);
  pollManagerHubs();
  setInterval(pollManagerHubs, 5000);
  loadConfig();
  setupEventListeners();
  initSpeechRecognition();
  initCyberTelemetry();
  initCyberCanvas();
  initArcWaveformVisualizer();
  initCyberCLI();
  initMobileClientBridge();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }
});

function setupEventListeners() {
  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
  });

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  btnSend.addEventListener("click", sendMessage);
  btnNewChat.addEventListener("click", createNewChat);

  // JARVIS Voice Toggle
  if (btnToggleVoice) {
    btnToggleVoice.addEventListener("click", toggleJarvisVoice);
  }

  // Wake Word Toggle & Cancel
  if (btnToggleWakeword) {
    btnToggleWakeword.addEventListener("click", toggleWakeWord);
  }
  if (btnCancelListening) {
    btnCancelListening.addEventListener("click", () => {
      exitConversationMode(true);
    });
  }

  // Mic dictation
  if (btnMic) {
    btnMic.addEventListener("click", toggleSpeechRecognition);
  }

  // Scope Buttons
  scopeAuto.addEventListener("click", () => setScope("auto"));
  scopeLaptop1.addEventListener("click", () => setScope("laptop1"));
  scopeLaptop2.addEventListener("click", () => setScope("laptop2"));
  scopePhone.addEventListener("click", () => setScope("phone"));

  // Device actions
  btnWakeLaptop1.addEventListener("click", wakeLaptop1);
  badgeLaptop1.addEventListener("click", wakeLaptop1);
  btnRefreshStatus.addEventListener("click", pollDeviceStatus);

  // Phone Modal
  badgePhone.addEventListener("click", () => phoneModal.classList.remove("hidden"));
  btnConnectPhoneModal.addEventListener("click", () => phoneModal.classList.remove("hidden"));
  btnClosePhone.addEventListener("click", () => phoneModal.classList.add("hidden"));
  btnCancelPhone.addEventListener("click", () => phoneModal.classList.add("hidden"));
  btnSubmitPhone.addEventListener("click", connectPhone);

  // Quick Action Pills
  document.querySelectorAll(".quick-pill, .welcome-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const prompt = btn.getAttribute("data-prompt");
      if (prompt) {
        chatInput.value = prompt;
        sendMessage();
      }
    });
  });

  // Settings
  btnOpenSettings.addEventListener("click", () => {
    loadConfig();
    settingsModal.classList.remove("hidden");
  });
  btnCloseSettings.addEventListener("click", () => settingsModal.classList.add("hidden"));
  btnCancelSettings.addEventListener("click", () => settingsModal.classList.add("hidden"));
  btnSaveSettings.addEventListener("click", saveSettings);

  if (btnTestVoice) {
    btnTestVoice.addEventListener("click", playTestVoice);
  }

  // JARVIS Manager Hub Ribbons & Modals
  if (btnHudBriefing) btnHudBriefing.addEventListener("click", () => { playHudClickSound(); openBriefingModal(); });
  if (btnHudCalendar) btnHudCalendar.addEventListener("click", () => { playHudClickSound(); openCalendarModal(); });
  if (btnHudAlarms) btnHudAlarms.addEventListener("click", () => { playHudClickSound(); openAlarmsModal(); });
  if (btnHudEmails) btnHudEmails.addEventListener("click", () => { playHudClickSound(); openEmailsModal(); });
  if (btnHudPhone) btnHudPhone.addEventListener("click", () => { playHudClickSound(); openPhoneHubModal(); });
  if (btnHudNews) btnHudNews.addEventListener("click", () => { playHudClickSound(); openNewsModal("all"); });
  if (hudNewsTicker) hudNewsTicker.addEventListener("click", () => { playHudClickSound(); openNewsModal("all"); });

  const btnHudTodos = document.getElementById("btn-hud-todos");
  if (btnHudTodos) btnHudTodos.addEventListener("click", () => {
    playHudClickSound();
    chatInput.value = "What are my pending tasks and to-dos today?";
    sendMessage();
  });

  const btnHudSmartHome = document.getElementById("btn-hud-smarthome");
  if (btnHudSmartHome) btnHudSmartHome.addEventListener("click", () => {
    playHudClickSound();
    chatInput.value = "Show connected smart home devices and lighting status.";
    sendMessage();
  });

  const btnHudVision = document.getElementById("btn-hud-vision");
  if (btnHudVision) btnHudVision.addEventListener("click", () => {
    playHudClickSound();
    chatInput.value = "Capture screen and tell me what is currently on my display.";
    sendMessage();
  });

  // Modal Closers
  const closeBriefing = document.getElementById("btn-close-briefing");
  if (closeBriefing) closeBriefing.addEventListener("click", () => { playHudClickSound(); modalBriefing.classList.add("hidden"); });
  const closeCal = document.getElementById("btn-close-calendar");
  if (closeCal) closeCal.addEventListener("click", () => { playHudClickSound(); modalCalendar.classList.add("hidden"); });
  const closeAlarms = document.getElementById("btn-close-alarms");
  if (closeAlarms) closeAlarms.addEventListener("click", () => {
    playHudClickSound();
    modalAlarms.classList.add("hidden");
    if (alarmsCountdownInterval) {
      clearInterval(alarmsCountdownInterval);
      alarmsCountdownInterval = null;
    }
  });
  const closeEmails = document.getElementById("btn-close-emails");
  if (closeEmails) closeEmails.addEventListener("click", () => { playHudClickSound(); modalEmails.classList.add("hidden"); });
  const closePhoneHub = document.getElementById("btn-close-phone-hub");
  if (closePhoneHub) closePhoneHub.addEventListener("click", () => { playHudClickSound(); modalPhoneHub.classList.add("hidden"); });
  const closeNews = document.getElementById("btn-close-news");
  if (closeNews) closeNews.addEventListener("click", () => { playHudClickSound(); modalNews.classList.add("hidden"); });

  // Inner Manager Actions
  const btnSpeakBriefing = document.getElementById("btn-speak-briefing");
  if (btnSpeakBriefing) btnSpeakBriefing.addEventListener("click", speakCurrentBriefing);

  const bOpenCal = document.getElementById("btn-briefing-open-calendar");
  if (bOpenCal) bOpenCal.addEventListener("click", () => { modalBriefing.classList.add("hidden"); openCalendarModal(); });
  const bOpenMail = document.getElementById("btn-briefing-open-emails");
  if (bOpenMail) bOpenMail.addEventListener("click", () => { modalBriefing.classList.add("hidden"); openEmailsModal(); });
  const bOpenPhone = document.getElementById("btn-briefing-open-phone");
  if (bOpenPhone) bOpenPhone.addEventListener("click", () => { modalBriefing.classList.add("hidden"); openPhoneHubModal(); });
  const bOpenNews = document.getElementById("btn-briefing-open-news");
  if (bOpenNews) bOpenNews.addEventListener("click", () => { modalBriefing.classList.add("hidden"); openNewsModal("all"); });

  const btnAddEvt = document.getElementById("btn-add-event");
  if (btnAddEvt) btnAddEvt.addEventListener("click", handleAddCalendarEvent);

  document.querySelectorAll(".btn-preset-timer").forEach(b => {
    b.addEventListener("click", () => handlePresetTimer(parseInt(b.getAttribute("data-seconds"))));
  });

  const btnAddAlarm = document.getElementById("btn-add-alarm");
  if (btnAddAlarm) btnAddAlarm.addEventListener("click", handleAddCustomAlarm);

  const btnToggleGmail = document.getElementById("btn-toggle-gmail-config");
  if (btnToggleGmail) btnToggleGmail.addEventListener("click", () => {
    document.getElementById("gmail-config-drawer").classList.toggle("hidden");
    loadGmailStatus();
  });
  const btnSaveGmail = document.getElementById("btn-save-gmail-config");
  if (btnSaveGmail) btnSaveGmail.addEventListener("click", handleSaveGmailConfig);
  const btnSyncGmail = document.getElementById("btn-sync-gmail-now");
  if (btnSyncGmail) btnSyncGmail.addEventListener("click", handleSyncGmailNow);

  const btnToggleCompose = document.getElementById("btn-toggle-compose-email");
  if (btnToggleCompose) btnToggleCompose.addEventListener("click", () => {
    document.getElementById("compose-email-drawer").classList.toggle("hidden");
  });
  const btnCancelCompose = document.getElementById("btn-cancel-compose");
  if (btnCancelCompose) btnCancelCompose.addEventListener("click", () => {
    document.getElementById("compose-email-drawer").classList.add("hidden");
  });
  const btnSendMail = document.getElementById("btn-send-mail");
  if (btnSendMail) btnSendMail.addEventListener("click", handleSendEmail);

  const btnSyncPhone = document.getElementById("btn-sync-phone-notifs");
  if (btnSyncPhone) btnSyncPhone.addEventListener("click", handleSyncPhoneNotifs);
  const btnPhoneTest = document.getElementById("btn-phone-push-test");
  if (btnPhoneTest) btnPhoneTest.addEventListener("click", handlePushTestAlert);
  const btnClearPhone = document.getElementById("btn-clear-phone-notifs");
  if (btnClearPhone) btnClearPhone.addEventListener("click", handleClearPhoneNotifs);

  // Cyber Remote Deck
  const btnPhoneYt = document.getElementById("btn-phone-quick-youtube");
  if (btnPhoneYt) btnPhoneYt.addEventListener("click", () => dispatchPhoneCommand("open_url", { url: "https://www.youtube.com" }));

  const btnPhoneWa = document.getElementById("btn-phone-quick-whatsapp");
  if (btnPhoneWa) btnPhoneWa.addEventListener("click", () => dispatchPhoneCommand("open_url", { url: "whatsapp://send" }));

  const btnPhoneVib = document.getElementById("btn-phone-quick-vibrate");
  if (btnPhoneVib) btnPhoneVib.addEventListener("click", () => dispatchPhoneCommand("vibrate", {}));

  const btnPhoneSpk = document.getElementById("btn-phone-quick-speak");
  if (btnPhoneSpk) btnPhoneSpk.addEventListener("click", () => {
    const text = prompt("Enter text to broadcast through phone speaker:", "Roborabbit online. All systems operational.");
    if (text) dispatchPhoneCommand("speak", { text });
  });

  const btnPhoneDispatch = document.getElementById("btn-phone-dispatch-url");
  const inputPhoneCustom = document.getElementById("input-phone-custom-url");
  if (btnPhoneDispatch && inputPhoneCustom) {
    btnPhoneDispatch.addEventListener("click", () => {
      const u = inputPhoneCustom.value.trim();
      if (u) {
        dispatchPhoneCommand("open_url", { url: u });
        inputPhoneCustom.value = "";
      }
    });
  }

  const btnDismissAlarm = document.getElementById("btn-dismiss-alarm-overlay");
  if (btnDismissAlarm) btnDismissAlarm.addEventListener("click", dismissActiveAlarmOverlay);

  document.querySelectorAll(".news-category-btn").forEach(b => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".news-category-btn").forEach(x => {
        x.className = "news-category-btn px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200";
      });
      b.className = "news-category-btn px-2.5 py-1 rounded-full bg-cyan-900/60 border border-cyan-600 text-cyan-300 font-medium";
      loadNewsStories(b.getAttribute("data-cat"));
    });
  });

  // Mobile Bottom Cyber Dock Listeners
  const mobMic = document.getElementById("mobile-btn-mic");
  if (mobMic) mobMic.addEventListener("click", toggleSpeechRecognition);

  const mobPhone = document.getElementById("mobile-btn-phone");
  if (mobPhone) mobPhone.addEventListener("click", () => {
    if (modalPhoneHub) modalPhoneHub.classList.toggle("hidden");
  });

  const mobCli = document.getElementById("mobile-btn-cli");
  if (mobCli) mobCli.addEventListener("click", () => {
    const term = document.getElementById("modal-cyber-terminal");
    const input = document.getElementById("terminal-input");
    if (term) {
      term.classList.toggle("hidden");
      if (!term.classList.contains("hidden") && input) input.focus();
    }
  });

  const mobBriefing = document.getElementById("mobile-btn-briefing");
  if (mobBriefing && btnHudBriefing) mobBriefing.addEventListener("click", () => btnHudBriefing.click());

  const mobMatrix = document.getElementById("mobile-btn-matrix");
  if (mobMatrix) {
    const btnM = document.getElementById("btn-toggle-matrix");
    mobMatrix.addEventListener("click", () => { if (btnM) btnM.click(); });
  }
}

// ==========================================
// JARVIS VOICE & AUDIO ENGINE (TTS)
// ==========================================

function updateVoiceUI() {
  if (!btnToggleVoice) return;
  if (isAutoSpeak) {
    voiceStatusText.textContent = "Voice: ON";
    voiceIndicatorPing.classList.remove("hidden");
    voiceIndicatorDot.className = "relative inline-flex rounded-full h-2 w-2 bg-cyan-400";
    btnToggleVoice.classList.add("border-cyan-700/80");
  } else {
    voiceStatusText.textContent = "Voice: OFF";
    voiceIndicatorPing.classList.add("hidden");
    voiceIndicatorDot.className = "relative inline-flex rounded-full h-2 w-2 bg-slate-500";
    btnToggleVoice.classList.remove("border-cyan-700/80");
  }
}

function toggleJarvisVoice() {
  isAutoSpeak = !isAutoSpeak;
  localStorage.setItem("roborabbit_autospeak", isAutoSpeak);
  updateVoiceUI();
  if (!isAutoSpeak) {
    stopSpeaking();
  } else {
    // Quick audio confirmation
    playNotificationSound();
  }
}

function cleanTextForSpeech(raw) {
  if (!raw) return "";
  let t = raw;
  t = t.replace(/```[\s\S]*?```/g, " [Code omitted] ");
  t = t.replace(/`([^`]+)`/g, "$1");
  t = t.replace(/^#{1,6}\s+/gm, "");
  t = t.replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");
  t = t.replace(/https?:\/\/\S+/g, " link ");
  t = t.replace(/[*_~|]/g, " ");
  t = t.replace(/[-:]{3,}/g, " ");
  t = t.replace(/[^\w\s.,!?:;'"()/-]/g, " ");
  t = t.replace(/\bWoL\b/gi, "Wake on LAN");
  t = t.replace(/\bADB\b/gi, "A D B");
  t = t.replace(/\bSSH\b/gi, "S S H");
  t = t.replace(/\bRAM\b/gi, "ram");
  t = t.replace(/\bCPU\b/gi, "C P U");
  t = t.replace(/\bGiB\b/gi, "gigabytes");
  t = t.replace(/\bGB\b/gi, "gigabytes");
  t = t.replace(/\bMiB\b/gi, "megabytes");
  t = t.replace(/\bMB\b/gi, "megabytes");
  t = t.replace(/\bIP\b/gi, "I P");
  t = t.replace(/\s+/g, " ").trim();
  
  // Keep voice response to the first 2 concise sentences so TTS is brief and easy to listen to
  const sentences = t.match(/[^.!?]+[.!?]+/g);
  if (sentences && sentences.length > 2) {
    t = sentences.slice(0, 2).join(" ");
  } else if (t.length > 280) {
    t = t.substring(0, 280).replace(/\s+\S*$/, "") + ".";
  }
  return t;
}

function stopSpeaking() {
  isAudioSpeaking = false;
  if (currentAudio) {
    try {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    } catch (e) {}
    currentAudio = null;
  }
  if (window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch (e) {}
  }
  if (activeSpeakBtn) {
    activeSpeakBtn.innerHTML = `<i data-lucide="volume-2" class="w-3.5 h-3.5 text-cyan-400"></i><span>Speak</span>`;
    activeSpeakBtn.classList.remove("btn-speak-active");
    activeSpeakBtn = null;
    lucide.createIcons();
  }
  if (jarvisVisualizer) {
    jarvisVisualizer.classList.add("hidden");
    jarvisVisualizer.classList.remove("inline-flex");
  }
  if (arcReactorCore) {
    arcReactorCore.classList.remove("speaking");
  }
}

// Emergency Stop Keyboard Shortcut (Escape Key) (#12 Security & Privacy)
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    stopSpeaking();
    fetch("/api/emergency_stop", { method: "POST" }).catch(() => {});
  }
});

function onTTSSpeechFinished() {
  isAudioSpeaking = false;
  if (arcReactorCore) {
    arcReactorCore.classList.remove("speaking");
  }
  if (isWakeWordEnabled) {
    // Keep mic open for natural conversational follow-up ("talk like humans")
    enterConversationMode("Listening for your reply... (hands-free)");
    startSpeechRecognitionIfNeeded();
  }
}

async function speakMessage(rawText, buttonElement = null) {
  const clean = cleanTextForSpeech(rawText);
  if (!clean) return;

  // If clicking on already playing button, stop it
  if (activeSpeakBtn === buttonElement && currentAudio && !currentAudio.paused) {
    stopSpeaking();
    return;
  }

  stopSpeaking();
  isAudioSpeaking = true;
  if (arcReactorCore) {
    arcReactorCore.classList.add("speaking");
  }

  if (buttonElement) {
    activeSpeakBtn = buttonElement;
    activeSpeakBtn.innerHTML = `<i data-lucide="square" class="w-3.5 h-3.5 text-red-400"></i><span>Stop</span>`;
    activeSpeakBtn.classList.add("btn-speak-active");
    lucide.createIcons();
  }

  if (jarvisVisualizer) {
    jarvisVisualizer.classList.remove("hidden");
    jarvisVisualizer.classList.add("inline-flex");
  }

  const voice = selectedVoice || "en-GB-RyanNeural";
  const rate = selectedRate || "+0%";
  const ttsUrl = `/api/tts?text=${encodeURIComponent(clean)}&voice=${encodeURIComponent(voice)}&rate=${encodeURIComponent(rate)}`;

  try {
    currentAudio = new Audio(ttsUrl);
    
    currentAudio.onplay = () => {
      isAudioSpeaking = true;
      if (jarvisVisualizer) {
        jarvisVisualizer.classList.remove("hidden");
        jarvisVisualizer.classList.add("inline-flex");
      }
    };

    currentAudio.onended = () => {
      stopSpeaking();
      onTTSSpeechFinished();
    };

    currentAudio.onerror = (err) => {
      console.warn("Server TTS audio error, falling back to Web Speech API:", err);
      fallbackWebSpeech(clean);
    };

    await currentAudio.play();
  } catch (err) {
    console.warn("Audio play prevented or failed, using client fallback:", err);
    fallbackWebSpeech(clean);
  }
}

function fallbackWebSpeech(cleanText) {
  if (!window.speechSynthesis) {
    stopSpeaking();
    return;
  }
  isAudioSpeaking = true;
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.05;
  utterance.pitch = 0.95;

  const voices = window.speechSynthesis.getVoices();
  const britishVoice = voices.find(v => v.lang.includes("GB") || v.name.toLowerCase().includes("british") || v.name.toLowerCase().includes("uk")) || voices[0];
  if (britishVoice) utterance.voice = britishVoice;

  utterance.onend = () => {
    stopSpeaking();
    onTTSSpeechFinished();
  };
  utterance.onerror = () => {
    stopSpeaking();
  };

  window.speechSynthesis.speak(utterance);
}

// ==========================================
// AUDIO CHIMES & SOUND SYNTHESIS
// ==========================================

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume().catch(() => {});
  }
  return audioCtx;
}

function playWakeChime() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    
    // Low tone (659Hz - E5)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = "sine";
    osc1.frequency.setValueAtTime(659.25, now);
    gain1.gain.setValueAtTime(0.12, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.12);

    // High tone (1046Hz - C6) - JARVIS activation tone
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = "sine";
    osc2.frequency.setValueAtTime(1046.50, now + 0.08);
    gain2.gain.setValueAtTime(0.14, now + 0.08);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.08);
    osc2.stop(now + 0.28);
  } catch (e) {
    console.warn("Chime error:", e);
  }
}

function playSleepChime() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(783.99, now);
    osc.frequency.exponentialRampToValueAtTime(523.25, now + 0.18);
    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.2);
  } catch (e) {}
}

function playHudClickSound() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(1760, now + 0.04);
    gain.gain.setValueAtTime(0.035, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.05);
  } catch (e) {}
}

function playSuccessChime() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = "sine";
    osc1.frequency.setValueAtTime(587.33, now); // D5
    gain1.gain.setValueAtTime(0.08, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.12);

    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = "sine";
    osc2.frequency.setValueAtTime(880, now + 0.08); // A5
    gain2.gain.setValueAtTime(0.1, now + 0.08);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.24);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.08);
    osc2.stop(now + 0.24);
  } catch (e) {}
}

function playNotificationSound() {
  playSuccessChime();
}

async function playTestVoice() {
  if (testVoiceStatus) testVoiceStatus.textContent = "Synthesizing...";
  try {
    const voice = cfgTtsVoice.value;
    const rate = cfgTtsRate.value;
    const testAudio = new Audio(`/api/tts?text=Roborabbit+neural+voice+online%2C+sir.+All+systems+nominal.&voice=${encodeURIComponent(voice)}&rate=${encodeURIComponent(rate)}`);
    testAudio.onplay = () => {
      if (testVoiceStatus) testVoiceStatus.textContent = "Playing...";
    };
    testAudio.onended = () => {
      if (testVoiceStatus) testVoiceStatus.textContent = "Ready";
    };
    await testAudio.play();
  } catch (e) {
    if (testVoiceStatus) testVoiceStatus.textContent = "Error: " + e.message;
  }
}

// ==========================================
// WAKE WORD & CONVERSATIONAL VOICE ENGINE
// ==========================================

function updateWakeWordUI() {
  if (!wakewordIndicator) return;
  if (isWakeWordEnabled) {
    wakewordIndicator.className = "w-2 h-2 rounded-full bg-emerald-400 animate-pulse";
    if (btnToggleWakeword) {
      btnToggleWakeword.title = "Wake Word Engine: ACTIVE (Say 'Robo' anytime to talk hands-free)";
      btnToggleWakeword.classList.remove("opacity-50");
    }
  } else {
    wakewordIndicator.className = "w-2 h-2 rounded-full bg-slate-600";
    if (btnToggleWakeword) {
      btnToggleWakeword.title = "Wake Word Engine: OFF (Click to enable hands-free 'Robo')";
      btnToggleWakeword.classList.add("opacity-50");
    }
  }
}

function toggleWakeWord() {
  isWakeWordEnabled = !isWakeWordEnabled;
  localStorage.setItem("roborabbit_wakeword", isWakeWordEnabled);
  updateWakeWordUI();
  if (isWakeWordEnabled) {
    playWakeChime();
    startSpeechRecognitionIfNeeded();
  } else {
    exitConversationMode(false);
    if (speechRecognizer && isRecognizing) {
      try { speechRecognizer.stop(); } catch (e) {}
    }
  }
}

function showListeningPill(text = "Robo is listening, sir...") {
  if (listeningIndicator) {
    listeningIndicator.classList.remove("hidden");
    if (listeningStatusText) listeningStatusText.textContent = text;
  }
  if (btnMic) {
    btnMic.classList.add("mic-recording");
  }
}

function hideListeningPill() {
  if (listeningIndicator) {
    listeningIndicator.classList.add("hidden");
  }
  if (btnMic) {
    btnMic.classList.remove("mic-recording");
  }
}

function enterConversationMode(statusText = "Robo is listening, sir...") {
  isConversationMode = true;
  if (arcReactorCore) {
    arcReactorCore.classList.remove("speaking");
    arcReactorCore.classList.add("listening");
  }
  showListeningPill(statusText);
  resetConversationExpiryTimer(8500);
}

function resetConversationExpiryTimer(durationMs = 8500) {
  if (conversationExpiryTimer) clearTimeout(conversationExpiryTimer);
  conversationExpiryTimer = setTimeout(() => {
    exitConversationMode(true);
  }, durationMs);
}

function exitConversationMode(playChime = true) {
  if (conversationExpiryTimer) {
    clearTimeout(conversationExpiryTimer);
    conversationExpiryTimer = null;
  }
  if (silenceTimer) {
    clearTimeout(silenceTimer);
    silenceTimer = null;
  }
  if (arcReactorCore) {
    arcReactorCore.classList.remove("listening");
  }
  if (isConversationMode && playChime) {
    playSleepChime();
  }
  isConversationMode = false;
  hideListeningPill();
}

function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    if (btnMic) {
      btnMic.title = "Voice recognition not supported in this browser (Use Chrome or Edge)";
      btnMic.classList.add("opacity-40");
    }
    if (btnToggleWakeword) {
      btnToggleWakeword.classList.add("opacity-40");
      btnToggleWakeword.title = "Speech recognition unsupported";
    }
    return;
  }

  speechRecognizer = new SpeechRec();
  speechRecognizer.continuous = true;
  speechRecognizer.interimResults = true;
  speechRecognizer.lang = "en-US";

  speechRecognizer.onstart = () => {
    isRecognizing = true;
    if (isConversationMode) {
      showListeningPill();
    }
  };

  speechRecognizer.onresult = (event) => {
    // Check if RoboRabbit is currently speaking aloud via TTS
    if (isAudioSpeaking || (currentAudio && !currentAudio.paused)) {
      // Barge-in / Interruption detection (#2 Voice Assistant)
      let bargeTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        bargeTranscript += event.results[i][0].transcript + " ";
      }
      if (/\b(stop|quiet|shut up|wait|pause|hold on|cancel|robo|roborabbit)\b/i.test(bargeTranscript)) {
        stopSpeaking();
        if (typeof playWakeChime === "function") playWakeChime();
        enterConversationMode("I am listening, sir...");
        return;
      }
      return;
    }

    let fullTranscript = "";
    for (let i = 0; i < event.results.length; i++) {
      fullTranscript += event.results[i][0].transcript + " ";
    }

    const trimmed = fullTranscript.trim();
    if (!trimmed) return;

    // Check for exit commands when in conversation mode
    const EXIT_PATTERN = /\b(stop\s+listening|goodbye\s+robo|goodbye|bye\s+robo|nevermind|never\s+mind|exit\s+voice|sleep\s+robo)\b/i;
    if (isConversationMode && EXIT_PATTERN.test(trimmed)) {
      chatInput.value = "";
      exitConversationMode(true);
      return;
    }

    if (!isConversationMode) {
      // Passive Wake Word Listening ("robo", "hey robo", "ok robo", "roborabbit")
      const wakeMatch = trimmed.match(/\b(?:robo|roborabbit|hey\s+robo|ok\s+robo|okay\s+robo|hello\s+robo|robot)\b[,:\s-]*(.*)/i);

      if (wakeMatch) {
        playWakeChime();
        const initialQuery = wakeMatch[1] ? wakeMatch[1].trim() : "";
        enterConversationMode("Robo is listening, sir...");
        if (initialQuery) {
          chatInput.value = initialQuery;
          showListeningPill(`Listening: "${initialQuery}"`);
        }

        if (silenceTimer) clearTimeout(silenceTimer);
        silenceTimer = setTimeout(() => {
          if (chatInput.value.trim().length > 0 && !isStreaming) {
            exitConversationMode(false);
            sendMessage();
          }
        }, 1800);
      }
    } else {
      // Active conversational mode ("talk like humans")
      resetConversationExpiryTimer(12000);
      let cleaned = trimmed.replace(/^\b(?:robo|roborabbit|hey\s+robo|ok\s+robo)\b[,:\s-]*/i, "").trim();
      if (!cleaned) cleaned = trimmed;

      chatInput.value = cleaned;
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
      showListeningPill(`Listening: "${cleaned}"`);

      if (silenceTimer) clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {
        if (chatInput.value.trim().length > 0 && !isStreaming) {
          exitConversationMode(false);
          sendMessage();
        }
      }, 1800);
    }
  };

  speechRecognizer.onerror = (event) => {
    console.warn("Speech recognition notice:", event.error);
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      isWakeWordEnabled = false;
      updateWakeWordUI();
      hideListeningPill();
    } else if (isConversationMode) {
      clearTimeout(recognizerRestartTimeout);
      recognizerRestartTimeout = setTimeout(startSpeechRecognitionIfNeeded, 150);
    } else if (isWakeWordEnabled) {
      clearTimeout(recognizerRestartTimeout);
      recognizerRestartTimeout = setTimeout(startSpeechRecognitionIfNeeded, 1000);
    }
  };

  speechRecognizer.onend = () => {
    isRecognizing = false;
    clearTimeout(recognizerRestartTimeout);
    if (isConversationMode) {
      // Actively listening to user dictation: restart immediately without dropping UI
      recognizerRestartTimeout = setTimeout(startSpeechRecognitionIfNeeded, 80);
    } else if (isWakeWordEnabled) {
      // Background idle wake word: restart smoothly after 800ms
      recognizerRestartTimeout = setTimeout(startSpeechRecognitionIfNeeded, 800);
    }
  };

  if (isWakeWordEnabled) {
    startSpeechRecognitionIfNeeded();
  }
}

function startSpeechRecognitionIfNeeded() {
  if (!speechRecognizer) return;
  if (!isRecognizing) {
    try {
      speechRecognizer.start();
    } catch (e) {
      // Already running or pending
    }
  }
}

function toggleSpeechRecognition() {
  if (!speechRecognizer) {
    alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or a modern Android browser.");
    return;
  }
  getAudioContext();
  if (isConversationMode) {
    if (chatInput.value.trim().length > 0 && !isStreaming) {
      exitConversationMode(false);
      sendMessage();
    } else {
      exitConversationMode(true);
    }
  } else {
    stopSpeaking();
    playWakeChime();
    chatInput.value = "";
    enterConversationMode("Listening... Speak your command");
    startSpeechRecognitionIfNeeded();
  }
}

// User Interaction Unlocker for Browser Autoplay & AudioContext
function unlockAudioContextOnGesture() {
  getAudioContext();
  if (isWakeWordEnabled) {
    startSpeechRecognitionIfNeeded();
  }
}
window.addEventListener("click", unlockAudioContextOnGesture, { passive: true });
window.addEventListener("touchstart", unlockAudioContextOnGesture, { passive: true });

// ==========================================
// SESSION & UI STATE
// ==========================================

function setScope(scope) {
  targetScope = scope;
  [scopeAuto, scopeLaptop1, scopeLaptop2, scopePhone].forEach(b => {
    b.className = "scope-btn px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 whitespace-nowrap";
  });
  const activeBtn = scope === "auto" ? scopeAuto : (scope === "laptop1" ? scopeLaptop1 : (scope === "laptop2" ? scopeLaptop2 : scopePhone));
  activeBtn.className = "scope-btn px-2.5 py-0.5 rounded-full bg-cyan-900/60 border border-cyan-700 text-cyan-300 font-medium whitespace-nowrap";
}

async function initSession() {
  if (!currentSessionId) {
    currentSessionId = Math.random().toString(36).substring(2, 10);
    localStorage.setItem("roborabbit_session_id", currentSessionId);
  }
  loadCurrentSessionMessages();
}

async function createNewChat() {
  stopSpeaking();
  currentSessionId = Math.random().toString(36).substring(2, 10);
  localStorage.setItem("roborabbit_session_id", currentSessionId);
  loadSessions();
  loadCurrentSessionMessages();
  chatInput.focus();
}

async function pollDeviceStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();

    // Laptop
    const l1 = data.laptop1 || {};
    if (l1.online) {
      laptop1StatusDot.className = "w-2 h-2 rounded-full bg-emerald-500";
      laptop1StatsText.textContent = `${l1.battery || 'Online'}`;
      badgeLaptop1.classList.remove("opacity-60");
    } else {
      laptop1StatusDot.className = "w-2 h-2 rounded-full bg-slate-500";
      laptop1StatsText.textContent = "Asleep";
      badgeLaptop1.classList.add("opacity-60");
    }

    // Server
    const l2 = data.laptop2 || {};
    if (l2.online) {
      laptop2StatsText.textContent = `${l2.ram_percent}% RAM • ${l2.temperature}`;
    }

    // Mobile
    const ph = data.phone || {};
    if (ph.online) {
      phoneStatusDot.className = "w-2 h-2 rounded-full bg-emerald-500 animate-pulse";
      phoneStatsText.textContent = `${ph.battery || 'Connected'}`;
      badgePhone.classList.remove("opacity-60");
    } else {
      phoneStatusDot.className = "w-2 h-2 rounded-full bg-slate-500";
      phoneStatsText.textContent = "Standby";
      badgePhone.classList.add("opacity-60");
    }
  } catch (e) {
    console.error("Status poll error:", e);
  }
}

async function wakeLaptop1() {
  try {
    btnWakeLaptop1.classList.add("animate-pulse");
    const res = await fetch("/api/wake", { method: "POST" });
    const data = await res.json();
    alert(data.message || "Wake-on-LAN magic packet sent to Laptop!");
    setTimeout(pollDeviceStatus, 3000);
  } catch (e) {
    alert("Failed to send Wake packet: " + e.message);
  } finally {
    btnWakeLaptop1.classList.remove("animate-pulse");
  }
}

async function connectPhone() {
  const ip = phoneIpInput.value.trim();
  const port = parseInt(phonePortInput.value.trim()) || 5555;
  if (!ip) {
    alert("Please enter your phone's Wi-Fi IP address.");
    return;
  }

  btnSubmitPhone.disabled = true;
  btnSubmitPhone.textContent = "Connecting...";

  try {
    const res = await fetch("/api/phone/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ip, port })
    });
    const data = await res.json();
    phoneModal.classList.add("hidden");
    alert(`Phone connection attempt:\n${data.stdout || data.stderr || 'Sent connect request'}`);
    pollDeviceStatus();
  } catch (e) {
    alert("Connect error: " + e.message);
  } finally {
    btnSubmitPhone.disabled = false;
    btnSubmitPhone.textContent = "Connect Phone";
  }
}

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) return;
    const cfg = await res.json();

    cfgProvider.value = cfg.llm_provider || "gemini";
    cfgModel.value = cfg.model || "gemini-2.5-flash";
    cfgBaseUrl.value = cfg.base_url || "";

    if (cfg.tts_voice) {
      cfgTtsVoice.value = cfg.tts_voice;
      selectedVoice = cfg.tts_voice;
      localStorage.setItem("roborabbit_voice", selectedVoice);
    }
    if (cfg.tts_rate) {
      cfgTtsRate.value = cfg.tts_rate;
      selectedRate = cfg.tts_rate;
      localStorage.setItem("roborabbit_rate", selectedRate);
    }
    if (cfg.tts_enabled !== undefined) {
      cfgTtsAutoSpeak.checked = cfg.tts_enabled;
    }

    if (cfg.llm_provider === "freellmapi") {
      apiKeyStatus.textContent = "⚡ Powered by FreeLLMAPI Fast Hybrid (Bridged to Antigravity on Laptop)";
      apiKeyStatus.className = "text-xs text-cyan-400 mt-1";
      providerIndicator.textContent = "RoboRabbit: FreeLLMAPI ⚡ AGY Bridge";
    } else if (cfg.llm_provider === "agy") {
      apiKeyStatus.textContent = "✨ Powered by Antigravity (AGY) on Laptop (No API key needed!)";
      apiKeyStatus.className = "text-xs text-cyan-400 mt-1";
      providerIndicator.textContent = "Brain: AGY (Laptop)";
    } else if (cfg.has_api_key) {
      apiKeyStatus.textContent = `Configured: ${cfg.api_key_masked} (enter new key to replace)`;
      apiKeyStatus.className = "text-xs text-emerald-400 mt-1";
      providerIndicator.textContent = `RoboRabbit: ${cfg.llm_provider.toUpperCase()} (${cfg.model})`;
    } else {
      apiKeyStatus.textContent = "No API key set (Running in Local OS Command Mode).";
      apiKeyStatus.className = "text-xs text-slate-500 mt-1";
      providerIndicator.textContent = "RoboRabbit: Local OS Mode";
    }
  } catch (e) {
    console.error(e);
  }
}

async function saveSettings() {
  const payload = {
    llm_provider: cfgProvider.value,
    model: cfgModel.value,
    base_url: cfgBaseUrl.value,
    tts_voice: cfgTtsVoice.value,
    tts_rate: cfgTtsRate.value,
    tts_enabled: cfgTtsAutoSpeak.checked
  };
  if (cfgApiKey.value.trim()) {
    payload.api_key = cfgApiKey.value.trim();
  }

  selectedVoice = cfgTtsVoice.value;
  selectedRate = cfgTtsRate.value;
  isAutoSpeak = cfgTtsAutoSpeak.checked;
  localStorage.setItem("roborabbit_voice", selectedVoice);
  localStorage.setItem("roborabbit_rate", selectedRate);
  localStorage.setItem("roborabbit_autospeak", isAutoSpeak);
  updateVoiceUI();

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      cfgApiKey.value = "";
      settingsModal.classList.add("hidden");
      loadConfig();
      alert("Settings saved successfully!");
    }
  } catch (e) {
    alert("Save failed: " + e.message);
  }
}

async function loadSessions() {
  try {
    const res = await fetch("/api/sessions");
    if (!res.ok) return;
    const list = await res.json();

    sessionsContainer.innerHTML = '<div class="text-xs font-semibold uppercase tracking-wider text-slate-500 px-2 py-1">Conversations</div>';

    list.forEach(s => {
      const btn = document.createElement("div");
      const isCurrent = s.id === currentSessionId;
      btn.className = `group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition ${
        isCurrent ? "bg-slate-800 text-white font-medium border border-slate-700/80" : "text-slate-400 hover:bg-slate-850 hover:text-slate-200"
      }`;
      btn.innerHTML = `
        <div class="flex items-center gap-2 truncate">
          <i data-lucide="message-square" class="w-3.5 h-3.5 shrink-0 text-cyan-400"></i>
          <span class="truncate">${s.title || "Conversation"}</span>
        </div>
        <button class="btn-del-session opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition" title="Delete chat">
          <i data-lucide="trash-2" class="w-3 h-3"></i>
        </button>
      `;

      btn.querySelector(".truncate").addEventListener("click", () => {
        stopSpeaking();
        currentSessionId = s.id;
        localStorage.setItem("roborabbit_session_id", currentSessionId);
        loadSessions();
        loadCurrentSessionMessages();
      });

      btn.querySelector(".btn-del-session").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (confirm("Delete this conversation?")) {
          stopSpeaking();
          await fetch(`/api/sessions/${s.id}`, { method: "DELETE" });
          if (currentSessionId === s.id) {
            createNewChat();
          } else {
            loadSessions();
          }
        }
      });

      sessionsContainer.appendChild(btn);
    });
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

async function loadCurrentSessionMessages() {
  if (!currentSessionId) return;
  try {
    const res = await fetch(`/api/sessions/${currentSessionId}`);
    if (!res.ok) return;
    const data = await res.json();
    const msgs = data.messages || [];

    messagesContainer.innerHTML = "";
    if (msgs.length === 0) {
      if (welcomeCard) {
        messagesContainer.appendChild(welcomeCard);
        welcomeCard.classList.remove("hidden");
      }
      return;
    }

    if (welcomeCard) welcomeCard.classList.add("hidden");

    msgs.forEach(m => {
      if (m.role === "user") {
        appendUserMessage(m.content);
      } else {
        appendAssistantMessage(m.content, m.tool_events);
      }
    });

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  } catch (e) {
    console.error(e);
  }
}

function appendUserMessage(text) {
  if (welcomeCard) welcomeCard.classList.add("hidden");
  const div = document.createElement("div");
  div.className = "flex justify-end";
  div.innerHTML = `
    <div class="max-w-[85%] rounded-2xl rounded-tr-sm bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-600 text-white px-4 py-2.5 text-sm shadow-md shadow-blue-900/20 whitespace-pre-wrap font-medium">
      ${escapeHtml(text)}
    </div>
  `;
  messagesContainer.appendChild(div);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendAssistantMessage(text, toolEvents = []) {
  const div = document.createElement("div");
  div.className = "flex gap-3 text-slate-100 max-w-[92%]";

  let toolHtml = "";
  if (toolEvents && toolEvents.length > 0) {
    toolEvents.forEach(evt => {
      toolHtml += renderToolCard(evt);
    });
  }

  const renderedContent = marked.parse(text || "");

  div.innerHTML = `
    <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shrink-0 shadow-md shadow-cyan-500/20 mt-1">
      <span class="text-base">🐰</span>
    </div>
    <div class="flex-1 space-y-2 overflow-hidden">
      ${toolHtml}
      <div class="markdown-body text-slate-200">
        ${renderedContent}
      </div>
      <div class="flex items-center gap-2 pt-1 border-t border-slate-800/60 mt-2">
        <button class="btn-speak-msg flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/60 text-slate-400 hover:text-cyan-300 transition text-[11px]" title="Play JARVIS Voice">
          <i data-lucide="volume-2" class="w-3.5 h-3.5 text-cyan-400"></i>
          <span>Speak</span>
        </button>
      </div>
    </div>
  `;

  const speakBtn = div.querySelector(".btn-speak-msg");
  if (speakBtn) {
    speakBtn.addEventListener("click", () => speakMessage(text, speakBtn));
  }

  messagesContainer.appendChild(div);
  lucide.createIcons();
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function renderToolCard(evt) {
  let hostLabel = "🖥️ Server";
  if (evt.host === "laptop1") hostLabel = "💻 Laptop";
  else if (evt.host === "phone") hostLabel = "📱 Mobile";
  else if (evt.host === "all") hostLabel = "🌐 All 3 Devices";

  const badgeColor = evt.exit_code === 0 ? "text-emerald-400 bg-emerald-950/80 border-emerald-800/80" : "text-red-400 bg-red-950/80 border-red-800/80";
  const output = evt.stdout ? evt.stdout : (evt.stderr ? `Error:\n${evt.stderr}` : "(Command executed with no output)");

  return `
    <div class="tool-card">
      <div class="p-2.5 px-3 flex items-center justify-between text-xs cursor-pointer select-none bg-slate-900/80 hover:bg-slate-850" onclick="this.nextElementSibling.classList.toggle('hidden')">
        <div class="flex items-center gap-2 truncate">
          <i data-lucide="terminal" class="w-3.5 h-3.5 text-cyan-400 shrink-0"></i>
          <span class="font-semibold text-slate-300">${hostLabel}:</span>
          <code class="text-cyan-300 font-mono truncate max-w-xs sm:max-w-md">$ ${escapeHtml(evt.command)}</code>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="text-[10px] text-slate-500">${evt.duration_ms || 0}ms</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full border ${badgeColor}">Exit ${evt.exit_code ?? 0}</span>
        </div>
      </div>
      <div class="terminal-box">
        <div class="flex justify-end pb-1">
          <button class="text-[10px] text-slate-400 hover:text-cyan-300 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700" onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.textContent); this.textContent='Copied!'">Copy</button>
        </div>
        <pre>${escapeHtml(output)}</pre>
      </div>
    </div>
  `;
}

// ==========================================
// SEND MESSAGE & STREAMING RESPONSE
// ==========================================

async function sendMessage() {
  if (isStreaming) return;
  let text = chatInput.value.trim();
  if (!text) return;

  stopSpeaking();
  if (speechRecognizer && isRecognizing) {
    try { speechRecognizer.abort(); } catch (e) {}
  }

  if (targetScope === "laptop1" && !text.toLowerCase().includes("laptop")) {
    text = `run on laptop: ${text}`;
  } else if (targetScope === "laptop2" && !text.toLowerCase().includes("server")) {
    text = `run on server: ${text}`;
  } else if (targetScope === "phone" && !text.toLowerCase().includes("mobile") && !text.toLowerCase().includes("phone")) {
    text = `run on mobile: ${text}`;
  }

  chatInput.value = "";
  chatInput.style.height = "auto";
  appendUserMessage(text);

  isStreaming = true;
  btnSend.disabled = true;

  const msgWrapper = document.createElement("div");
  msgWrapper.className = "flex gap-3 text-slate-100 max-w-[92%]";
  msgWrapper.innerHTML = `
    <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shrink-0 shadow-md shadow-cyan-500/20 mt-1">
      <span class="text-base">🐰</span>
    </div>
    <div class="flex-1 space-y-2 overflow-hidden">
      <div class="tools-stream-container"></div>
      <div class="markdown-body text-slate-200">
        <span class="inline-flex gap-1.5 items-center text-slate-500 text-xs">
          <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
          <span>RoboRabbit is calculating...</span>
        </span>
      </div>
      <div class="msg-footer-toolbar hidden flex items-center gap-2 pt-1 border-t border-slate-800/60 mt-2">
        <button class="btn-speak-msg flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/60 text-slate-400 hover:text-cyan-300 transition text-[11px]" title="Play JARVIS Voice">
          <i data-lucide="volume-2" class="w-3.5 h-3.5 text-cyan-400"></i>
          <span>Speak</span>
        </button>
      </div>
    </div>
  `;
  messagesContainer.appendChild(msgWrapper);
  lucide.createIcons();
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  const toolsStreamContainer = msgWrapper.querySelector(".tools-stream-container");
  const markdownBody = msgWrapper.querySelector(".markdown-body");
  const footerToolbar = msgWrapper.querySelector(".msg-footer-toolbar");
  const speakBtn = msgWrapper.querySelector(".btn-speak-msg");

  let fullContent = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: text
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const block of lines) {
        if (!block.startsWith("data: ")) continue;
        const dataStr = block.replace("data: ", "").trim();
        if (!dataStr) continue;

        try {
          const evt = JSON.parse(dataStr);
          if (evt.type === "tool_call") {
            const runningDiv = document.createElement("div");
            runningDiv.id = "running-tool-pill";
            runningDiv.className = "flex items-center gap-2 text-xs py-1 px-2.5 rounded-lg bg-cyan-950/80 border border-cyan-800 text-cyan-300 animate-pulse my-1.5";
            runningDiv.innerHTML = `
              <i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i>
              <span>Executing on ${evt.host || 'system'}: <code class="font-mono">${escapeHtml(evt.command)}</code></span>
            `;
            toolsStreamContainer.appendChild(runningDiv);
            lucide.createIcons();
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          } else if (evt.type === "tool_result") {
            const pill = document.getElementById("running-tool-pill");
            if (pill) pill.remove();
            const cardWrapper = document.createElement("div");
            cardWrapper.innerHTML = renderToolCard(evt);
            toolsStreamContainer.appendChild(cardWrapper.firstElementChild);
            lucide.createIcons();
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          } else if (evt.type === "content") {
            fullContent += evt.delta || "";
            markdownBody.innerHTML = marked.parse(fullContent);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          }
        } catch (err) {
          console.error("Error parsing SSE event:", err);
        }
      }
    }

    // Response finished streaming
    if (footerToolbar && fullContent) {
      footerToolbar.classList.remove("hidden");
      if (speakBtn) {
        speakBtn.addEventListener("click", () => speakMessage(fullContent, speakBtn));
      }
      lucide.createIcons();

      // Auto-speak if JARVIS Voice Mode or Wake Word is active
      if (isAutoSpeak || isWakeWordEnabled) {
        speakMessage(fullContent, speakBtn);
      }
    }

  } catch (err) {
    markdownBody.innerHTML += `<div class="text-red-400 text-xs mt-2">Error streaming response: ${err.message}</div>`;
  } finally {
    isStreaming = false;
    btnSend.disabled = false;
    chatInput.focus();
    loadSessions();
    pollDeviceStatus();
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ==========================================
// MARVEL JARVIS MANAGER HUBS & RADAR ENGINE
// ==========================================

let currentBriefingText = "";
let alarmAudioInterval = null;
let isKlaxonRinging = false;

async function pollManagerHubs() {
  try {
    // 1. Calendar
    fetch("/api/calendar")
      .then(r => r.json())
      .then(d => {
        const count = (d.today || []).length;
        if (badgeCalendarCount) badgeCalendarCount.textContent = count;
      }).catch(() => {});

    // 2. Emails
    fetch("/api/emails")
      .then(r => r.json())
      .then(d => {
        if (badgeEmailsCount) badgeEmailsCount.textContent = d.unread_count || 0;
      }).catch(() => {});

    // 3. Phone Notifications
    fetch("/api/notifications/phone")
      .then(r => r.json())
      .then(d => {
        if (badgePhoneNotifsCount) badgePhoneNotifsCount.textContent = d.unread_count || 0;
      }).catch(() => {});

    // 4. Alarms & Active Ringing
    fetch("/api/alarms")
      .then(r => r.json())
      .then(d => {
        const activeCount = (d.alarms || []).filter(a => a.status === "active").length;
        if (badgeAlarmsCount) badgeAlarmsCount.textContent = activeCount;

        const ringing = d.active_ringing || [];
        if (ringing.length > 0 && !isKlaxonRinging) {
          triggerAlarmOverlay(ringing[0]);
        }
      }).catch(() => {});

    // 5. Internet Intel News Ticker
    fetch("/api/internet/news?limit=1")
      .then(r => r.json())
      .then(d => {
        if (d.stories && d.stories.length > 0 && hudNewsHeadline) {
          hudNewsHeadline.textContent = d.stories[0].title;
        }
      }).catch(() => {});

  } catch (e) {
    console.warn("Poll manager error:", e);
  }
}

// ==========================================
// ALARM KLAXON AUDIO & OVERLAY
// ==========================================

function triggerAlarmOverlay(alarm) {
  isKlaxonRinging = true;
  if (alarmTriggerOverlay) {
    alarmTriggerOverlay.classList.remove("hidden");
    const labelEl = document.getElementById("alarm-trigger-label");
    const devEl = document.getElementById("alarm-trigger-device");
    if (labelEl) labelEl.textContent = alarm.label || "Timer Complete";
    if (devEl) devEl.textContent = `Triggered on: ${alarm.device || 'Server & Workstation'}`;
  }
  startAlarmKlaxon();
}

function startAlarmKlaxon() {
  if (alarmAudioInterval) clearInterval(alarmAudioInterval);
  playSingleKlaxonBeep();
  alarmAudioInterval = setInterval(playSingleKlaxonBeep, 1200);
}

function playSingleKlaxonBeep() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(440, now + 0.35);
    gain.gain.setValueAtTime(0.2, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.45);
  } catch (e) {}
}

function dismissActiveAlarmOverlay() {
  isKlaxonRinging = false;
  if (alarmAudioInterval) {
    clearInterval(alarmAudioInterval);
    alarmAudioInterval = null;
  }
  if (alarmTriggerOverlay) {
    alarmTriggerOverlay.classList.add("hidden");
  }
  fetch("/api/alarms/active/clear", { method: "POST" })
    .then(() => pollManagerHubs())
    .catch(() => {});
}

// ==========================================
// EXECUTIVE BRIEFING
// ==========================================

async function openBriefingModal() {
  if (!modalBriefing) return;
  modalBriefing.classList.remove("hidden");
  
  const greetingEl = document.getElementById("briefing-greeting");
  const timeTextEl = document.getElementById("briefing-time-text");
  const summaryEl = document.getElementById("briefing-summary-text");
  const calList = document.getElementById("briefing-calendar-list");
  const emailList = document.getElementById("briefing-emails-list");
  const phoneList = document.getElementById("briefing-phone-list");
  const newsText = document.getElementById("briefing-news-text");

  try {
    const res = await fetch("/api/briefing");
    const d = await res.json();

    if (greetingEl) greetingEl.textContent = d.greeting || "Good day, sir.";
    if (timeTextEl) timeTextEl.textContent = `${d.date || 'Today'} • ${d.time || ''}`;
    
    if (d.weather && d.weather.success) {
      const weatherBadge = document.getElementById("briefing-weather-badge");
      const weatherTemp = document.getElementById("briefing-weather-temp");
      if (weatherBadge) weatherBadge.classList.remove("hidden");
      if (weatherTemp) weatherTemp.textContent = `${d.weather.temperature_c}°C • ${d.weather.condition}`;
      if (summaryEl) summaryEl.textContent = `All systems nominal. ${d.weather.summary}`;
      currentBriefingText = `${d.greeting} The time is ${d.time}. Current weather is ${d.weather.summary}. You have ${(d.calendar_agenda.events || []).length} scheduled agenda items today, and ${d.emails.unread_count || 0} unread emails.`;
    } else {
      currentBriefingText = `${d.greeting} Current time is ${d.time}. You have ${(d.calendar_agenda.events || []).length} scheduled agenda items today, and ${d.emails.unread_count || 0} unread emails. Top intel headline: ${d.breaking_intel.top_story}`;
    }

    // Agenda List
    if (calList) {
      calList.innerHTML = "";
      const evts = d.calendar_agenda.events || [];
      if (evts.length === 0) {
        calList.innerHTML = `<div class="text-slate-500">No events scheduled for today.</div>`;
      } else {
        evts.forEach(e => {
          const item = document.createElement("div");
          item.className = "flex items-center justify-between p-2 rounded-lg bg-slate-800/60";
          item.innerHTML = `
            <span class="font-medium text-slate-200">${escapeHtml(e.title)}</span>
            <span class="text-cyan-400 font-mono text-[10px]">${e.start_time}</span>
          `;
          calList.appendChild(item);
        });
      }
    }

    // Emails List
    if (emailList) {
      emailList.innerHTML = "";
      const topMails = d.emails.top_unread || [];
      if (topMails.length === 0) {
        emailList.innerHTML = `<div class="text-slate-500">Inbox is clean. Zero unread emails.</div>`;
      } else {
        topMails.forEach(m => {
          const item = document.createElement("div");
          item.className = "p-2 rounded-lg bg-slate-800/60";
          item.innerHTML = `
            <div class="font-medium text-slate-200 truncate">${escapeHtml(m.subject)}</div>
            <div class="text-[10px] text-slate-400 truncate">From: ${escapeHtml(m.sender)}</div>
          `;
          emailList.appendChild(item);
        });
      }
    }

    // Phone Alerts
    if (phoneList) {
      phoneList.innerHTML = "";
      const notifs = d.phone_notifications.recent || [];
      if (notifs.length === 0) {
        phoneList.innerHTML = `<div class="text-slate-500">Zero phone alerts.</div>`;
      } else {
        notifs.forEach(n => {
          const item = document.createElement("div");
          item.className = "p-2 rounded-lg bg-slate-800/60 flex items-center justify-between";
          item.innerHTML = `
            <div class="truncate">
              <span class="font-semibold text-emerald-400">[${escapeHtml(n.app_name)}]</span>
              <span class="text-slate-300 ml-1">${escapeHtml(n.title)}</span>
            </div>
            <span class="text-[10px] text-slate-500 shrink-0 ml-2">${n.timestamp || ''}</span>
          `;
          phoneList.appendChild(item);
        });
      }
    }

    // News Text
    if (newsText) {
      newsText.textContent = `"${d.breaking_intel.top_story}"`;
    }

  } catch (e) {
    console.error("Error loading briefing:", e);
  }
}

function speakCurrentBriefing() {
  if (currentBriefingText) {
    speakMessage(currentBriefingText);
  } else {
    speakMessage("All systems are operational, sir. Your schedule and notifications are up to date.");
  }
}

// ==========================================
// CALENDAR & AGENDA
// ==========================================

async function openCalendarModal() {
  if (!modalCalendar) return;
  modalCalendar.classList.remove("hidden");
  loadCalendarEvents();
}

async function loadCalendarEvents() {
  const container = document.getElementById("calendar-events-container");
  if (!container) return;
  container.innerHTML = `<div class="text-slate-500 py-2">Loading schedule...</div>`;

  try {
    const res = await fetch("/api/calendar");
    const d = await res.json();
    const events = d.events || [];

    if (events.length === 0) {
      container.innerHTML = `<div class="text-slate-500 py-3 text-center">No upcoming events scheduled. Add one above!</div>`;
      return;
    }

    container.innerHTML = "";
    events.forEach(e => {
      const card = document.createElement("div");
      let catColor = "bg-blue-900/40 border-blue-700/60 text-blue-300";
      if (e.category === "meeting") catColor = "bg-amber-900/40 border-amber-700/60 text-amber-300";
      else if (e.category === "personal") catColor = "bg-emerald-900/40 border-emerald-700/60 text-emerald-300";
      else if (e.category === "system") catColor = "bg-cyan-900/40 border-cyan-700/60 text-cyan-300";

      card.className = "p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition";
      card.innerHTML = `
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="font-bold text-slate-100 text-xs">${escapeHtml(e.title)}</span>
            <span class="text-[9px] px-2 py-0.5 rounded-full border uppercase font-mono ${catColor}">${e.category}</span>
          </div>
          <div class="text-[11px] text-slate-400 flex items-center gap-2">
            <span>📅 ${e.date || 'Today'}</span>
            <span>⏰ ${e.start_time}${e.end_time ? ' - ' + e.end_time : ''}</span>
          </div>
          ${e.description ? `<div class="text-[10px] text-slate-500">${escapeHtml(e.description)}</div>` : ''}
        </div>
        <button class="btn-del-event p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-800 transition" title="Delete event">
          <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
        </button>
      `;

      card.querySelector(".btn-del-event").addEventListener("click", () => handleDeleteCalendarEvent(e.id));
      container.appendChild(card);
    });
    lucide.createIcons();
  } catch (err) {
    container.innerHTML = `<div class="text-red-400 py-2">Error loading calendar: ${err.message}</div>`;
  }
}

async function handleAddCalendarEvent() {
  const titleInput = document.getElementById("input-event-title");
  const timeInput = document.getElementById("input-event-time");
  const catInput = document.getElementById("input-event-cat");
  
  const title = titleInput.value.trim();
  const start_time = timeInput.value.trim() || "14:00";
  const category = catInput.value || "work";

  if (!title) {
    alert("Please enter an event title.");
    return;
  }

  await fetch("/api/calendar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, start_time, category })
  });

  titleInput.value = "";
  loadCalendarEvents();
  pollManagerHubs();
}

async function handleDeleteCalendarEvent(id) {
  if (confirm("Delete this event?")) {
    await fetch(`/api/calendar/${id}`, { method: "DELETE" });
    loadCalendarEvents();
    pollManagerHubs();
  }
}

// ==========================================
// ALARMS & TIMERS
// ==========================================

let alarmsCountdownInterval = null;

async function openAlarmsModal() {
  if (!modalAlarms) return;
  modalAlarms.classList.remove("hidden");
  loadAlarmsList();
  if (alarmsCountdownInterval) clearInterval(alarmsCountdownInterval);
  alarmsCountdownInterval = setInterval(updateActiveTimerCountdowns, 1000);
}

function updateActiveTimerCountdowns() {
  const timerElements = document.querySelectorAll("[data-trigger-ts]");
  const now = Date.now() / 1000;
  timerElements.forEach(el => {
    const ts = parseFloat(el.getAttribute("data-trigger-ts"));
    if (ts) {
      const remaining = Math.max(0, Math.floor(ts - now));
      const mins = Math.floor(remaining / 60);
      const secs = remaining % 60;
      el.textContent = `⏱️ ${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')} remaining`;
      if (remaining <= 0) {
        el.textContent = "🔔 Complete!";
        el.className = "text-amber-400 font-mono font-bold animate-pulse";
      }
    }
  });
}

async function loadAlarmsList() {
  const container = document.getElementById("alarms-container");
  if (!container) return;
  container.innerHTML = `<div class="text-slate-500 py-2">Loading active alerts...</div>`;

  try {
    const res = await fetch("/api/alarms");
    const d = await res.json();
    const alarms = d.alarms || [];

    if (alarms.length === 0) {
      container.innerHTML = `<div class="text-slate-500 py-3 text-center">No active alarms or timers. Set one above!</div>`;
      return;
    }

    container.innerHTML = "";
    alarms.forEach(a => {
      const card = document.createElement("div");
      const isTimer = a.duration_seconds > 0;
      const statusColor = a.status === "active" ? "text-emerald-400 border-emerald-800" : "text-slate-500 border-slate-800";

      let countdownSpan = "";
      if (isTimer && a.status === "active" && a.trigger_timestamp) {
        const remaining = Math.max(0, Math.floor(a.trigger_timestamp - Date.now() / 1000));
        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        countdownSpan = `<span class="text-cyan-300 font-mono font-medium" data-trigger-ts="${a.trigger_timestamp}">⏱️ ${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')} remaining</span>`;
      } else if (isTimer) {
        countdownSpan = `<span>⏰ ${Math.round(a.duration_seconds / 60)} min timer</span>`;
      } else {
        countdownSpan = `<span>⏰ ${a.time_str || 'Scheduled'}</span>`;
      }

      card.className = "p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between";
      card.innerHTML = `
        <div class="space-y-0.5">
          <div class="flex items-center gap-2">
            <span class="font-bold text-slate-100">${escapeHtml(a.label)}</span>
            <span class="text-[9px] px-2 py-0.5 rounded-full border ${statusColor} uppercase font-mono">${a.status}</span>
          </div>
          <div class="text-[11px] text-slate-400 flex items-center gap-2">
            ${countdownSpan}
            <span>📱 ${a.device}</span>
          </div>
        </div>
        <button class="btn-del-alarm p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-800 transition" title="Delete alarm">
          <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
        </button>
      `;

      card.querySelector(".btn-del-alarm").addEventListener("click", () => handleDeleteAlarm(a.id));
      container.appendChild(card);
    });
    lucide.createIcons();
  } catch (err) {
    container.innerHTML = `<div class="text-red-400 py-2">Error: ${err.message}</div>`;
  }
}

async function handlePresetTimer(seconds) {
  const mins = Math.round(seconds / 60);
  await fetch("/api/alarms", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      label: `${mins} Minute Timer`,
      duration_seconds: seconds,
      device: "laptop2"
    })
  });
  playNotificationSound();
  loadAlarmsList();
  pollManagerHubs();
}

async function handleAddCustomAlarm() {
  const labelInput = document.getElementById("input-alarm-label");
  const timeInput = document.getElementById("input-alarm-time");
  const devSelect = document.getElementById("input-alarm-device");

  const label = labelInput.value.trim() || "Daily Alarm";
  const time_str = timeInput.value.trim() || "07:30";
  const device = devSelect.value || "laptop2";

  await fetch("/api/alarms", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, time_str, device })
  });

  labelInput.value = "";
  playNotificationSound();
  loadAlarmsList();
  pollManagerHubs();
}

async function handleDeleteAlarm(id) {
  if (confirm("Delete this alarm?")) {
    await fetch(`/api/alarms/${id}`, { method: "DELETE" });
    loadAlarmsList();
    pollManagerHubs();
  }
}

// ==========================================
// EXECUTIVE MAILBOX HUB & GMAIL SYNC
// ==========================================

async function loadGmailStatus() {
  const lbl = document.getElementById("gmail-status-label");
  const emailInput = document.getElementById("input-gmail-address");
  try {
    const res = await fetch("/api/gmail/config");
    const d = await res.json();
    if (d.configured) {
      if (lbl) lbl.innerHTML = `<span class="text-emerald-400 font-semibold">Linked: ${escapeHtml(d.gmail_user)}</span>`;
      if (emailInput && !emailInput.value) emailInput.value = d.gmail_user;
    } else {
      if (lbl) lbl.innerHTML = `<span class="text-slate-400">Status: Not connected</span>`;
    }
  } catch (e) {}
}

async function handleSaveGmailConfig() {
  const email = document.getElementById("input-gmail-address")?.value.trim();
  const pass = document.getElementById("input-gmail-app-pass")?.value.trim();
  if (!email || !pass) {
    alert("Please enter both your Gmail address and 16-character Google App Password.");
    return;
  }
  try {
    const res = await fetch("/api/gmail/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_email: email, app_password: pass })
    });
    const d = await res.json();
    if (d.success) {
      alert("Gmail credentials saved! Click 'Sync Gmail Now' to fetch unread emails.");
      loadGmailStatus();
    }
  } catch (err) {
    alert("Save error: " + err.message);
  }
}

async function handleSyncGmailNow() {
  const btn = document.getElementById("btn-sync-gmail-now");
  if (btn) btn.classList.add("animate-pulse");
  try {
    const res = await fetch("/api/gmail/sync", { method: "POST" });
    const d = await res.json();
    if (d.success) {
      alert(d.message || "Gmail synced successfully!");
      loadEmailsList("inbox");
      pollManagerHubs();
    } else {
      alert("Gmail sync error: " + (d.error || "Check credentials"));
    }
  } catch (err) {
    alert("Sync error: " + err.message);
  } finally {
    if (btn) btn.classList.remove("animate-pulse");
  }
}

async function openEmailsModal() {
  if (!modalEmails) return;
  modalEmails.classList.remove("hidden");
  loadGmailStatus();
  loadEmailsList("inbox");
}

async function loadEmailsList(folder = "inbox") {
  const container = document.getElementById("emails-container");
  if (!container) return;
  container.innerHTML = `<div class="text-slate-500 py-2">Loading mailbox messages...</div>`;

  try {
    const res = await fetch(`/api/emails?folder=${folder}`);
    const d = await res.json();
    const emails = d.emails || [];

    if (emails.length === 0) {
      container.innerHTML = `<div class="text-slate-500 py-3 text-center">No messages in ${folder}.</div>`;
      return;
    }

    container.innerHTML = "";
    emails.forEach(m => {
      const card = document.createElement("div");
      const isUnread = m.is_read === 0;

      card.className = `p-3 rounded-xl border transition cursor-pointer ${
        isUnread ? "bg-slate-850 border-cyan-800/80 shadow-sm shadow-cyan-900/10" : "bg-slate-900 border-slate-800 hover:border-slate-700"
      }`;

      card.innerHTML = `
        <div class="flex items-center justify-between pb-1">
          <div class="flex items-center gap-2">
            ${isUnread ? '<span class="w-2 h-2 rounded-full bg-cyan-400"></span>' : ''}
            <span class="font-bold text-slate-100 text-xs">${escapeHtml(m.sender)}</span>
          </div>
          <span class="text-[10px] text-slate-500">${m.received_at || ''}</span>
        </div>
        <div class="font-medium text-slate-200 text-xs truncate">${escapeHtml(m.subject)}</div>
        <div class="text-[11px] text-slate-400 line-clamp-2 mt-1">${escapeHtml(m.body)}</div>
      `;

      card.addEventListener("click", () => {
        // Expand or view email
        alert(`Subject: ${m.subject}\nFrom: ${m.sender} <${m.sender_email}>\nDate: ${m.received_at}\n\n${m.body}`);
        fetch(`/api/emails/${m.id}/read`, { method: "POST" }).then(() => {
          loadEmailsList(folder);
          pollManagerHubs();
        });
      });

      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<div class="text-red-400 py-2">Error: ${err.message}</div>`;
  }
}

async function handleSendEmail() {
  const toInput = document.getElementById("input-mail-to");
  const subjInput = document.getElementById("input-mail-subject");
  const bodyInput = document.getElementById("input-mail-body");

  const to = toInput.value.trim();
  const subject = subjInput.value.trim();
  const body = bodyInput.value.trim();

  if (!to || !subject) {
    alert("Please fill in recipient and subject.");
    return;
  }

  await fetch("/api/emails", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to, subject, body })
  });

  toInput.value = "";
  subjInput.value = "";
  bodyInput.value = "";
  document.getElementById("compose-email-drawer").classList.add("hidden");
  alert("Message sent successfully!");
  loadEmailsList("inbox");
  pollManagerHubs();
}

// ==========================================
// ANDROID PHONE HUB
// ==========================================

async function openPhoneHubModal() {
  if (!modalPhoneHub) return;
  modalPhoneHub.classList.remove("hidden");
  loadPhoneNotifs();
}

async function loadPhoneNotifs() {
  const container = document.getElementById("phone-notifs-container");
  if (!container) return;
  container.innerHTML = `<div class="text-slate-500 py-2">Loading notifications...</div>`;

  try {
    const res = await fetch("/api/notifications/phone");
    const d = await res.json();
    const notifs = d.notifications || [];

    if (notifs.length === 0) {
      container.innerHTML = `<div class="text-slate-500 py-3 text-center">No notifications on phone. Sync via ADB above!</div>`;
      return;
    }

    container.innerHTML = "";
    notifs.forEach(n => {
      const card = document.createElement("div");
      card.className = "p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-start justify-between";
      card.innerHTML = `
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-emerald-400">[${escapeHtml(n.app_name)}]</span>
            <span class="font-medium text-slate-200 text-xs">${escapeHtml(n.title)}</span>
          </div>
          <div class="text-[11px] text-slate-300">${escapeHtml(n.content)}</div>
        </div>
        <span class="text-[10px] text-slate-500 shrink-0 ml-2">${n.timestamp || ''}</span>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<div class="text-red-400 py-2">Error: ${err.message}</div>`;
  }
}

async function handleSyncPhoneNotifs() {
  const btn = document.getElementById("btn-sync-phone-notifs");
  if (btn) btn.classList.add("animate-pulse");
  await fetch("/api/notifications/phone/sync", { method: "POST" });
  if (btn) btn.classList.remove("animate-pulse");
  loadPhoneNotifs();
  pollManagerHubs();
}

async function handlePushTestAlert() {
  await fetch("/api/notifications/phone/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      app_name: "RoboRabbit",
      title: "Executive Alert",
      content: "All systems nominal. Neural bridge synced across 3 nodes."
    })
  });
  playNotificationSound();
  loadPhoneNotifs();
  pollManagerHubs();
}

async function handleClearPhoneNotifs() {
  if (confirm("Clear all phone notifications?")) {
    await fetch("/api/notifications/phone", { method: "DELETE" });
    loadPhoneNotifs();
    pollManagerHubs();
  }
}

async function handlePhoneQuickOpenUrl() {
  const url = prompt("Enter URL to open on your phone:", "https://google.com");
  if (url) {
    chatInput.value = `open URL on phone: ${url}`;
    modalPhoneHub.classList.add("hidden");
    sendMessage();
  }
}

// ==========================================
// INTERNET NEWS RADAR
// ==========================================

async function openNewsModal(category = "all") {
  if (!modalNews) return;
  modalNews.classList.remove("hidden");
  loadNewsStories(category);
}

async function loadNewsStories(category = "all") {
  const container = document.getElementById("news-articles-container");
  if (!container) return;
  container.innerHTML = `<div class="text-slate-500 py-2">Scanning global news networks...</div>`;

  try {
    const res = await fetch(`/api/internet/news?category=${category}&limit=8`);
    const d = await res.json();
    const stories = d.stories || [];

    if (stories.length === 0) {
      container.innerHTML = `<div class="text-slate-500 py-3 text-center">No news stories found for ${category}.</div>`;
      return;
    }

    container.innerHTML = "";
    stories.forEach(s => {
      const card = document.createElement("div");
      card.className = "p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-800/80 transition space-y-2";
      card.innerHTML = `
        <div class="flex items-center justify-between text-[11px] text-slate-400">
          <span class="font-bold text-cyan-400 uppercase tracking-wider text-[10px]">${escapeHtml(s.source || 'News')}</span>
          <span>${s.published ? s.published.split(' ').slice(0, 4).join(' ') : ''}</span>
        </div>
        <div class="font-semibold text-slate-100 text-xs leading-snug">${escapeHtml(s.title)}</div>
        <div class="pt-1 flex items-center justify-between">
          <a href="${s.link}" target="_blank" class="text-[11px] text-slate-400 hover:text-cyan-300 flex items-center gap-1 transition">
            <span>Read full story</span>
            <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
          <button class="btn-summarize-news text-[11px] px-2.5 py-1 rounded-lg bg-cyan-950/70 hover:bg-cyan-900/90 border border-cyan-700/60 text-cyan-300 font-medium transition flex items-center gap-1">
            <i data-lucide="sparkles" class="w-3 h-3 text-cyan-400"></i>
            <span>Summarize with Robo</span>
          </button>
        </div>
      `;

      card.querySelector(".btn-summarize-news").addEventListener("click", () => {
        modalNews.classList.add("hidden");
        chatInput.value = `Robo, what's going on with this story: "${s.title}"`;
        sendMessage();
      });

      container.appendChild(card);
    });
    lucide.createIcons();
  } catch (err) {
    container.innerHTML = `<div class="text-red-400 py-2">Error scanning news: ${err.message}</div>`;
  }
}

// ==========================================
// SCEMPYY // CYBER COMMAND MATRIX RAIN & TELEMETRY
// ==========================================

function initCyberTelemetry() {
  const liveUtcEl = document.getElementById("live-utc");
  function updateUtc() {
    if (liveUtcEl) {
      const now = new Date();
      const h = String(now.getUTCHours()).padStart(2, '0');
      const m = String(now.getUTCMinutes()).padStart(2, '0');
      const s = String(now.getUTCSeconds()).padStart(2, '0');
      liveUtcEl.textContent = `${h}:${m}:${s} UTC`;
    }
  }
  updateUtc();
  setInterval(updateUtc, 1000);

  // Matrix Rain Engine (from scempyy.me)
  const matrixCanvas = document.getElementById("matrix-canvas");
  const btnToggleMatrix = document.getElementById("btn-toggle-matrix");
  if (!matrixCanvas) return;

  const mctx = matrixCanvas.getContext("2d");
  const chars = "0123456789ABCDEFｦｱｳｴｵｶｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ";
  let drops = [];
  let fontSize = 14;
  let matrixRunning = false;
  let matrixInterval = null;

  function resizeMatrix() {
    matrixCanvas.width = window.innerWidth;
    matrixCanvas.height = window.innerHeight;
    const cols = Math.floor(matrixCanvas.width / fontSize);
    drops = Array(cols).fill(1);
  }
  window.addEventListener("resize", resizeMatrix);
  resizeMatrix();

  function drawMatrix() {
    mctx.fillStyle = "rgba(3, 7, 11, 0.08)";
    mctx.fillRect(0, 0, matrixCanvas.width, matrixCanvas.height);
    mctx.fillStyle = "#00ff73";
    mctx.font = `${fontSize}px monospace`;

    for (let i = 0; i < drops.length; i++) {
      const text = chars.charAt(Math.floor(Math.random() * chars.length));
      mctx.fillText(text, i * fontSize, drops[i] * fontSize);

      if (drops[i] * fontSize > matrixCanvas.height && Math.random() > 0.975) {
        drops[i] = 0;
      }
      drops[i]++;
    }
  }

  if (btnToggleMatrix) {
    btnToggleMatrix.addEventListener("click", () => {
      matrixRunning = !matrixRunning;
      document.body.classList.toggle("matrix-active", matrixRunning);
      btnToggleMatrix.classList.toggle("active", matrixRunning);
      playHudClickSound();

      if (matrixRunning) {
        if (!matrixInterval) matrixInterval = setInterval(drawMatrix, 35);
      } else {
        if (matrixInterval) {
          clearInterval(matrixInterval);
          matrixInterval = null;
        }
        mctx.clearRect(0, 0, matrixCanvas.width, matrixCanvas.height);
      }
    });
  }
}

// ==========================================
// CLIENT-SIDE MOBILE COMMAND RECEIVER (Zero-ADB Persistent Bridge)
// ==========================================

function initMobileClientBridge() {
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

  // 1. Report battery and device telemetry if on mobile
  if (isMobile && navigator.getBattery) {
    navigator.getBattery().then(bat => {
      function sendBat() {
        fetch("/api/phone/telemetry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            battery: `${Math.round(bat.level * 100)}%${bat.charging ? ' (Charging)' : ''}`,
            model: navigator.userAgent.includes("V2437") ? "Vivo V2437" : "Android Device"
          })
        }).catch(() => {});
      }
      sendBat();
      bat.addEventListener("levelchange", sendBat);
      bat.addEventListener("chargingchange", sendBat);
    }).catch(() => {});
  }

  // 2. Poll for queued actions (e.g. Open YouTube, Launch App, Alert)
  async function pollMobileActions() {
    try {
      const res = await fetch("/api/phone/poll");
      if (!res.ok) return;
      const data = await res.json();
      const cmds = data.commands || [];
      for (const c of cmds) {
        if (c.action === "open_url" && c.url) {
          playSuccessChime();
          // Visual toast banner
          showListeningPill(`🚀 Launching: ${c.url}`);
          setTimeout(hideListeningPill, 3000);
          // Open URL / native app
          const opened = window.open(c.url, "_blank");
          if (!opened) {
            window.location.href = c.url;
          }
        }
      }
    } catch (e) {}
  }

  // Poll mobile actions every 2.5s
  setInterval(pollMobileActions, 2500);
}

// ==========================================
// DIRECT PHONE COMMAND DISPATCHER
// ==========================================

async function dispatchPhoneCommand(action, payload = {}) {
  try {
    playHudClickSound();
    const res = await fetch("/api/phone/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, ...payload })
    });
    if (res.ok) {
      playSuccessChime();
      showListeningPill(`⚡ Phone: ${action.toUpperCase()} dispatched`);
      setTimeout(hideListeningPill, 2500);
    }
  } catch (e) {
    console.error("Phone command dispatch error:", e);
  }
}

// ==========================================
// SCEMPYY // INTERACTIVE CONSTELLATION GRID (scempyy.me)
// ==========================================

function initCyberCanvas() {
  const canvas = document.getElementById("cyber-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let width, height;
  let particles = [];
  const particleCount = window.innerWidth < 768 ? 40 : 80;
  const mouse = { x: null, y: null, radius: 140 };

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  window.addEventListener("mouseout", () => {
    mouse.x = null;
    mouse.y = null;
  });

  class Particle {
    constructor() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * 0.6;
      this.vy = (Math.random() - 0.5) * 0.6;
      this.radius = Math.random() * 1.5 + 1;
      this.baseColor = Math.random() > 0.85 ? "#f59e0b" : "#00f0ff";
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < 0 || this.x > width) this.vx *= -1;
      if (this.y < 0 || this.y > height) this.vy *= -1;

      if (mouse.x !== null && mouse.y !== null) {
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.radius) {
          const force = (mouse.radius - dist) / mouse.radius;
          const fx = (dx / dist) * force * 1.2;
          const fy = (dy / dist) * force * 1.2;
          this.x -= fx;
          this.y -= fy;
        }
      }
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = this.baseColor;
      ctx.shadowBlur = 8;
      ctx.shadowColor = this.baseColor;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle());
  }

  function connectParticles() {
    const maxDist = 120;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist) {
          const alpha = (1 - dist / maxDist) * 0.22;
          ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }

      if (mouse.x !== null && mouse.y !== null) {
        const dx = mouse.x - particles[i].x;
        const dy = mouse.y - particles[i].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.radius) {
          const alpha = (1 - dist / mouse.radius) * 0.45;
          ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);
    for (let p of particles) {
      p.update();
      p.draw();
    }
    connectParticles();
    requestAnimationFrame(animate);
  }
  animate();
}

// ==========================================
// ARC REACTOR HOLOGRAPHIC WAVEFORM
// ==========================================

function initArcWaveformVisualizer() {
  const canvas = document.getElementById("arc-waveform-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  const cx = w / 2;
  const cy = h / 2;
  const radius = 24;
  let phase = 0;

  function draw() {
    ctx.clearRect(0, 0, w, h);
    phase += 0.05;

    const speaking = isAudioSpeaking || (currentAudio && !currentAudio.paused);
    const bars = 24;

    for (let i = 0; i < bars; i++) {
      const angle = (i / bars) * Math.PI * 2;
      let barLen = 2;

      if (speaking) {
        const wave = Math.sin(phase * 4 + i * 0.8) * Math.cos(phase * 2 + i * 0.4);
        barLen = 3 + Math.abs(wave) * 7;
      } else {
        barLen = 1.5 + Math.sin(phase + i * 0.5) * 1.5;
      }

      const x1 = cx + Math.cos(angle) * (radius - 1);
      const y1 = cy + Math.sin(angle) * (radius - 1);
      const x2 = cx + Math.cos(angle) * (radius + barLen);
      const y2 = cy + Math.sin(angle) * (radius + barLen);

      ctx.strokeStyle = speaking ? "rgba(0, 240, 255, 0.9)" : "rgba(0, 240, 255, 0.35)";
      ctx.lineWidth = speaking ? 1.5 : 1;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }

    requestAnimationFrame(draw);
  }
  draw();
}

// ==========================================
// SCEMPYY // CYBER COMMAND CLI TERMINAL MODAL
// ==========================================

function initCyberCLI() {
  const modal = document.getElementById("modal-cyber-terminal");
  const btnToggle = document.getElementById("btn-toggle-cli");
  const btnClose = document.getElementById("btn-close-terminal");
  const btnDotClose = document.getElementById("btn-terminal-dot-close");
  const input = document.getElementById("terminal-input");
  const output = document.getElementById("terminal-output-container");
  const terminalBody = document.getElementById("terminal-body");

  if (!modal || !input) return;

  const history = [];
  let historyIdx = -1;

  function toggleTerminal(show) {
    playHudClickSound();
    const shouldShow = show !== undefined ? show : modal.classList.contains("hidden");
    if (shouldShow) {
      modal.classList.remove("hidden");
      input.focus();
    } else {
      modal.classList.add("hidden");
    }
  }

  if (btnToggle) btnToggle.addEventListener("click", () => toggleTerminal());
  if (btnClose) btnClose.addEventListener("click", () => toggleTerminal(false));
  if (btnDotClose) btnDotClose.addEventListener("click", () => toggleTerminal(false));

  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey && e.code === "Backquote") || (e.key === "\\" && document.activeElement !== chatInput && document.activeElement !== input)) {
      e.preventDefault();
      toggleTerminal();
    }
    if (e.key === "Escape" && !modal.classList.contains("hidden")) {
      toggleTerminal(false);
    }
  });

  function appendLine(html, type = "normal") {
    const line = document.createElement("div");
    line.className = "mb-1 text-xs " + (type === "cmd" ? "text-slate-300 font-bold" : type === "error" ? "text-rose-400" : type === "success" ? "text-emerald-400" : "text-sky-300");
    line.innerHTML = html;
    output.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  async function executeCli(cmdStr) {
    const trimmed = cmdStr.trim();
    if (!trimmed) return;

    history.push(trimmed);
    historyIdx = history.length;

    appendLine(`<span class="text-emerald-400 select-none">scempyy@roborabbit:~$</span> ${escapeHtml(trimmed)}`, "cmd");
    input.value = "";

    const parts = trimmed.split(" ");
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1).join(" ");

    switch (cmd) {
      case "help":
        appendLine(`
AVAILABLE PROTOCOLS:<br>
&nbsp;&nbsp;<span class="text-amber-400">devices</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Query active network topology (Phone, Laptop, Server)<br>
&nbsp;&nbsp;<span class="text-amber-400">status</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Real-time multi-node diagnostic<br>
&nbsp;&nbsp;<span class="text-amber-400">briefing</span>&nbsp;&nbsp;&nbsp;&nbsp;- Trigger JARVIS executive briefing report<br>
&nbsp;&nbsp;<span class="text-amber-400">calendar</span>&nbsp;&nbsp;&nbsp;&nbsp;- Display scheduled agenda and meetings<br>
&nbsp;&nbsp;<span class="text-amber-400">alarms</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Display active alarms and countdown timers<br>
&nbsp;&nbsp;<span class="text-amber-400">news</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Fetch top internet intelligence radar<br>
&nbsp;&nbsp;<span class="text-amber-400">youtube</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Launch YouTube search on mobile/server (e.g. youtube lofi beats)<br>
&nbsp;&nbsp;<span class="text-amber-400">vibrate</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Trigger tactile haptic pulse on phone<br>
&nbsp;&nbsp;<span class="text-amber-400">ping</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Measure server round-trip latency<br>
&nbsp;&nbsp;<span class="text-amber-400">matrix</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Toggle Scempyy digital rain background<br>
&nbsp;&nbsp;<span class="text-amber-400">clear</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Wipe terminal buffer<br>
&nbsp;&nbsp;<span class="text-cyan-400">&lt;query&gt;</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Transmit direct AI inquiry to Roborabbit core
        `);
        break;

      case "devices":
        // CRITICAL SYSTEM RULE: Must answer directly:
        appendLine("We are connected to 3 devices: your phone, your main laptop, and this server.", "success");
        break;

      case "status":
        appendLine("<span class='text-slate-400'>Querying cluster telemetry...</span>");
        try {
          const res = await fetch("/api/status");
          const d = await res.json();
          appendLine(`
NODE TOPOLOGY REPORT:<br>
&nbsp;&nbsp;[📱 YOUR PHONE]&nbsp;&nbsp;&nbsp;: <span class="text-emerald-400">${d.phone?.online ? 'ONLINE' : 'CONNECTED'}</span> • Battery: ${d.phone?.battery || 'Active'} • Role: ${d.phone?.role || 'Android Device'}<br>
&nbsp;&nbsp;[💻 MAIN LAPTOP]&nbsp;&nbsp;: <span class="${d.laptop1?.online ? 'text-emerald-400' : 'text-slate-500'}">${d.laptop1?.online ? 'ONLINE' : 'SUSPENDED/OFFLINE'}</span> • IP: ${d.laptop1?.ip || '192.168.1.12'}<br>
&nbsp;&nbsp;[🖥️ THIS SERVER]&nbsp;&nbsp;: <span class="text-emerald-400">ONLINE</span> • 24/7 Arch Linux Node • Port 7777 • Uptime: ${d.laptop2?.uptime || 'Active'}
          `, "success");
        } catch (e) {
          appendLine("Failed to retrieve node telemetry.", "error");
        }
        break;

      case "briefing":
        appendLine("Initiating JARVIS executive briefing sequence...", "success");
        if (btnHudBriefing) btnHudBriefing.click();
        break;

      case "calendar":
        try {
          const res = await fetch("/api/manager/calendar");
          const d = await res.json();
          const items = d.events || [];
          let out = `TODAY'S SCHEDULE (${items.length} items):<br>`;
          items.forEach(ev => {
            out += `&nbsp;&nbsp;• <span class="text-amber-300 font-bold">${ev.time}</span> - ${escapeHtml(ev.title)} (${ev.category})<br>`;
          });
          appendLine(out);
        } catch (e) {
          appendLine("Calendar protocol unavailable.", "error");
        }
        break;

      case "alarms":
        try {
          const res = await fetch("/api/manager/alarms");
          const d = await res.json();
          const alarms = d.alarms || [];
          let out = `ACTIVE ALARMS & TIMERS (${alarms.length}):<br>`;
          alarms.forEach(a => {
            out += `&nbsp;&nbsp;• [${a.type.toUpperCase()}] <span class="text-rose-400 font-bold">${a.time}</span> - ${escapeHtml(a.label)} (${a.device})<br>`;
          });
          appendLine(out);
        } catch (e) {
          appendLine("Alarms protocol unavailable.", "error");
        }
        break;

      case "news":
        try {
          const res = await fetch("/api/internet/news?limit=4");
          const d = await res.json();
          const stories = d.stories || [];
          let out = "GLOBAL INTELLIGENCE RADAR:<br>";
          stories.forEach(s => {
            out += `&nbsp;&nbsp;⚡ <a href="${s.url}" target="_blank" class="text-cyan-400 underline hover:text-white">${escapeHtml(s.title)}</a> (${s.source})<br>`;
          });
          appendLine(out);
        } catch (e) {
          appendLine("News feed offline.", "error");
        }
        break;

      case "youtube":
        const query = args || "lofi hip hop radio";
        const ytUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
        appendLine(`Dispatching YouTube intent: <span class="text-amber-300">${escapeHtml(query)}</span> to phone bridge...`, "success");
        fetch("/api/phone/command", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "open_url", url: ytUrl })
        }).catch(() => {});
        break;

      case "vibrate":
        appendLine("Sending haptic pulse to phone...", "success");
        fetch("/api/phone/command", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "vibrate" })
        }).catch(() => {});
        break;

      case "ping":
        const t0 = performance.now();
        try {
          await fetch("/api/health");
          const t1 = performance.now();
          appendLine(`Pong! 192.168.1.22 round-trip latency: <span class="text-emerald-400 font-bold">${(t1 - t0).toFixed(1)} ms</span>`, "success");
        } catch (e) {
          appendLine("Ping request timed out.", "error");
        }
        break;

      case "matrix":
        const btnM = document.getElementById("btn-toggle-matrix");
        if (btnM) btnM.click();
        appendLine("Toggled Scempyy Digital Matrix Rain layer.", "success");
        break;

      case "clear":
        output.innerHTML = "";
        break;

      default:
        appendLine(`Transmitting to Roborabbit core: <span class="text-cyan-300">"${escapeHtml(trimmed)}"</span>...`);
        chatInput.value = trimmed;
        toggleTerminal(false);
        sendMessage();
        break;
    }
  }

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      executeCli(input.value);
    } else if (e.key === "ArrowUp") {
      if (history.length > 0 && historyIdx > 0) {
        historyIdx--;
        input.value = history[historyIdx];
      }
    } else if (e.key === "ArrowDown") {
      if (history.length > 0 && historyIdx < history.length - 1) {
        historyIdx++;
        input.value = history[historyIdx];
      } else {
        historyIdx = history.length;
        input.value = "";
      }
    }
  });
}

