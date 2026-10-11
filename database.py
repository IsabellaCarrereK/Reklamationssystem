
from contextlib import closing
from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).parent / "reklamationssystem.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_receipt_items(receipt_id):
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            SELECT
                receipts.receipt_id,
                receipts.purchase_date,
                receipt_items.item_id,
                products.product_name,
                products.brand,
                receipt_items.purchase_price,
                receipt_items.quantity
            FROM receipts
            JOIN receipt_items
                ON receipts.receipt_id = receipt_items.receipt_id
            JOIN products
                ON receipt_items.product_id = products.product_id
            WHERE receipts.receipt_id = ?
            """,
            (receipt_id,),
        )
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def create_tables():
    with closing(get_connection()) as connection, connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                receipt_id TEXT PRIMARY KEY,
                purchase_date TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                brand TEXT
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS receipt_items (
                item_id INTEGER PRIMARY KEY,
                receipt_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                purchase_price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (receipt_id)
                    REFERENCES receipts(receipt_id),
                FOREIGN KEY (product_id)
                    REFERENCES products(product_id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                reason TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Registrerad',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                decision TEXT,
                closed_at TEXT,
                FOREIGN KEY (item_id)
                    REFERENCES receipt_items(item_id)
            )
        """)
