import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
import json

DB_PATH = "bot.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Инициализация базы данных"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                plan TEXT DEFAULT 'free',
                subscribed_until TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT 0
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                count INTEGER DEFAULT 0,
                date TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE (user_id, action, date)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id TEXT UNIQUE,
                amount INTEGER,
                currency TEXT DEFAULT 'RUB',
                status TEXT DEFAULT 'PENDING',
                payment_id TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target_user_id INTEGER DEFAULT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(user_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

def ensure_user(user_id, username=None):
    """Создать пользователя, если его нет"""
    user = get_user(user_id)
    if not user:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (user_id, username, plan) VALUES (?, ?, 'free')",
                (user_id, username)
            )

def get_user(user_id):
    """Получить информацию о пользователе"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_id, username, email, plan, subscribed_until, is_admin FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row:
            return dict(row)
    return None

def set_premium(user_id, days=30):
    """Активировать премиум подписку"""
    expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET plan = 'premium', subscribed_until = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (expires, user_id)
        )

def is_premium(user_id):
    """Проверить, активна ли премиум подписка"""
    user = get_user(user_id)
    if not user:
        return False
    
    if user['plan'] != 'premium':
        return False
    
    if user['subscribed_until']:
        expires = datetime.strptime(user['subscribed_until'], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < expires:
            return True
        else:
            # Истекла подписка, вернуть в free
            with get_db() as conn:
                conn.execute(
                    "UPDATE users SET plan = 'free', subscribed_until = NULL WHERE user_id = ?",
                    (user_id,)
                )
            return False
    
    return False

def increment_usage(user_id, action):
    """Увеличить счётчик использования"""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        row = conn.execute(
            "SELECT count FROM usage WHERE user_id = ? AND action = ? AND date = ?",
            (user_id, action, today)
        ).fetchone()
        if row:
            new_count = row[0] + 1
            conn.execute(
                "UPDATE usage SET count = ? WHERE user_id = ? AND action = ? AND date = ?",
                (new_count, user_id, action, today)
            )
        else:
            conn.execute(
                "INSERT INTO usage (user_id, action, count, date) VALUES (?, ?, 1, ?)",
                (user_id, action, today)
            )

def get_usage_today(user_id, action):
    """Получить использование за сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        row = conn.execute(
            "SELECT count FROM usage WHERE user_id = ? AND action = ? AND date = ?",
            (user_id, action, today)
        ).fetchone()
    if row:
        return row[0]
    return 0

def get_weekly_usage(user_id):
    """Получить использование за неделю"""
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT SUM(count)
            FROM usage
            WHERE user_id = ? AND action = 'text' AND date >= ?
            """,
            (user_id, week_ago)
        ).fetchone()
    return row[0] or 0 if row else 0

def create_payment(user_id, order_id, amount):
    """Создать запись о платеже"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO payments (user_id, order_id, amount) VALUES (?, ?, ?)",
            (user_id, order_id, amount)
        )

def update_payment_status(order_id, status, payment_id=None):
    """Обновить статус платежа"""
    with get_db() as conn:
        conn.execute(
            "UPDATE payments SET status = ?, payment_id = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?",
            (status, payment_id, order_id)
        )

def get_payment(order_id):
    """Получить информацию о платеже"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM payments WHERE order_id = ?",
            (order_id,)
        ).fetchone()
        if row:
            return dict(row)
    return None

def get_user_payments(user_id):
    """Получить все платежи пользователя"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]

def get_all_users():
    """Получить всех пользователей"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT user_id, username, plan, subscribed_until, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]

def get_admin_logs(limit=100):
    """Получить логи админа"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(row) for row in rows]

def add_admin_log(admin_id, action, target_user_id=None, details=None):
    """Добавить лог админа"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO admin_logs (admin_id, action, target_user_id, details) VALUES (?, ?, ?, ?)",
            (admin_id, action, target_user_id, details)
        )

def get_statistics():
    """Получить статистику бота"""
    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        premium_users = conn.execute("SELECT COUNT(*) FROM users WHERE plan = 'premium' AND subscribed_until > datetime('now')").fetchone()[0]
        total_revenue = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'CONFIRMED'").fetchone()[0]
        total_requests = conn.execute("SELECT COALESCE(SUM(count), 0) FROM usage").fetchone()[0]
    
    return {
        'total_users': total_users,
        'premium_users': premium_users,
        'total_revenue': total_revenue,
        'total_requests': total_requests
    }
