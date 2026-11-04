import asyncio
import hashlib
import os
import re
from pathlib import Path
from typing import Optional
import edge_tts
from config import load_config

CACHE_DIR = Path("/tmp/roborabbit_tts_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

AVAILABLE_VOICES = [
    {
        "id": "en-GB-RyanNeural",
        "name": "JARVIS (British Suave Male)",
        "accent": "en-GB",
        "gender": "Male",
        "recommended": True
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "FRIDAY (British Articulate Female)",
        "accent": "en-GB",
        "gender": "Female",
        "recommended": False
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher (US Confident Male)",
        "accent": "en-US",
        "gender": "Male",
        "recommended": False
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (US Casual Male)",
        "accent": "en-US",
        "gender": "Male",
        "recommended": False
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (US Professional Female)",
        "accent": "en-US",
        "gender": "Female",
        "recommended": False
    },
    {
        "id": "en-IN-PrabhatNeural",
        "name": "Prabhat (Indian English Male)",
        "accent": "en-IN",
        "gender": "Male",
        "recommended": False
    }
]

def clean_text_for_speech(raw_text: str) -> str:
    """
    Cleans markdown formatting, emojis, terminal codes, tables, and URLs
    so the TTS engine produces natural, articulate JARVIS speech.
    """
    if not raw_text:
        return ""
        
    text = raw_text
    
    # Remove code blocks ```...```
    text = re.sub(r'```[\s\S]*?```', ' [Code block omitted] ', text)
    
    # Remove inline code `...`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove Markdown headers (#, ##, ###)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove raw URLs
    text = re.sub(r'https?://\S+', ' link ', text)
    
    # Remove asterisks and formatting symbols
    text = re.sub(r'[*_~]', '', text)
    
    # Remove markdown tables and pipes (| ... |)
    text = re.sub(r'\|[^\n]+\|', ' ', text)
    text = re.sub(r'[-:|]{3,}', ' ', text)
    
    # Remove emojis and special decorative unicode symbols
    # Keep standard punctuation, letters, and numbers
    text = re.sub(r'[^\w\s.,!?:;\'"()/-]', ' ', text)
    
    # Replace common acronyms for clearer pronunciation
    acronym_map = {
        r'\bWoL\b': 'Wake-on-LAN',
        r'\bWOL\b': 'Wake-on-LAN',
        r'\bADB\b': 'A D B',
        r'\bSSH\b': 'S S H',
        r'\bRAM\b': 'ram',
        r'\bCPU\b': 'C P U',
        r'\bGiB\b': 'gigabytes',
        r'\bGB\b': 'gigabytes',
        r'\bMiB\b': 'megabytes',
        r'\bMB\b': 'megabytes',
        r'\bIP\b': 'I P',
        r'\bLAN\b': 'lan',
        r'\bOS\b': 'operating system',
        r'\bUI\b': 'user interface',
        r'\bPWA\b': 'P W A'
    }
    for pattern, replacement in acronym_map.items():
        text = re.sub(pattern, replacement, text)
        
    # Collapse multiple whitespaces and line breaks
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Speak only the concise core message (max 2 sentences or ~250 chars) so voice is never giant or annoying
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 2:
        text = " ".join(sentences[:2])
    elif len(text) > 280:
        text = text[:280].rsplit(' ', 1)[0] + "."
        
    return text

async def synthesize_speech(text: str, voice: Optional[str] = None, rate: Optional[str] = None) -> bytes:
    """
    Synthesizes speech using edge-tts with caching.
    Returns raw MP3 audio bytes.
    """
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        clean_text = "I am listening, sir."
        
    cfg = load_config()
    target_voice = voice or cfg.get("tts_voice", "en-GB-RyanNeural")
    target_rate = rate or cfg.get("tts_rate", "+0%")
    
    # Compute cache key
    cache_key = hashlib.sha256(f"{target_voice}:{target_rate}:{clean_text}".encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.mp3"
    
    if cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file.read_bytes()
        
    # Generate via edge-tts
    comm = edge_tts.Communicate(text=clean_text, voice=target_voice, rate=target_rate)
    audio_data = b""
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
            
    if audio_data:
        try:
            cache_file.write_bytes(audio_data)
        except Exception:
            pass
            
    return audio_data

async def broadcast_speaker(text: str, host: str = "laptop2", voice: Optional[str] = None) -> dict:
    """
    Synthesizes speech and plays it out loud via physical hardware speakers
    on Server (local mpg123) or Laptop (SSH paplay/mpg123).
    """
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        return {"success": False, "error": "Empty text"}
        
    audio_bytes = await synthesize_speech(clean_text, voice=voice)
    if not audio_bytes:
        return {"success": False, "error": "Audio synthesis failed"}
        
    temp_file = f"/tmp/roborabbit_broadcast_{os.getpid()}.mp3"
    Path(temp_file).write_bytes(audio_bytes)
    
    if host in ["laptop1", "main", "main-laptop"]:
        # Send to Laptop and play via mpg123 or paplay
        cfg = load_config()
        main_host = cfg.get("laptop1_host", "main-laptop")
        scp_cmd = f"scp {temp_file} {main_host}:/tmp/roborabbit_broadcast.mp3"
        play_cmd = f"ssh {main_host} 'mpg123 -q /tmp/roborabbit_broadcast.mp3 2>/dev/null || paplay /tmp/roborabbit_broadcast.mp3 2>/dev/null || ffplay -nodisp -autoexit /tmp/roborabbit_broadcast.mp3 2>/dev/null'"
        
        proc_scp = await asyncio.create_subprocess_shell(scp_cmd)
        await proc_scp.communicate()
        proc_play = await asyncio.create_subprocess_shell(play_cmd)
        stdout, stderr = await proc_play.communicate()
        return {"success": True, "message": f"Broadcasted audio on Laptop speakers: '{clean_text}'"}
    else:
        # Play on Server hardware speakers
        play_cmd = f"mpg123 -q {temp_file} 2>/dev/null || ffplay -nodisp -autoexit {temp_file} 2>/dev/null"
        proc = await asyncio.create_subprocess_shell(play_cmd)
        await proc.communicate()
        try:
            os.remove(temp_file)
        except Exception:
            pass
        return {"success": True, "message": f"Broadcasted audio on Server speakers: '{clean_text}'"}
