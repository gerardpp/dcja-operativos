import os, sqlite3

DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_db():
    if DATABASE_URL:
        import psycopg2, psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return PgWrapper(conn)
    else:
        conn = sqlite3.connect('dcja.db')
        conn.row_factory = sqlite3.Row
        return SqliteWrapper(conn)

def get_db_schema():
    """Autocommit connection for schema migrations — each statement is independent."""
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return PgSchemaWrapper(conn)
    else:
        conn = sqlite3.connect('dcja.db')
        conn.row_factory = sqlite3.Row
        return SqliteWrapper(conn)

class SqliteWrapper:
    def __init__(self, conn): self.conn = conn
    def execute(self, sql, params=()):
        return self.conn.execute(sql, params)
    def executescript(self, sql):
        return self.conn.executescript(sql)
    def fetchone(self, sql, params=()):
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None
    def fetchall(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]
    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.conn.commit(); self.conn.close()

class PgSchemaWrapper:
    """autocommit=True — each CREATE TABLE is its own transaction."""
    def __init__(self, conn): self.conn = conn
    def _q(self, sql):
        sql = sql.replace('?', '%s')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        return sql
    def executescript(self, sql):
        for stmt in self._q(sql).split(';'):
            s = stmt.strip()
            if not s: continue
            try:
                cur = self.conn.cursor(); cur.execute(s)
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    pass
                else:
                    raise
    def execute(self, sql, params=()):
        cur = self.conn.cursor(); cur.execute(self._q(sql), params); return cur
    def fetchone(self, sql, params=()):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(self._q(sql), params)
        row = cur.fetchone(); return dict(row) if row else None
    def fetchall(self, sql, params=()):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(self._q(sql), params)
        return [dict(r) for r in cur.fetchall()]
    def commit(self): pass
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.conn.close()

class PgWrapper:
    def __init__(self, conn): self.conn = conn
    def _q(self, sql):
        sql = sql.replace('?', '%s')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        return sql
    def execute(self, sql, params=()):
        cur = self.conn.cursor(); cur.execute(self._q(sql), params); return cur
    def executescript(self, sql):
        for stmt in self._q(sql).split(';'):
            s = stmt.strip()
            if not s: continue
            try:
                cur = self.conn.cursor(); cur.execute(s); self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                if 'already exists' in str(e).lower(): pass
                else: raise
    def fetchone(self, sql, params=()):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(self._q(sql), params)
        row = cur.fetchone(); return dict(row) if row else None
    def fetchall(self, sql, params=()):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(self._q(sql), params)
        return [dict(r) for r in cur.fetchall()]
    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a):
        try: self.conn.commit()
        except: self.conn.rollback()
        self.conn.close()
