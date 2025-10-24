import sqlite3
from pathlib import Path
import json
from datetime import datetime

DB_PATH = Path("ai_backend_demo.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not DB_PATH.exists():
        conn = get_conn()
        cur = conn.cursor()
        # Conversations table: store raw + normalized
        cur.execute(
            """
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            channel TEXT,
            subject TEXT,
            raw_message TEXT,
            normalized_json TEXT,
            status TEXT,
            created_at TEXT
        )
        """
        )
        # Payloads table (from AI Bot)
        cur.execute(
            """
        CREATE TABLE payloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            payload_json TEXT,
            status TEXT,
            created_at TEXT
        )
        """
        )
        # Tickets table (Teamwork)
        cur.execute(
            """
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id TEXT,
            ticket_title TEXT,
            description TEXT,
            assigned_to TEXT,
            status TEXT,
            created_at TEXT
        )
        """
        )
        # Rules table (consultant assignment)
        cur.execute(
            """
        CREATE TABLE rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            mode TEXT,
            static_consultant TEXT,
            rr_cursor INTEGER DEFAULT 0
        )
        """
        )
        # Consultants table
        cur.execute(
            """
        CREATE TABLE consultants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
        """
        )

        cur.execute("INSERT INTO consultants (username) VALUES (?)", ("consultant_a",))
        cur.execute("INSERT INTO consultants (username) VALUES (?)", ("consultant_b",))
        conn.commit()
        conn.close()


# Helper functions
def insert_conversation(sender, channel, subject, raw_message, normalized):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
    INSERT INTO conversations (sender, channel, subject, raw_message, normalized_json, status, created_at)
    VALUES (?,?,?,?,?,? ,?)
    """,
        (
            sender,
            channel,
            subject,
            raw_message,
            json.dumps(normalized),
            "new",
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def list_conversations_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM conversations ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def update_conversation_status(conversation_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversations SET status=? WHERE id=?", (status, conversation_id)
    )
    conn.commit()
    conn.close()


def insert_payload(conversation_id, payload):
    import json

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO payloads (conversation_id, payload_json, status, created_at) VALUES (?,?,?,?)",
        (
            conversation_id,
            json.dumps(payload),
            "ready" if payload.get("complete") else "waiting",
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def list_ready_payloads():
    import json

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM payloads WHERE status='ready' ORDER BY id ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    for r in rows:
        r["payload"] = json.loads(r["payload_json"])
    return rows


def mark_payload_processed(payload_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE payloads SET status='processed' WHERE id=?", (payload_id,))
    conn.commit()
    conn.close()


def insert_ticket(service_id, ticket_title, description, assigned_to):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
    INSERT INTO tickets (service_id, ticket_title, description, assigned_to, status, created_at)
    VALUES (?,?,?,?,?,?)
    """,
        (
            service_id,
            ticket_title,
            description,
            assigned_to,
            "New",
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid


def list_tickets_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# rules helpers
def get_rule_for_service(service):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rules WHERE service=?", (service,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def save_rule(service, mode, static_consultant=None):
    conn = get_conn()
    cur = conn.cursor()
    existing = get_rule_for_service(service)
    if existing:
        cur.execute(
            "UPDATE rules SET mode=?, static_consultant=? WHERE service=?",
            (mode, static_consultant, service),
        )
    else:
        cur.execute(
            "INSERT INTO rules (service, mode, static_consultant) VALUES (?,?,?)",
            (service, mode, static_consultant),
        )
    conn.commit()
    conn.close()


def list_consultants():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM consultants ORDER BY username")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def add_consultant(username):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO consultants (username) VALUES (?)", (username,))
        conn.commit()
    except:
        pass
    conn.close()


def get_and_increment_rr(service):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT rr_cursor FROM rules WHERE service=?", (service,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return 0
    cursor = row[0] if row[0] is not None else 0
    cur.execute("UPDATE rules SET rr_cursor=? WHERE service=?", (cursor + 1, service))
    conn.commit()
    conn.close()
    return cursor
