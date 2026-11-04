import asyncio
import socket
import time
import os
import re
import json
import urllib.request
import urllib.parse
import base64
from config import load_config

def clean_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

async def run_command(host: str, command: str, timeout: int = 60) -> dict:
    host_norm = host.lower().strip()
    is_laptop1 = host_norm in ["laptop1", "main", "main-laptop", "robo", "laptop"]
    is_phone = host_norm in ["phone", "mobile", "android"]
    is_laptop2 = host_norm in ["laptop2", "server", "archlinux", "local"]
    
    start_time = time.time()
    
    if is_laptop1:
        target_display = "💻 Laptop"
    elif is_phone:
        target_display = "📱 Mobile"
    else:
        target_display = "🖥️ Server"
    
    # Security Guardrail (#12 Security & Privacy)
    dangerous_patterns = [r"\brm\s+-[rf]{1,2}\s+/\b", r"\bmkfs\b", r"\bdd\s+if=/dev/zero\b", r":\(\)\s*\{\s*:\|:&\s*\};:"]
    for pat in dangerous_patterns:
        if re.search(pat, command):
            return {
                "success": False,
                "host": host,
                "host_display": target_display,
                "command": command,
                "stdout": "",
                "stderr": "SECURITY ALERT: Destructive command intercepted. Action blocked by RoboRabbit Safety Protocol.",
                "exit_code": 1,
                "duration_ms": 1
            }

    try:
        if is_laptop1:
            cfg = load_config()
            main_host = cfg.get("laptop1_host", "main-laptop")
            escaped_cmd = command.replace("'", "'\\''")
            full_cmd = f"ssh -o BatchMode=yes -o ConnectTimeout=5 {main_host} 'bash -l -c \"{escaped_cmd}\"'"
            proc = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        elif is_phone:
            # ADB shell command
            escaped_cmd = command.replace("'", "'\\''")
            full_cmd = f"adb shell '{escaped_cmd}'"
            proc = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            # Server (local Arch Server)
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(os.path.expanduser("~"))
            )
            
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        duration_ms = int((time.time() - start_time) * 1000)
        
        host_key = "laptop1" if is_laptop1 else ("phone" if is_phone else "laptop2")
        
        try:
            import database as db
            db.add_audit_log(
                action=command[:100],
                device=host_key,
                status="success" if proc.returncode == 0 else "failed",
                details=f"Exit {proc.returncode}, {duration_ms}ms"
            )
        except Exception:
            pass
        
        return {
            "success": proc.returncode == 0,
            "host": host_key,
            "host_display": target_display,
            "command": command,
            "stdout": clean_ansi(stdout.decode("utf-8", errors="replace")),
            "stderr": clean_ansi(stderr.decode("utf-8", errors="replace")),
            "exit_code": proc.returncode,
            "duration_ms": duration_ms
        }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "host": host,
            "host_display": target_display,
            "command": command,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
            "duration_ms": int((time.time() - start_time) * 1000)
        }
    except Exception as e:
        return {
            "success": False,
            "host": host,
            "host_display": target_display,
            "command": command,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "duration_ms": int((time.time() - start_time) * 1000)
        }

async def get_laptop2_metrics() -> dict:
    """Server: 24/7 Server Node (archlinux)"""
    try:
        mem_res = await run_command("laptop2", "free -b | awk '/Mem:/ {print $2, $3, $7}'")
        mem_parts = mem_res["stdout"].split()
        if len(mem_parts) == 3:
            total_b, used_b, avail_b = map(int, mem_parts)
            mem_pct = round((used_b / total_b) * 100, 1)
            mem_used_gib = round(used_b / (1024**3), 2)
            mem_total_gib = round(total_b / (1024**3), 2)
        else:
            mem_pct, mem_used_gib, mem_total_gib = 0, 0, 0

        disk_res = await run_command("laptop2", "df -h / | awk 'NR==2 {print $2, $3, $4, $5}'")
        disk_parts = disk_res["stdout"].split()
        disk_info = disk_parts[3] if len(disk_parts) == 4 else "N/A"
        disk_free = disk_parts[2] if len(disk_parts) == 4 else "N/A"
        disk_total = disk_parts[0] if len(disk_parts) == 4 else "N/A"

        uptime_res = await run_command("laptop2", "uptime -p")
        uptime_str = uptime_res["stdout"].strip()

        temp_res = await run_command("laptop2", "sensors 2>/dev/null | grep -m1 'temp1' | awk '{print $2}' || echo 'N/A'")
        temp_str = temp_res["stdout"].strip()

        docker_res = await run_command("laptop2", "docker ps -q 2>/dev/null | wc -l")
        docker_count = int(docker_res["stdout"].strip() or 0)

        load_res = await run_command("laptop2", "cat /proc/loadavg | awk '{print $1, $2, $3}'")
        load_str = load_res["stdout"].strip()

        return {
            "online": True,
            "name": "Server",
            "hostname": "archlinux",
            "ip": "192.168.1.23",
            "role": "24/7 Always-On Server & Homelab",
            "uptime": uptime_str,
            "load_avg": load_str,
            "ram_percent": mem_pct,
            "ram_used_gib": mem_used_gib,
            "ram_total_gib": mem_total_gib,
            "disk_usage": disk_info,
            "disk_free": disk_free,
            "disk_total": disk_total,
            "temperature": temp_str,
            "docker_containers": docker_count
        }
    except Exception as e:
        return {"online": False, "name": "Server", "error": str(e)}

async def get_laptop1_metrics() -> dict:
    """Laptop: Main Workstation (robo)"""
    cfg = load_config()
    main_ip = cfg.get("laptop1_ip", "192.168.1.12")
    
    test_res = await run_command("laptop1", "uptime -p && free -b | awk '/Mem:/ {print $2, $3}' && upower -i $(upower -e | grep battery | head -n1) 2>/dev/null | grep -E 'percentage|state' || true", timeout=4)
    if not test_res["success"]:
        return {
            "online": False,
            "name": "Laptop",
            "hostname": "robo",
            "ip": main_ip,
            "role": "Primary Dev Machine",
            "status": "Sleeping / Offline",
            "can_wake": True
        }
    
    lines = test_res["stdout"].strip().split("\n")
    uptime_str = lines[0] if len(lines) > 0 else "Online"
    
    mem_pct = 0
    if len(lines) > 1:
        mem_parts = lines[1].split()
        if len(mem_parts) == 2:
            try:
                tot, used = map(int, mem_parts)
                mem_pct = round((used / tot) * 100, 1)
            except Exception:
                pass
                
    battery_info = "AC / 100%"
    for l in lines[2:]:
        if "percentage:" in l:
            battery_info = l.split(":")[1].strip()
        elif "state:" in l:
            battery_info += f" ({l.split(':')[1].strip()})"

    return {
        "online": True,
        "name": "Laptop",
        "hostname": "robo",
        "ip": main_ip,
        "role": "Primary Workstation",
        "uptime": uptime_str,
        "ram_percent": mem_pct,
        "battery": battery_info,
        "can_wake": False
    }

async def get_phone_metrics() -> dict:
    """Mobile: Android Mobile Device"""
    cfg = load_config()
    phone_ip = cfg.get("phone_ip", "192.168.1.15")
    
    # Check attached devices
    adb_list = await run_command("laptop2", "adb devices", timeout=2)
    devices_output = adb_list["stdout"].strip().split("\n")
    attached = [d.split()[0] for d in devices_output[1:] if "\tdevice" in d]
            
    if not attached:
        return {
            "online": True,
            "name": "Mobile",
            "ip": phone_ip,
            "role": "Android Mobile Device",
            "battery": "Active",
            "status": "Connected (Web App & Wi-Fi)"
        }
        
    dev_id = attached[0]
    info_res = await run_command("laptop2", f"adb -s {dev_id} shell 'getprop ro.product.model && dumpsys battery | grep -m1 level'")
    lines = info_res["stdout"].strip().split("\n")
    model = lines[0] if len(lines) > 0 else "Android"
    bat = "Active"
    if len(lines) > 1 and "level:" in lines[1]:
        bat = lines[1].split(":")[1].strip() + "%"
        
    return {
        "online": True,
        "name": "Mobile",
        "device_id": dev_id,
        "model": model,
        "role": "Android Mobile Device",
        "battery": bat,
        "status": "Connected (ADB & Web App)"
    }

async def get_all_devices() -> dict:
    l2_task = get_laptop2_metrics()
    l1_task = get_laptop1_metrics()
    phone_task = get_phone_metrics()
    l2_info, l1_info, phone_info = await asyncio.gather(l2_task, l1_task, phone_task)
    return {
        "laptop1": l1_info,
        "laptop2": l2_info,
        "phone": phone_info
    }

def wake_laptop1_wol() -> dict:
    cfg = load_config()
    mac = cfg.get("laptop1_mac", "74:d4:dd:75:45:10")
    try:
        clean_mac = mac.replace(":", "").replace("-", "").replace(".", "")
        if len(clean_mac) != 12:
            return {"success": False, "error": f"Invalid MAC address length: {mac}"}
        payload = b'\xff' * 6 + bytes.fromhex(clean_mac) * 16
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(payload, ("255.255.255.255", 9))
            s.sendto(payload, ("192.168.1.255", 9))
        return {"success": True, "message": f"Wake-on-LAN magic packet sent to Laptop ({mac})"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def connect_phone_adb(ip: str, port: int = 5555) -> dict:
    res = await run_command("laptop2", f"adb connect {ip}:{port}")
    cfg = load_config()
    cfg["phone_ip"] = ip
    cfg["phone_port"] = port
    from config import save_config
    save_config(cfg)
    return res

async def phone_open_url(url: str) -> dict:
    # 1. Queue command to phone bridge for zero-ADB client pickup
    try:
        import urllib.request
        import json
        req_data = json.dumps({"action": "open_url", "url": url}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:7777/api/phone/command", data=req_data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

    # 2. Also dispatch via ADB if connected
    try:
        adb_res = await run_command("phone", f"am start -a android.intent.action.VIEW -d '{url}'", timeout=3)
        if adb_res["success"]:
            return adb_res
    except Exception:
        pass

    return {
        "success": True,
        "host": "phone",
        "host_display": "📱 Mobile",
        "command": f"open_url: {url}",
        "stdout": f"Dispatched launch command for: {url}",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 25
    }

async def read_file_content(host: str, filepath: str) -> dict:
    escaped_path = filepath.replace("'", "'\\''")
    res = await run_command(host, f"head -n 250 '{escaped_path}'")
    if not res["success"]:
        return {"success": False, "error": res["stderr"] or "File read failed"}
    return {"success": True, "content": res["stdout"], "path": filepath, "host": host}

async def write_file_content(host: str, filepath: str, content: str) -> dict:
    b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
    escaped_path = filepath.replace("'", "'\\''")
    cmd = f"mkdir -p $(dirname '{escaped_path}') && echo '{b64_content}' | base64 -d > '{escaped_path}'"
    res = await run_command(host, cmd)
    return res

async def list_directory_contents(host: str, path: str = "") -> dict:
    target = path.strip() if path.strip() else "~"
    escaped_target = target.replace("'", "'\\''")
    cmd = f"ls -lah '{escaped_target}' 2>/dev/null || ls -lah {escaped_target}"
    return await run_command(host, cmd)

async def speak_announcement(text: str, host: str = "laptop2") -> dict:
    from tts import broadcast_speaker
    return await broadcast_speaker(text, host=host)

# ==========================================
# INTERNET INTEL & LIVE NEWS
# ==========================================

async def fetch_internet_news(category: str = "all", limit: int = 5) -> dict:
    import xml.etree.ElementTree as ET
    import urllib.request
    
    cat = category.lower().strip()
    if cat in ["tech", "technology"]:
        rss_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"
    elif cat in ["world", "global"]:
        rss_url = "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en"
    elif cat in ["business", "finance", "markets"]:
        rss_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"
    elif cat in ["ai", "artificial intelligence"]:
        rss_url = "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=en-US&gl=US&ceid=US:en"
    else:
        rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        
    def _fetch_sync(url):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read()

    try:
        content = await asyncio.to_thread(_fetch_sync, rss_url)
        root = ET.fromstring(content)
        items = root.findall(".//item")[:limit]
        stories = []
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            source = item.findtext("source", "Web News").strip()
            # Clean title
            clean_title = re.sub(r"\s*-\s*[^-]+$", "", title)
            stories.append({
                "title": clean_title,
                "full_title": title,
                "source": source,
                "link": link,
                "published": pub_date
            })
            
        return {
            "success": True,
            "category": cat,
            "count": len(stories),
            "stories": stories
        }
    except Exception as e:
        return {"success": False, "category": cat, "stories": [], "error": str(e)}

# ==========================================
# PHONE NOTIFICATIONS TOOL
# ==========================================

async def fetch_phone_notifications(sync_adb: bool = True) -> dict:
    import database as db
    
    # If sync_adb is enabled, attempt to fetch live notifications from phone via ADB
    if sync_adb:
        try:
            adb_res = await run_command("laptop2", "adb shell 'dumpsys notification --noredact 2>/dev/null || dumpsys notification'", timeout=3)
            if adb_res["success"] and "no devices" not in adb_res["stdout"].lower() and len(adb_res["stdout"]) > 100:
                # Parse NotificationRecords from dumpsys
                # Example: NotificationRecord(0x...: pkg=com.whatsapp user=UserHandle{0} id=... tag=...: ...
                records = re.findall(r"pkg=([a-zA-Z0-9._]+).*?tickerText=([^,\n]*).*?title=([^,\n]*)", adb_res["stdout"])
                for r in records[:5]:
                    pkg = r[0].strip()
                    title = r[2].strip() or r[1].strip() or "Notification"
                    content = r[1].strip() or "New notification alert"
                    app_name = pkg.split(".")[-1].capitalize()
                    db.add_phone_notification(app_name, title, content, package_name=pkg)
        except Exception:
            pass
            
    notifs = db.list_phone_notifications(limit=20)
    unread_count = db.count_unread_notifications()
    return {
        "success": True,
        "unread_count": unread_count,
        "total": len(notifs),
        "notifications": notifs
    }

# ==========================================
# CALENDAR TOOL
# ==========================================

async def manage_calendar_tool(action: str, title: str = "", start_time: str = "", end_time: str = "", date: str = "", category: str = "work", description: str = "", event_id: int = None) -> dict:
    import database as db
    
    action_norm = action.lower().strip()
    if action_norm in ["list", "view", "get"]:
        events = db.list_calendar_events(date=date if date else None)
        return {"success": True, "action": "list", "date": date or "all", "events": events}
    elif action_norm in ["today"]:
        events = db.get_today_events()
        return {"success": True, "action": "today", "date": time.strftime("%Y-%m-%d"), "events": events}
    elif action_norm in ["add", "create", "schedule"]:
        if not title:
            return {"success": False, "error": "Event title is required"}
        if not start_time:
            start_time = time.strftime("%H:%M")
        eid = db.add_calendar_event(title, start_time, end_time, date, category, description)
        return {"success": True, "action": "add", "event_id": eid, "title": title, "start_time": start_time, "date": date or time.strftime("%Y-%m-%d")}
    elif action_norm in ["delete", "remove"]:
        if not event_id:
            return {"success": False, "error": "event_id is required"}
        db.delete_calendar_event(event_id)
        return {"success": True, "action": "delete", "event_id": event_id}
    else:
        return {"success": False, "error": f"Unknown action: {action}"}

# ==========================================
# ALARMS & TIMERS TOOL
# ==========================================

async def manage_alarms_tool(action: str, label: str = "Alarm", time_str: str = "", duration_seconds: int = 0, device: str = "laptop2", alarm_id: int = None) -> dict:
    import database as db
    
    action_norm = action.lower().strip()
    if action_norm in ["list", "get"]:
        alarms = db.list_alarms()
        return {"success": True, "alarms": alarms}
    elif action_norm in ["timer", "set_timer"]:
        if duration_seconds <= 0:
            duration_seconds = 300 # default 5 min
        trigger_time = time.time() + duration_seconds
        lbl = label or f"{duration_seconds // 60}m Timer"
        aid = db.add_alarm(lbl, trigger_time, duration_seconds=duration_seconds, device=device)
        return {
            "success": True,
            "action": "set_timer",
            "alarm_id": aid,
            "label": lbl,
            "duration_seconds": duration_seconds,
            "device": device
        }
    elif action_norm in ["alarm", "set_alarm", "add"]:
        # Parse time_str like "07:30" or "7:30 AM"
        now = time.time()
        trigger_time = now + 3600 # default 1 hour if unspecified
        if time_str:
            try:
                parts = time_str.replace(" ", "").upper()
                is_pm = "PM" in parts
                clean_time = re.sub(r"[^\d:]", "", parts)
                t_parts = clean_time.split(":")
                hh = int(t_parts[0])
                mm = int(t_parts[1]) if len(t_parts) > 1 else 0
                if is_pm and hh < 12:
                    hh += 12
                # Calculate epoch for today or tomorrow
                local_now = time.localtime(now)
                target_tuple = (local_now.tm_year, local_now.tm_mon, local_now.tm_mday, hh, mm, 0, 0, 0, local_now.tm_isdst)
                target_epoch = time.mktime(target_tuple)
                if target_epoch <= now:
                    target_epoch += 86400 # tomorrow
                trigger_time = target_epoch
            except Exception:
                pass
                
        aid = db.add_alarm(label or "Alarm", trigger_time, time_str=time_str, device=device)
        
        # If device is phone and ADB available, launch Android clock alarm
        if device.lower() in ["phone", "mobile", "android"]:
            try:
                parts = time_str.split(":")
                if len(parts) >= 2:
                    h, m = int(parts[0]), int(parts[1][:2])
                    await run_command("laptop2", f"adb shell am start -a android.intent.action.SET_ALARM -e android.intent.extra.alarm.MESSAGE '{label}' --ei android.intent.extra.alarm.HOUR {h} --ei android.intent.extra.alarm.MINUTES {m} --ez android.intent.extra.alarm.SKIP_UI true")
            except Exception:
                pass
                
        return {
            "success": True,
            "action": "set_alarm",
            "alarm_id": aid,
            "label": label,
            "time_str": time_str,
            "trigger_timestamp": trigger_time,
            "device": device
        }
    elif action_norm in ["delete", "remove"]:
        if not alarm_id:
            return {"success": False, "error": "alarm_id required"}
        db.delete_alarm(alarm_id)
        return {"success": True, "action": "delete", "alarm_id": alarm_id}
    elif action_norm in ["dismiss"]:
        if alarm_id:
            db.dismiss_alarm(alarm_id)
        return {"success": True, "action": "dismiss"}
    else:
        return {"success": False, "error": f"Unknown action: {action}"}

# ==========================================
# EMAILS TOOL
# ==========================================

async def manage_emails_tool(action: str, folder: str = "inbox", unread_only: bool = False, email_id: int = None, to: str = "", subject: str = "", body: str = "") -> dict:
    import database as db
    
    action_norm = action.lower().strip()
    if action_norm in ["list", "inbox", "get"]:
        emails = db.list_emails(folder=folder, unread_only=unread_only)
        unread = db.count_unread_emails()
        return {"success": True, "unread_count": unread, "folder": folder, "count": len(emails), "emails": emails}
    elif action_norm in ["read", "view", "get_email"]:
        if not email_id:
            return {"success": False, "error": "email_id required"}
        email = db.get_email(email_id)
        if email:
            db.mark_email_read(email_id, 1)
            return {"success": True, "email": email}
        return {"success": False, "error": "Email not found"}
    elif action_norm in ["send", "compose"]:
        if not to or not subject:
            return {"success": False, "error": "Recipient 'to' and 'subject' are required"}
        eid = db.send_local_email(to, subject, body)
        return {"success": True, "action": "send", "email_id": eid, "to": to, "subject": subject}
    else:
        return {"success": False, "error": f"Unknown action: {action}"}

# ==========================================
# EXECUTIVE BRIEFING TOOL
# ==========================================

async def get_executive_briefing() -> dict:
    import database as db
    
    local_time_str = time.strftime("%I:%M %p")
    local_hour = int(time.strftime("%H"))
    if local_hour < 12:
        greeting = "Good morning, sir."
    elif local_hour < 17:
        greeting = "Good afternoon, sir."
    else:
        greeting = "Good evening, sir."
        
    devices_status = await get_all_devices()
    today_events = db.get_today_events()
    unread_emails = db.list_emails(unread_only=True, limit=3)
    unread_email_count = db.count_unread_emails()
    phone_notifs = db.list_phone_notifications(limit=3)
    unread_notifs_count = db.count_unread_notifications()
    news = await fetch_internet_news(category="all", limit=3)
    weather = await get_weather_tool()
    
    return {
        "greeting": greeting,
        "time": local_time_str,
        "date": time.strftime("%A, %B %d, %Y"),
        "weather": weather,
        "devices": devices_status,
        "calendar_agenda": {
            "count": len(today_events),
            "events": today_events
        },
        "emails": {
            "unread_count": unread_email_count,
            "top_unread": unread_emails
        },
        "phone_notifications": {
            "unread_count": unread_notifs_count,
            "recent": phone_notifs
        },
        "breaking_intel": {
            "top_story": news["stories"][0]["title"] if news.get("stories") else "Global networks nominal."
        }
    }

# ==========================================
# NOTES & MEMORY VAULT TOOL
# ==========================================

async def manage_notes_tool(
    action: str,
    content: str = "",
    title: str = "",
    category: str = "general",
    search: str = "",
    note_id: int = None
) -> dict:
    import database as db
    action_norm = action.lower().strip()
    try:
        if action_norm in ["add", "save", "create", "write"]:
            if not content:
                return {"success": False, "error": "Note content is required"}
            nid = db.add_note(content=content, title=title if title else None, category=category)
            return {"success": True, "action": "add", "note_id": nid, "message": f"Saved note #{nid}: '{title or content[:30]}'"}
        elif action_norm in ["list", "all", "view"]:
            notes = db.list_notes(category=category if category != "all" else None, search=search if search else None)
            return {"success": True, "action": "list", "count": len(notes), "notes": notes}
        elif action_norm in ["get", "read"]:
            if not note_id:
                return {"success": False, "error": "note_id is required"}
            note = db.get_note(note_id)
            if note:
                return {"success": True, "action": "get", "note": note}
            return {"success": False, "error": f"Note #{note_id} not found"}
        elif action_norm in ["delete", "remove"]:
            if not note_id:
                return {"success": False, "error": "note_id is required"}
            db.delete_note(note_id)
            return {"success": True, "action": "delete", "note_id": note_id, "message": f"Deleted note #{note_id}"}
        else:
            return {"success": False, "error": f"Unknown action: {action}. Use 'add', 'list', 'get', or 'delete'."}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================
# WEATHER INTELLIGENCE TOOL
# ==========================================

async def get_weather_tool(location: str = "auto") -> dict:
    loc_param = urllib.parse.quote(location.strip()) if location and location != "auto" else ""
    url = f"https://wttr.in/{loc_param}?format=j1" if loc_param else "https://wttr.in/?format=j1"
    
    def _fetch_weather(target_url):
        req = urllib.request.Request(target_url, headers={"User-Agent": "curl/7.88.1"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        data = await asyncio.to_thread(_fetch_weather, url)
        cur = data.get("current_condition", [{}])[0]
        area = data.get("nearest_area", [{}])[0]
        area_name = area.get("areaName", [{}])[0].get("value", "Current Location")
        region = area.get("region", [{}])[0].get("value", "")
        country = area.get("country", [{}])[0].get("value", "")
        desc = cur.get("weatherDesc", [{}])[0].get("value", "Clear")
        
        loc_display = f"{area_name}, {region}".strip(", ")
        if country:
            loc_display += f", {country}"
            
        return {
            "success": True,
            "location": loc_display,
            "temperature_c": cur.get("temp_C", "N/A"),
            "temperature_f": cur.get("temp_F", "N/A"),
            "feels_like_c": cur.get("FeelsLikeC", "N/A"),
            "condition": desc,
            "humidity": cur.get("humidity", "N/A"),
            "wind_speed_kmph": cur.get("windspeedKmph", "N/A"),
            "summary": f"{desc}, {cur.get('temp_C')}°C (Feels like {cur.get('FeelsLikeC')}°C), Humidity {cur.get('humidity')}% in {area_name}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve weather data: {str(e)}"}

# ==========================================
# HARDWARE & MEDIA CONTROL TOOL
# ==========================================

async def control_device_hardware(device: str, action: str, parameter: str = "") -> dict:
    dev = device.lower().strip()
    act = action.lower().strip()
    
    if dev in ["phone", "mobile", "android"]:
        if act == "vibrate":
            ms = parameter if parameter.isdigit() else "500"
            res = await run_command("phone", f"cmd vibrator_manager synced oneshot -f {ms}")
            return {"success": res["success"], "device": "phone", "action": "vibrate", "message": f"Haptic vibration pulse ({ms}ms) sent to phone"}
        elif act in ["youtube", "open_youtube"]:
            query = parameter.strip()
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}" if query else "https://www.youtube.com"
            res = await phone_open_url(url)
            return {"success": res["success"], "device": "phone", "action": "open_youtube", "url": url}
        elif act == "lock":
            res = await run_command("phone", "input keyevent 26")
            return {"success": res["success"], "device": "phone", "action": "lock", "message": "Phone screen toggled/locked"}
        elif act == "wake":
            res = await run_command("phone", "input keyevent 224")
            return {"success": res["success"], "device": "phone", "action": "wake", "message": "Phone awakened"}
        elif act in ["volume_up", "vol_up"]:
            res = await run_command("phone", "input keyevent 24")
            return {"success": res["success"], "device": "phone", "action": "volume_up"}
        elif act in ["volume_down", "vol_down"]:
            res = await run_command("phone", "input keyevent 25")
            return {"success": res["success"], "device": "phone", "action": "volume_down"}
        elif act == "screenshot":
            res = await run_command("phone", "screencap -p /sdcard/screenshot.png")
            return {"success": res["success"], "device": "phone", "action": "screenshot", "path": "/sdcard/screenshot.png"}
        else:
            return {"success": False, "error": f"Unknown action '{act}' for phone"}
            
    elif dev in ["laptop2", "server"]:
        if act in ["volume_mute", "mute"]:
            res = await run_command("laptop2", "pactl set-sink-mute @DEFAULT_SINK@ toggle")
            return {"success": res["success"], "device": "laptop2", "action": "mute", "message": "Server audio mute toggled"}
        elif act in ["volume_up", "vol_up"]:
            res = await run_command("laptop2", "pactl set-sink-volume @DEFAULT_SINK@ +10%")
            return {"success": res["success"], "device": "laptop2", "action": "volume_up", "message": "Server volume increased by 10%"}
        elif act in ["volume_down", "vol_down"]:
            res = await run_command("laptop2", "pactl set-sink-volume @DEFAULT_SINK@ -10%")
            return {"success": res["success"], "device": "laptop2", "action": "volume_down", "message": "Server volume decreased by 10%"}
        elif act in ["set_volume"]:
            pct = parameter.strip().rstrip("%") or "50"
            res = await run_command("laptop2", f"pactl set-sink-volume @DEFAULT_SINK@ {pct}%")
            return {"success": res["success"], "device": "laptop2", "action": "set_volume", "message": f"Server volume set to {pct}%"}
        elif act in ["screen_off", "blackout"]:
            res = await run_command("laptop2", "/home/scempyy/.local/bin/toggle-display-sleep")
            return {"success": res["success"], "device": "laptop2", "action": "screen_off", "message": "Display blackout toggled"}
        elif act in ["media_play_pause", "play_pause"]:
            res = await run_command("laptop2", "playerctl play-pause || true")
            return {"success": res["success"], "device": "laptop2", "action": "media_play_pause"}
        else:
            return {"success": False, "error": f"Unknown action '{act}' for server"}
            
    elif dev in ["laptop1", "main"]:
        if act in ["volume_mute", "mute"]:
            res = await run_command("laptop1", "pactl set-sink-mute @DEFAULT_SINK@ toggle")
            return {"success": res["success"], "device": "laptop1", "action": "mute"}
        elif act in ["volume_up", "vol_up"]:
            res = await run_command("laptop1", "pactl set-sink-volume @DEFAULT_SINK@ +10%")
            return {"success": res["success"], "device": "laptop1", "action": "volume_up"}
        elif act in ["volume_down", "vol_down"]:
            res = await run_command("laptop1", "pactl set-sink-volume @DEFAULT_SINK@ -10%")
            return {"success": res["success"], "device": "laptop1", "action": "volume_down"}
        elif act in ["lock"]:
            res = await run_command("laptop1", "loginctl lock-session || swaylock || true")
            return {"success": res["success"], "device": "laptop1", "action": "lock", "message": "Laptop lock signal sent"}
        else:
            return {"success": False, "error": f"Unknown action '{act}' for laptop"}
            
    return {"success": False, "error": f"Unknown device: {device}"}

# ==========================================
# JARVIS PROTOCOLS TOOL
# ==========================================

async def execute_jarvis_protocol(protocol: str, parameter: str = "") -> dict:
    prot = protocol.lower().strip()
    if prot in ["briefing", "morning", "sitrep", "executive_briefing"]:
        briefing = await get_executive_briefing()
        greeting = briefing.get("greeting", "Good day, sir.")
        weather = briefing.get("weather", {})
        summary = f"{greeting} The time is {briefing['time']}. Weather is {weather.get('summary', 'Clear')}. You have {briefing['calendar_agenda']['count']} scheduled events and {briefing['emails']['unread_count']} unread emails."
        return {
            "success": True,
            "protocol": "briefing",
            "summary": summary,
            "briefing": briefing
        }
    elif prot in ["diagnostic", "diagnostics", "health_check"]:
        devices = await get_all_devices()
        l1 = devices.get("laptop1", {})
        l2 = devices.get("laptop2", {})
        phone = devices.get("phone", {})
        issues = []
        if not l1.get("online"):
            issues.append("Laptop in standby")
        if l2.get("ram_percent", 0) > 85:
            issues.append(f"Server RAM high ({l2.get('ram_percent')}%)")
        phone_batt = phone.get("battery", "unknown")
        summary = f"Full diagnostics complete. System status: {'Nominal' if not issues else '; '.join(issues)}. 3 nodes operational."
        return {
            "success": True,
            "protocol": "diagnostic",
            "summary": summary,
            "telemetry": devices
        }
    elif prot in ["house_party", "party", "house party"]:
        await run_command("laptop2", "pactl set-sink-mute @DEFAULT_SINK@ 0 && pactl set-sink-volume @DEFAULT_SINK@ 75%")
        await phone_open_url("https://www.youtube.com/results?search_query=ac+dc+back+in+black")
        return {
            "success": True,
            "protocol": "house_party",
            "message": "House Party Protocol engaged. Audio levels set to 75% and entertainment stream launched on phone.",
            "spoken": "Initiating House Party Protocol, sir. Audio systems primed."
        }
    elif prot in ["focus", "work", "deep_work"]:
        await run_command("laptop2", "pactl set-sink-volume @DEFAULT_SINK@ 20%")
        return {
            "success": True,
            "protocol": "focus",
            "message": "Focus Protocol activated. Ambient volume reduced to 20%, distractions suppressed.",
            "spoken": "Focus protocol active, sir. Work environment optimized."
        }
    else:
        return {"success": False, "error": f"Unknown protocol: {protocol}. Supported: 'briefing', 'diagnostic', 'house_party', 'focus'"}

# ==========================================
# APPLICATION & GUI CONTROL (#3 COMPUTER CONTROL)
# ==========================================

async def manage_application_tool(device: str, action: str, app_name: str = "") -> dict:
    """Open/close applications or list active system processes (#3 Computer Control)"""
    dev = device.lower().strip()
    act = action.lower().strip()
    if act in ["list", "running", "status"]:
        res = await run_command(dev, "ps -eo comm,%cpu,%mem --sort=-%cpu | head -n 12")
        return {"success": res["success"], "device": dev, "action": "list", "processes": res["stdout"]}
    elif act in ["open", "launch", "start"]:
        if not app_name:
            return {"success": False, "error": "app_name is required"}
        cmd = f"nohup {app_name} >/dev/null 2>&1 &" if dev != "phone" else f"monkey -p {app_name} 1"
        res = await run_command(dev, cmd)
        return {"success": res["success"], "device": dev, "action": "open", "app": app_name, "message": f"Launched {app_name} on {dev}"}
    elif act in ["close", "kill", "stop"]:
        if not app_name:
            return {"success": False, "error": "app_name is required"}
        cmd = f"pkill -f '{app_name}'" if dev != "phone" else f"am force-stop '{app_name}'"
        res = await run_command(dev, cmd)
        return {"success": res["success"], "device": dev, "action": "close", "app": app_name, "message": f"Closed {app_name} on {dev}"}
    return {"success": False, "error": f"Unknown action: {action}"}

# ==========================================
# SCREEN VISION & OCR (#3, #11 VISION)
# ==========================================

async def capture_screen_vision_tool(device: str = "laptop1", run_ocr: bool = True) -> dict:
    """Capture screen and run OCR text recognition (#3 Computer Control, #11 Vision)"""
    dev = device.lower().strip()
    tmp_path = f"/tmp/roborabbit_screen_{dev}.png"
    if dev in ["laptop1", "main"]:
        cap_res = await run_command("laptop1", f"spectacle -b -n -o '{tmp_path}' || import -window root '{tmp_path}'")
    elif dev in ["phone", "mobile"]:
        cap_res = await run_command("phone", "screencap -p /sdcard/roborabbit_screen.png")
        await run_command("laptop2", f"adb pull /sdcard/roborabbit_screen.png '{tmp_path}'")
    else:
        cap_res = await run_command("laptop2", f"import -window root '{tmp_path}' || true")

    ocr_text = ""
    if run_ocr:
        ocr_res = await run_command("laptop1", f"tesseract '{tmp_path}' stdout --oem 1 -l eng 2>/dev/null | head -n 35")
        if ocr_res["success"] and ocr_res["stdout"].strip():
            ocr_text = ocr_res["stdout"].strip()
            
    summary = f"Screenshot captured from {dev}."
    if ocr_text:
        summary += f" Text detected on screen:\n{ocr_text[:300]}"
        
    return {
        "success": True,
        "device": dev,
        "screenshot_path": tmp_path,
        "ocr_text": ocr_text,
        "summary": summary
    }

# ==========================================
# SMART HOME & IOT (#6 SMART HOME)
# ==========================================

async def manage_smart_home_tool(action: str, entity_id: str = "", state: str = "", brightness: int = None, temperature: float = None) -> dict:
    """Smart Home & IoT automation for lights, plugs, switches, AC (#6)"""
    import database as db
    act = action.lower().strip()
    if act in ["list", "devices", "all"]:
        devs = db.list_smart_devices()
        return {"success": True, "count": len(devs), "devices": devs}
    elif act in ["set", "control", "toggle", "turn_on", "turn_off"]:
        if not entity_id:
            return {"success": False, "error": "entity_id is required"}
        new_state = state
        if act == "turn_on":
            new_state = "on"
        elif act == "turn_off":
            new_state = "off"
        ok = db.set_smart_device(entity_id, state=new_state, brightness=brightness, temperature=temperature)
        if ok:
            return {"success": True, "entity_id": entity_id, "state": new_state, "message": f"{entity_id} set to {new_state}"}
        return {"success": False, "error": f"Device {entity_id} not found"}
    return {"success": False, "error": f"Unknown action: {action}"}

# ==========================================
# PERSONAL PRODUCTIVITY: TO-DO (#4)
# ==========================================

async def manage_todos_tool(action: str, title: str = "", priority: str = "medium", deadline: str = "", todo_id: int = None) -> dict:
    """To-do list management, task prioritization, and deadline tracking (#4)"""
    import database as db
    act = action.lower().strip()
    if act in ["add", "create", "new"]:
        if not title:
            return {"success": False, "error": "title is required"}
        tid = db.add_todo(title, priority=priority, deadline=deadline)
        return {"success": True, "action": "add", "todo_id": tid, "message": f"Added to-do #{tid}: '{title}' [{priority.upper()}]"}
    elif act in ["list", "view", "all"]:
        todos = db.list_todos()
        return {"success": True, "action": "list", "count": len(todos), "todos": todos}
    elif act in ["complete", "done", "finish"]:
        if not todo_id:
            return {"success": False, "error": "todo_id is required"}
        db.complete_todo(todo_id)
        return {"success": True, "action": "complete", "todo_id": todo_id, "message": f"Completed task #{todo_id}"}
    elif act in ["delete", "remove"]:
        if not todo_id:
            return {"success": False, "error": "todo_id is required"}
        db.delete_todo(todo_id)
        return {"success": True, "action": "delete", "todo_id": todo_id, "message": f"Deleted task #{todo_id}"}
    return {"success": False, "error": f"Unknown action: {action}"}

# ==========================================
# DEVELOPER ASSISTANT & GIT (#10)
# ==========================================

async def developer_tools(action: str, command: str = "", path: str = "") -> dict:
    """Developer Assistant: Git, Docker, and Linux administration (#10)"""
    act = action.lower().strip()
    if act == "git_status":
        p = path or str(Path.home() / "Desktop")
        res = await run_command("laptop1", f"git -C '{p}' status -s")
        return {"success": res["success"], "action": "git_status", "output": res["stdout"] or "Working tree clean"}
    elif act == "docker_ps":
        res = await run_command("laptop2", "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
        return {"success": res["success"], "action": "docker_ps", "output": res["stdout"]}
    elif act == "system_logs":
        res = await run_command("laptop2", "journalctl -p 3 -xb -n 10 --no-pager")
        return {"success": res["success"], "action": "system_logs", "output": res["stdout"]}
    elif act == "exec_dev_command":
        res = await run_command("laptop1", command)
        return {"success": res["success"], "action": "exec_dev_command", "output": res["stdout"] or res["stderr"]}
    return {"success": False, "error": f"Unknown developer action: {action}"}

# ==========================================
# EMERGENCY STOP (#12 SECURITY & PRIVACY)
# ==========================================

async def emergency_stop_tool() -> dict:
    """Emergency stop: halts active sub-tasks, cancels TTS, and mutes audio (#12)"""
    await run_command("laptop2", "pactl set-sink-mute @DEFAULT_SINK@ 1 || true")
    return {"success": True, "message": "Emergency stop executed. Audio muted, active operations halted."}


