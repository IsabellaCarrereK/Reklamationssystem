
from contextlib import closing

from database import create_tables, get_connection


def seed_database():
    create_tables()

    receipts = [
        ("KV-1001", "2026-06-15"),
        ("KV-1002", "2026-09-20"),
        ("KV-1003", "2025-11-12"),
        ("KV-1004", "2026-10-01"),
        ("KV-1005", "2025-03-10"),
        ("KV-1006", "2026-08-05"),
        ("KV-1007", "2024-12-18"),
        ("KV-1008", "2026-07-22"),
    ]

    products = [
        (1, "Handväska Modell A", "Nordic Bags"),
        (2, "Sneakers", "Urban Steps"),
        (3, "Vinterjacka", "Nord Wear"),
        (4, "Ansiktskräm", "Skin Lab"),
        (5, "Plånbok", "Nordic Bags"),
        (6, "Klänning", "Studio Collection"),
        (7, "Kängor", "Urban Steps"),
        (8, "Solglasögon", "Sun Studio"),
        (9, "Halsduk", "Nord Wear"),
        (10, "Handkräm", "Skin Lab"),
    ]

    receipt_items = [
        ("KV-1001", 1, 1299.00, 1),
        ("KV-1001", 5, 399.00, 1),
        ("KV-1002", 2, 899.00, 1),
        ("KV-1003", 3, 1799.00, 1),
        ("KV-1003", 9, 299.00, 1),
        ("KV-1004", 4, 349.00, 1),
        ("KV-1004", 10, 129.00, 1),
        ("KV-1005", 5, 449.00, 1),
        ("KV-1006", 6, 999.00, 1),
        ("KV-1007", 7, 1499.00, 1),
        ("KV-1008", 8, 699.00, 1),
    ]

    with closing(get_connection()) as connection, connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO receipts
            (receipt_id, purchase_date)
            VALUES (?, ?)
            """,
            receipts,
        )

        connection.executemany(
            """
            INSERT OR IGNORE INTO products
            (product_id, product_name, brand)
            VALUES (?, ?, ?)
            """,
            products,
        )

        connection.executemany(
            """
            INSERT INTO receipt_items
            (receipt_id, product_id, purchase_price, quantity)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM receipt_items
                WHERE receipt_id = ?
                AND product_id = ?
            )
            """,
            [
                (receipt_id, product_id, price, quantity,
                 receipt_id, product_id)
                for receipt_id, product_id, price, quantity
                in receipt_items
            ],
        )

    print("Testdata har lagts in!")


if __name__ == "__main__":
    seed_database()
