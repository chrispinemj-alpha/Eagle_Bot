import os
import re
import json
import uuid
import secrets
import datetime as dt
from functools import wraps
from threading import Lock
from urllib.parse import urljoin

import requests
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# ============================================================
# EAGLE BOT — v0.1 PRODUCT FOUNDATION
# ============================================================
# Product, identity and intelligence are intentionally independent
# from Telegram. Telegram is only one transport/channel.
#
# Core direction:
#   LEARN WITHOUT COPYING
#   ACT WITHOUT LOSING HUMAN CONTROL
#   UPGRADE WITHOUT LOSING IDENTITY
#   REAL-WORLD SIGNALS -> EVIDENCE -> REASONING -> ACTION -> AUDIT
# ============================================================

PRODUCT_NAME = "Eagle Bot"
PRODUCT_VERSION = "0.1"
PRODUCT_TAGLINE = "A global work and intelligence platform built around outcomes."
PRODUCT_DESCRIPTION = (
    "Eagle Bot connects people to specialized Coworkers, knowledge, tools and governed execution. "
    "Its channels can change; its identity, memory, permissions and audit trail remain product-owned."
)

# ------------------------- Secrets ----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_USER_ID = os.environ.get("YOUR_USER_ID", "").strip()
PUBLIC_WEB_APP_URL = os.environ.get("PUBLIC_WEB_APP_URL", "").strip().rstrip("/")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
AI_GATEWAY_URL = os.environ.get("EAGLE_AI_API_URL", "").strip()
AI_GATEWAY_KEY = os.environ.get("EAGLE_AI_API_KEY", "").strip()
WORLD_ENGINE_URL = os.environ.get("EAGLE_WORLD_ENGINE_URL", "").strip()
WORLD_ENGINE_KEY = os.environ.get("EAGLE_WORLD_ENGINE_KEY", "").strip()
DATABASE_PATH = os.environ.get("DATABASE_PATH", "eagle_bot.db").strip()
PORT = int(os.environ.get("PORT", "5000"))

# ------------------------ Runtime ------------------------------
DB_LOCK = Lock()
STATE_LOCK = Lock()
HTTP_TIMEOUT = (5, 30)
AI_TIMEOUT = (10, 90)
WORLD_TIMEOUT = (10, 45)
MAX_MESSAGE_LENGTH = 12_000
MAX_TASK_LENGTH = 30_000

# Eagle is a digital service designed for global access. Human support
# schedules should never become a technical gate for the platform.
SERVICE_AVAILABILITY = "24/7 worldwide, subject to infrastructure, capacity and applicable law."

# ============================================================
# COWORKERS — specialized capabilities, not separate identities
# ============================================================
COWORKERS = {
    "general": {
        "name": "Eagle Generalist",
        "mission": "Understand the outcome, decompose the problem and coordinate the right capabilities.",
        "permissions": ["read_context", "propose_plan"],
    },
    "research": {
        "name": "Eagle Researcher",
        "mission": "Investigate evidence, compare sources, synthesize knowledge and surface uncertainty.",
        "permissions": ["read_context", "world_read", "propose_plan"],
    },
    "builder": {
        "name": "Eagle Builder",
        "mission": "Turn goals into architectures, software plans, prototypes, workflows and deliverables.",
        "permissions": ["read_context", "propose_plan", "create_artifact"],
    },
    "analyst": {
        "name": "Eagle Analyst",
        "mission": "Model trade-offs, numbers, risks, scenarios and measurable outcomes.",
        "permissions": ["read_context", "world_read", "propose_plan"],
    },
    "operator": {
        "name": "Eagle Operator",
        "mission": "Coordinate execution, dependencies, tasks, follow-ups and operational workflows.",
        "permissions": ["read_context", "propose_plan", "request_action"],
    },
    "educator": {
        "name": "Eagle Educator",
        "mission": "Teach, mentor and transform difficult concepts into practical learning paths.",
        "permissions": ["read_context", "propose_plan"],
    },
}

# Actions are intentionally conservative. Dangerous, irreversible,
# high-impact or external side effects require a human-approved path.
ACTION_POLICY = {
    "world_read": {"risk": "low", "requires_approval": False},
    "read_context": {"risk": "low", "requires_approval": False},
    "propose_plan": {"risk": "low", "requires_approval": False},
    "create_artifact": {"risk": "medium", "requires_approval": False},
    "request_action": {"risk": "medium", "requires_approval": True},
    "send_external_message": {"risk": "high", "requires_approval": True},
    "financial_transaction": {"risk": "critical", "requires_approval": True},
    "identity_change": {"risk": "critical", "requires_approval": True},
    "destructive_action": {"risk": "critical", "requires_approval": True},
}

# Simple conversational routing for the local MVP. In production,
# the AI gateway should use richer task classification and policies.
def choose_coworker(text):
    lower = text.lower()
    keyword_groups = {
        "research": ["research", "sources", "investigate", "study", "market", "competitor", "evidence", "latest"],
        "builder": ["build", "code", "website", "app", "software", "api", "prototype", "architecture", "github"],
        "analyst": ["analyze", "analysis", "compare", "strategy", "forecast", "numbers", "data", "risk", "market size"],
        "operator": ["execute", "automate", "workflow", "operations", "process", "task", "organize", "launch"],
        "educator": ["learn", "teach", "explain", "mentor", "course", "lesson", "understand", "study plan"],
    }
    scores = {key: 0 for key in keyword_groups}
    for key, words in keyword_groups.items():
        scores[key] = sum(1 for word in words if re.search(rf"\b{re.escape(word)}\b", lower))
    best = max(scores, key=scores.get)
    return best if scores[best] else "general"

# ============================================================
# PERSISTENCE — SQLite for development/single instance
# ============================================================
# The schema deliberately keeps a path to a managed PostgreSQL layer.
# SQLite is a bootstrap, not the final global-scale database.

def db():
    import sqlite3
    connection = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def init_db():
    with DB_LOCK, db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_number TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                topic TEXT NOT NULL,
                word_count INTEGER NOT NULL,
                deadline TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Processing',
                source TEXT NOT NULL DEFAULT 'web',
                telegram_user_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_orders_telegram ON orders(telegram_user_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_orders_email ON orders(email, created_at);

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                external_id TEXT,
                display_name TEXT,
                email TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                coworker_key TEXT NOT NULL DEFAULT 'general',
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                coworker_key TEXT,
                source TEXT NOT NULL DEFAULT 'unknown',
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                coworker_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                risk TEXT NOT NULL DEFAULT 'low',
                requires_approval INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                reason TEXT NOT NULL,
                decided_by TEXT,
                decided_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS world_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                observed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                task_id TEXT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                actor_type TEXT NOT NULL,
                actor_id TEXT,
                event TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at);
            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id, updated_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, updated_at);
            CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status, created_at);
            CREATE INDEX IF NOT EXISTS idx_world_events_time ON world_events(observed_at);
            CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(created_at);
            """
        )


init_db()


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def safe_json(value):
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return json.dumps({"unserializable": True})


def audit(actor_type, actor_id, event, target_type=None, target_id=None, metadata=None):
    with DB_LOCK, db() as conn:
        conn.execute(
            """
            INSERT INTO audit_log (id, actor_type, actor_id, event, target_type, target_id, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), actor_type, str(actor_id) if actor_id is not None else None,
             event, target_type, str(target_id) if target_id is not None else None, safe_json(metadata or {}), now_iso()),
        )


def generate_order_number():
    for _ in range(20):
        code = secrets.randbelow(900000) + 100000
        order_number = f"EAGLE-{code}"
        with DB_LOCK, db() as conn:
            exists = conn.execute("SELECT 1 FROM orders WHERE order_number = ?", (order_number,)).fetchone()
        if not exists:
            return order_number
    raise RuntimeError("Unable to create a unique order number")


def save_order(order):
    with DB_LOCK, db() as conn:
        conn.execute(
            """INSERT INTO orders (order_number, customer_name, email, topic, word_count, deadline, date, status, source, telegram_user_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order["order_number"], order["customer_name"], order["email"], order["topic"], order["word_count"],
             order["deadline"], order["date"], order.get("status", "Processing"), order.get("source", "web"),
             order.get("telegram_user_id"), order.get("created_at", now_iso())),
        )


def get_order(order_number):
    with DB_LOCK, db() as conn:
        row = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number.upper(),)).fetchone()
    return dict(row) if row else None


def get_user_orders(external_id):
    with DB_LOCK, db() as conn:
        rows = conn.execute("SELECT * FROM orders WHERE telegram_user_id = ? ORDER BY created_at DESC", (str(external_id),)).fetchall()
    return [dict(r) for r in rows]


def ensure_user(channel, external_id=None, display_name=None, email=None):
    key = f"{channel}:{external_id}" if external_id else f"{channel}:anonymous"
    user_id = secrets.token_hex(16) if external_id is None else key
    timestamp = now_iso()
    with DB_LOCK, db() as conn:
        if external_id is not None:
            existing = conn.execute(
                "SELECT id FROM users WHERE channel = ? AND external_id = ?",
                (channel, str(external_id)),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE users SET display_name = COALESCE(?, display_name), email = COALESCE(?, email), updated_at = ? WHERE id = ?",
                    (display_name, email, timestamp, existing["id"]),
                )
                return existing["id"]
        conn.execute(
            "INSERT INTO users (id, channel, external_id, display_name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, channel, str(external_id) if external_id is not None else None, display_name, email, timestamp, timestamp),
        )
    audit("system", "eagle", "user.created", "user", user_id, {"channel": channel})
    return user_id


def create_conversation(user_id, coworker_key="general", title=None):
    conversation_id = str(uuid.uuid4())
    timestamp = now_iso()
    with DB_LOCK, db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, user_id, coworker_key, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, user_id, coworker_key, title, timestamp, timestamp),
        )
    audit("user", user_id, "conversation.created", "conversation", conversation_id, {"coworker": coworker_key})
    return conversation_id


def save_message(conversation_id, role, content, coworker_key=None, source="unknown"):
    with DB_LOCK, db() as conn:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, coworker_key, source, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), conversation_id, role, content, coworker_key, source, now_iso()),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now_iso(), conversation_id))


def create_task(user_id, description, coworker_key, conversation_id=None, title=None):
    policy = ACTION_POLICY["request_action"]
    task_id = str(uuid.uuid4())
    timestamp = now_iso()
    title = title or f"Eagle task: {description[:70]}"
    with DB_LOCK, db() as conn:
        conn.execute(
            """
            INSERT INTO tasks (id, user_id, conversation_id, title, description, coworker_key, status, risk, requires_approval, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?, ?)
            """,
            (task_id, user_id, conversation_id, title, description, coworker_key,
             policy["risk"], 1 if policy["requires_approval"] else 0, timestamp, timestamp),
        )
    audit("coworker", coworker_key, "task.created", "task", task_id, {"requires_approval": True})
    approval_id = create_approval(task_id, user_id, "Execution is an external side effect and requires human approval.")
    return task_id, approval_id


def create_approval(task_id, requested_by, reason):
    approval_id = str(uuid.uuid4())
    with DB_LOCK, db() as conn:
        conn.execute(
            "INSERT INTO approvals (id, task_id, requested_by, status, reason, created_at) VALUES (?, ?, ?, 'pending', ?, ?)",
            (approval_id, task_id, requested_by, reason, now_iso()),
        )
    audit("system", "eagle", "approval.requested", "approval", approval_id, {"task_id": task_id})
    return approval_id


def get_task(task_id):
    with DB_LOCK, db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def list_tasks(user_id, limit=30):
    with DB_LOCK, db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def record_world_event(event_type, source, payload):
    event_id = str(uuid.uuid4())
    with DB_LOCK, db() as conn:
        conn.execute(
            "INSERT INTO world_events (id, event_type, source, payload_json, observed_at) VALUES (?, ?, ?, ?, ?)",
            (event_id, event_type, source, safe_json(payload), now_iso()),
        )
    audit("world", source, "world.event.observed", "world_event", event_id, {"event_type": event_type})
    return event_id

# ============================================================
# WORLD ENGINE — real-world signals are a separate subsystem
# ============================================================

def fetch_world_context(query, user_id):
    """Optional real-world signal gateway.

    Eagle Bot itself remains independent from a single search/data vendor.
    WORLD_ENGINE_URL can point to a service that aggregates web/search/news/
    market/weather/public-data/tool signals with its own source policies.
    """
    if not WORLD_ENGINE_URL:
        return None

    headers = {"Content-Type": "application/json"}
    if WORLD_ENGINE_KEY:
        headers["Authorization"] = f"Bearer {WORLD_ENGINE_KEY}"

    response = requests.post(
        WORLD_ENGINE_URL,
        json={"query": query, "user_id": user_id, "product": PRODUCT_NAME},
        headers=headers,
        timeout=WORLD_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    record_world_event("query", data.get("source", "world-engine"), data)
    return data

# ============================================================
# AI GATEWAY — model/provider independent
# ============================================================

def call_ai_gateway(message, coworker_key, context=None, world_context=None):
    if not AI_GATEWAY_URL:
        return None

    coworker = COWORKERS[coworker_key]
    payload = {
        "product": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "coworker": {
            "key": coworker_key,
            "name": coworker["name"],
            "mission": coworker["mission"],
            "permissions": coworker["permissions"],
        },
        "governance": {
            "human_authority": True,
            "autonomous_external_actions": False,
            "audit_required": True,
            "approval_required_for_high_impact_actions": True,
        },
        "message": message,
        "context": context or {},
        "world_context": world_context or {},
    }
    headers = {"Content-Type": "application/json"}
    if AI_GATEWAY_KEY:
        headers["Authorization"] = f"Bearer {AI_GATEWAY_KEY}"

    response = requests.post(AI_GATEWAY_URL, json=payload, headers=headers, timeout=AI_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    answer = data.get("answer") or data.get("message") or data.get("text")
    if not answer:
        raise RuntimeError("AI gateway returned no answer")
    return {
        "answer": str(answer),
        "coworker": data.get("coworker", coworker_key),
        "task_id": data.get("task_id"),
        "actions": data.get("actions", []),
        "sources": data.get("sources", []),
    }


def fallback_response(message, coworker_key, user_id, conversation_id):
    coworker = COWORKERS[coworker_key]
    lower = message.lower()

    # Requests that clearly seek research can use a world engine when configured.
    world_context = None
    if coworker_key in {"research", "analyst"} or any(token in lower for token in ["latest", "today", "current", "news"]):
        try:
            world_context = fetch_world_context(message, user_id)
        except Exception as exc:
            app.logger.warning("World engine unavailable: %s", exc)

    if world_context:
        source_note = ""
        sources = world_context.get("sources") or []
        if sources:
            source_note = "\n\nI also received current-world signals from Eagle's configured world engine."
        return {
            "answer": (
                f"🦅 **{coworker['name']}** is handling the request.\n\n"
                "Eagle has separated real-world signals from its core reasoning layer so data providers can change without changing Eagle's identity."
                f"{source_note}"
            ),
            "coworker": coworker_key,
            "task_id": None,
            "actions": [],
            "sources": sources,
        }

    task_id, approval_id = create_task(user_id, message, coworker_key, conversation_id)
    return {
        "answer": (
            f"🦅 **{coworker['name']}** has been selected.\n\n"
            f"Mission: {coworker['mission']}\n\n"
            "This request has entered Eagle's governed work layer. Because execution can create external side effects, "
            "Eagle does not silently act on the world: the task is auditable and approval-gated.\n\n"
            f"Task: `{task_id}`\nApproval: `{approval_id}`"
        ),
        "coworker": coworker_key,
        "task_id": task_id,
        "actions": [],
        "sources": [],
    }


def generate_response(message, coworker_key, user_id, conversation_id):
    world_context = None
    if coworker_key in {"research", "analyst"}:
        try:
            world_context = fetch_world_context(message, user_id)
        except Exception as exc:
            app.logger.info("World engine not configured/available: %s", exc)
    try:
        result = call_ai_gateway(message, coworker_key, {"conversation_id": conversation_id}, world_context)
        if result:
            audit("coworker", coworker_key, "ai.response.generated", "conversation", conversation_id,
                  {"sources": len(result.get("sources", [])), "actions": len(result.get("actions", []))})
            return result
    except Exception as exc:
        app.logger.warning("AI gateway unavailable: %s", exc)
    return fallback_response(message, coworker_key, user_id, conversation_id)

# ============================================================
# HTTP / AUTH HELPERS
# ============================================================

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        supplied = request.headers.get("X-Eagle-Admin-Key", "")
        admin_key = os.environ.get("EAGLE_ADMIN_KEY", "").strip()
        if not admin_key or not secrets.compare_digest(supplied, admin_key):
            return jsonify({"error": "admin authentication required"}), 401
        return fn(*args, **kwargs)
    return wrapper


def webhook_authorized():
    if not TELEGRAM_WEBHOOK_SECRET:
        return True
    supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return secrets.compare_digest(supplied, TELEGRAM_WEBHOOK_SECRET)

# ============================================================
# TELEGRAM — transport adapter
# ============================================================

def telegram_api(method):
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


def telegram_request(method, payload):
    response = requests.post(telegram_api(method), json=payload, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    body = response.json()
    if not body.get("ok"):
        raise RuntimeError(body.get("description", "Telegram API request failed"))
    return body


def eagle_web_url(path="/app"):
    return urljoin(PUBLIC_WEB_APP_URL + "/", path.lstrip("/")) if PUBLIC_WEB_APP_URL else None


def telegram_web_buttons():
    url = eagle_web_url("/app")
    if not url:
        return None
    buttons = [[{"text": "🦅 Open Eagle Bot", "url": url}]]
    if url.startswith("https://"):
        buttons.append([{"text": "⚡ Open Eagle Workspace", "web_app": {"url": url}}])
    return {"inline_keyboard": buttons}


def send_telegram_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_request("sendMessage", payload)


def send_telegram_file(chat_id, file_id):
    return telegram_request("sendDocument", {"chat_id": chat_id, "document": file_id})

# ============================================================
# WEB APP
# ============================================================
WEB_APP_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Eagle Bot — global AI-assisted work and intelligence platform.">
<title>Eagle Bot</title>
<style>
:root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
* { box-sizing: border-box; }
body { margin:0; background:#06100a; color:#eef8f0; }
header { position:sticky; top:0; z-index:5; padding:16px 20px; border-bottom:1px solid #193523; background:rgba(6,16,10,.94); backdrop-filter:blur(14px); }
.nav { width:min(1180px,calc(100% - 24px)); margin:auto; display:flex; justify-content:space-between; align-items:center; }
.brand { display:flex; align-items:center; gap:10px; font-weight:900; font-size:18px; }
.logo { width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:#12391f;border:1px solid #2a6540; }
.pill { padding:7px 10px;border-radius:999px;border:1px solid #244a32;color:#9ac0a5;font-size:12px; }
main { width:min(1180px,calc(100% - 24px)); margin:26px auto 70px; display:grid; grid-template-columns:.9fr 1.4fr; gap:18px; }
.card { background:#0a170e;border:1px solid #183521;border-radius:22px;padding:22px;box-shadow:0 18px 55px rgba(0,0,0,.24); }
.hero h1 { font-size:clamp(40px,7vw,78px);line-height:.92;margin:12px 0 18px;letter-spacing:-2px; }
.hero p { color:#b9ccbE; line-height:1.6; }
.grid { display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:20px; }
.cap { padding:12px;border:1px solid #1c3926;border-radius:14px;background:#0d1d13;font-size:13px;color:#cce1d1; }
.chat { display:flex; flex-direction:column; min-height:650px; }
.messages { flex:1; overflow:auto; padding:3px; }
.msg { margin:10px 0; padding:13px 15px; border-radius:16px; max-width:88%; white-space:pre-wrap; line-height:1.5; }
.user { margin-left:auto; background:#174326; }
.bot { background:#101d15;border:1px solid #1e3d29; }
.composer { display:flex; gap:10px; margin-top:12px; }
textarea { flex:1;min-height:56px;max-height:180px;resize:vertical;border-radius:15px;border:1px solid #2a4c35;background:#07110b;color:#fff;padding:14px;outline:none; }
button { border:0;border-radius:15px;padding:0 19px;background:#b9ffd0;color:#0a1a0e;font-weight:900;cursor:pointer; }
.status { margin-top:10px;font-size:12px;color:#779981; }
@media(max-width:850px){ main{grid-template-columns:1fr;} .chat{min-height:570px;} }
</style>
</head>
<body>
<header><div class="nav"><div class="brand"><div class="logo">🦅</div>Eagle Bot</div><div class="pill">{{ availability }}</div></div></header>
<main>
<section class="card hero">
<div class="pill">v{{ version }} · independent product layer</div>
<h1>Turn intent into work.</h1>
<p>{{ tagline }}</p>
<p>{{ description }}</p>
<div class="grid">
<div class="cap">🧠 Specialized Coworkers</div>
<div class="cap">🌍 World-signal ready</div>
<div class="cap">🛡 Governed actions</div>
<div class="cap">📚 Persistent work memory</div>
<div class="cap">🔎 Evidence-oriented research</div>
<div class="cap">🤝 Human approval when needed</div>
</div>
<p class="status">Telegram is a channel. Eagle Bot itself is the product.</p>
</section>
<section class="card chat">
<div id="messages" class="messages"><div class="msg bot">🦅 Welcome to Eagle Bot. Tell me the outcome you want to achieve.</div></div>
<div class="composer"><textarea id="input" placeholder="Research something, build something, learn something, analyze a problem, or organize work..."></textarea><button id="send">Send</button></div>
<div id="status" class="status">Ready.</div>
</section>
</main>
<script>
const visitorKey=localStorage.getItem('eagle_visitor_id')||crypto.randomUUID();localStorage.setItem('eagle_visitor_id',visitorKey);
let conversationId=localStorage.getItem('eagle_conversation_id')||'';
const input=document.getElementById('input'),send=document.getElementById('send'),messages=document.getElementById('messages'),statusEl=document.getElementById('status');
function add(role,text){const d=document.createElement('div');d.className='msg '+(role==='user'?'user':'bot');d.textContent=text;messages.appendChild(d);messages.scrollTop=messages.scrollHeight;}
async function submit(){const text=input.value.trim();if(!text||send.disabled)return;add('user',text);input.value='';send.disabled=true;statusEl.textContent='Eagle is routing the work...';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({visitor_id:visitorKey,conversation_id:conversationId,message:text})});const data=await r.json();if(data.conversation_id){conversationId=data.conversation_id;localStorage.setItem('eagle_conversation_id',conversationId);}add('assistant',data.answer||'Eagle returned no answer.');statusEl.textContent=(data.coworker?('Coworker: '+data.coworker.name):'Completed.');}catch(e){add('assistant','Eagle is temporarily unable to complete the request. Please try again.');statusEl.textContent='Temporarily unavailable.';}finally{send.disabled=false;input.focus();}}
send.addEventListener('click',submit);input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit();}});
</script>
</body></html>
"""


@app.get("/")
@app.get("/app")
def app_home():
    return render_template_string(
        WEB_APP_HTML,
        version=PRODUCT_VERSION,
        availability=SERVICE_AVAILABILITY,
        tagline=PRODUCT_TAGLINE,
        description=PRODUCT_DESCRIPTION,
    )


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "product": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "telegram_configured": bool(BOT_TOKEN),
        "ai_gateway_configured": bool(AI_GATEWAY_URL),
        "world_engine_configured": bool(WORLD_ENGINE_URL),
        "web_app_configured": bool(PUBLIC_WEB_APP_URL),
        "global_access": True,
        "service_availability": SERVICE_AVAILABILITY,
        "timestamp": now_iso(),
    })


@app.get("/api/coworkers")
def api_coworkers():
    return jsonify({"ok": True, "coworkers": COWORKERS})


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    visitor_id = str(data.get("visitor_id", "")).strip() or secrets.token_hex(12)
    conversation_id = str(data.get("conversation_id", "")).strip()

    if not message:
        return jsonify({"error": "message is required"}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": "message is too long"}), 413

    user_id = ensure_user("web", visitor_id)
    coworker_key = choose_coworker(message)
    if not conversation_id:
        conversation_id = create_conversation(user_id, coworker_key, message[:80])
    save_message(conversation_id, "user", message, coworker_key, "web")

    result = generate_response(message, coworker_key, user_id, conversation_id)
    save_message(conversation_id, "assistant", result["answer"], coworker_key, "eagle")

    return jsonify({
        "ok": True,
        "product": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "conversation_id": conversation_id,
        "coworker": {"key": coworker_key, **COWORKERS[coworker_key]},
        "task_id": result.get("task_id"),
        "sources": result.get("sources", []),
        "answer": result["answer"],
    })


@app.post("/api/orders")
def api_orders():
    data = request.get_json(silent=True) or {}
    name = str(data.get("customer_name", "")).strip()
    email = str(data.get("email", "")).strip()
    topic = str(data.get("topic", "")).strip()
    deadline = str(data.get("deadline", "")).strip()
    try:
        word_count = int(data.get("word_count"))
    except (TypeError, ValueError):
        return jsonify({"error": "word_count must be a number"}), 400
    if not name or not topic or not deadline or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "valid customer_name, email, topic and deadline are required"}), 400
    if word_count <= 0 or word_count > 1000000:
        return jsonify({"error": "word_count is outside supported range"}), 400
    order = {
        "order_number": generate_order_number(), "customer_name": name, "email": email, "topic": topic,
        "word_count": word_count, "deadline": deadline, "date": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "status": "Processing", "source": "web", "telegram_user_id": None, "created_at": now_iso(),
    }
    save_order(order)
    audit("web", "public", "order.created", "order", order["order_number"], {"source": "web"})
    return jsonify({"ok": True, "order": order}), 201


@app.get("/api/orders/<order_number>")
def api_order(order_number):
    order = get_order(order_number)
    if not order:
        return jsonify({"error": "order not found"}), 404
    visitor_id = request.args.get("visitor_id", "").strip()
    if order.get("source") == "web":
        # Web-created orders are returned only with a one-time lookup token in a future auth layer.
        # Until then, only admin access should be used for detailed customer data.
        return jsonify({"error": "authenticated customer order lookup is not enabled yet"}), 403
    if visitor_id and str(order.get("telegram_user_id")) != visitor_id:
        return jsonify({"error": "order belongs to another customer"}), 403
    return jsonify({"ok": True, "order": order})


@app.get("/api/tasks")
def api_tasks():
    visitor_id = request.args.get("visitor_id", "").strip()
    if not visitor_id:
        return jsonify({"error": "visitor_id is required"}), 400
    user_id = ensure_user("web", visitor_id)
    return jsonify({"ok": True, "tasks": list_tasks(user_id)})


@app.get("/api/tasks/<task_id>")
def api_task(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    visitor_id = request.args.get("visitor_id", "").strip()
    if not visitor_id:
        return jsonify({"error": "visitor_id is required"}), 400
    user_id = ensure_user("web", visitor_id)
    if str(task["user_id"]) != str(user_id):
        return jsonify({"error": "task belongs to another customer"}), 403
    return jsonify({"ok": True, "task": task})


@app.post("/api/approvals/<approval_id>/decide")
@admin_required
def api_decide_approval(approval_id):
    data = request.get_json(silent=True) or {}
    decision = str(data.get("decision", "")).strip().lower()
    if decision not in {"approve", "reject"}:
        return jsonify({"error": "decision must be approve or reject"}), 400

    with DB_LOCK, db() as conn:
        approval = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        if not approval:
            return jsonify({"error": "approval not found"}), 404
        if approval["status"] != "pending":
            return jsonify({"error": "approval already decided"}), 409
        status = "approved" if decision == "approve" else "rejected"
        conn.execute(
            "UPDATE approvals SET status = ?, decided_by = ?, decided_at = ? WHERE id = ?",
            (status, "admin", now_iso(), approval_id),
        )
        conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            ("approved" if decision == "approve" else "blocked", now_iso(), approval["task_id"]),
        )

    audit("admin", "admin", f"approval.{status}", "approval", approval_id, {"task_id": approval["task_id"]})
    return jsonify({"ok": True, "approval_id": approval_id, "status": status})


@app.post("/api/world/events")
@admin_required
def api_world_event():
    data = request.get_json(silent=True) or {}
    event_type = str(data.get("event_type", "")).strip()
    source = str(data.get("source", "manual")).strip()
    payload = data.get("payload", {})
    if not event_type:
        return jsonify({"error": "event_type is required"}), 400
    event_id = record_world_event(event_type, source, payload)
    return jsonify({"ok": True, "event_id": event_id}), 201


# ============================================================
# TELEGRAM HANDLER
# ============================================================

def handle_telegram_message(msg):
    sender = msg.get("from") or {}
    if not sender:
        return
    user_id = str(sender.get("id"))
    display_name = sender.get("username") or sender.get("first_name") or "Unknown"
    eagle_user_id = ensure_user("telegram", user_id, display_name)

    if "document" in msg:
        file_id = msg["document"].get("file_id")
        if file_id and BOT_TOKEN and ADMIN_USER_ID:
            send_telegram_message(ADMIN_USER_ID, f"📎 File received from {display_name} (`{user_id}`).", telegram_web_buttons())
            send_telegram_file(ADMIN_USER_ID, file_id)
        return

    text = msg.get("text", "").strip()
    if not text:
        return

    # ---------------- Legacy command compatibility ----------------
    if text == "/start":
        send_telegram_message(
            user_id,
            "🦅 **Welcome to Eagle Bot!**\n\n"
            "Eagle is an independent work and intelligence platform. Telegram is one doorway; Eagle's own web app is another.\n\n"
            "📝 `/new` — Start a new order\n"
            "🔍 `/status EAGLE-XXXXXX` — Check order status\n"
            "📊 `/analytics` — Admin statistics\n"
            "🧠 `/coworkers` — Meet the Coworkers\n"
            "🌍 `/web` — Open Eagle\n"
            "🕒 `/hours` — Service availability\n"
            "ℹ️ `/help` — Commands\n\n"
            "You can also simply tell Eagle what you want to accomplish.",
            telegram_web_buttons(),
        )
        return

    if text == "/web":
        url = eagle_web_url("/app")
        send_telegram_message(user_id, f"🌍 **Open Eagle Bot**\n\n{url if url else 'The public web address is not configured yet.'}", telegram_web_buttons())
        return

    if text == "/coworkers":
        lines = ["🧠 **Eagle Coworkers**\n"]
        for key, coworker in COWORKERS.items():
            lines.append(f"• **{coworker['name']}** — {coworker['mission']}")
        lines.append("\nSpecialized Coworkers can expand over time without changing Eagle's core identity.")
        send_telegram_message(user_id, "\n".join(lines), telegram_web_buttons())
        return

    if text == "/hours":
        send_telegram_message(user_id, f"🟢 **Eagle Bot is designed for 24/7 worldwide digital availability.**\n\n{SERVICE_AVAILABILITY}", telegram_web_buttons())
        return

    if text == "/help":
        send_telegram_message(
            user_id,
            "📋 **Eagle Bot**\n\n"
            "`/new` — Place a new order\n"
            "`/status EAGLE-XXXXXX` — Check your order\n"
            "`/analytics` — Admin stats\n"
            "`/coworkers` — Specialized Coworkers\n"
            "`/web` — Open Eagle's web app\n"
            "`/hours` — Availability\n"
            "`/help` — Help\n\n"
            "Or just tell Eagle what you need.",
            telegram_web_buttons(),
        )
        return

    if text.startswith("/status"):
        parts = text.split()
        if len(parts) < 2:
            send_telegram_message(user_id, "⚠️ Please provide an order number. Example: `/status EAGLE-123456`")
            return
        order = get_order(parts[1].upper())
        if not order:
            send_telegram_message(user_id, f"❌ Order {parts[1].upper()} not found. Please check and try again.")
            return
        if not is_admin(user_id) and str(order.get("telegram_user_id") or "") != user_id:
            send_telegram_message(user_id, "🔒 That order belongs to another customer account.")
            return
        status_text = (
            f"📋 **Order {order['order_number']}**\n\n"
            f"👤 **Customer:** {order['customer_name']}\n"
            f"📧 **Email:** {order['email']}\n"
            f"📝 **Topic:** {order['topic']}\n"
            f"📄 **Words:** {order['word_count']}\n"
            f"📅 **Deadline:** {order['deadline']}\n"
            f"📊 **Status:** {order['status']}"
        )
        send_telegram_message(user_id, status_text)
        return

    if text == "/analytics":
        if not is_admin(user_id):
            send_telegram_message(user_id, "🔒 Analytics is available to administrators only.")
            return
        with DB_LOCK, db() as conn:
            total_orders = conn.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"]
            today_orders = conn.execute("SELECT COUNT(*) AS n FROM orders WHERE date = ?", (dt.datetime.now(dt.timezone.utc).date().isoformat(),)).fetchone()["n"]
            tasks = conn.execute("SELECT COUNT(*) AS n FROM tasks WHERE status IN ('queued','running')").fetchone()["n"]
            conversations = conn.execute("SELECT COUNT(*) AS n FROM conversations").fetchone()["n"]
        send_telegram_message(user_id, f"📊 **Eagle Bot Analytics**\n\n📦 Orders: {total_orders}\n📅 Today: {today_orders}\n🧠 Active tasks: {tasks}\n💬 Conversations: {conversations}\n🕒 UTC: {dt.datetime.now(dt.timezone.utc).strftime('%I:%M %p')}\n🌍 Availability: 24/7 Worldwide")
        return

    # ---------------- Original order wizard ----------------
    with STATE_LOCK:
        state = user_states.setdefault(user_id, {"step": "start", "data": {}})

    if state["step"] == "start" and (text == "/new" or text.lower() == "new order"):
        with STATE_LOCK:
            state["step"] = "name"
            state["data"] = {}
        send_telegram_message(user_id, "📝 **New Order Form**\n\nPlease enter your **full name** 👇\n\n*(You can say 'cancel' anytime.)*")
        return

    if text.lower() == "cancel" and state["step"] != "start":
        with STATE_LOCK:
            state["step"] = "start"; state["data"] = {}
        send_telegram_message(user_id, "✅ Order cancelled. Use `/new` to start again.")
        return

    if state["step"] == "name":
        state["data"]["customer_name"] = text; state["step"] = "email"
        send_telegram_message(user_id, "📧 **Great!** Now enter your **email address** 👇"); return

    if state["step"] == "email":
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text):
            send_telegram_message(user_id, "⚠️ Please enter a valid email address."); return
        state["data"]["email"] = text; state["step"] = "topic"
        send_telegram_message(user_id, "📝 **What topic** do you need help with? 👇"); return

    if state["step"] == "topic":
        state["data"]["topic"] = text; state["step"] = "word_count"
        send_telegram_message(user_id, "📄 **How many words** do you need? (Approximately) 👇\n\n*Example: 2000*"); return

    if state["step"] == "word_count":
        try:
            words = int(text)
            if words <= 0: raise ValueError
        except ValueError:
            send_telegram_message(user_id, "⚠️ Please enter a valid number of words. Example: `2000`"); return
        state["data"]["word_count"] = words; state["step"] = "deadline"
        send_telegram_message(user_id, "📅 **When is your deadline?** 👇\n\n*Example: Friday, 11:59 PM*"); return

    if state["step"] == "deadline":
        data = state["data"]
        order = {
            "order_number": generate_order_number(), "customer_name": data["customer_name"], "email": data["email"],
            "topic": data["topic"], "word_count": data["word_count"], "deadline": text,
            "date": dt.datetime.now(dt.timezone.utc).date().isoformat(), "status": "Processing", "source": "telegram",
            "telegram_user_id": user_id, "created_at": now_iso(),
        }
        save_order(order)
        task_id, approval_id = create_task(eagle_user_id, f"Order {order['order_number']}: {order['topic']}", "operator", None,
                                            title=f"Fulfil order {order['order_number']}")
        audit("user", eagle_user_id, "order.created", "order", order["order_number"], {"task_id": task_id})

        admin_text = (
            f"📨 **NEW ORDER #{order['order_number']}**\n\n👤 **Customer:** {order['customer_name']}\n"
            f"📧 **Email:** {order['email']}\n📝 **Topic:** {order['topic']}\n📄 **Words:** {order['word_count']}\n"
            f"📅 **Deadline:** {order['deadline']}\n🕒 **Received:** {dt.datetime.now(dt.timezone.utc).strftime('%I:%M %p UTC')}\n\n"
            f"🧠 Task: `{task_id}`\n🔐 Approval: `{approval_id}`")
        if ADMIN_USER_ID and BOT_TOKEN:
            send_telegram_message(ADMIN_USER_ID, admin_text, telegram_web_buttons())

        customer_text = (
            "✅ **ORDER CONFIRMED!**\n\n"
            f"📋 **Order Number:** `{order['order_number']}`\n👤 **Name:** {order['customer_name']}\n"
            f"📧 **Email:** {order['email']}\n📝 **Topic:** {order['topic']}\n📄 **Words:** {order['word_count']}\n"
            f"📅 **Deadline:** {order['deadline']}\n\n📌 **What's next?**\n"
            "1️⃣ Eagle records the request\n2️⃣ The task enters the governed work layer\n"
            "3️⃣ The appropriate Coworker/team can be assigned\n4️⃣ Execution remains auditable and approval-gated\n\n"
            f"🔍 Check status: `/status {order['order_number']}`\n🌍 Continue outside Telegram using Eagle's web app.")
        send_telegram_message(user_id, customer_text, telegram_web_buttons())
        with STATE_LOCK:
            state["step"] = "start"; state["data"] = {}
        return

    # ---------------- Free-form work requests ----------------
    coworker_key = choose_coworker(text)
    conversation_id = create_conversation(eagle_user_id, coworker_key, text[:80])
    save_message(conversation_id, "user", text, coworker_key, "telegram")
    result = generate_response(text, coworker_key, eagle_user_id, conversation_id)
    save_message(conversation_id, "assistant", result["answer"], coworker_key, "eagle")
    send_telegram_message(user_id, result["answer"], telegram_web_buttons())


@app.post("/telegram/webhook")
def telegram_webhook():
    if not webhook_authorized():
        return "forbidden", 403
    try:
        data = request.get_json(silent=True) or {}
        if "message" in data:
            handle_telegram_message(data["message"])
        return "ok", 200
    except Exception as exc:
        app.logger.exception("Telegram webhook failure: %s", exc)
        try:
            if BOT_TOKEN and ADMIN_USER_ID:
                send_telegram_message(ADMIN_USER_ID, "⚠️ Eagle Bot encountered an internal processing error.")
        except Exception:
            pass
        return "error", 500


# Backward-compatible endpoint from the original bot.
@app.post("/")
def legacy_webhook():
    return telegram_webhook()


@app.get("/api/identity")
def api_identity():
    return jsonify({
        "product": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "identity_principles": [
            "Learn without copying",
            "Keep product identity independent from channels",
            "Use real-world evidence when configured",
            "Keep high-impact actions approval-gated",
            "Audit meaningful system decisions",
            "Upgrade capability without surrendering human authority",
        ],
    })


if __name__ == "__main__":
    # Development fallback only. Deploy behind a production WSGI server.
    app.run(host="0.0.0.0", port=PORT)
