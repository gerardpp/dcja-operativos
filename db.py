"""
Database abstraction layer.
Uses PostgreSQL if DATABASE_URL env var is set (Render production),
falls back to SQLite for local development.
"""
import os, sqlite3, json

DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_db():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return PgWrapper(conn)
    else:
        conn = sqlite3.connect('dcja.db')
        conn.row_factory = sqlite3.Row
        return SqliteWrapper(conn)

class SqliteWrapper:
    def __init__(self, conn): self.conn = conn
    def execute(self, sql, params=()): return self.conn.execute(sql, params)
    def executescript(self, sql): return self.conn.executescript(sql)
    def fetchone(self, sql, params=()): return self.conn.execute(sql, params).fetchone()
    def fetchall(self, sql, params=()): return self.conn.execute(sql, params).fetchall()
    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a):
        self.conn.commit()
        self.conn.close()

class PgWrapper:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
    def _adapt(self, sql):
        # Convert SQLite ? placeholders to PostgreSQL %s
        return sql.replace('?', '%s')
    def execute(self, sql, params=()):
        self.cur.execute(self._adapt(sql), params)
        return self.cur
    def executescript(self, sql):
        # Convert SQLite syntax to PostgreSQL
        pg_sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        pg_sql = pg_sql.replace("DEFAULT '{}'", "DEFAULT '{}'")
        # Split and run statements
        for stmt in pg_sql.split(';'):
            s = stmt.strip()
            if s:
                try:
                    self.cur.execute(s)
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        pass  # Table already exists, skip
                    else:
                        raise
        return self.cur
    def fetchone(self, sql, params=()):
        self.cur.execute(self._adapt(sql), params)
        return self.cur.fetchone()
    def fetchall(self, sql, params=()):
        self.cur.execute(self._adapt(sql), params)
        return self.cur.fetchall()
    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a):
        self.conn.commit()
        self.conn.close()
