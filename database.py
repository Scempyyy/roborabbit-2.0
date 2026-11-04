import sqlite3
import json
import time
from pathlib import Path

DB_PATH = Path.home() / ".config" / "agy-assistant" / "chat_history.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                tool_events TEXT,
                created_at REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                date TEXT,
                category TEXT DEFAULT 'work',
                description TEXT,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                time_str TEXT,
                trigger_timestamp REAL,
                duration_seconds INTEGER DEFAULT 0,
                device TEXT DEFAULT 'laptop2',
                status TEXT DEFAULT 'active',
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                sender_email TEXT,
                recipient TEXT,
                subject TEXT,
                body TEXT,
                folder TEXT DEFAULT 'inbox',
                is_read INTEGER DEFAULT 0,
                is_starred INTEGER DEFAULT 0,
                received_at TEXT,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS phone_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT,
                package_name TEXT,
                title TEXT,
                content TEXT,
                timestamp TEXT,
                is_read INTEGER DEFAULT 0,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at REAL,
                updated_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                device TEXT DEFAULT 'laptop2',
                status TEXT DEFAULT 'success',
                details TEXT,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS smart_devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT DEFAULT 'light',
                state TEXT DEFAULT 'off',
                brightness INTEGER DEFAULT 100,
                color TEXT DEFAULT '#ffffff',
                temperature REAL DEFAULT 24.0,
                updated_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todo_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                deadline TEXT,
                status TEXT DEFAULT 'pending',
                created_at REAL
            )
        """)
        conn.commit()
        
        # Seed starter data if empty
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM smart_devices")
        if cur.fetchone()[0] == 0:
            now = time.time()
            devs = [
                ("light.office_desk", "Office Desk Ambient Arc Light", "light", "on", 85, "#00ffff", 24.0, now),
                ("light.ceiling_main", "Laboratory Overhead Main Lights", "light", "on", 70, "#ffffff", 24.0, now),
                ("switch.workstation_power", "Workstation Rig Power Supply", "switch", "on", 100, "", 24.0, now),
                ("climate.lab_ac", "Main Lab Climate AC Control", "climate", "cool", 100, "", 23.5, now)
            ]
            conn.executemany("INSERT INTO smart_devices (id, name, domain, state, brightness, color, temperature, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", devs)

        conn.commit()

def list_sessions():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM sessions ORDER BY updated_at DESC LIMIT 50")
        return [dict(r) for r in cur.fetchall()]

def create_session(session_id: str, title: str):
    init_db()
    now = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now)
        )
        conn.commit()

def save_message(session_id: str, role: str, content: str, tool_events: list = None):
    init_db()
    now = time.time()
    events_json = json.dumps(tool_events or [])
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_events, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, events_json, now)
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id)
        )
        conn.commit()

def get_session_messages(session_id: str):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["tool_events"] = json.loads(d["tool_events"])
            except Exception:
                d["tool_events"] = []
            result.append(d)
        return result

def delete_session(session_id: str):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()

def set_session_metadata(session_id: str, key: str, value: str):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_metadata (
                session_id TEXT,
                key TEXT,
                value TEXT,
                PRIMARY KEY (session_id, key)
            )
        """)
        conn.execute(
            "INSERT OR REPLACE INTO session_metadata (session_id, key, value) VALUES (?, ?, ?)",
            (session_id, key, value)
        )
        conn.commit()

def get_session_metadata(session_id: str, key: str):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_metadata (
                session_id TEXT,
                key TEXT,
                value TEXT,
                PRIMARY KEY (session_id, key)
            )
        """)
        cur = conn.cursor()
        cur.execute("SELECT value FROM session_metadata WHERE session_id = ? AND key = ?", (session_id, key))
        row = cur.fetchone()
        return row[0] if row else None

# ==========================================
# CALENDAR CRUD
# ==========================================

def list_calendar_events(date: str = None, limit: int = 50):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if date:
            cur.execute("SELECT * FROM calendar_events WHERE date = ? ORDER BY start_time ASC", (date,))
        else:
            cur.execute("SELECT * FROM calendar_events ORDER BY date ASC, start_time ASC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def add_calendar_event(title: str, start_time: str, end_time: str = "", date: str = "", category: str = "work", description: str = ""):
    init_db()
    if not date:
        date = time.strftime("%Y-%m-%d")
    now = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO calendar_events (title, start_time, end_time, date, category, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, start_time, end_time, date, category, description, now)
        )
        conn.commit()
        return cur.lastrowid

def delete_calendar_event(event_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
        conn.commit()
        return True

def get_today_events():
    today = time.strftime("%Y-%m-%d")
    return list_calendar_events(date=today)

# ==========================================
# ALARMS & TIMERS CRUD
# ==========================================

def list_alarms(status: str = None):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if status:
            cur.execute("SELECT * FROM alarms WHERE status = ? ORDER BY trigger_timestamp ASC", (status,))
        else:
            cur.execute("SELECT * FROM alarms ORDER BY trigger_timestamp ASC")
        return [dict(r) for r in cur.fetchall()]

def add_alarm(label: str, trigger_timestamp: float, time_str: str = "", duration_seconds: int = 0, device: str = "laptop2"):
    init_db()
    now = time.time()
    if not time_str and trigger_timestamp > 0:
        time_str = time.strftime("%H:%M", time.localtime(trigger_timestamp))
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO alarms (label, time_str, trigger_timestamp, duration_seconds, device, status, created_at) VALUES (?, ?, ?, ?, ?, 'active', ?)",
            (label, time_str, trigger_timestamp, duration_seconds, device, now)
        )
        conn.commit()
        return cur.lastrowid

def delete_alarm(alarm_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
        conn.commit()
        return True

def mark_alarm_triggered(alarm_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE alarms SET status = 'triggered' WHERE id = ?", (alarm_id,))
        conn.commit()

def dismiss_alarm(alarm_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE alarms SET status = 'dismissed' WHERE id = ?", (alarm_id,))
        conn.commit()
        return True

def get_due_alarms():
    init_db()
    now = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM alarms WHERE status = 'active' AND trigger_timestamp <= ?", (now,))
        return [dict(r) for r in cur.fetchall()]

# ==========================================
# EMAILS CRUD
# ==========================================

def list_emails(folder: str = "inbox", unread_only: bool = False, limit: int = 50):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if unread_only:
            cur.execute("SELECT * FROM emails WHERE folder = ? AND is_read = 0 ORDER BY created_at DESC LIMIT ?", (folder, limit))
        else:
            cur.execute("SELECT * FROM emails WHERE folder = ? ORDER BY created_at DESC LIMIT ?", (folder, limit))
        return [dict(r) for r in cur.fetchall()]

def get_email(email_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def send_local_email(recipient: str, subject: str, body: str, sender: str = "Me <admin@roborabbit.local>"):
    init_db()
    now = time.time()
    time_str = time.strftime("%I:%M %p")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO emails (sender, sender_email, recipient, subject, body, folder, is_read, is_starred, received_at, created_at) VALUES (?, ?, ?, ?, ?, 'sent', 1, 0, ?, ?)",
            (sender, "admin@roborabbit.local", recipient, subject, body, time_str, now)
        )
        conn.commit()
        return cur.lastrowid

def insert_inbox_email(sender: str, sender_email: str, recipient: str, subject: str, body: str, is_read: int = 0, is_starred: int = 0) -> int:
    init_db()
    now = time.time()
    time_str = time.strftime("%I:%M %p")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # Avoid duplicate email entries
        cur.execute("SELECT id FROM emails WHERE sender_email = ? AND subject = ? AND created_at > ?", (sender_email, subject, now - 86400))
        existing = cur.fetchone()
        if existing:
            return existing[0]
        cur.execute(
            "INSERT INTO emails (sender, sender_email, recipient, subject, body, folder, is_read, is_starred, received_at, created_at) VALUES (?, ?, ?, ?, ?, 'inbox', ?, ?, ?, ?)",
            (sender, sender_email, recipient, subject, body, is_read, is_starred, time_str, now)
        )
        conn.commit()
        return cur.lastrowid


def mark_email_read(email_id: int, is_read: int = 1):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE emails SET is_read = ? WHERE id = ?", (is_read, email_id))
        conn.commit()
        return True

def delete_email(email_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))
        conn.commit()
        return True

def count_unread_emails():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM emails WHERE folder = 'inbox' AND is_read = 0")
        return cur.fetchone()[0]

# ==========================================
# PHONE NOTIFICATIONS CRUD
# ==========================================

def list_phone_notifications(limit: int = 50):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM phone_notifications ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def add_phone_notification(app_name: str, title: str, content: str, package_name: str = "android", timestamp: str = None):
    init_db()
    now = time.time()
    if not timestamp:
        timestamp = time.strftime("%I:%M %p")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO phone_notifications (app_name, package_name, title, content, timestamp, is_read, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
            (app_name, package_name, title, content, timestamp, now)
        )
        conn.commit()
        return cur.lastrowid

def clear_phone_notifications():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM phone_notifications")
        conn.commit()
        return True

def mark_notification_read(notification_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE phone_notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        conn.commit()
        return True

def count_unread_notifications():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM phone_notifications WHERE is_read = 0")
        return cur.fetchone()[0]

# ==========================================
# PERSONAL NOTES & MEMORY VAULT
# ==========================================

def add_note(content: str, title: str = None, category: str = "general") -> int:
    init_db()
    now = time.time()
    if not title:
        title = content[:30].strip() + ("..." if len(content) > 30 else "")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notes (title, content, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (title, content, category, now, now)
        )
        conn.commit()
        return cur.lastrowid

def list_notes(category: str = None, search: str = None, limit: int = 20) -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]

def get_note(note_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def delete_note(note_id: int) -> bool:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        return True

# ==========================================
# AUDIT LOGS (SECURITY & PRIVACY #12)
# ==========================================

def add_audit_log(action: str, device: str = "laptop2", status: str = "success", details: str = "") -> int:
    init_db()
    now = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_logs (action, device, status, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (action, device, status, details, now)
        )
        conn.commit()
        return cur.lastrowid

def list_audit_logs(limit: int = 50) -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

# ==========================================
# SMART HOME & IOT (#6)
# ==========================================

def list_smart_devices() -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM smart_devices ORDER BY domain, name")
        return [dict(r) for r in cur.fetchall()]

def set_smart_device(device_id: str, state: str = None, brightness: int = None, color: str = None, temperature: float = None) -> bool:
    init_db()
    now = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM smart_devices WHERE id = ?", (device_id,))
        row = cur.fetchone()
        if not row:
            return False
        
        updates = ["updated_at = ?"]
        params = [now]
        if state is not None:
            updates.append("state = ?")
            params.append(state)
        if brightness is not None:
            updates.append("brightness = ?")
            params.append(brightness)
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        if temperature is not None:
            updates.append("temperature = ?")
            params.append(temperature)
            
        params.append(device_id)
        cur.execute(f"UPDATE smart_devices SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return True

# ==========================================
# PERSONAL PRODUCTIVITY: TO-DO (#4)
# ==========================================

def add_todo(title: str, priority: str = "medium", deadline: str = "") -> int:
    init_db()
    now = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO todo_tasks (title, priority, deadline, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (title, priority, deadline or "Today", now)
        )
        conn.commit()
        return cur.lastrowid

def list_todos(status: str = None) -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if status:
            cur.execute("SELECT * FROM todo_tasks WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cur.execute("SELECT * FROM todo_tasks ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, created_at DESC")
        return [dict(r) for r in cur.fetchall()]

def complete_todo(todo_id: int) -> bool:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE todo_tasks SET status = 'completed' WHERE id = ?", (todo_id,))
        conn.commit()
        return True

def delete_todo(todo_id: int) -> bool:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM todo_tasks WHERE id = ?", (todo_id,))
        conn.commit()
        return True
