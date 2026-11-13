"""C5-M01 SQL construction controls. Synthetic; never executed."""
import sqlite3


def unsafe_fstring(conn: sqlite3.Connection, name):
    # ruleid: morrow.py.sql-built-query
    return conn.execute(f"SELECT id FROM products WHERE name = '{name}'").fetchall()


def unsafe_percent(conn: sqlite3.Connection, category):
    # ruleid: morrow.py.sql-built-query
    return conn.execute("SELECT id FROM products WHERE category = '%s'" % category).fetchall()


def unsafe_variable(conn: sqlite3.Connection, order):
    sql = "SELECT id FROM products ORDER BY " + order
    # ruleid: morrow.py.sql-built-query
    return conn.execute(sql).fetchall()


def safe_bound(conn: sqlite3.Connection, name):
    # ok: morrow.py.sql-built-query
    return conn.execute("SELECT id FROM products WHERE name = ?", (name,)).fetchall()
