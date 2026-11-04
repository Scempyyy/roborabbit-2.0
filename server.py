import asyncio
import json
import time
import uuid
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import load_config, save_config
from tools import (
    get_all_devices,
    wake_laptop1_wol,
    run_command,
    connect_phone_adb,
    fetch_internet_news,
    fetch_phone_notifications,
    manage_calendar_tool,
    manage_alarms_tool,
    manage_emails_tool,
    get_executive_briefing,
    manage_notes_tool,
    get_weather_tool,
    manage_smart_home_tool,
    manage_todos_tool,
    capture_screen_vision_tool,
    emergency_stop_tool,
    developer_tools,
    manage_application_tool,
    sync_gmail_tool,
    manage_integrations_tool,
    notion_tool,
    github_tool,
    media_player_tool,
    clipboard_tool,
    control_device_deep_tool
)
from agent import chat_stream
from tts import synthesize_speech, clean_text_for_speech, AVAILABLE_VOICES, broadcast_speaker
import database as db

app = FastAPI(title="RoboRabbit Multi-Device OS Assistant", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

active_ringing_alarms = []

async def alarm_monitor_loop():
    while True:
        try:
            due = db.get_due_alarms()
            for al in due:
                db.mark_alarm_triggered(al["id"])
                active_ringing_alarms.append(al)
                label = al.get("label", "Alarm")
                asyncio.create_task(broadcast_speaker(f"Attention sir, alarm: {label}", host="laptop2"))
        except Exception:
            pass
        await asyncio.sleep(1.5)

@app.on_event("startup")
async def startup_event():
    db.init_db()
    asyncio.create_task(alarm_monitor_loop())

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_file = STATIC_DIR / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

@app.get("/api/status")
@app.get("/api/devices")
async def api_status():
    return await get_all_devices()

@app.post("/api/wake")
async def api_wake():
    return wake_laptop1_wol()

class PhoneConnectRequest(BaseModel):
    ip: str
    port: int = 5555

@app.post("/api/phone/connect")
async def api_phone_connect(req: PhoneConnectRequest):
    return await connect_phone_adb(req.ip, req.port)

@app.get("/api/config")
async def api_get_config():
    cfg = load_config()
    safe_cfg = cfg.copy()
    key = safe_cfg.get("api_key", "")
    if key and len(key) > 8:
        safe_cfg["api_key_masked"] = key[:4] + "..." + key[-4:]
    else:
        safe_cfg["api_key_masked"] = ""
    safe_cfg["has_api_key"] = bool(key)
    safe_cfg.pop("api_key", None)
    return safe_cfg

class ConfigUpdateRequest(BaseModel):
    llm_provider: str | None = None
    freellmapi_url: str | None = None
    freellmapi_key: str | None = None
    freellmapi_model: str | None = None
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    phone_ip: str | None = None
    system_prompt: str | None = None
    tts_voice: str | None = None
    tts_rate: str | None = None
    tts_enabled: bool | None = None

@app.post("/api/config")
async def api_update_config(req: ConfigUpdateRequest):
    cfg = load_config()
    if req.llm_provider is not None:
        cfg["llm_provider"] = req.llm_provider
    if req.freellmapi_url is not None:
        cfg["freellmapi_url"] = req.freellmapi_url.strip()
    if req.freellmapi_key is not None and req.freellmapi_key.strip():
        cfg["freellmapi_key"] = req.freellmapi_key.strip()
    if req.freellmapi_model is not None:
        cfg["freellmapi_model"] = req.freellmapi_model.strip()
    if req.api_key is not None and req.api_key.strip():
        cfg["api_key"] = req.api_key.strip()
    if req.model is not None:
        cfg["model"] = req.model.strip()
    if req.base_url is not None:
        cfg["base_url"] = req.base_url.strip()
    if req.phone_ip is not None:
        cfg["phone_ip"] = req.phone_ip.strip()
    if req.system_prompt is not None:
        cfg["system_prompt"] = req.system_prompt
    if req.tts_voice is not None:
        cfg["tts_voice"] = req.tts_voice.strip()
    if req.tts_rate is not None:
        cfg["tts_rate"] = req.tts_rate.strip()
    if req.tts_enabled is not None:
        cfg["tts_enabled"] = req.tts_enabled
    save_config(cfg)
    return {"success": True, "message": "Settings updated"}

class TTSRequest(BaseModel):
    text: str
    voice: str | None = None
    rate: str | None = None

@app.post("/api/tts")
async def api_post_tts(req: TTSRequest):
    audio_data = await synthesize_speech(req.text, req.voice, req.rate)
    return Response(content=audio_data, media_type="audio/mpeg", headers={
        "Cache-Control": "public, max-age=86400",
        "Accept-Ranges": "bytes"
    })

@app.get("/api/tts")
async def api_get_tts(text: str, voice: str | None = None, rate: str | None = None):
    audio_data = await synthesize_speech(text, voice, rate)
    return Response(content=audio_data, media_type="audio/mpeg", headers={
        "Cache-Control": "public, max-age=86400",
        "Accept-Ranges": "bytes"
    })

@app.get("/api/tts/voices")
async def api_get_voices():
    return AVAILABLE_VOICES

class BroadcastRequest(BaseModel):
    text: str
    host: str = "laptop2"
    voice: str | None = None

@app.post("/api/tts/broadcast")
async def api_broadcast_speaker(req: BroadcastRequest):
    return await broadcast_speaker(req.text, host=req.host, voice=req.voice)


@app.get("/api/sessions")
async def api_list_sessions():
    return db.list_sessions()

class CreateSessionRequest(BaseModel):
    title: str = "New Conversation"

@app.post("/api/sessions")
async def api_create_session(req: CreateSessionRequest):
    sess_id = str(uuid.uuid4())[:8]
    db.create_session(sess_id, req.title)
    return {"session_id": sess_id, "title": req.title}

@app.get("/api/sessions/{session_id}")
async def api_get_session(session_id: str):
    return {
        "session_id": session_id,
        "messages": db.get_session_messages(session_id)
    }

@app.delete("/api/sessions/{session_id}")
async def api_delete_session(session_id: str):
    db.delete_session(session_id)
    return {"success": True}

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    session_id = req.session_id.strip() or str(uuid.uuid4())[:8]
    user_msg = req.message.strip()
    
    db.save_message(session_id, "user", user_msg)
    history = db.get_session_messages(session_id)
    
    async def event_generator():
        tool_events = []
        full_assistant_reply = ""
        
        async for evt in chat_stream(user_msg, history, session_id=session_id):
            evt_type = evt.get("type")
            if evt_type == "tool_result":
                tool_events.append(evt)
            elif evt_type == "content":
                full_assistant_reply += evt.get("delta", "")
                
            yield f"data: {json.dumps(evt)}\n\n"
            
        db.save_message(session_id, "assistant", full_assistant_reply, tool_events)
        
        if len(history) <= 2:
            auto_title = user_msg[:35] + ("..." if len(user_msg) > 35 else "")
            db.create_session(session_id, auto_title)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

class ExecRequest(BaseModel):
    host: str = "laptop2"
    command: str

@app.post("/api/exec")
async def api_exec(req: ExecRequest):
    return await run_command(req.host, req.command)

# ==========================================
# CALENDAR ENDPOINTS
# ==========================================

@app.get("/api/calendar")
async def api_get_calendar(date: str | None = None):
    events = db.list_calendar_events(date=date)
    return {"events": events, "today": db.get_today_events()}

class CalendarEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: str = ""
    date: str = ""
    category: str = "work"
    description: str = ""

@app.post("/api/calendar")
async def api_create_calendar_event(req: CalendarEventRequest):
    eid = db.add_calendar_event(req.title, req.start_time, req.end_time, req.date, req.category, req.description)
    return {"success": True, "event_id": eid}

@app.delete("/api/calendar/{event_id}")
async def api_delete_calendar_event(event_id: int):
    db.delete_calendar_event(event_id)
    return {"success": True}

# ==========================================
# ALARMS & TIMERS ENDPOINTS
# ==========================================

@app.get("/api/alarms")
async def api_get_alarms():
    return {
        "alarms": db.list_alarms(),
        "active_ringing": active_ringing_alarms
    }

class AlarmRequest(BaseModel):
    label: str = "Alarm"
    time_str: str = ""
    duration_seconds: int = 0
    device: str = "laptop2"

@app.post("/api/alarms")
async def api_create_alarm(req: AlarmRequest):
    res = await manage_alarms_tool(
        action="timer" if req.duration_seconds > 0 else "alarm",
        label=req.label,
        time_str=req.time_str,
        duration_seconds=req.duration_seconds,
        device=req.device
    )
    return res

@app.delete("/api/alarms/{alarm_id}")
async def api_delete_alarm(alarm_id: int):
    db.delete_alarm(alarm_id)
    return {"success": True}

@app.post("/api/alarms/{alarm_id}/dismiss")
async def api_dismiss_alarm(alarm_id: int):
    db.dismiss_alarm(alarm_id)
    global active_ringing_alarms
    active_ringing_alarms = [a for a in active_ringing_alarms if a.get("id") != alarm_id]
    return {"success": True}

@app.get("/api/alarms/active")
async def api_get_active_ringing_alarms():
    return {"active_ringing": active_ringing_alarms}

@app.post("/api/alarms/active/clear")
async def api_clear_active_ringing():
    global active_ringing_alarms
    for al in active_ringing_alarms:
        db.dismiss_alarm(al["id"])
    active_ringing_alarms.clear()
    return {"success": True}

# ==========================================
# EMAILS ENDPOINTS
# ==========================================

@app.get("/api/emails")
async def api_get_emails(folder: str = "inbox", unread_only: bool = False):
    return {
        "emails": db.list_emails(folder=folder, unread_only=unread_only),
        "unread_count": db.count_unread_emails()
    }

@app.get("/api/emails/{email_id}")
async def api_get_email_detail(email_id: int):
    email = db.get_email(email_id)
    if email:
        db.mark_email_read(email_id, 1)
        return {"email": email}
    return JSONResponse(status_code=404, content={"error": "Not found"})

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str

@app.post("/api/emails")
async def api_send_email(req: SendEmailRequest):
    eid = db.send_local_email(req.to, req.subject, req.body)
    return {"success": True, "email_id": eid}

@app.post("/api/emails/{email_id}/read")
async def api_mark_email_read(email_id: int):
    db.mark_email_read(email_id, 1)
    return {"success": True}

@app.delete("/api/emails/{email_id}")
async def api_delete_email(email_id: int):
    db.delete_email(email_id)
    return {"success": True}

class GmailConfigRequest(BaseModel):
    user_email: str
    app_password: str

@app.post("/api/gmail/config")
async def api_set_gmail_config(req: GmailConfigRequest):
    cfg = load_config()
    cfg["gmail_user"] = req.user_email
    cfg["gmail_app_password"] = req.app_password
    save_config(cfg)
    return {"success": True, "gmail_user": req.user_email}

@app.get("/api/gmail/config")
async def api_get_gmail_config():
    cfg = load_config()
    configured = bool(cfg.get("gmail_user") and cfg.get("gmail_app_password"))
    return {"configured": configured, "gmail_user": cfg.get("gmail_user", "")}

@app.post("/api/gmail/sync")
async def api_sync_gmail():
    return await sync_gmail_tool()

# ==========================================
# PHONE NOTIFICATIONS ENDPOINTS
# ==========================================

class PhonePushNotification(BaseModel):
    app_name: str
    title: str
    content: str
    package_name: str = "com.android.notification"

@app.post("/api/notifications/phone/push")
async def api_push_phone_notification(req: PhonePushNotification):
    nid = db.add_phone_notification(
        app_name=req.app_name,
        title=req.title,
        content=req.content,
        package_name=req.package_name
    )
    return {"success": True, "notification_id": nid}

@app.get("/api/notifications/phone")
async def api_get_phone_notifications():
    return await fetch_phone_notifications(sync_adb=False)

@app.post("/api/notifications/phone/sync")
async def api_sync_phone_notifications():
    return await fetch_phone_notifications(sync_adb=True)

class TestNotificationRequest(BaseModel):
    app_name: str = "WhatsApp"
    title: str = "Incoming Message"
    content: str = "Hello from Android phone!"

@app.post("/api/notifications/phone/test")
async def api_test_phone_notification(req: TestNotificationRequest):
    nid = db.add_phone_notification(req.app_name, req.title, req.content)
    return {"success": True, "notification_id": nid}

@app.delete("/api/notifications/phone")
async def api_clear_notifications():
    db.clear_phone_notifications()
    return {"success": True}

# ==========================================
# INTERNET INTEL & LIVE NEWS
# ==========================================

@app.get("/api/internet/news")
async def api_get_internet_news(category: str = "all", limit: int = 6):
    return await fetch_internet_news(category=category, limit=limit)

# ==========================================
# PHONE COMMAND BRIDGE (Zero-ADB Persistent Channel)
# ==========================================
phone_pending_commands = []
phone_telemetry = {
    "online": True,
    "battery": "70%",
    "model": "Vivo V2437",
    "last_seen": time.time()
}

@app.get("/api/phone/poll")
async def api_phone_poll():
    global phone_pending_commands, phone_telemetry
    phone_telemetry["last_seen"] = time.time()
    cmds = list(phone_pending_commands)
    phone_pending_commands.clear()
    return {"commands": cmds, "server_time": time.time()}

class PhoneCommandRequest(BaseModel):
    action: str # open_url, speak, vibrate
    url: str | None = None
    data: dict | None = None

@app.post("/api/phone/command")
async def api_post_phone_command(cmd: PhoneCommandRequest):
    global phone_pending_commands
    c = {
        "id": int(time.time() * 1000),
        "action": cmd.action,
        "url": cmd.url,
        "data": cmd.data or {},
        "timestamp": time.time()
    }
    phone_pending_commands.append(c)
    return {"success": True, "queued": c}

class PhoneTelemetryReport(BaseModel):
    battery: str | None = None
    model: str | None = None

@app.post("/api/phone/telemetry")
async def api_post_phone_telemetry(t: PhoneTelemetryReport):
    global phone_telemetry
    phone_telemetry["last_seen"] = time.time()
    if t.battery:
        phone_telemetry["battery"] = t.battery
    if t.model:
        phone_telemetry["model"] = t.model
    return {"success": True}

@app.get("/sw.js")
async def api_serve_sw():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})

@app.get("/manifest.json")
async def api_serve_manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")

# ==========================================
# EXECUTIVE BRIEFING
# ==========================================

@app.get("/api/briefing")
async def api_get_briefing():
    return await get_executive_briefing()

# ==========================================
# PERSONAL NOTES & MEMORY VAULT
# ==========================================

@app.get("/api/notes")
async def api_get_notes(category: str = None, search: str = None):
    return await manage_notes_tool(action="list", category=category or "all", search=search or "")

class NoteCreateRequest(BaseModel):
    content: str
    title: str = None
    category: str = "general"

@app.post("/api/notes")
async def api_create_note(req: NoteCreateRequest):
    return await manage_notes_tool(action="add", content=req.content, title=req.title, category=req.category)

@app.delete("/api/notes/{note_id}")
async def api_delete_note(note_id: int):
    return await manage_notes_tool(action="delete", note_id=note_id)

# ==========================================
# WEATHER INTELLIGENCE
# ==========================================

@app.get("/api/weather")
async def api_get_weather(location: str = "auto"):
    return await get_weather_tool(location=location)

# ==========================================
# PERSONAL PRODUCTIVITY: TO-DO (#4)
# ==========================================

@app.get("/api/todos")
async def api_get_todos():
    return await manage_todos_tool(action="list")

class TodoCreateRequest(BaseModel):
    title: str
    priority: str = "medium"
    deadline: str = "Today"

@app.post("/api/todos")
async def api_create_todo(req: TodoCreateRequest):
    return await manage_todos_tool(action="add", title=req.title, priority=req.priority, deadline=req.deadline)

@app.post("/api/todos/{todo_id}/complete")
async def api_complete_todo(todo_id: int):
    return await manage_todos_tool(action="complete", todo_id=todo_id)

@app.delete("/api/todos/{todo_id}")
async def api_delete_todo(todo_id: int):
    return await manage_todos_tool(action="delete", todo_id=todo_id)

# ==========================================
# SMART HOME & IOT (#6)
# ==========================================

@app.get("/api/smarthome")
async def api_get_smarthome():
    return await manage_smart_home_tool(action="list")

class SmartHomeSetRequest(BaseModel):
    entity_id: str
    state: str = None
    brightness: int = None
    temperature: float = None

@app.post("/api/smarthome/set")
async def api_set_smarthome(req: SmartHomeSetRequest):
    return await manage_smart_home_tool(action="set", entity_id=req.entity_id, state=req.state, brightness=req.brightness, temperature=req.temperature)

# ==========================================
# SECURITY & AUDIT TRAIL (#12)
# ==========================================

@app.get("/api/audit")
async def api_get_audit(limit: int = 50):
    return {"audit_logs": db.list_audit_logs(limit=limit)}

@app.post("/api/emergency_stop")
async def api_emergency_stop():
    return await emergency_stop_tool()

# ==========================================
# SCREEN VISION & OCR (#11)
# ==========================================

@app.post("/api/screen/capture")
async def api_screen_capture(device: str = "laptop1", ocr: bool = True):
    return await capture_screen_vision_tool(device=device, run_ocr=ocr)

# ==========================================
# CONNECTED APPS & INTEGRATIONS API
# ==========================================

@app.get("/api/integrations")
async def api_get_integrations():
    return await manage_integrations_tool(action="list")

@app.get("/api/integrations/{service}")
async def api_get_integration_detail(service: str):
    return await manage_integrations_tool(action="get", service=service)

class IntegrationSaveRequest(BaseModel):
    credentials: dict

@app.post("/api/integrations/{service}")
async def api_save_integration(service: str, req: IntegrationSaveRequest):
    return await manage_integrations_tool(action="save", service=service, credentials=req.credentials)

@app.post("/api/integrations/{service}/test")
async def api_test_integration(service: str):
    return await manage_integrations_tool(action="test", service=service)

@app.delete("/api/integrations/{service}")
async def api_delete_integration(service: str):
    return await manage_integrations_tool(action="delete", service=service)

# ==========================================
# NOTION & GITHUB WORKSPACE API
# ==========================================

class NotionRequest(BaseModel):
    action: str = "search"
    title: str = ""
    content: str = ""
    database_id: str = ""

@app.post("/api/notion")
async def api_notion_action(req: NotionRequest):
    return await notion_tool(action=req.action, title=req.title, content=req.content, database_id=req.database_id)

class GitHubRequest(BaseModel):
    action: str = "list_repos"
    repo: str = ""
    title: str = ""
    body: str = ""

@app.post("/api/github")
async def api_github_action(req: GitHubRequest):
    return await github_tool(action=req.action, repo=req.repo, title=req.title, body=req.body)

# ==========================================
# MEDIA PLAYERCTL & AUDIO CONTROL
# ==========================================

class MediaControlRequest(BaseModel):
    device: str = "laptop1"
    action: str = "play_pause"
    parameter: str = ""

@app.post("/api/media/control")
async def api_media_control(req: MediaControlRequest):
    return await media_player_tool(device=req.device, action=req.action, parameter=req.parameter)

@app.get("/api/media/status")
async def api_media_status(device: str = "laptop1"):
    return await media_player_tool(device=device, action="status")

# ==========================================
# CROSS-DEVICE CLIPBOARD
# ==========================================

class ClipboardRequest(BaseModel):
    device: str = "laptop1"
    action: str = "read"
    text: str = ""

@app.post("/api/clipboard")
async def api_clipboard_action(req: ClipboardRequest):
    return await clipboard_tool(device=req.device, action=req.action, text=req.text)

# ==========================================
# DEEP HARDWARE & PHONE CONTROL API
# ==========================================

class DeepControlRequest(BaseModel):
    target: str = "laptop1"
    action: str
    parameter: str = ""

@app.post("/api/hardware/deep")
async def api_deep_hardware_control(req: DeepControlRequest):
    return await control_device_deep_tool(target=req.target, action=req.action, parameter=req.parameter)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=7777, reload=False)
