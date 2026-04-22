import os, sqlite3

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

def get_db_schema():
    """Separate connection for schema migrations — uses autocommit so each
    CREATE TABLE is independent and a failure does not abort the transaction."""
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True          # Each statement is its own transaction
        return PgSchemaWrapper(conn)
    else:
        conn = sqlite3.connect('dcja.db')
        conn.row_factory = sqlite3.Row
        return SqliteWrapper(conn)

# ── SQLite ────────────────────────────────────────────────────
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

# ── PostgreSQL — schema migrations (autocommit) ───────────────
class PgSchemaWrapper:
    """Used only in init_db(). autocommit=True means each statement is atomic."""
    def __init__(self, conn): self.conn = conn

    def _q(self, sql):
        sql = sql.replace('?', '%s')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        return sql

    def executescript(self, sql):
        stmts = [s.strip() for s in self._q(sql).split(';') if s.strip()]
        for stmt in stmts:
            try:
                cur = self.conn.cursor()
                cur.execute(stmt)
            except Exception as e:
                err = str(e).lower()
                if 'already exists' in err or 'duplicate' in err:
                    pass   # normal — table already created
                else:
                    raise

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

    def commit(self): pass   # autocommit — nothing to do
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.conn.close()

# ── PostgreSQL — regular queries (transactional) ─────────────
class PgWrapper:
    def __init__(self, conn): self.conn = conn

    def _q(self, sql):
        sql = sql.replace('?', '%s')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        return sql

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(self._q(sql), params)
        return cur

    def executescript(self, sql):
        # Should not be called on regular PgWrapper — delegate to schema wrapper
        stmts = [s.strip() for s in self._q(sql).split(';') if s.strip()]
        for stmt in stmts:
            try:
                cur = self.conn.cursor()
                cur.execute(stmt)
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                if 'already exists' in str(e).lower(): pass
                else: raise

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

    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a):
        try: self.conn.commit()
        except: self.conn.rollback()
        self.conn.close() 
