import os
import re
from threading import Lock
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
import psycopg2
from psycopg2 import sql

# You can still keep DB_FILE for legacy reasons if you want (unused here)
from cogs.constants import DB_FILE, DB_PATH  # DB_PATH unused now, retained for compatibility

class DatabaseHandler:
    """
    PostgreSQL implementation with a compatibility layer for existing '?'
    placeholders (converted to '%s').
    """
    def __init__(
        self,
        minconn: int = 1,
        maxconn: int = 5,
        host: str = None,
        port: int = None,
        dbname: str = None,
        user: str = None,
        password: str = None
    ):
        self._lock = Lock()
        self._pool = None

        # Pull from env if not explicitly provided
        self._cfg = {
            "host": host or os.getenv("POSTGRES_HOST", "localhost"),
            "port": port or int(os.getenv("POSTGRES_PORT", "5432")),
            "dbname": dbname or os.getenv("POSTGRES_DB", "umbreon"),
            "user": user or os.getenv("POSTGRES_USER", "umbreon"),
            "password": password or os.getenv("POSTGRES_PASSWORD", "umbreon_pwd"),
        }
        self._minconn = minconn
        self._maxconn = maxconn
        self._init_pool()

    def _init_pool(self):
        with self._lock:
            if self._pool is None:
                self._pool = SimpleConnectionPool(
                    self._minconn,
                    self._maxconn,
                    **self._cfg
                )

    def close_pool(self):
        with self._lock:
            if self._pool:
                self._pool.closeall()
                self._pool = None

    @contextmanager
    def get_connection(self):
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    # --- Public API (kept synchronous & signature-compatible) ---

    def createDatabase(self):
        """
        Create database schema using the PostgreSQL schema file.
        """
        schema_file = "bot_postgres_schema.sql"
        if not os.path.exists(schema_file):
            print(f"Warning: {schema_file} not found. Using legacy schema adaptation.")
            self._create_legacy_schema()
            return

        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        statements = self._split_statements(schema_sql)
        for stmt in statements:
            if self._is_effective_sql(stmt):
                self.execute_db_query(stmt)

    def _create_legacy_schema(self):
        """
        Fallback: read the old SQLite schema and adapt it minimally.
        """
        if not os.path.exists(DB_FILE):
            return

        with open(DB_FILE, "r", encoding="utf-8") as f:
            raw_sql = f.read()

        statements = self._split_statements(raw_sql)
        for stmt in statements:
            if self._is_effective_sql(stmt):
                # Basic SQLite to PostgreSQL adaptations
                adapted_stmt = stmt.replace("INT", "BIGINT")
                adapted_stmt = adapted_stmt.replace("BOOL", "BOOLEAN")
                # Fix the logsettings table missing type
                if "logsettings" in adapted_stmt and "is_enabled)" in adapted_stmt:
                    adapted_stmt = adapted_stmt.replace("is_enabled)", "is_enabled BOOLEAN)")
                self.execute_db_query(adapted_stmt)

    def execute_db_query(self, query, params=None):
        q, params = self._prepare(query, params)
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(q, params or [])
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def extract_value(self, result, index=0):
        """
        Safely extract a value from a database result.

        PostgreSQL and SQLite return results differently:
        - SQLite returns tuple-like objects
        - psycopg returns tuples

        This method handles both cases and provides a consistent way to extract values.

        Args:
            result: The database result (tuple, None, or scalar value)
            index: The index to extract (default 0 for first column)

        Returns:
            The extracted value or None if result is None
        """
        if result is None:
            return None
        if isinstance(result, (list, tuple)):
            return result[index] if len(result) > index else None
        return result  # Direct scalar value

    def fetch_one_from_db(self, query, params=None):
        q, params = self._prepare(query, params)
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(q, params or [])
                return cur.fetchone()

    def fetch_all_from_db(self, query, params=None):
        q, params = self._prepare(query, params)
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(q, params or [])
                return cur.fetchall()

    # --- Internal helpers ---

    _qmark_pattern = re.compile(r'\?')

    def _convert_qmarks_to_psycopg(self, query: str):
        """
        Converts each '?' to '%s' while preserving order.
        """
        # If no question marks, return early
        if '?' not in query:
            return query
        # Replace all ? with %s
        return self._qmark_pattern.sub('%s', query)

    def _prepare(self, query, params):
        converted = self._convert_qmarks_to_psycopg(query)
        return converted, params

    # Comment handling helpers
    _line_comment_pattern = re.compile(r"--.*?(?=\n|$)")
    _block_comment_pattern = re.compile(r"/\*.*?\*/", re.S)

    def _strip_sql_comments(self, sql_text: str) -> str:
        """Remove SQL line (--) and block (/* */) comments."""
        without_block = self._block_comment_pattern.sub("", sql_text)
        without_line = self._line_comment_pattern.sub("", without_block)
        return without_line

    def _is_effective_sql(self, sql_text: str) -> bool:
        """Return True if the SQL has non-comment, non-whitespace content."""
        return bool(self._strip_sql_comments(sql_text).strip())

    @staticmethod
    def _split_statements(sql_text: str):
        # Simple split on semicolons not inside quotes (naive but okay for your small file)
        statements = []
        current = []
        in_single = False
        in_double = False
        for ch in sql_text:
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            if ch == ';' and not in_single and not in_double:
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(ch)
        tail = ''.join(current).strip()
        if tail:
            statements.append(tail)
        return statements
