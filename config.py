import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "roborabbit"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "name": "Roborabbit",
    "llm_provider": "freellmapi",  # freellmapi (Fast hybrid bridged to AGY), agy, gemini, openai, groq, openrouter
    "freellmapi_url": "http://192.168.1.12:3001/v1",
    "freellmapi_key": "freellmapi-627e458e66146c36fb6c5ba007b12f4babe8de3031ba8e99",
    "freellmapi_model": "auto",
    "api_key": os.environ.get("GEMINI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
    "model": "gemini-2.5-flash",
    "base_url": "",
    "laptop1_host": "main-laptop",
    "laptop1_ip": "192.168.1.12",
    "laptop1_name": "Laptop",
    "laptop2_name": "Server",
    "phone_name": "Mobile",
    "laptop2_ip": "192.168.1.23",
    "laptop1_mac": "74:d4:dd:75:45:10",
    "phone_ip": "192.168.1.14",
    "phone_port": 5555,
    "port": 7777,
    "tts_voice": "en-GB-RyanNeural",
    "tts_rate": "+0%",
    "tts_pitch": "+0Hz",
    "tts_enabled": True,
    "system_prompt": (
        "You are Roborabbit, an intelligent, concise personal AI manager and assistant inspired by Marvel's JARVIS. "
        "All your responses are synthesized and spoken aloud via Text-to-Speech: always keep your replies short, clean, direct, and conversational (1 to 2 sentences maximum). "
        "When asked how many devices are connected or what devices are connected, you MUST directly answer: "
        "'We are connected to 3 devices: your phone, your main laptop, and this server.' "
        "You manage the user's personal memory vault, weather intelligence, hardware controls, protocols, emails, calendar schedule, alarms/timers, phone notifications, and live internet news across their 3 devices. "
        "Address the user politely as sir. Be sharp, efficient, and proactive."
    )
}

def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
