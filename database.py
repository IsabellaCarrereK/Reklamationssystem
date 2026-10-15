
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
                resolution TEXT,
                assessed_by_staff_id TEXT,
                assessed_at TEXT,
                closed_at TEXT,
                FOREIGN KEY (item_id)
                    REFERENCES receipt_items(item_id)
            )
        """)

        claim_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(claims)")
        }
        if "received_by" not in claim_columns:
            connection.execute("ALTER TABLE claims ADD COLUMN received_by TEXT")
        for column_name in (
            "decision",
            "resolution",
            "assessed_by_staff_id",
            "assessed_at",
        ):
            if column_name not in claim_columns:
                connection.execute(
                    f"ALTER TABLE claims ADD COLUMN {column_name} TEXT"
                )


def create_claim(item_id, customer_name, customer_phone, reason, description, received_by):
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO claims (
                item_id,
                customer_name,
                customer_phone,
                reason,
                description,
                status,
                received_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                customer_name,
                customer_phone,
                reason,
                description,
                "Registrerad",
                received_by,
            ),
        )
        return cursor.lastrowid


def update_claim_assessment(claim_id, decision, resolution, assessed_by_staff_id):
    with closing(get_connection()) as connection, connection:
        connection.execute(
            """
            UPDATE claims
            SET
                decision = ?,
                resolution = ?,
                assessed_by_staff_id = ?,
                assessed_at = CURRENT_TIMESTAMP
            WHERE claim_id = ?
            """,
            (decision, resolution, assessed_by_staff_id, claim_id),
        )


def get_all_claims():
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            SELECT
                claims.claim_id,
                claims.customer_name,
                claims.customer_phone,
                claims.reason,
                claims.description,
                claims.status,
                claims.received_by,
                claims.created_at,
                products.product_name,
                receipts.receipt_id,
                claims.decision,
                claims.resolution,
                claims.assessed_by_staff_id,
                claims.assessed_at
            FROM claims
            JOIN receipt_items
                ON claims.item_id = receipt_items.item_id
            JOIN products
                ON receipt_items.product_id = products.product_id
            JOIN receipts
                ON receipt_items.receipt_id = receipts.receipt_id
            ORDER BY claims.claim_id DESC
            """
        )
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_existing_claim_for_item(item_id):
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            SELECT claim_id, status, decision
            FROM claims
            WHERE item_id = ? AND status != ?
            ORDER BY claim_id DESC
            LIMIT 1
            """,
            (item_id, "Avslutad"),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
