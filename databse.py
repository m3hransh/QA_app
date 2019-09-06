from flask import g
import sqlite3
import os

def connect_db():
    cur_dir = os.path.dirname(os.path.abspath(__name__))
    db_path = os.path.join(cur_dir,'questions.db')
    g.sqlite_db = sqlite3.connect(db_path)
    return g.sqlite_db

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
