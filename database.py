import sqlite3
import datetime
import re
from collections import Counter
from contextlib import closing

DB_FILE = "shiina.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_connection()) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hearts (
                user_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                name TEXT,
                hearts INTEGER DEFAULT 0,
                last_date TEXT,
                PRIMARY KEY (user_id, chat_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hearts_chat_hearts
            ON hearts (chat_id, hearts DESC)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat_user
            ON messages (chat_id, user_id, id DESC)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                last_interaction_id TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT,
                event_type TEXT NOT NULL,
                text TEXT,
                response TEXT,
                model TEXT,
                mode TEXT,
                duration_ms INTEGER,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_type_time
            ON metrics (event_type, created_at DESC)
        """)

        conn.commit()


def get_hearts(chat_id: str, user_id: str):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT hearts, last_date, name FROM hearts WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        )
        return cursor.fetchone()


def add_hearts(chat_id: str, user_id: str, name: str, amount: int, today: str):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hearts (user_id, chat_id, name, hearts, last_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET
                hearts = hearts + ?,
                last_date = ?,
                name = ?
        """, (user_id, chat_id, name, amount, today, amount, today, name))
        conn.commit()


def get_top(chat_id: str, limit: int = 10):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, hearts FROM hearts
            WHERE chat_id = ?
            ORDER BY hearts DESC
            LIMIT ?
        """, (chat_id, limit))
        return cursor.fetchall()


def get_user_rank(chat_id: str, user_id: str):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) + 1 FROM hearts
            WHERE chat_id = ? AND hearts > (
                SELECT hearts FROM hearts WHERE chat_id = ? AND user_id = ?
            )
        """, (chat_id, chat_id, user_id))
        row = cursor.fetchone()
        return row[0] if row else None



def add_message(chat_id: str, user_id: str, role: str, content: str):
    if len(content) > 500:
        content = content[:500] + "..."

    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (chat_id, user_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, user_id, role, content, datetime.datetime.now().isoformat()))
        conn.commit()


def get_history(chat_id: str, user_id: str, limit: int = 10):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM messages
            WHERE chat_id = ? AND user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (chat_id, user_id, limit))
        rows = cursor.fetchall()
        return list(reversed(rows))



def get_last_interaction_id(chat_id: str, user_id: str):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_interaction_id FROM interactions WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        )
        row = cursor.fetchone()
        return row["last_interaction_id"] if row else None


def save_interaction_id(chat_id: str, user_id: str, interaction_id: str):
    now = datetime.datetime.now().isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interactions (chat_id, user_id, last_interaction_id, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                last_interaction_id = ?,
                updated_at = ?
        """, (chat_id, user_id, interaction_id, now, interaction_id, now))
        conn.commit()


def clear_interaction_id(chat_id: str, user_id: str):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM interactions WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        )
        conn.commit()



def cleanup_old_messages(days: int = 30):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE created_at < ?", (cutoff,))
        conn.commit()
        return cursor.rowcount


def cleanup_old_metrics(days: int = 90):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM metrics WHERE created_at < ?", (cutoff,))
        conn.commit()
        return cursor.rowcount


def cleanup_old_interactions(days: int = 30):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM interactions WHERE updated_at < ?", (cutoff,))
        conn.commit()
        return cursor.rowcount



def log_metric(
    chat_id: str,
    user_id: str,
    event_type: str,
    text: str = None,
    response: str = None,
    model: str = None,
    mode: str = None,
    duration_ms: int = None,
    username: str = None,
):
    if text and len(text) > 1000:
        text = text[:1000] + "..."
    if response and len(response) > 1000:
        response = response[:1000] + "..."

    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics
            (chat_id, user_id, username, event_type, text, response, model, mode, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id, user_id, username, event_type, text, response,
            model, mode, duration_ms, datetime.datetime.now().isoformat()
        ))
        conn.commit()


def get_metrics_summary(days: int = 7):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type, COUNT(*) as cnt
            FROM metrics
            WHERE created_at >= ?
            GROUP BY event_type
            ORDER BY cnt DESC
        """, (cutoff,))
        return cursor.fetchall()


def get_mode_breakdown(days: int = 7):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mode, COUNT(*) as cnt
            FROM metrics
            WHERE created_at >= ? AND event_type = 'ai_request' AND mode IS NOT NULL
            GROUP BY mode
        """, (cutoff,))
        return cursor.fetchall()


def get_avg_duration(days: int = 7):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT AVG(duration_ms) FROM metrics
            WHERE created_at >= ? AND event_type = 'ai_request' AND duration_ms IS NOT NULL
        """, (cutoff,))
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] else None


def get_top_users(days: int = 7, limit: int = 10):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, COUNT(*) as cnt
            FROM metrics
            WHERE created_at >= ? AND event_type = 'ai_request'
            GROUP BY user_id
            ORDER BY cnt DESC
            LIMIT ?
        """, (cutoff, limit))
        return cursor.fetchall()


def get_recent_errors(limit: int = 20):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id, model, response, created_at
            FROM metrics
            WHERE event_type = 'ai_error'
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()


def get_top_words(days: int = 7, limit: int = 20):
    stop_words = {
        "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как",
        "а", "то", "все", "она", "так", "его", "но", "да", "ты", "к",
        "у", "же", "вы", "за", "бы", "по", "только", "ее", "мне", "было",
        "вот", "от", "меня", "еще", "нет", "о", "из", "ему", "теперь",
        "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или",
        "ни", "быть", "был", "него", "до", "вас", "нибудь", "опять",
        "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей",
        "может", "они", "тут", "где", "есть", "надо", "ней", "для",
        "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без",
        "будто", "чего", "раз", "тоже", "себе", "под", "будет",
        "ж", "тогда", "кто", "этот", "того", "потому", "этого",
        "какой", "совсем", "ним", "здесь", "этом", "один", "почти",
        "мой", "тем", "чтобы", "нее", "сейчас", "были", "куда",
        "зачем", "всех", "никогда", "можно", "при", "наконец",
        "два", "об", "другой", "хоть", "после", "над", "больше",
        "тот", "через", "эти", "нас", "про", "всего", "них",
        "какая", "много", "разве", "три", "эту", "моя", "впрочем",
        "хорошо", "свою", "этой", "перед", "иногда", "лучше",
        "чуть", "том", "нельзя", "такой", "им", "более", "всегда",
        "конечно", "всю", "между",
    }

    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT text FROM metrics
            WHERE created_at >= ? AND event_type = 'ai_request' AND text IS NOT NULL
        """, (cutoff,))
        rows = cursor.fetchall()

    words = []
    for row in rows:
        text = row["text"].lower()
        for word in re.findall(r"[а-яёa-z]+", text):
            if len(word) > 2 and word not in stop_words:
                words.append(word)

    return Counter(words).most_common(limit)