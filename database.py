from flask import g
import sqlite3
import os
import psycopg2
from psycopg2.extras import DictCursor

def connect_db():
    conn = psycopg2.connect('postgres://jpppagepytstsl:3a271c4cc54d58a83535d73344b886d5a5b0ff9cdca30915394fb90ce86d93f7@ec2-184-73-169-163.compute-1.amazonaws.com:5432/df16pjbfjocj4l', cursor_factory=DictCursor)
    conn.autocommit = True
    sql= conn.cursor()
    return conn, sql


def get_db():
    db = connect_db()

    if not hasattr(g, 'postgres_db_conn') :
        g.postgres_db_conn = db[0]

    if not hasattr(g, 'postgres_db_cur') :
        g.postgres_db_cur = db[1]

    return g.postgres_db_cur

def init_db():
    db = connect_db()

    db[1].execute(open('schema.sql', 'r').read())
    db[1].close()

    db[0].close()

def init_admin():
    db = connect_db()

    db[1].execute('update users set admin=True where name=%s', ('Admin', ))

    db[1].close()
    db[0].close()