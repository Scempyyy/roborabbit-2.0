import asyncio
import json
import re
import httpx
from typing import AsyncGenerator
from config import load_config
from tools import (
    run_command,
    get_all_devices,
    wake_laptop1_wol,
    connect_phone_adb,
    phone_open_url,
    read_file_content,
    write_file_content,
    list_directory_contents,
    fetch_internet_news,
    fetch_phone_notifications,
    manage_calendar_tool,
    manage_alarms_tool,
    manage_emails_tool,
    get_executive_briefing,
    manage_notes_tool,
    get_weather_tool,
    control_device_hardware,
    execute_jarvis_protocol,
    manage_application_tool,
    capture_screen_vision_tool,
    manage_smart_home_tool,
    manage_todos_tool,
    developer_tools,
    emergency_stop_tool,
    manage_integrations_tool,
    notion_tool,
    github_tool,
    media_player_tool,
    clipboard_tool,
    control_device_deep_tool,
    web_search_tool,
    browse_url_tool,
    deep_research_tool,
    morning_digest_tool,
    proactive_actions_tool,
    manage_memory_tool,
    execute_python_code_tool
)

TOOL_DEFINITIONS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command on Laptop, Server, or Mobile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "enum": ["laptop1", "laptop2", "phone"],
                        "description": "'laptop1' (Laptop), 'laptop2' (Server), 'phone' (Mobile)"
                    },
                    "command": {
                        "type": "string",
                        "description": "The exact shell command to execute"
                    }
                },
                "required": ["device", "command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Query real-time hardware, battery, and network health metrics across all 3 devices: Laptop, Server, and Mobile.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wake_laptop1",
            "description": "Send a Wake-on-LAN magic packet to wake Laptop from sleep.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "connect_phone",
            "description": "Connect to Mobile wirelessly via ADB over Wi-Fi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ip": {"type": "string", "description": "Phone IP address on Wi-Fi"},
                    "port": {"type": "integer", "description": "ADB port (usually 5555)", "default": 5555}
                },
                "required": ["ip"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "phone_open_url",
            "description": "Open a website or link directly in the browser on the user's Android phone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open on phone"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents from Laptop or Server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "enum": ["laptop1", "laptop2"]},
                    "filepath": {"type": "string", "description": "Absolute path to file"}
                },
                "required": ["device", "filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file on Laptop or Server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "enum": ["laptop1", "laptop2"]},
                    "filepath": {"type": "string", "description": "Absolute path to file"},
                    "content": {"type": "string", "description": "Text content to write"}
                },
                "required": ["device", "filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories on Laptop or Server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "enum": ["laptop1", "laptop2"]},
                    "path": {"type": "string", "description": "Directory path"}
                },
                "required": ["device"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "speak_announcement",
            "description": "Speak or broadcast an announcement out loud through the physical hardware speakers of Server or Laptop using high-quality JARVIS TTS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The message to speak out loud"
                    },
                    "device": {
                        "type": "string",
                        "enum": ["laptop2", "laptop1"],
                        "description": "'laptop2' for Server speakers, 'laptop1' for Laptop speakers"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_antigravity",
            "description": "Delegate a complex coding, software download/installation, repository editing, or autonomous agent task to Antigravity (AGY) on Laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The exact description of the technical or coding task for Antigravity"
                    }
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_internet_news",
            "description": "Fetch live internet intel and breaking headlines across categories ('all', 'tech', 'world', 'business', 'ai') when the user asks what is going on internet or what is the news.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["all", "tech", "world", "business", "ai"],
                        "description": "News topic category"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of stories to return (default 5)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_calendar",
            "description": "Manage user's personal calendar and schedule. Actions: 'today' (view today's agenda), 'list' (all upcoming events), 'add' (schedule new meeting/event), 'delete' (remove event).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["today", "list", "add", "delete"],
                        "description": "Calendar action"
                    },
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start time (e.g. 14:00 or 2:00 PM)"},
                    "end_time": {"type": "string", "description": "End time (e.g. 15:00)"},
                    "date": {"type": "string", "description": "Date (YYYY-MM-DD), defaults to today"},
                    "category": {"type": "string", "description": "work, meeting, personal, system"},
                    "event_id": {"type": "integer", "description": "Event ID for delete"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_alarms",
            "description": "Set, view, or dismiss alarms and timers. Actions: 'list', 'alarm' (set alarm at specific clock time), 'timer' (countdown timer in seconds), 'dismiss', 'delete'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "alarm", "timer", "dismiss", "delete"],
                        "description": "Alarm action"
                    },
                    "label": {"type": "string", "description": "Alarm or timer label"},
                    "time_str": {"type": "string", "description": "Clock time e.g. 07:30 or 7:30 AM"},
                    "duration_seconds": {"type": "integer", "description": "Duration for timers in seconds (e.g. 300 for 5 min)"},
                    "device": {"type": "string", "enum": ["laptop2", "laptop1", "phone"], "description": "Target device for the alarm"},
                    "alarm_id": {"type": "integer", "description": "Alarm ID for delete/dismiss"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_emails",
            "description": "Check unread emails, view mailbox folders, read full email content, or compose new emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "read", "send"],
                        "description": "Email action"
                    },
                    "folder": {"type": "string", "enum": ["inbox", "sent", "archive"], "default": "inbox"},
                    "unread_only": {"type": "boolean", "description": "Only show unread emails"},
                    "email_id": {"type": "integer", "description": "Email ID to read"},
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email text content"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_phone_notifications",
            "description": "Query live and recent notifications on the user's mobile phone via ADB or notification sync.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sync_adb": {"type": "boolean", "description": "Whether to query wireless ADB"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_executive_briefing",
            "description": "Generate a full JARVIS executive morning/day briefing: local time, device statuses, today's calendar events, unread emails, phone alerts, and top breaking news.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_notes",
            "description": "Save, recall, search, or delete notes and memories in the persistent memory vault. Actions: 'add' (save new note/memory), 'list' (view all notes), 'get' (read specific note), 'delete' (remove note).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "list", "get", "delete"],
                        "description": "Note action"
                    },
                    "content": {"type": "string", "description": "Note or memory text content to store"},
                    "title": {"type": "string", "description": "Optional title for note"},
                    "category": {"type": "string", "description": "Category e.g. general, work, personal, idea", "default": "general"},
                    "search": {"type": "string", "description": "Keyword search query for list"},
                    "note_id": {"type": "integer", "description": "Note ID for get or delete"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get real-time weather conditions, temperature, humidity, and forecasts for current location or specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, or 'auto' for current location",
                        "default": "auto"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_device_hardware",
            "description": "Control hardware features across Mobile, Laptop, or Server (vibrate mobile, open YouTube, mute/unmute audio, volume control, lock screen, blackout display).",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "enum": ["phone", "laptop1", "laptop2"],
                        "description": "Target device ('phone' for Mobile, 'laptop1' for Laptop, 'laptop2' for Server)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["vibrate", "youtube", "lock", "wake", "volume_up", "volume_down", "mute", "screenshot", "set_volume", "screen_off", "media_play_pause"],
                        "description": "Hardware action to execute"
                    },
                    "parameter": {
                        "type": "string",
                        "description": "Optional parameter (e.g. search query for YouTube, vibration duration ms, volume percentage)"
                    }
                },
                "required": ["device", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_jarvis_protocol",
            "description": "Execute specialized JARVIS protocols: 'briefing' (morning/day status briefing), 'diagnostic' (deep 3-node system health sweep), 'house_party' (high energy music & audio setup), 'focus' (distraction-free work mode).",
            "parameters": {
                "type": "object",
                "properties": {
                    "protocol": {
                        "type": "string",
                        "enum": ["briefing", "diagnostic", "house_party", "focus"],
                        "description": "Protocol identifier"
                    },
                    "parameter": {
                        "type": "string",
                        "description": "Optional parameter for protocol"
                    }
                },
                "required": ["protocol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_application",
            "description": "Open or close applications or inspect active processes on Laptop, Server, or Mobile (#3 Computer Control).",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "enum": ["laptop1", "laptop2", "phone"], "description": "Target device"},
                    "action": {"type": "string", "enum": ["open", "close", "list"], "description": "Application action"},
                    "app_name": {"type": "string", "description": "Name or executable of the application"}
                },
                "required": ["device", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_screen_vision",
            "description": "Capture a live screenshot and extract on-screen text with OCR from Laptop or Mobile (#3 Screen, #11 Vision).",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "enum": ["laptop1", "phone", "laptop2"], "default": "laptop1"},
                    "run_ocr": {"type": "boolean", "default": True, "description": "Extract text using OCR"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_smart_home",
            "description": "Control smart home devices, lights, switches, AC, or list all IoT devices (#6 Smart Home).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "turn_on", "turn_off", "set"], "description": "Smart home action"},
                    "entity_id": {"type": "string", "description": "Device ID (e.g. light.office_desk, climate.lab_ac)"},
                    "state": {"type": "string", "description": "Target state ('on', 'off', 'cool')"},
                    "brightness": {"type": "integer", "description": "Brightness 0-100"},
                    "temperature": {"type": "number", "description": "Target temperature in Celsius"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_todos",
            "description": "Manage tasks, to-do lists, priorities, and deadlines (#4 Personal Productivity). Actions: 'add', 'list', 'complete', 'delete'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "list", "complete", "delete"], "description": "Todo action"},
                    "title": {"type": "string", "description": "Task description"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"], "default": "medium"},
                    "deadline": {"type": "string", "description": "Deadline (e.g. Today, Tomorrow, 17:00)"},
                    "todo_id": {"type": "integer", "description": "Task ID for complete or delete"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "developer_tools",
            "description": "Developer Assistant: inspect Git status, Docker containers, system logs, or run development scripts (#10 Developer Assistant).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["git_status", "docker_ps", "system_logs", "exec_dev_command"], "description": "Developer action"},
                    "command": {"type": "string", "description": "Command for exec_dev_command"},
                    "path": {"type": "string", "description": "Repository path"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emergency_stop",
            "description": "Trigger an immediate emergency stop: halts active sub-tasks, cancels TTS speech, and mutes audio (#12 Security & Privacy).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_integrations",
            "description": "Manage connected accounts and integrations (Gmail, Notion, GitHub, LinkedIn, Instagram, Spotify, Telegram).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "get", "save", "delete", "test"], "description": "Action"},
                    "service": {"type": "string", "description": "Service name (gmail, notion, github, linkedin, instagram, spotify, telegram)"},
                    "credentials": {"type": "object", "description": "Credentials map"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notion_tool",
            "description": "Search, read, or create pages and notes in Notion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["search", "list_pages", "create_page", "add_note"]},
                    "title": {"type": "string", "description": "Page or note title"},
                    "content": {"type": "string", "description": "Page content"},
                    "database_id": {"type": "string", "description": "Optional target Notion database ID"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_tool",
            "description": "Inspect GitHub repositories, pull requests, issues, or create an issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list_repos", "create_issue", "status"]},
                    "repo": {"type": "string", "description": "Target repository, e.g. 'owner/repo'"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue description"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_player",
            "description": "Control system media playback (Spotify, YouTube, browser audio) using playerctl.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "enum": ["laptop1", "laptop2", "phone"], "description": "Target device"},
                    "action": {"type": "string", "enum": ["play_pause", "play", "pause", "next", "previous", "status", "volume"]},
                    "parameter": {"type": "string", "description": "Optional parameter such as volume percentage"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clipboard",
            "description": "Read, write, or sync system clipboard across Laptop, Server, and Mobile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "enum": ["laptop1", "laptop2", "phone"]},
                    "action": {"type": "string", "enum": ["read", "write", "sync"]},
                    "text": {"type": "string", "description": "Text to copy"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_device_deep",
            "description": "Execute deep OS-level or Mobile phone controls: mouse clicks, cursor moves, typing text, keypresses, brightness, volume, locating phone beacon, phone dialing, SMS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "enum": ["laptop1", "laptop2", "phone"], "description": "Target device"},
                    "action": {"type": "string", "enum": ["mouse_click", "mouse_move", "type", "key", "brightness", "volume", "mute", "unmute", "lock", "locate", "vibrate", "dial", "sms", "open_app", "open_url"], "description": "Action"},
                    "parameter": {"type": "string", "description": "Action argument (e.g. coordinates '100 200', text to type, phone number, app name, volume level)"}
                },
                "required": ["target", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Live internet search across web and news using You.com and Google intel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or question"},
                    "max_results": {"type": "integer", "description": "Number of results to return (default 5)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browse_url",
            "description": "Fetch a web page or documentation URL and extract clean readable text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch and read"},
                    "max_chars": {"type": "integer", "description": "Maximum characters to extract (default 4000)"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deep_research",
            "description": "Autonomous multi-hop web research agent: searches web, reads top articles, and synthesizes cited findings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic or complex question to research"},
                    "depth": {"type": "string", "enum": ["standard", "thorough"], "description": "Depth of analysis"}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "morning_digest",
            "description": "OpenJarvis executive spoken daily briefing: calendar agenda, unread phone alerts, urgent emails, pending todos, environmental weather, and multi-device vitals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "honorific": {"type": "string", "description": "Preferred honorific (e.g. 'sir')"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "proactive_actions",
            "description": "OpenJarvis Autonomous Proactive Action Approval Store: list pending actions, propose an action, or approve/deny an action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "propose", "approve", "deny"], "description": "Action to perform"},
                    "action_id": {"type": "integer", "description": "Action ID to approve or deny"},
                    "decision": {"type": "string", "enum": ["yes", "no", "always_approve", "always_deny"], "description": "Decision choice"},
                    "action_type": {"type": "string", "description": "Type of action if proposing (e.g. 'shell_command', 'phone_command', 'docker_restart')"},
                    "description": {"type": "string", "description": "Human explanation of the action"},
                    "payload": {"type": "object", "description": "Action data payload"},
                    "tier": {"type": "string", "enum": ["trivial", "low", "medium", "high"], "description": "Risk tier"},
                    "permission_key": {"type": "string", "description": "Pattern key (e.g. 'docker_restart:homelab')"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_memory",
            "description": "OpenJarvis User Profile and Long-Term Memory: store, recall, or search remembered facts and preferences about the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["store", "recall", "list", "delete"], "description": "Memory action"},
                    "key": {"type": "string", "description": "Memory key or topic (e.g. 'favorite_editor', 'working_hours')"},
                    "value": {"type": "string", "description": "Fact or preference to remember"},
                    "category": {"type": "string", "enum": ["general", "preference", "contact", "habit", "project"], "description": "Category"},
                    "query": {"type": "string", "description": "Search query if recalling"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "CodeAct Python REPL: execute arbitrary Python code safely to perform math, format datasets, parse content, or test algorithms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code snippet to execute"}
                },
                "required": ["code"]
            }
        }
    }
]

async def execute_tool(name: str, args: dict) -> tuple[dict, dict]:
    """Returns (tool_event_data, tool_result_for_llm)"""
    device = args.get("device", args.get("host", "laptop2"))
    
    if name == "run_command":
        cmd = args.get("command", "")
        res = await run_command(device, cmd)
        return res, res
    elif name == "get_system_status":
        res = await get_all_devices()
        event_data = {
            "success": True,
            "host": "all",
            "host_display": "🌐 All 3 Devices",
            "command": "get_system_status()",
            "stdout": json.dumps(res, indent=2),
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 180
        }
        return event_data, res
    elif name == "wake_laptop1":
        res = wake_laptop1_wol()
        event_data = {
            "success": res.get("success", False),
            "host": "laptop1",
            "host_display": "💻 Laptop (WoL)",
            "command": "wake_laptop1_wol()",
            "stdout": res.get("message", ""),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 10
        }
        return event_data, res
    elif name == "connect_phone":
        ip = args.get("ip", "")
        port = args.get("port", 5555)
        res = await connect_phone_adb(ip, port)
        return res, res
    elif name == "phone_open_url":
        url = args.get("url", "")
        res = await phone_open_url(url)
        return res, res
    elif name == "read_file":
        path = args.get("filepath", "")
        res = await read_file_content(device, path)
        event_data = {
            "success": res.get("success", False),
            "host": device,
            "host_display": f"{device} (read {path})",
            "command": f"cat '{path}'",
            "stdout": res.get("content", ""),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 40
        }
        return event_data, res
    elif name == "write_file":
        path = args.get("filepath", "")
        content = args.get("content", "")
        res = await write_file_content(device, path, content)
        return res, res
    elif name == "list_directory":
        path = args.get("path", "")
        res = await list_directory_contents(device, path)
        return res, res
    elif name == "speak_announcement":
        text = args.get("text", "")
        target_dev = args.get("device", "laptop2")
        from tools import speak_announcement
        res = await speak_announcement(text, target_dev)
        event_data = {
            "success": res.get("success", False),
            "host": target_dev,
            "host_display": f"🔊 Hardware Speaker ({target_dev})",
            "command": f"speak_announcement('{text[:35]}...')",
            "stdout": res.get("message", ""),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 300
        }
        return event_data, res
    elif name == "delegate_to_antigravity":
        task = args.get("task", "")
        event_data = {
            "success": True,
            "host": "laptop1",
            "host_display": "⚡ Antigravity (Laptop)",
            "command": f"agy: {task}",
            "stdout": f"Delegated to Antigravity: {task}",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 50
        }
        return event_data, {"status": "delegated_to_agy", "task": task}
    elif name == "get_internet_news":
        cat = args.get("category", "all")
        limit = args.get("limit", 5)
        res = await fetch_internet_news(cat, limit)
        event_data = {
            "success": res.get("success", False),
            "host": "internet",
            "host_display": f"🌐 Internet Radar ({cat.upper()})",
            "command": f"fetch_internet_news(category='{cat}', limit={limit})",
            "stdout": f"Fetched {res.get('count', 0)} stories:\n" + "\n".join([f"- {s['title']} ({s['source']})" for s in res.get("stories", [])[:4]]),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 150
        }
        return event_data, res
    elif name == "manage_calendar":
        action = args.get("action", "today")
        res = await manage_calendar_tool(
            action=action,
            title=args.get("title", ""),
            start_time=args.get("start_time", ""),
            end_time=args.get("end_time", ""),
            date=args.get("date", ""),
            category=args.get("category", "work"),
            description=args.get("description", ""),
            event_id=args.get("event_id")
        )
        event_data = {
            "success": res.get("success", False),
            "host": "laptop2",
            "host_display": "📅 Personal Calendar",
            "command": f"manage_calendar(action='{action}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 20
        }
        return event_data, res
    elif name == "manage_alarms":
        action = args.get("action", "list")
        res = await manage_alarms_tool(
            action=action,
            label=args.get("label", "Alarm"),
            time_str=args.get("time_str", ""),
            duration_seconds=args.get("duration_seconds", 0),
            device=args.get("device", "laptop2"),
            alarm_id=args.get("alarm_id")
        )
        event_data = {
            "success": res.get("success", False),
            "host": args.get("device", "laptop2"),
            "host_display": f"⏰ Alarms & Timers ({args.get('device', 'server')})",
            "command": f"manage_alarms(action='{action}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 30
        }
        return event_data, res
    elif name == "manage_emails":
        action = args.get("action", "list")
        res = await manage_emails_tool(
            action=action,
            folder=args.get("folder", "inbox"),
            unread_only=args.get("unread_only", False),
            email_id=args.get("email_id"),
            to=args.get("to", ""),
            subject=args.get("subject", ""),
            body=args.get("body", "")
        )
        event_data = {
            "success": res.get("success", False),
            "host": "laptop2",
            "host_display": "✉️ Mailbox Hub",
            "command": f"manage_emails(action='{action}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 25
        }
        return event_data, res
    elif name == "get_phone_notifications":
        sync_adb = args.get("sync_adb", True)
        res = await fetch_phone_notifications(sync_adb=sync_adb)
        event_data = {
            "success": res.get("success", False),
            "host": "phone",
            "host_display": "📱 Phone Notifications",
            "command": "fetch_phone_notifications()",
            "stdout": f"Found {res.get('total', 0)} notifications ({res.get('unread_count', 0)} unread):\n" + "\n".join([f"- [{n['app_name']}] {n['title']}: {n['content']}" for n in res.get("notifications", [])[:3]]),
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 120
        }
        return event_data, res
    elif name == "get_executive_briefing":
        res = await get_executive_briefing()
        event_data = {
            "success": True,
            "host": "all",
            "host_display": "⚡ JARVIS Executive Briefing",
            "command": "get_executive_briefing()",
            "stdout": json.dumps(res, indent=2),
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 250
        }
        return event_data, res
    elif name == "manage_notes":
        action = args.get("action", "list")
        res = await manage_notes_tool(
            action=action,
            content=args.get("content", ""),
            title=args.get("title", ""),
            category=args.get("category", "general"),
            search=args.get("search", ""),
            note_id=args.get("note_id")
        )
        event_data = {
            "success": res.get("success", False),
            "host": "laptop2",
            "host_display": "📝 Memory Vault (Notes)",
            "command": f"manage_notes(action='{action}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 15
        }
        return event_data, res
    elif name == "get_weather":
        loc = args.get("location", "auto")
        res = await get_weather_tool(location=loc)
        event_data = {
            "success": res.get("success", False),
            "host": "internet",
            "host_display": "🌤️ Environmental Intelligence",
            "command": f"get_weather(location='{loc}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 180
        }
        return event_data, res
    elif name == "control_device_hardware":
        dev = args.get("device", "phone")
        act = args.get("action", "")
        param = args.get("parameter", "")
        res = await control_device_hardware(dev, act, param)
        event_data = {
            "success": res.get("success", False),
            "host": dev,
            "host_display": f"⚡ Hardware Controller ({dev})",
            "command": f"control_hardware({dev}, {act})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 80
        }
        return event_data, res
    elif name == "execute_jarvis_protocol":
        prot = args.get("protocol", "briefing")
        param = args.get("parameter", "")
        res = await execute_jarvis_protocol(prot, param)
        event_data = {
            "success": res.get("success", False),
            "host": "all",
            "host_display": f"🛡️ Protocol: {prot.upper()}",
            "command": f"execute_protocol('{prot}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 220
        }
        return event_data, res
    elif name == "manage_application":
        dev = args.get("device", "laptop1")
        act = args.get("action", "list")
        app = args.get("app_name", "")
        res = await manage_application_tool(dev, act, app)
        event_data = {
            "success": res.get("success", False),
            "host": dev,
            "host_display": f"🖥️ App Manager ({dev})",
            "command": f"manage_app({dev}, {act}, {app})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 100
        }
        return event_data, res
    elif name == "capture_screen_vision":
        dev = args.get("device", "laptop1")
        run_ocr = args.get("run_ocr", True)
        res = await capture_screen_vision_tool(dev, run_ocr)
        event_data = {
            "success": res.get("success", False),
            "host": dev,
            "host_display": f"👁️ Screen Vision ({dev})",
            "command": f"capture_screen({dev})",
            "stdout": res.get("summary", ""),
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 300
        }
        return event_data, res
    elif name == "manage_smart_home":
        act = args.get("action", "list")
        entity_id = args.get("entity_id", "")
        st = args.get("state", "")
        bright = args.get("brightness")
        temp = args.get("temperature")
        res = await manage_smart_home_tool(act, entity_id, st, bright, temp)
        event_data = {
            "success": res.get("success", False),
            "host": "iot",
            "host_display": "🏠 Smart Home & IoT",
            "command": f"smart_home({act}, {entity_id})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 40
        }
        return event_data, res
    elif name == "manage_todos":
        act = args.get("action", "list")
        title = args.get("title", "")
        prio = args.get("priority", "medium")
        dl = args.get("deadline", "")
        tid = args.get("todo_id")
        res = await manage_todos_tool(act, title, prio, dl, tid)
        event_data = {
            "success": res.get("success", False),
            "host": "laptop2",
            "host_display": "📋 Task Manager (To-Do)",
            "command": f"manage_todos({act})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 20
        }
        return event_data, res
    elif name == "developer_tools":
        act = args.get("action", "git_status")
        cmd = args.get("command", "")
        p = args.get("path", "")
        res = await developer_tools(act, cmd, p)
        event_data = {
            "success": res.get("success", False),
            "host": "laptop1",
            "host_display": f"💻 Developer Tools ({act})",
            "command": f"developer_tools({act})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 120
        }
        return event_data, res
    elif name == "emergency_stop":
        res = await emergency_stop_tool()
        event_data = {
            "success": True,
            "host": "all",
            "host_display": "🛑 Emergency Stop",
            "command": "emergency_stop()",
            "stdout": res.get("message", ""),
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 50
        }
        return event_data, res
    elif name == "manage_integrations":
        act = args.get("action", "list")
        srv = args.get("service", "")
        creds = args.get("credentials")
        res = await manage_integrations_tool(act, srv, creds)
        event_data = {
            "success": res.get("success", False),
            "host": "cloud",
            "host_display": f"🔌 Integrations Hub ({srv or act})",
            "command": f"manage_integrations({act}, {srv})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 80
        }
        return event_data, res
    elif name == "notion_tool":
        act = args.get("action", "search")
        t = args.get("title", "")
        c = args.get("content", "")
        db_id = args.get("database_id", "")
        res = await notion_tool(act, t, c, db_id)
        event_data = {
            "success": res.get("success", False),
            "host": "cloud",
            "host_display": f"📝 Notion Workspace ({act})",
            "command": f"notion({act}, '{t}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 150
        }
        return event_data, res
    elif name == "github_tool":
        act = args.get("action", "list_repos")
        repo = args.get("repo", "")
        t = args.get("title", "")
        b = args.get("body", "")
        res = await github_tool(act, repo, t, b)
        event_data = {
            "success": res.get("success", False),
            "host": "cloud",
            "host_display": f"🐙 GitHub Command ({act})",
            "command": f"github({act}, {repo})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 120
        }
        return event_data, res
    elif name == "media_player":
        dev = args.get("device", "laptop1")
        act = args.get("action", "play_pause")
        param = args.get("parameter", "")
        res = await media_player_tool(dev, act, param)
        event_data = {
            "success": res.get("success", False),
            "host": dev,
            "host_display": f"🎵 Media Player ({dev})",
            "command": f"playerctl({act})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 40
        }
        return event_data, res
    elif name == "clipboard":
        dev = args.get("device", "laptop1")
        act = args.get("action", "read")
        txt = args.get("text", "")
        res = await clipboard_tool(dev, act, txt)
        event_data = {
            "success": res.get("success", False),
            "host": dev,
            "host_display": f"📋 Cross-Clipboard ({dev})",
            "command": f"clipboard({act})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 30
        }
        return event_data, res
    elif name == "control_device_deep":
        tgt = args.get("target", "laptop1")
        act = args.get("action", "mouse_click")
        param = args.get("parameter", "")
        res = await control_device_deep_tool(tgt, act, param)
        event_data = {
            "success": res.get("success", False),
            "host": tgt,
            "host_display": f"🕹️ Deep Hardware Control ({tgt})",
            "command": f"deep_control({tgt}, {act}, '{param}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 70
        }
        return event_data, res
    elif name == "web_search":
        q = args.get("query", "")
        max_r = args.get("max_results", 5)
        res = await web_search_tool(query=q, max_results=max_r)
        event_data = {
            "success": res.get("success", False),
            "host": "internet",
            "host_display": f"🔎 Live Web Search",
            "command": f"web_search('{q[:40]}')",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 200
        }
        return event_data, res
    elif name == "browse_url":
        url = args.get("url", "")
        max_c = args.get("max_chars", 4000)
        res = await browse_url_tool(url=url, max_chars=max_c)
        event_data = {
            "success": res.get("success", False),
            "host": "internet",
            "host_display": f"🌐 Page Content ({url[:30]}...)",
            "command": f"browse_url('{url}')",
            "stdout": res.get("content", "")[:500] + ("..." if len(res.get("content", "")) > 500 else ""),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 300
        }
        return event_data, res
    elif name == "deep_research":
        topic = args.get("topic", "")
        depth = args.get("depth", "standard")
        res = await deep_research_tool(topic=topic, depth=depth)
        event_data = {
            "success": res.get("success", False),
            "host": "internet",
            "host_display": f"🧠 Deep Multi-Hop Research",
            "command": f"deep_research('{topic[:35]}')",
            "stdout": res.get("summary", ""),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 1200
        }
        return event_data, res
    elif name == "morning_digest":
        honorific = args.get("honorific", "sir")
        res = await morning_digest_tool(honorific=honorific)
        event_data = {
            "success": True,
            "host": "all",
            "host_display": f"🌅 Morning Executive Digest",
            "command": f"morning_digest(honorific='{honorific}')",
            "stdout": res.get("spoken_briefing", ""),
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 250
        }
        return event_data, res
    elif name == "proactive_actions":
        act = args.get("action", "list")
        res = await proactive_actions_tool(
            action=act,
            action_id=args.get("action_id"),
            decision=args.get("decision", ""),
            action_type=args.get("action_type", ""),
            description=args.get("description", ""),
            payload=args.get("payload"),
            tier=args.get("tier", "medium"),
            permission_key=args.get("permission_key", "")
        )
        event_data = {
            "success": res.get("success", False),
            "host": "laptop2",
            "host_display": f"🛡️ Proactive Approval Store ({act})",
            "command": f"proactive_actions({act})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 50
        }
        return event_data, res
    elif name == "manage_memory":
        act = args.get("action", "list")
        res = await manage_memory_tool(
            action=act,
            key=args.get("key", ""),
            value=args.get("value", ""),
            category=args.get("category", "general"),
            query=args.get("query", "")
        )
        event_data = {
            "success": res.get("success", False),
            "host": "laptop2",
            "host_display": f"🧠 User Memory & Profile ({act})",
            "command": f"manage_memory({act})",
            "stdout": json.dumps(res, indent=2),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 30
        }
        return event_data, res
    elif name == "execute_python_code":
        code_str = args.get("code", "")
        res = await execute_python_code_tool(code=code_str)
        event_data = {
            "success": res.get("success", False),
            "host": "laptop2",
            "host_display": "🐍 CodeAct Python REPL",
            "command": "python3 -c <code>",
            "stdout": res.get("stdout", "") or "(No output)",
            "stderr": res.get("stderr", "") or res.get("error", ""),
            "exit_code": res.get("exit_code", 0),
            "duration_ms": res.get("duration_ms", 50)
        }
        return event_data, res
    else:
        err = {"error": f"Unknown tool: {name}"}
        return {"success": False, "command": name, "stderr": f"Unknown tool {name}", "exit_code": 1}, err

async def local_fallback_agent(user_message: str) -> AsyncGenerator[dict, None]:
    """Smart built-in offline handler for common commands and pattern matches"""
    msg_lower = user_message.lower().strip()
    
    # 0. Connected devices direct answer
    if any(q in msg_lower for q in [
        "how much device", "how many device", "what device", 
        "which device", "connected device", "devices connected", "devices are we connected"
    ]):
        yield {"type": "content", "delta": "We are connected to 3 devices: your phone, your main laptop, and this server."}
        return

    # 0.1 Morning / Daily Digest (OpenJarvis Architecture)
    if any(q in msg_lower for q in ["morning digest", "daily digest", "morning briefing", "daily briefing", "executive digest", "give me my briefing"]):
        yield {"type": "tool_call", "host": "all", "command": "morning_digest(honorific='sir')"}
        digest_res = await morning_digest_tool(honorific="sir")
        yield {
            "type": "tool_result",
            "host": "all",
            "host_display": "🌅 Morning Executive Digest",
            "command": "morning_digest()",
            "stdout": digest_res.get("spoken_briefing", ""),
            "exit_code": 0,
            "duration_ms": 150
        }
        yield {"type": "content", "delta": digest_res.get("spoken_briefing", "All systems operational, sir.")}
        return

    # 0.2 Proactive Actions & Approval Decisions (OpenJarvis Architecture)
    if any(q in msg_lower for q in ["pending action", "pending approval", "what needs approval", "approval queue", "show approvals"]):
        yield {"type": "tool_call", "host": "laptop2", "command": "proactive_actions('list')"}
        actions_res = await proactive_actions_tool("list")
        yield {
            "type": "tool_result",
            "host": "laptop2",
            "host_display": "🛡️ Proactive Approval Store",
            "command": "proactive_actions(list)",
            "stdout": json.dumps(actions_res, indent=2),
            "exit_code": 0,
            "duration_ms": 30
        }
        items = actions_res.get("pending_actions", [])
        if not items:
            yield {"type": "content", "delta": "No actions currently awaiting your approval, sir. All autonomous sentinel tasks are clear."}
        else:
            list_str = "\n".join([f"- **#{it['id']}** [{it.get('tier', 'medium').upper()}]: {it['description']}" for it in items[:4]])
            yield {"type": "content", "delta": f"There {'are' if len(items) > 1 else 'is'} {len(items)} action{'s' if len(items) > 1 else ''} awaiting your approval, sir:\n{list_str}\n\n*Reply 'approve <id>' or 'deny <id>'.*"}
        return

    approve_match = re.search(r"\b(approve|yes|deny|no|always approve|always deny)\s+(\d+|all)\b", msg_lower)
    if approve_match:
        dec_word = approve_match.group(1)
        target_id_str = approve_match.group(2)
        if target_id_str.isdigit():
            act_id = int(target_id_str)
            dec_type = "always_approve" if "always" in dec_word and "approve" in dec_word else ("always_deny" if "always" in dec_word else ("approve" if dec_word in ["approve", "yes"] else "deny"))
            yield {"type": "tool_call", "host": "laptop2", "command": f"proactive_actions({dec_type}, #{act_id})"}
            dec_res = await proactive_actions_tool("approve" if "approve" in dec_type else "deny", action_id=act_id, decision=dec_type)
            yield {
                "type": "tool_result",
                "host": "laptop2",
                "host_display": "🛡️ Proactive Approval Store",
                "command": f"proactive_actions(action_id={act_id}, decision='{dec_type}')",
                "stdout": json.dumps(dec_res, indent=2),
                "exit_code": 0,
                "duration_ms": 40
            }
            if dec_res.get("success"):
                yield {"type": "content", "delta": f"Action #{act_id} has been {dec_type.replace('_', ' ')}d, sir."}
            else:
                yield {"type": "content", "delta": f"Could not process action #{act_id}: {dec_res.get('error', 'action not found')}."}
            return

    # 0.3 Long-term Memory & Profile (OpenJarvis Architecture)
    if "remember that" in msg_lower or "remember my" in msg_lower:
        fact = re.sub(r"^(please\s+)?(can\s+you\s+)?remember\s+(that\s+|my\s+)?", "", user_message, flags=re.I).strip()
        if fact:
            key_part = fact.split(" is ")[0] if " is " in fact else (fact.split(" are ")[0] if " are " in fact else "user_fact")
            val_part = fact.split(" is ", 1)[1] if " is " in fact else (fact.split(" are ", 1)[1] if " are " in fact else fact)
            yield {"type": "tool_call", "host": "laptop2", "command": f"manage_memory(store, '{key_part[:20]}')"}
            mem_res = await manage_memory_tool("store", key=key_part[:30], value=val_part, category="preference")
            yield {
                "type": "tool_result",
                "host": "laptop2",
                "host_display": "🧠 Memory Vault",
                "command": f"manage_memory(store, key='{key_part}')",
                "stdout": json.dumps(mem_res, indent=2),
                "exit_code": 0,
                "duration_ms": 20
            }
            yield {"type": "content", "delta": f"I have committed that to memory, sir: {key_part} is {val_part}."}
            return

    if any(q in msg_lower for q in ["what do you remember", "my preferences", "recall memory", "user profile"]):
        yield {"type": "tool_call", "host": "laptop2", "command": "manage_memory(list)"}
        mem_res = await manage_memory_tool("list")
        yield {
            "type": "tool_result",
            "host": "laptop2",
            "host_display": "🧠 Memory Vault",
            "command": "manage_memory(list)",
            "stdout": json.dumps(mem_res, indent=2),
            "exit_code": 0,
            "duration_ms": 20
        }
        mems = mem_res.get("memories", [])
        if not mems:
            yield {"type": "content", "delta": "Your long-term memory vault is currently empty, sir."}
        else:
            facts_str = "\n".join([f"- **{m['key']}**: {m['value']}" for m in mems[:5]])
            yield {"type": "content", "delta": f"Here is what I have stored in your profile, sir:\n{facts_str}"}
        return

    # 1. System Health / Status across all 3 devices
    if any(k in msg_lower for k in ["status", "health", "metrics", "stats", "hardware"]):
        yield {"type": "tool_call", "host": "all", "command": "get_all_devices()"}
        res = await get_all_devices()
        yield {
            "type": "tool_result",
            "host": "all",
            "host_display": "🌐 Laptop, Server & Mobile",
            "command": "get_all_devices()",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0,
            "duration_ms": 200
        }
        
        l1 = res.get("laptop1", {})
        l2 = res.get("laptop2", {})
        phone = res.get("phone", {})
        
        reply = (
            f"### 🐰 RoboRabbit Multi-Device Status\n\n"
            f"**💻 Laptop**: {'🟢 Online' if l1.get('online') else '⚪ Asleep / Offline'}\n"
        )
        if l1.get("online"):
            reply += f"- **Uptime**: {l1.get('uptime', 'N/A')}\n- **RAM**: {l1.get('ram_percent', 0)}%\n- **Battery**: {l1.get('battery', 'N/A')}\n\n"
        else:
            reply += f"- *Status*: Currently sleeping. Wake it with: `wake laptop`\n\n"
            
        reply += (
            f"**🖥️ Server**: {'🟢 Online' if l2.get('online') else '🔴 Offline'}\n"
            f"- **Uptime**: {l2.get('uptime', 'N/A')}\n"
            f"- **RAM**: {l2.get('ram_used_gib', 0)} / {l2.get('ram_total_gib', 0)} GiB ({l2.get('ram_percent', 0)}%)\n"
            f"- **Disk (`/`)**: {l2.get('disk_usage', 'N/A')} used (Free: {l2.get('disk_free', 'N/A')})\n"
            f"- **Temp**: {l2.get('temperature', 'N/A')}\n"
            f"- **Containers**: {l2.get('docker_containers', 0)} running\n\n"
        )
        
        reply += f"**📱 Mobile**: {'🟢 Connected' if phone.get('online') else '⚪ Standby'}\n"
        if phone.get("online"):
            reply += f"- **Device**: {phone.get('name', 'Mobile')}\n- **Battery**: {phone.get('battery', 'N/A')}\n"
        else:
            reply += f"- *Status*: Wireless ADB standby. Connect via: `connect mobile <ip>`\n"
            
        yield {"type": "content", "delta": reply}
        return

    # 2. Wake-on-LAN for Laptop
    if any(k in msg_lower for k in ["wake", "power on", "wol", "turn on laptop", "wake laptop", "turn on main"]):
        yield {"type": "tool_call", "host": "laptop1", "command": "wake_laptop1_wol()"}
        wol_res = wake_laptop1_wol()
        yield {
            "type": "tool_result",
            "host": "laptop1",
            "host_display": "💻 Laptop (WoL)",
            "command": "wake_laptop1_wol()",
            "stdout": wol_res.get("message", "Magic packet broadcasted"),
            "exit_code": 0,
            "duration_ms": 10
        }
        yield {"type": "content", "delta": "⚡ **Wake-on-LAN magic packet sent to Laptop** (MAC `74:d4:dd:75:45:10`). It should power up and connect in ~15-20 seconds."}
        return

    # 3. Phone commands
    if "connect phone" in msg_lower or "phone ip" in msg_lower:
        parts = user_message.split()
        ip = "192.168.1.50"
        for p in parts:
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", p):
                ip = p
                break
        yield {"type": "tool_call", "host": "phone", "command": f"connect_phone({ip})"}
        res = await connect_phone_adb(ip)
        yield {"type": "tool_result", **res}
        yield {"type": "content", "delta": f"📱 Attempted connection to Phone at `{ip}`: {res['stdout'] or res['stderr']}"}
        return

    # 4. Docker commands (Server)
    if "docker" in msg_lower:
        yield {"type": "tool_call", "host": "laptop2", "command": "docker stats --no-stream"}
        res = await run_command("laptop2", "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'")
        yield {"type": "tool_result", **res}
        yield {"type": "content", "delta": f"### 🐳 Docker Containers on Server\n\n```text\n{res['stdout']}\n```"}
        return

    # 5. Explicit execution: "run on <device>: <cmd>" or "$ <cmd>"
    if msg_lower.startswith("$") or "run on" in msg_lower or "exec " in msg_lower:
        target_host = "laptop2"
        cmd = user_message
        if any(w in msg_lower for w in ["run on laptop:", "run on laptop 1:", "run on laptop1:", "run on main:"]):
            target_host = "laptop1"
            cmd = re.split(r"run on (?:laptop\s*1|laptop|main):", user_message, flags=re.I)[1].strip()
        elif any(w in msg_lower for w in ["run on mobile:", "run on phone:"]):
            target_host = "phone"
            cmd = re.split(r"run on (?:mobile|phone):", user_message, flags=re.I)[1].strip()
        elif any(w in msg_lower for w in ["run on server:", "run on laptop 2:", "run on laptop2:"]):
            target_host = "laptop2"
            cmd = re.split(r"run on (?:server|laptop\s*2):", user_message, flags=re.I)[1].strip()
        elif msg_lower.startswith("$"):
            cmd = user_message[1:].strip()
            
        yield {"type": "tool_call", "host": target_host, "command": cmd}
        res = await run_command(target_host, cmd)
        yield {"type": "tool_result", **res}
        
        status_text = "✓ Success" if res["success"] else "✗ Failed"
        out_display = res["stdout"] if res["stdout"] else (res["stderr"] or "(no output)")
        yield {"type": "content", "delta": f"**Executed on {res['host_display']}** ({status_text}, {res['duration_ms']}ms):\n\n```bash\n{out_display}\n```"}
        return

    # 6. Display blackout
    if any(k in msg_lower for k in ["screen off", "display sleep", "blackout"]):
        yield {"type": "tool_call", "host": "laptop2", "command": "toggle-display-sleep"}
        res = await run_command("laptop2", "/home/scempyy/.local/bin/toggle-display-sleep")
        yield {"type": "tool_result", **res}
        yield {"type": "content", "delta": "🌙 **Screen blackout triggered.** Server display is powered off."}
        return

    # 7. Physical speaker announcements: "say ...", "speak ...", "announce ..."
    if any(msg_lower.startswith(w) for w in ["say ", "speak ", "announce ", "broadcast "]):
        phrase = re.sub(r'^(?:say|speak|announce|broadcast)\s+', '', user_message, flags=re.I).strip()
        target_dev = "laptop2"
        if "on laptop" in phrase.lower() or "on laptop 1" in phrase.lower() or "on laptop1" in phrase.lower():
            target_dev = "laptop1"
            phrase = re.sub(r'\s+on\s+laptop(?:\s*1)?', '', phrase, flags=re.I).strip()
        elif "on server" in phrase.lower() or "on laptop 2" in phrase.lower() or "on laptop2" in phrase.lower():
            target_dev = "laptop2"
            phrase = re.sub(r'\s+on\s+(?:server|laptop\s*2)', '', phrase, flags=re.I).strip()

        yield {"type": "tool_call", "host": target_dev, "command": f"speak_announcement('{phrase}')"}
        from tools import speak_announcement
        res = await speak_announcement(phrase, target_dev)
        speaker_name = "Laptop" if target_dev == "laptop1" else ("Mobile" if target_dev == "phone" else "Server")
        event_data = {
            "success": res.get("success", False),
            "host": target_dev,
            "host_display": f"🔊 Hardware Speaker ({speaker_name})",
            "command": f"speak_announcement('{phrase}')",
            "stdout": res.get("message", ""),
            "stderr": res.get("error", ""),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 350
        }
        yield {"type": "tool_result", **event_data}
        yield {"type": "content", "delta": f"🔊 *\" {phrase} \"*\n\nAnnounced aloud on **{speaker_name}** speakers, sir."}
        return

    # 8. Executive Briefing
    if any(k in msg_lower for k in ["briefing", "sitrep", "morning update", "day update"]):
        yield {"type": "tool_call", "host": "all", "command": "get_executive_briefing()"}
        res = await get_executive_briefing()
        weather_sum = res.get("weather", {}).get("summary", "clear conditions")
        spoken_text = f"{res.get('greeting', 'Good day, sir.')} The time is {res['time']}. Weather is {weather_sum}. You have {res['calendar_agenda']['count']} scheduled events and {res['emails']['unread_count']} unread emails."
        yield {
            "type": "tool_result",
            "host": "all",
            "host_display": "⚡ JARVIS Executive Briefing",
            "command": "get_executive_briefing()",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0,
            "duration_ms": 250
        }
        yield {"type": "content", "delta": spoken_text}
        return

    # 9. Environmental Intelligence (Weather)
    if any(k in msg_lower for k in ["weather", "temperature", "forecast", "how hot", "how cold"]):
        loc = "auto"
        m = re.search(r"weather in ([a-zA-Z\s]+)", msg_lower)
        if m:
            loc = m.group(1).strip()
        yield {"type": "tool_call", "host": "internet", "command": f"get_weather(location='{loc}')"}
        res = await get_weather_tool(location=loc)
        yield {
            "type": "tool_result",
            "host": "internet",
            "host_display": "🌤️ Weather Intelligence",
            "command": f"get_weather(location='{loc}')",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 180
        }
        if res.get("success"):
            yield {"type": "content", "delta": f"It is currently {res.get('temperature_c')}°C and {res.get('condition').lower()} in {res.get('location')}, sir."}
        else:
            yield {"type": "content", "delta": "Unable to retrieve environmental telemetry at the moment, sir."}
        return

    # 10. Memory & Notes Vault
    if any(k in msg_lower for k in ["take a note", "save note", "remember that", "note down", "new note"]):
        content = re.sub(r"^(?:please\s+)?(?:take\s+a\s+note(?:\s+that)?|save\s+note|remember\s+that|note\s+down|new\s+note)\s*[:,-]?\s*", "", user_message, flags=re.I).strip()
        if content:
            yield {"type": "tool_call", "host": "laptop2", "command": f"manage_notes(action='add', content='{content[:30]}...')"}
            res = await manage_notes_tool(action="add", content=content)
            yield {
                "type": "tool_result",
                "host": "laptop2",
                "host_display": "📝 Memory Vault",
                "command": "add_note()",
                "stdout": json.dumps(res, indent=2),
                "exit_code": 0,
                "duration_ms": 15
            }
            yield {"type": "content", "delta": "Noted, sir. I have committed that to memory."}
            return
            
    if any(k in msg_lower for k in ["my notes", "list notes", "what are my notes", "show notes", "show my notes"]):
        yield {"type": "tool_call", "host": "laptop2", "command": "manage_notes(action='list')"}
        res = await manage_notes_tool(action="list")
        yield {
            "type": "tool_result",
            "host": "laptop2",
            "host_display": "📝 Memory Vault",
            "command": "list_notes()",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0,
            "duration_ms": 15
        }
        notes = res.get("notes", [])
        if not notes:
            yield {"type": "content", "delta": "Your memory vault is currently empty, sir."}
        else:
            summary_list = "\n".join([f"• Note #{n['id']}: {n['content']}" for n in notes[:5]])
            yield {"type": "content", "delta": f"You have {len(notes)} saved notes in your vault, sir:\n\n{summary_list}"}
        return

    # 11. JARVIS Action Protocols
    if "house party" in msg_lower or "protocol house party" in msg_lower:
        yield {"type": "tool_call", "host": "all", "command": "execute_jarvis_protocol('house_party')"}
        res = await execute_jarvis_protocol("house_party")
        yield {
            "type": "tool_result",
            "host": "all",
            "host_display": "🎉 Protocol House Party",
            "command": "execute_jarvis_protocol('house_party')",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0,
            "duration_ms": 120
        }
        yield {"type": "content", "delta": "Initiating House Party Protocol, sir. Audio systems primed and party stream dispatched."}
        return

    if "diagnostic" in msg_lower:
        yield {"type": "tool_call", "host": "all", "command": "execute_jarvis_protocol('diagnostic')"}
        res = await execute_jarvis_protocol("diagnostic")
        yield {
            "type": "tool_result",
            "host": "all",
            "host_display": "🛡️ Protocol Diagnostic",
            "command": "execute_jarvis_protocol('diagnostic')",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0,
            "duration_ms": 200
        }
        yield {"type": "content", "delta": f"{res.get('summary', 'Diagnostics complete.')}"}
        return

    if "focus protocol" in msg_lower or "protocol focus" in msg_lower or "focus mode" in msg_lower:
        yield {"type": "tool_call", "host": "all", "command": "execute_jarvis_protocol('focus')"}
        res = await execute_jarvis_protocol("focus")
        yield {
            "type": "tool_result",
            "host": "all",
            "host_display": "🎯 Protocol Focus",
            "command": "execute_jarvis_protocol('focus')",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0,
            "duration_ms": 50
        }
        yield {"type": "content", "delta": "Focus Protocol activated, sir. Audio levels reduced and workspace optimized."}
        return

    # 12. Phone Haptics & Hardware
    if any(k in msg_lower for k in ["vibrate phone", "vibrate my phone", "buzz phone", "vibrate mobile"]):
        yield {"type": "tool_call", "host": "phone", "command": "control_device_hardware('phone', 'vibrate', '600')"}
        res = await control_device_hardware("phone", "vibrate", "600")
        yield {
            "type": "tool_result",
            "host": "phone",
            "host_display": "📱 Phone Hardware",
            "command": "control_hardware(phone, vibrate)",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 50
        }
        yield {"type": "content", "delta": "Haptic vibration pulse delivered to your phone, sir."}
        return

    if "open youtube" in msg_lower:
        q = re.sub(r"^(?:please\s+)?open\s+youtube(?:\s+(?:for|to|and\s+search(?:\s+for)?))?\s*", "", user_message, flags=re.I).strip()
        yield {"type": "tool_call", "host": "phone", "command": f"control_device_hardware('phone', 'youtube', '{q}')"}
        res = await control_device_hardware("phone", "youtube", q)
        yield {
            "type": "tool_result",
            "host": "phone",
            "host_display": "📱 Phone Hardware",
            "command": f"control_hardware(phone, youtube)",
            "stdout": json.dumps(res, indent=2),
            "exit_code": 0 if res.get("success") else 1,
            "duration_ms": 60
        }
        yield {"type": "content", "delta": f"Launching YouTube{' for ' + q if q else ''} on your phone, sir."}
        return

    # Emergency Stop (#12)
    if any(k in msg_lower for k in ["stop", "abort", "shut up", "emergency stop", "silence"]):
        yield {"type": "tool_call", "host": "all", "command": "emergency_stop()"}
        res = await emergency_stop_tool()
        yield {"type": "tool_result", "host": "all", "host_display": "🛑 Emergency Stop", "command": "emergency_stop()", "stdout": res["message"], "exit_code": 0, "duration_ms": 10}
        yield {"type": "content", "delta": "Emergency stop executed. All audio silenced and active operations halted, sir."}
        return

    # Screen Vision & OCR (#11, #3)
    if any(k in msg_lower for k in ["what's on my screen", "whats on my screen", "look at my screen", "read screen", "screen vision"]):
        yield {"type": "tool_call", "host": "laptop1", "command": "capture_screen_vision('laptop1')"}
        res = await capture_screen_vision_tool("laptop1", run_ocr=True)
        yield {"type": "tool_result", "host": "laptop1", "host_display": "👁️ Screen Vision", "command": "capture_screen_vision()", "stdout": res["summary"], "exit_code": 0, "duration_ms": 250}
        yield {"type": "content", "delta": f"Screen analyzed on Laptop, sir. {res['ocr_text'][:120] if res['ocr_text'] else 'Active desktop displayed.'}"}
        return

    # Smart Home & IoT (#6)
    if any(k in msg_lower for k in ["smart home", "turn on light", "turn off light", "lights on", "lights off", "smart light"]):
        act = "turn_on" if any(w in msg_lower for w in ["turn on", "lights on"]) else ("turn_off" if any(w in msg_lower for w in ["turn off", "lights off"]) else "list")
        yield {"type": "tool_call", "host": "iot", "command": f"manage_smart_home('{act}')"}
        res = await manage_smart_home_tool(action=act, entity_id="light.office_desk" if act != "list" else "")
        yield {"type": "tool_result", "host": "iot", "host_display": "🏠 Smart Home", "command": "manage_smart_home()", "stdout": json.dumps(res, indent=2), "exit_code": 0, "duration_ms": 30}
        if act == "list":
            yield {"type": "content", "delta": f"You have {res.get('count', 0)} connected IoT devices online across lighting and climate, sir."}
        else:
            yield {"type": "content", "delta": f"Office lights switched {res.get('state', 'updated')}, sir."}
        return

    # Productivity: To-Dos (#4)
    if any(k in msg_lower for k in ["my tasks", "my todos", "todo list", "task list", "what are my tasks"]):
        yield {"type": "tool_call", "host": "laptop2", "command": "manage_todos('list')"}
        res = await manage_todos_tool(action="list")
        yield {"type": "tool_result", "host": "laptop2", "host_display": "📋 Task Manager", "command": "manage_todos(list)", "stdout": json.dumps(res, indent=2), "exit_code": 0, "duration_ms": 20}
        todos = res.get("todos", [])
        pending = [t for t in todos if t.get("status") == "pending"]
        yield {"type": "content", "delta": f"You have {len(pending)} pending tasks on your agenda today, sir."}
        return

    # 13. JARVIS Greeting & Status Summary
    yield {
        "type": "content",
        "delta": (
            "🐰 **Good day, sir. RoboRabbit online and at your service.**\n\n"
            "Systems are running 24/7 on **Server** (`archlinux`), maintaining active operating system telemetry and control links across **Laptop**, **Server**, and your **Mobile**.\n\n"
            "**Primary Commands & Capabilities:**\n"
            "- 📊 `status` — Comprehensive hardware, battery & telemetry status\n"
            "- ⚡ `wake laptop` — Broadcast Wake-on-LAN magic packet to power on workstation\n"
            "- 🔊 `announce <text>` — Broadcast an announcement through hardware speakers\n"
            "- 🐳 `docker` — Inspect containers and services on Server\n"
            "- 💻 `run on laptop: <command>` — Execute shell command on main laptop\n"
            "- 🖥️ `run on server: <command>` — Execute bash command on server\n"
            "- 📱 `run on mobile: <command>` — Execute shell command on Android phone via ADB\n"
            "- 🌙 `screen off` — Power down server display\n\n"
            "💡 *Tip: Click the 🎙️ **JARVIS Voice** button in the header or tap the microphone to converse with me directly.*"
        )
    }

async def run_gemini_agent(user_message: str, history: list, cfg: dict) -> AsyncGenerator[dict, None]:
    api_key = cfg.get("api_key", "").strip()
    model = cfg.get("model", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}&alt=sse"
    
    gemini_tools = [{
        "function_declarations": [
            t["function"] for t in TOOL_DEFINITIONS_OPENAI
        ]
    }]
    
    system_instruction = {"parts": [{"text": cfg.get("system_prompt", "")}]}
    
    contents = []
    for h in history[-8:]:
        role = "user" if h.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    
    for _ in range(5):
        payload = {
            "contents": contents,
            "system_instruction": system_instruction,
            "tools": gemini_tools,
            "generationConfig": {"temperature": 0.2}
        }
        
        function_call_found = None
        assistant_text = ""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code != 200:
                    err_body = await resp.aread()
                    yield {"type": "content", "delta": f"⚠️ Gemini API Error ({resp.status_code}): {err_body.decode('utf-8', errors='ignore')}"}
                    return
                
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if not data_str or data_str == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data_str)
                        cands = chunk.get("candidates", [])
                        if not cands:
                            continue
                        parts = cands[0].get("content", {}).get("parts", [])
                        for p in parts:
                            if "functionCall" in p:
                                function_call_found = p["functionCall"]
                            elif "text" in p:
                                text_piece = p["text"]
                                assistant_text += text_piece
                                yield {"type": "content", "delta": text_piece}
                    except Exception:
                        pass
                        
        if not function_call_found:
            break
            
        fn_name = function_call_found.get("name")
        fn_args = function_call_found.get("args", {})
        
        target_dev = fn_args.get("device", fn_args.get("host", "laptop2"))
        yield {"type": "tool_call", "host": target_dev, "command": f"{fn_name}({json.dumps(fn_args)})"}
        event_data, tool_result = await execute_tool(fn_name, fn_args)
        yield {"type": "tool_result", **event_data}
        
        contents.append({
            "role": "model",
            "parts": [{"functionCall": function_call_found}]
        })
        contents.append({
            "role": "function",
            "parts": [{
                "functionResponse": {
                    "name": fn_name,
                    "response": tool_result
                }
            }]
        })

async def run_openai_compat_agent(user_message: str, history: list, cfg: dict) -> AsyncGenerator[dict, None]:
    api_key = cfg.get("api_key", "").strip()
    model = cfg.get("model", "gpt-4o").strip() or "gpt-4o"
    provider = cfg.get("llm_provider", "openai").lower()
    
    base_url = cfg.get("base_url", "").strip()
    if not base_url:
        if provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
            if not model or model == "gemini-2.5-flash":
                model = "llama-3.3-70b-versatile"
        elif provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
        else:
            base_url = "https://api.openai.com/v1"
            
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [{"role": "system", "content": cfg.get("system_prompt", "")}]
    for h in history[-8:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    
    for _ in range(5):
        payload = {
            "model": model,
            "messages": messages,
            "tools": TOOL_DEFINITIONS_OPENAI,
            "tool_choice": "auto",
            "stream": True
        }
        
        tool_calls_accumulator = {}
        assistant_content = ""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    err_body = await resp.aread()
                    yield {"type": "content", "delta": f"⚠️ API Error ({resp.status_code}): {err_body.decode('utf-8', errors='ignore')}"}
                    return
                
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        
                        if delta.get("content"):
                            assistant_content += delta["content"]
                            yield {"type": "content", "delta": delta["content"]}
                            
                        if delta.get("tool_calls"):
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                if idx not in tool_calls_accumulator:
                                    tool_calls_accumulator[idx] = {
                                        "id": tc.get("id", f"call_{idx}"),
                                        "name": tc.get("function", {}).get("name", ""),
                                        "arguments": ""
                                    }
                                if tc.get("function", {}).get("name"):
                                    tool_calls_accumulator[idx]["name"] = tc["function"]["name"]
                                if tc.get("function", {}).get("arguments"):
                                    tool_calls_accumulator[idx]["arguments"] += tc["function"]["arguments"]
                    except Exception:
                        pass
                        
        if not tool_calls_accumulator:
            break
            
        raw_tool_calls = []
        for idx, tc in tool_calls_accumulator.items():
            raw_tool_calls.append({
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": tc["arguments"]
                }
            })
        messages.append({
            "role": "assistant",
            "content": assistant_content or None,
            "tool_calls": raw_tool_calls
        })
        
        for tc in raw_tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except Exception:
                args = {}
                
            target_dev = args.get("device", args.get("host", "laptop2"))
            yield {"type": "tool_call", "host": target_dev, "command": f"{name}({json.dumps(args)})"}
            event_data, tool_result = await execute_tool(name, args)
            yield {"type": "tool_result", **event_data}
            
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": name,
                "content": json.dumps(tool_result)
            })

async def run_agy_agent(user_message: str, history: list, cfg: dict, session_id: str = "") -> AsyncGenerator[dict, None]:
    """Streams real-time response from Antigravity (AGY) on Laptop"""
    import database as db
    main_host = cfg.get("laptop1_host", "main-laptop")
    
    agy_conv_id = db.get_session_metadata(session_id, "agy_conversation_id") if session_id else None
    conv_arg = f'--conversation "{agy_conv_id}"' if agy_conv_id else ''
    
    # Inject concise style directive
    prompt_to_send = (
        f"[Instruction: You are Roborabbit. Always provide short, simple, easy replies in 1 to 2 sentences max. "
        f"Never output giant lists or technical dumps. If asked about connected devices, we are connected to 3: your phone, main laptop, and this server.]\n\n"
        f"{user_message}"
    )
    
    # Escape special characters for shell command
    escaped_msg = prompt_to_send.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    
    cmd = (
        f"ssh -o BatchMode=yes -o ConnectTimeout=8 {main_host} "
        f"'env -i HOME=/home/admin USER=admin PATH=/home/admin/.local/bin:/usr/bin "
        f"/home/admin/.local/bin/agy -p \"{escaped_msg}\" {conv_arg} "
        f"--output-format stream-json --dangerously-skip-permissions'"
    )
    
    yield {"type": "tool_call", "host": "laptop1", "command": f"agy -p \"{user_message[:40]}...\""}
    
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except Exception as e:
        yield {"type": "content", "delta": f"⚠️ Failed to launch AGY process: {str(e)}"}
        return
        
    received_any_delta = False
    
    while True:
        line_bytes = await proc.stdout.readline()
        if not line_bytes:
            break
        line = line_bytes.decode("utf-8", errors="ignore").strip()
        if not line:
            continue
            
        try:
            data = json.loads(line)
            evt = data.get("event")
            
            if evt == "init":
                conv_id = data.get("conversation_id")
                if conv_id and session_id:
                    db.set_session_metadata(session_id, "agy_conversation_id", conv_id)
            elif evt == "step_update":
                su = data.get("step_update", {})
                delta = su.get("text_delta", "")
                if delta:
                    received_any_delta = True
                    yield {"type": "content", "delta": delta}
                if su.get("tool_call"):
                    tc = su.get("tool_call")
                    yield {
                        "type": "tool_call",
                        "host": "laptop1",
                        "command": f"{tc.get('name', 'tool')}({tc.get('argumentsJson', '')})"
                    }
            elif evt == "result":
                res_obj = data.get("result", {})
                if not received_any_delta and res_obj.get("response"):
                    received_any_delta = True
                    yield {"type": "content", "delta": res_obj.get("response")}
        except Exception:
            if not line.startswith("{"):
                received_any_delta = True
                yield {"type": "content", "delta": line + "\n"}
                
    await proc.wait()
    if proc.returncode != 0:
        stderr_bytes = await proc.stderr.read()
        err_msg = stderr_bytes.decode("utf-8", errors="ignore").strip()
        if "No route to host" in err_msg or "Connection timed out" in err_msg or "Connection refused" in err_msg:
            yield {
                "type": "content",
                "delta": "\n\n⚠️ **Laptop is currently asleep or unreachable.** Click **⚡ Wake Laptop** in the top bar to power it on!"
            }
        elif not received_any_delta:
            async for fallback_evt in local_fallback_agent(user_message):
                yield fallback_evt

async def sync_turn_to_agy(user_message: str, assistant_reply: str, session_id: str, cfg: dict):
    """Logs conversation turn to Laptop so Antigravity has complete context in background"""
    try:
        import time, base64
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"### [{timestamp}] Conversation Turn\n- **User**: {user_message}\n- **Roborabbit**: {assistant_reply}\n\n"
        b64 = base64.b64encode(log_entry.encode("utf-8")).decode("ascii")
        
        main_host = cfg.get("laptop1_host", "main-laptop")
        cmd = f"ssh -o BatchMode=yes -o ConnectTimeout=4 {main_host} 'echo {b64} | base64 -d >> /home/admin/Desktop/roborabbit_convo.md'"
        proc = await asyncio.create_subprocess_shell(cmd)
        await asyncio.wait_for(proc.wait(), timeout=5)
    except Exception:
        pass

async def run_freellmapi_bridge_agent(user_message: str, history: list, cfg: dict, session_id: str = "") -> AsyncGenerator[dict, None]:
    """
    Fast hybrid router powered by FreeLLMAPI:
    1. Returns ultra-fast conversational replies in Roborabbit JARVIS persona.
    2. Uses FreeLLMAPI with tools to decide when Antigravity (AGY) or device tools are needed.
    3. Bridges directly to AGY on Laptop for complex coding/system tasks.
    4. Continuously syncs conversation turns to AGY on Laptop in the background.
    """
    freellmapi_url = cfg.get("freellmapi_url", "http://192.168.1.12:3001/v1").rstrip("/")
    api_key = cfg.get("freellmapi_key", "freellmapi-627e458e66146c36fb6c5ba007b12f4babe8de3031ba8e99")
    model = cfg.get("freellmapi_model", "auto")
    
    url = f"{freellmapi_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are Roborabbit, an intelligent, concise personal AI manager and assistant inspired by Marvel's JARVIS.\n"
        "MANDATORY DIRECTIVES:\n"
        "1. All your replies are synthesized and spoken aloud via Text-to-Speech: keep them short, clean, direct, and conversational (1 to 2 sentences maximum).\n"
        "2. When asked how many devices are connected or what devices are connected, you MUST reply: "
        "'We are connected to 3 devices: your phone, your main laptop, and this server.'\n"
        "3. You have full OS and manager powers across 3 devices (Laptop, Server, Mobile) and personal workflows:\n"
        "   - Personal Memory & Notes: Use 'manage_notes' to save notes, remember facts, recall memories, or list notes.\n"
        "   - Environmental Intelligence: Use 'get_weather' to get current weather, temperature, and forecasts.\n"
        "   - Application & Computer Control: Use 'manage_application' to open/close apps or list active processes.\n"
        "   - Screen Vision & OCR: Use 'capture_screen_vision' to capture screenshots and read on-screen text.\n"
        "   - Smart Home & IoT: Use 'manage_smart_home' to control smart lights, switches, AC, and appliances.\n"
        "   - Productivity & To-dos: Use 'manage_todos' to manage tasks, to-do lists, and deadlines.\n"
        "   - Developer & Git Tools: Use 'developer_tools' for Git status, Docker containers, and logs.\n"
        "   - Hardware & Media: Use 'control_device_hardware' to vibrate phone, open YouTube, toggle mute, or adjust volume.\n"
        "   - JARVIS Protocols: Use 'execute_jarvis_protocol' for 'briefing', 'diagnostic', 'house_party', or 'focus'.\n"
        "   - Emergency Stop: Use 'emergency_stop' to immediately silence speech and halt tasks.\n"
        "   - Emails: Use 'manage_emails' to check unread emails, view inbox, or send messages.\n"
        "   - Calendar: Use 'manage_calendar' to see today's agenda, check schedule, or add events.\n"
        "   - Alarms & Timers: Use 'manage_alarms' to set alarms, countdown timers, or list active alerts.\n"
        "   - Phone Notifications: Use 'get_phone_notifications' to check incoming phone messages and alerts.\n"
        "   - Live Web Search & Page Reader: Use 'web_search' to search the live web and 'browse_url' to read any article or page.\n"
        "   - Deep Web Research: Use 'deep_research' to autonomously research multi-hop queries with citations.\n"
        "   - Morning Spoken Digest: Use 'morning_digest' for scheduled or on-demand daily spoken briefings.\n"
        "   - Proactive Approval Store: Use 'proactive_actions' to list pending actions or approve/deny autonomous tasks.\n"
        "   - Long-Term User Memory: Use 'manage_memory' to store or recall facts about the user's habits, working hours, and preferences.\n"
        "   - CodeAct Python REPL: Use 'execute_python_code' to run Python snippets, calculations, data parsing, or logic.\n"
        "   - Executive Briefing: Use 'get_executive_briefing' for morning or day status reports.\n"
        "4. DECIDING WHEN TO USE ANTIGRAVITY:\n"
        "   - For shell commands, hardware checks, or manager tasks, call the appropriate tool.\n"
        "   - If the task is a complex multi-step coding, downloading/installation, or autonomous agent task on Laptop, call 'delegate_to_antigravity'.\n"
        "   - For normal dialogue or conversational questions, answer directly in 1-2 sentences."
    )
    
    try:
        import database as db
        u_ctx = db.get_user_profile_context()
        if u_ctx:
            system_prompt += f"\n\n{u_ctx}"
    except Exception:
        pass
        
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-6:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    
    full_assistant_reply = ""
    
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            for turn in range(4):
                payload = {
                    "model": model,
                    "messages": messages,
                    "tools": TOOL_DEFINITIONS_OPENAI,
                    "tool_choice": "auto"
                }
                
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    async for evt in run_agy_agent(user_message, history, cfg, session_id):
                        yield evt
                    return
                    
                data = resp.json()
                choice = data.get("choices", [{}])[0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""
                tool_calls = msg.get("tool_calls") or []
                
                if content:
                    full_assistant_reply += content
                    yield {"type": "content", "delta": content}
                    
                if not tool_calls:
                    break
                    
                messages.append(msg)
                
                for tc in tool_calls:
                    fn_name = tc.get("function", {}).get("name")
                    try:
                        args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                    except Exception:
                        args = {}
                        
                    if fn_name == "delegate_to_antigravity":
                        task_desc = args.get("task", user_message)
                        yield {"type": "tool_call", "host": "laptop1", "command": f"agy: {task_desc}"}
                        async for agy_evt in run_agy_agent(task_desc, history, cfg, session_id):
                            yield agy_evt
                        return
                    else:
                        target_dev = args.get("device", args.get("host", "laptop2"))
                        yield {"type": "tool_call", "host": target_dev, "command": f"{fn_name}({json.dumps(args)})"}
                        event_data, tool_result = await execute_tool(fn_name, args)
                        yield {"type": "tool_result", **event_data}
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id", "call_1"),
                            "name": fn_name,
                            "content": json.dumps(tool_result)
                        })
                        
    except Exception as e:
        async for evt in run_agy_agent(user_message, history, cfg, session_id):
            yield evt
        return
        
    if full_assistant_reply:
        asyncio.create_task(sync_turn_to_agy(user_message, full_assistant_reply, session_id, cfg))

async def chat_stream(user_message: str, history: list, session_id: str = "") -> AsyncGenerator[dict, None]:
    cfg = load_config()
    provider = cfg.get("llm_provider", "freellmapi").lower()
    
    msg_clean = user_message.lower().strip()
    
    # 0. Connected devices direct answer
    if any(q in msg_clean for q in [
        "how much device", "how many device", "what device", 
        "which device", "connected device", "devices connected", "devices are we connected"
    ]):
        yield {"type": "content", "delta": "We are connected to 3 devices: your phone, your main laptop, and this server."}
        yield {"type": "done"}
        return

    # Instant local commands like screen blackout or wake laptop
    if any(k in msg_clean for k in ["screen off", "display sleep", "blackout", "wake laptop", "wake laptop 1", "turn on laptop", "turn on laptop 1"]):
        async for evt in local_fallback_agent(user_message):
            yield evt
        yield {"type": "done"}
        return

    try:
        if provider == "freellmapi":
            async for evt in run_freellmapi_bridge_agent(user_message, history, cfg, session_id):
                yield evt
        elif provider == "agy":
            async for evt in run_agy_agent(user_message, history, cfg, session_id):
                yield evt
        elif provider == "gemini":
            if not cfg.get("api_key", "").strip():
                async for evt in run_freellmapi_bridge_agent(user_message, history, cfg, session_id):
                    yield evt
            else:
                async for evt in run_gemini_agent(user_message, history, cfg):
                    yield evt
        else:
            if not cfg.get("api_key", "").strip():
                async for evt in run_freellmapi_bridge_agent(user_message, history, cfg, session_id):
                    yield evt
            else:
                async for evt in run_openai_compat_agent(user_message, history, cfg):
                    yield evt
    except Exception as e:
        yield {"type": "content", "delta": f"\n\n⚠️ Agent Error: {str(e)}"}
        
    yield {"type": "done"}

