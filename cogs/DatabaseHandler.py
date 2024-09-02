import sqlite3
import time
from contextlib import contextmanager
from threading import Lock
from cogs.constants import (
    DB_FILE, 
    DB_PATH
)


class DatabaseHandler:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.connection_pool = []
        self.pool_lock = Lock()
        self.max_connections = 5
        self.init_connection_pool()

    def createDatabase(self):
        with open(DB_FILE, 'r') as sql_file:
            sql_script = sql_file.read()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executescript(sql_script)
                conn.commit()

    def init_connection_pool(self):
        for _ in range(self.max_connections):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode
            self.connection_pool.append(conn)

    @contextmanager
    def get_connection(self):
        with self.pool_lock:
            if not self.connection_pool:
                time.sleep(0.1)  # Wait a bit if all connections are in use
            conn = self.connection_pool.pop()
        try:
            yield conn
        finally:
            with self.pool_lock:
                self.connection_pool.append(conn)

    def execute_db_query(self, query, params=None):
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def fetch_one_from_db(self, query, params=None):
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    return cursor.fetchone()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise


    def fetch_all_from_db(self, query, params=None):
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    return cursor.fetchall()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise