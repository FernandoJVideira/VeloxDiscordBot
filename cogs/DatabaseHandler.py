
import sqlite3

DATABASE_FILE = "botDB.sql"
DATABASE = "bot.db"

class DatabaseHandler:
    def __init__(self):
        self.database = sqlite3.connect(DATABASE)
        self.cursor = self.database.cursor()

    def createDatabase(self):
        with open(DATABASE_FILE, 'r') as sql_file:
            sql_script = sql_file.read()
            self.cursor.executescript(sql_script)
            self.database.commit()
            self.database.close()

    def fetch_all_from_db(self, query, params):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def fetch_one_from_db(self, query, params):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()
    
    def execute_db_query(self, query, params):
        self.cursor.execute(query, params)
        self.database.commit()