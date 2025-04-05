import sqlite3
from collections import defaultdict
from itertools import groupby

class Database:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)
        #self.con.isolation_level = None
        self.cursor = self.con.cursor()
        self.setup_tables()

    def setup_tables(self):
        with self.con:
            pass


db = Database('bot.db')
