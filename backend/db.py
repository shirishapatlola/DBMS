import os
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


def get_db_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "restaurant_db"),
        "charset": "utf8mb4",
        "autocommit": False,
        "raise_on_warnings": True,
    }


def get_connection():
    return mysql.connector.connect(**get_db_config())


def fetch_all(query: str, params: Optional[tuple] = None, db_name: Optional[str] = None):
    conn = get_connection()
    if db_name:
        conn.database = db_name
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()
        conn.close()


def fetch_one(query: str, params: Optional[tuple] = None, db_name: Optional[str] = None):
    conn = get_connection()
    if db_name:
        conn.database = db_name
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute_write(query: str, params: Optional[tuple] = None, db_name: Optional[str] = None):
    conn = get_connection()
    if db_name:
        conn.database = db_name
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def execute_transaction(statements):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        for query, params in statements:
            cursor.execute(query, params or ())
        conn.commit()
        return True
    except Error as exc:
        conn.rollback()
        raise exc
    finally:
        cursor.close()
        conn.close()
