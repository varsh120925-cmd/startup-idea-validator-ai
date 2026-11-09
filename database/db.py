import sqlite3
import os
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from config import Config

def get_connection():
    """Returns a new connection with Row factory configured"""
    db_path = Config.DATABASE_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    """Context manager for safe database access with auto-commit/rollback"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def close_db(e=None):
    """Utility to close connection if stored in flask g"""
    pass

def init_db():
    """Initialize database tables, indices, and seed default user"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'entrepreneur'
            );
        """)

        # Startup Ideas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS startup_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                raw_description TEXT NOT NULL,
                industry TEXT,
                target_audience TEXT,
                problem_statement TEXT,
                proposed_solution TEXT,
                revenue_model TEXT,
                status TEXT DEFAULT 'draft',
                viability_score INTEGER DEFAULT 0,
                recommendation TEXT DEFAULT 'Pending Validation',
                is_sample BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Analysis Results table (one row per agent per idea)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                result_json TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                execution_time_sec REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES startup_ideas (id) ON DELETE CASCADE,
                UNIQUE(idea_id, agent_name)
            );
        """)

        # Competitors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                competitor_type TEXT DEFAULT 'Direct',
                website_url TEXT,
                pricing_model TEXT,
                features TEXT,
                strengths TEXT,
                weaknesses TEXT,
                market_gap TEXT,
                source_reference TEXT,
                verified_source BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES startup_ideas (id) ON DELETE CASCADE
            );
        """)

        # Migration check: ensure features column exists for existing databases
        try:
            cursor.execute("ALTER TABLE competitors ADD COLUMN features TEXT;")
        except Exception:
            pass

        # Chat Messages table (AI Startup Advisor)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES startup_ideas (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Validation Reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                summary_text TEXT,
                viability_score INTEGER DEFAULT 0,
                market_score INTEGER DEFAULT 0,
                competition_score INTEGER DEFAULT 0,
                execution_score INTEGER DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                pdf_filename TEXT,
                full_report_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES startup_ideas (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ideas_user ON startup_ideas (user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_idea ON analysis_results (idea_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_idea ON chat_messages (idea_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitor_idea ON competitors (idea_id);")

        # Seed default demo account if none exists
        cursor.execute("SELECT id FROM users WHERE email = 'demo@startupvalidator.com'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "demofounder",
                "demo@startupvalidator.com",
                generate_password_hash("password123"),
                "Alex Rivera (Founder)",
                "entrepreneur"
            ))

    print("[Database] Initialized tables and schema successfully.")
