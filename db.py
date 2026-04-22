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

class PgWrapper:
    def __init__(self, conn):
        self.conn = conn

    def _q(self, sql):
        sql = sql.replace('?', '%s')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
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
        """Run each statement in its own savepoint so one failure doesn't kill the whole transaction."""
        pg_sql = self._q(sql)
        statements = [s.strip() for s in pg_sql.split(';') if s.strip()]
        for stmt in statements:
            try:
                self.conn.execute('SAVEPOINT sp_migrate')
                cur = self.conn.cursor()
                cur.execute(stmt)
                self.conn.execute('RELEASE SAVEPOINT sp_migrate')
            except Exception as e:
                self.conn.execute('ROLLBACK TO SAVEPOINT sp_migrate')
                err = str(e).lower()
                if 'already exists' in err or 'duplicate' in err:
                    pass  # Table/column already exists — skip silently
                else:
                    raise  # Real error — re-raise

    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, *a):
        try: self.conn.commit()
        except: self.conn.rollback()
        self.conn.close()
