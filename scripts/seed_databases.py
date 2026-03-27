"""
Seed all local development databases with sample tables and data.

Usage:
    python scripts/seed_databases.py
"""
import sqlite3
import sys

# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------

def seed_postgres():
    try:
        import psycopg2
    except ImportError:
        print("[postgres] SKIP — psycopg2 not installed")
        return

    dsn = "postgresql://testuser:testpass@localhost:5432/testdb"
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS order_items CASCADE")
        cur.execute("DROP TABLE IF EXISTS orders CASCADE")
        cur.execute("DROP TABLE IF EXISTS products CASCADE")
        cur.execute("DROP TABLE IF EXISTS customers CASCADE")

        cur.execute("""
            CREATE TABLE customers (
                id          SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                country     TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE products (
                id          SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                category    TEXT NOT NULL,
                price       NUMERIC(10,2) NOT NULL,
                stock       INTEGER NOT NULL DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE orders (
                id          SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                status      TEXT NOT NULL DEFAULT 'pending',
                total       NUMERIC(10,2) NOT NULL,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE order_items (
                id          SERIAL PRIMARY KEY,
                order_id    INTEGER NOT NULL REFERENCES orders(id),
                product_id  INTEGER NOT NULL REFERENCES products(id),
                quantity    INTEGER NOT NULL,
                unit_price  NUMERIC(10,2) NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO customers (name, email, country) VALUES
            ('Alice Ferreira',  'alice@example.com',   'Brazil'),
            ('Bob Smith',       'bob@example.com',     'USA'),
            ('Carlos Ruiz',     'carlos@example.com',  'Mexico'),
            ('Diana Chen',      'diana@example.com',   'China'),
            ('Eve Dupont',      'eve@example.com',     'France')
        """)
        cur.execute("""
            INSERT INTO products (name, category, price, stock) VALUES
            ('Laptop Pro 15',   'Electronics',  1299.99, 50),
            ('Wireless Mouse',  'Electronics',    29.99, 200),
            ('Desk Chair',      'Furniture',     349.00, 30),
            ('Python Book',     'Books',          49.90, 100),
            ('Coffee Maker',    'Appliances',     89.99, 75)
        """)
        cur.execute("""
            INSERT INTO orders (customer_id, status, total) VALUES
            (1, 'completed', 1329.98),
            (2, 'pending',     49.90),
            (3, 'completed',   439.00),
            (4, 'shipped',   1299.99),
            (5, 'completed',   119.98)
        """)
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
            (1, 1, 1, 1299.99),
            (1, 2, 1,   29.99),
            (2, 4, 1,   49.90),
            (3, 3, 1,  349.00),
            (3, 2, 1,   29.99),
            (4, 1, 1, 1299.99),
            (5, 5, 1,   89.99),
            (5, 2, 1,   29.99)
        """)

        cur.close()
        conn.close()
        print("[postgres] OK — customers, products, orders, order_items seeded")
    except Exception as e:
        print(f"[postgres] ERROR — {e}")


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------

def seed_mysql():
    try:
        import mysql.connector
    except ImportError:
        print("[mysql] SKIP — mysql-connector-python not installed")
        return

    try:
        conn = mysql.connector.connect(
            host="localhost", port=3306,
            user="testuser", password="testpass",
            database="testdb", autocommit=True,
        )
        cur = conn.cursor()

        for t in ("order_items", "orders", "products", "customers"):
            cur.execute(f"DROP TABLE IF EXISTS {t}")

        cur.execute("""
            CREATE TABLE customers (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(255) NOT NULL,
                email       VARCHAR(255) UNIQUE NOT NULL,
                country     VARCHAR(100) NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE products (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(255) NOT NULL,
                category    VARCHAR(100) NOT NULL,
                price       DECIMAL(10,2) NOT NULL,
                stock       INT NOT NULL DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE orders (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT NOT NULL,
                status      VARCHAR(50) NOT NULL DEFAULT 'pending',
                total       DECIMAL(10,2) NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)
        cur.execute("""
            CREATE TABLE order_items (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                order_id    INT NOT NULL,
                product_id  INT NOT NULL,
                quantity    INT NOT NULL,
                unit_price  DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id)   REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        cur.executemany(
            "INSERT INTO customers (name, email, country) VALUES (%s, %s, %s)",
            [
                ('Alice Ferreira', 'alice@example.com',  'Brazil'),
                ('Bob Smith',      'bob@example.com',    'USA'),
                ('Carlos Ruiz',    'carlos@example.com', 'Mexico'),
                ('Diana Chen',     'diana@example.com',  'China'),
                ('Eve Dupont',     'eve@example.com',    'France'),
            ]
        )
        cur.executemany(
            "INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)",
            [
                ('Laptop Pro 15',  'Electronics', 1299.99, 50),
                ('Wireless Mouse', 'Electronics',   29.99, 200),
                ('Desk Chair',     'Furniture',    349.00, 30),
                ('Python Book',    'Books',          49.90, 100),
                ('Coffee Maker',   'Appliances',    89.99, 75),
            ]
        )
        cur.executemany(
            "INSERT INTO orders (customer_id, status, total) VALUES (%s, %s, %s)",
            [
                (1, 'completed', 1329.98),
                (2, 'pending',     49.90),
                (3, 'completed',   439.00),
                (4, 'shipped',   1299.99),
                (5, 'completed',   119.98),
            ]
        )
        cur.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
            [
                (1, 1, 1, 1299.99),
                (1, 2, 1,   29.99),
                (2, 4, 1,   49.90),
                (3, 3, 1,  349.00),
                (3, 2, 1,   29.99),
                (4, 1, 1, 1299.99),
                (5, 5, 1,   89.99),
                (5, 2, 1,   29.99),
            ]
        )

        cur.close()
        conn.close()
        print("[mysql]   OK — customers, products, orders, order_items seeded")
    except Exception as e:
        print(f"[mysql]   ERROR — {e}")


# ---------------------------------------------------------------------------
# MSSQL
# ---------------------------------------------------------------------------

def seed_mssql():
    try:
        import pyodbc
    except ImportError:
        print("[mssql]   SKIP — pyodbc not installed")
        return

    dsn = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost,1434;"
        "Database=master;"
        "UID=sa;"
        "PWD=TestPass123!;"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
    )
    try:
        conn = pyodbc.connect(dsn, autocommit=True)
        cur = conn.cursor()

        # Create a dedicated database
        cur.execute("IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'testdb') CREATE DATABASE testdb")
        conn.close()

        dsn_testdb = dsn.replace("Database=master;", "Database=testdb;")
        conn = pyodbc.connect(dsn_testdb, autocommit=True)
        cur = conn.cursor()

        for t in ("order_items", "orders", "products", "customers"):
            cur.execute(f"IF OBJECT_ID('{t}', 'U') IS NOT NULL DROP TABLE {t}")

        cur.execute("""
            CREATE TABLE customers (
                id          INT IDENTITY(1,1) PRIMARY KEY,
                name        NVARCHAR(255) NOT NULL,
                email       NVARCHAR(255) NOT NULL UNIQUE,
                country     NVARCHAR(100) NOT NULL,
                created_at  DATETIME2 DEFAULT GETDATE()
            )
        """)
        cur.execute("""
            CREATE TABLE products (
                id          INT IDENTITY(1,1) PRIMARY KEY,
                name        NVARCHAR(255) NOT NULL,
                category    NVARCHAR(100) NOT NULL,
                price       DECIMAL(10,2) NOT NULL,
                stock       INT NOT NULL DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE orders (
                id          INT IDENTITY(1,1) PRIMARY KEY,
                customer_id INT NOT NULL REFERENCES customers(id),
                status      NVARCHAR(50) NOT NULL DEFAULT 'pending',
                total       DECIMAL(10,2) NOT NULL,
                created_at  DATETIME2 DEFAULT GETDATE()
            )
        """)
        cur.execute("""
            CREATE TABLE order_items (
                id          INT IDENTITY(1,1) PRIMARY KEY,
                order_id    INT NOT NULL REFERENCES orders(id),
                product_id  INT NOT NULL REFERENCES products(id),
                quantity    INT NOT NULL,
                unit_price  DECIMAL(10,2) NOT NULL
            )
        """)

        cur.executemany(
            "INSERT INTO customers (name, email, country) VALUES (?, ?, ?)",
            [
                ('Alice Ferreira', 'alice@example.com',  'Brazil'),
                ('Bob Smith',      'bob@example.com',    'USA'),
                ('Carlos Ruiz',    'carlos@example.com', 'Mexico'),
                ('Diana Chen',     'diana@example.com',  'China'),
                ('Eve Dupont',     'eve@example.com',    'France'),
            ]
        )
        cur.executemany(
            "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
            [
                ('Laptop Pro 15',  'Electronics', 1299.99, 50),
                ('Wireless Mouse', 'Electronics',   29.99, 200),
                ('Desk Chair',     'Furniture',    349.00, 30),
                ('Python Book',    'Books',          49.90, 100),
                ('Coffee Maker',   'Appliances',    89.99, 75),
            ]
        )
        cur.executemany(
            "INSERT INTO orders (customer_id, status, total) VALUES (?, ?, ?)",
            [
                (1, 'completed', 1329.98),
                (2, 'pending',     49.90),
                (3, 'completed',   439.00),
                (4, 'shipped',   1299.99),
                (5, 'completed',   119.98),
            ]
        )
        cur.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            [
                (1, 1, 1, 1299.99),
                (1, 2, 1,   29.99),
                (2, 4, 1,   49.90),
                (3, 3, 1,  349.00),
                (3, 2, 1,   29.99),
                (4, 1, 1, 1299.99),
                (5, 5, 1,   89.99),
                (5, 2, 1,   29.99),
            ]
        )

        cur.close()
        conn.close()
        print("[mssql]   OK — testdb created; customers, products, orders, order_items seeded")
    except Exception as e:
        print(f"[mssql]   ERROR — {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Seeding databases...")
    seed_postgres()
    seed_mysql()
    seed_mssql()
    print("Done.")
