import os, sqlite3, json

DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_db():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        return PgWrapper(conn)
    else:
        conn = sqlite3.connect('dcja.db')
        conn.row_factory = sqlite3.Row
        return SqliteWrapper(conn)

class SqliteWrapper:
    def __init__(self, conn): self.conn = conn
    def execute(self, sql, params=()):
        return self.conn.execute(sql, params)
    def fetchone(self, sql, params=()):
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None
    def fetchall(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]
    def executescript(self, sql):
        self.conn.executescript(sql)
    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.conn.commit(); self.conn.close()

class PgWrapper:
    def __init__(self, conn):
        self.conn = conn
        self.conn.autocommit = False

    def _q(self, sql):
        """Convert SQLite placeholders and syntax to PostgreSQL."""
        sql = sql.replace('?', '%s')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        sql = sql.replace("DEFAULT '{}'", "DEFAULT '{}'")
        return sql

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(self._q(sql), params)
        return cur

    def fetchone(self, sql, params=()):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(self._q(sql), params)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetchall(self, sql, params=()):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(self._q(sql), params)
        return [dict(r) for r in cur.fetchall()]

    def executescript(self, sql):
        """Run each CREATE TABLE individually, skip if already exists."""
        pg_sql = self._q(sql)
        statements = [s.strip() for s in pg_sql.split(';') if s.strip()]
        for stmt in statements:
            try:
                cur = self.conn.cursor()
                cur.execute(stmt)
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                err = str(e).lower()
                # Silently skip "already exists" errors
                if 'already exists' in err or 'duplicate' in err:
                    pass
                else:
                    raise

    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a):
        try: self.conn.commit()
        except: self.conn.rollback()
        self.conn.close()
