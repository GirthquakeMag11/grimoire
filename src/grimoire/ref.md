# SQLite3 Reference Sheet

## Python Connection Basics

```python
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Open a database (creates file if it doesn't exist)
conn: sqlite3.Connection = sqlite3.connect("app.db")

# In-memory database (lost when connection closes)
conn = sqlite3.connect(":memory:")

# Return rows as sqlite3.Row (dict-like access)
conn.row_factory = sqlite3.Row

# Cursor for executing statements
cur: sqlite3.Cursor = conn.cursor()

# Always close when done
conn.close()

# Preferred: use as context manager (auto-commits or rolls back)
with sqlite3.connect("app.db") as conn:
    conn.execute("SELECT 1")
```

### Reusable Connection Helper

```python
@contextmanager
def get_db(path: str | Path = "app.db") -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

---

## Pragmas (Configuration)

```sql
PRAGMA journal_mode=WAL;          -- write-ahead logging (better concurrency)
PRAGMA foreign_keys=ON;           -- enforce foreign key constraints (OFF by default!)
PRAGMA busy_timeout=5000;         -- wait 5s on lock instead of failing immediately
PRAGMA synchronous=NORMAL;        -- balance between safety and speed
PRAGMA cache_size=-64000;         -- 64MB cache (negative = kibibytes)
PRAGMA temp_store=MEMORY;         -- store temp tables in memory
PRAGMA mmap_size=268435456;       -- memory-map up to 256MB of the db file
PRAGMA optimize;                  -- run before closing long-lived connections
```

---

## Table Operations

### CREATE TABLE

```sql
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    email       TEXT    NOT NULL,
    age         INTEGER CHECK(age >= 0),
    balance     REAL    DEFAULT 0.0,
    is_active   INTEGER DEFAULT 1,             -- SQLite has no native BOOLEAN
    bio         TEXT,
    created_at  TEXT    DEFAULT (datetime('now')),
    updated_at  TEXT
);

-- Only create if it doesn't already exist
CREATE TABLE IF NOT EXISTS logs (
    id      INTEGER PRIMARY KEY,
    message TEXT NOT NULL,
    level   TEXT NOT NULL DEFAULT 'INFO'
);
```

### Column Type Affinities

| Affinity | Accepts                  | Use For                    |
|----------|--------------------------|----------------------------|
| INTEGER  | whole numbers            | ids, counts, booleans      |
| REAL     | floating-point           | prices, measurements       |
| TEXT     | strings                  | names, dates, JSON         |
| BLOB     | raw bytes                | files, images, binary data |
| NUMERIC  | any (coerces if possible)| mixed types                |

### Column Constraints

```sql
column_name TYPE
    PRIMARY KEY                        -- unique row identifier
    AUTOINCREMENT                      -- monotonically increasing (INTEGER only)
    NOT NULL                           -- disallow NULLs
    UNIQUE                             -- no duplicate values
    DEFAULT value                      -- fallback value
    DEFAULT (expression)               -- computed default
    CHECK(expression)                  -- validation rule
    REFERENCES other_table(column)     -- foreign key (inline syntax)
    COLLATE NOCASE                     -- case-insensitive comparisons
```

### Table Constraints

```sql
CREATE TABLE order_items (
    order_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity   INTEGER NOT NULL CHECK(quantity > 0),

    PRIMARY KEY (order_id, product_id),                          -- composite PK
    FOREIGN KEY (order_id)   REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    UNIQUE (order_id, product_id)
);
```

### Foreign Key Actions

```
ON DELETE CASCADE    -- delete child rows when parent is deleted
ON DELETE SET NULL   -- set FK column to NULL
ON DELETE SET DEFAULT
ON DELETE RESTRICT   -- block deletion if children exist (default)
ON UPDATE CASCADE    -- propagate parent PK changes to children
```

### ALTER TABLE

```sql
ALTER TABLE users RENAME TO members;
ALTER TABLE users RENAME COLUMN username TO handle;
ALTER TABLE users ADD COLUMN phone TEXT;
ALTER TABLE users DROP COLUMN bio;             -- SQLite 3.35.0+
```

### DROP TABLE

```sql
DROP TABLE users;
DROP TABLE IF EXISTS users;
```

---

## Indexes

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE INDEX idx_orders_multi ON orders(user_id, status);      -- composite
CREATE INDEX idx_users_email_nocase ON users(email COLLATE NOCASE);

-- Partial index (only indexes rows matching the WHERE)
CREATE INDEX idx_active_users ON users(username) WHERE is_active = 1;

-- Expression index
CREATE INDEX idx_users_lower_email ON users(lower(email));

DROP INDEX idx_users_email;
DROP INDEX IF EXISTS idx_users_email;
```

---

## INSERT

```sql
-- Single row
INSERT INTO users (username, email, age) VALUES ('alice', 'alice@example.com', 30);

-- Multiple rows
INSERT INTO users (username, email, age) VALUES
    ('bob',   'bob@example.com',   25),
    ('carol', 'carol@example.com', 28);

-- Insert or ignore (skip on conflict)
INSERT OR IGNORE INTO users (username, email) VALUES ('alice', 'alice@new.com');

-- Upsert (insert or update on conflict)
INSERT INTO users (username, email, age) VALUES ('alice', 'alice@new.com', 31)
    ON CONFLICT(username) DO UPDATE SET
        email = excluded.email,
        age   = excluded.age;

-- Insert from SELECT
INSERT INTO archive_users (username, email)
    SELECT username, email FROM users WHERE is_active = 0;

-- Insert with RETURNING (SQLite 3.35.0+)
INSERT INTO users (username, email) VALUES ('dave', 'dave@example.com')
    RETURNING id, created_at;
```

### Python Parameterized Inserts

```python
with get_db() as conn:
    # Single row — use ? placeholders
    conn.execute(
        "INSERT INTO users (username, email, age) VALUES (?, ?, ?)",
        ("alice", "alice@example.com", 30),
    )

    # Named placeholders
    conn.execute(
        "INSERT INTO users (username, email) VALUES (:name, :email)",
        {"name": "bob", "email": "bob@example.com"},
    )

    # Batch insert
    records: list[tuple[str, str, int]] = [
        ("carol", "carol@example.com", 28),
        ("dave",  "dave@example.com",  35),
    ]
    conn.executemany(
        "INSERT INTO users (username, email, age) VALUES (?, ?, ?)",
        records,
    )
```

---

## SELECT (Queries)

### Basic Queries

```sql
SELECT * FROM users;
SELECT username, email FROM users;
SELECT DISTINCT status FROM orders;
SELECT username AS name, email AS contact FROM users;
```

### WHERE Clauses

```sql
WHERE age = 30
WHERE age != 30                            -- or <>
WHERE age > 18 AND age < 65
WHERE age BETWEEN 18 AND 65               -- inclusive
WHERE age IN (25, 30, 35)
WHERE username LIKE 'a%'                   -- starts with 'a'
WHERE username LIKE '%son'                 -- ends with 'son'
WHERE username LIKE '_ob'                  -- 3 chars ending in 'ob'
WHERE email LIKE '%@gmail.com' ESCAPE '\'  -- custom escape char
WHERE username GLOB 'A*'                   -- case-sensitive, Unix-style globs
WHERE bio IS NULL
WHERE bio IS NOT NULL
WHERE username IN (SELECT username FROM admins)  -- subquery
```

### Ordering and Limiting

```sql
SELECT * FROM users ORDER BY age ASC;
SELECT * FROM users ORDER BY age DESC, username ASC;
SELECT * FROM users ORDER BY age LIMIT 10;
SELECT * FROM users ORDER BY age LIMIT 10 OFFSET 20;   -- pagination
```

### Aggregates

```sql
SELECT COUNT(*)           FROM users;
SELECT COUNT(DISTINCT age) FROM users;
SELECT AVG(age)           FROM users;
SELECT SUM(balance)       FROM users;
SELECT MIN(age), MAX(age) FROM users;
SELECT GROUP_CONCAT(username, ', ') FROM users;

-- Aggregate with GROUP BY
SELECT status, COUNT(*) AS cnt
FROM orders
GROUP BY status;

-- Filter groups with HAVING
SELECT status, COUNT(*) AS cnt
FROM orders
GROUP BY status
HAVING cnt > 5;
```

### Joins

```sql
-- Inner join
SELECT u.username, o.id AS order_id, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- Left join (all users, even without orders)
SELECT u.username, o.id
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;

-- Cross join (cartesian product)
SELECT * FROM colors CROSS JOIN sizes;

-- Self-join
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;

-- Multi-table
SELECT u.username, o.id, p.name
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;
```

### Subqueries

```sql
-- Scalar subquery
SELECT username, (SELECT COUNT(*) FROM orders WHERE orders.user_id = users.id) AS order_count
FROM users;

-- EXISTS
SELECT username FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- IN with subquery
SELECT * FROM products
WHERE id IN (SELECT product_id FROM order_items WHERE quantity > 10);
```

### Common Table Expressions (CTEs)

```sql
WITH active_users AS (
    SELECT id, username FROM users WHERE is_active = 1
)
SELECT au.username, COUNT(o.id) AS orders
FROM active_users au
LEFT JOIN orders o ON au.id = o.user_id
GROUP BY au.id;

-- Recursive CTE (e.g. tree traversal)
WITH RECURSIVE subordinates AS (
    SELECT id, name, manager_id FROM employees WHERE id = 1
    UNION ALL
    SELECT e.id, e.name, e.manager_id
    FROM employees e
    INNER JOIN subordinates s ON e.manager_id = s.id
)
SELECT * FROM subordinates;
```

### Window Functions (SQLite 3.25.0+)

```sql
SELECT
    username,
    age,
    ROW_NUMBER() OVER (ORDER BY age)                        AS row_num,
    RANK()       OVER (ORDER BY age)                        AS rank,
    DENSE_RANK() OVER (ORDER BY age)                        AS dense_rank,
    LAG(age)     OVER (ORDER BY age)                        AS prev_age,
    LEAD(age)    OVER (ORDER BY age)                        AS next_age,
    SUM(balance) OVER (ORDER BY created_at)                 AS running_total,
    AVG(age)     OVER (PARTITION BY is_active ORDER BY age) AS avg_age_by_group
FROM users;
```

### Python Query Patterns

```python
with get_db() as conn:
    # Fetch all rows as sqlite3.Row objects
    rows: list[sqlite3.Row] = conn.execute(
        "SELECT id, username, email FROM users WHERE age > ?", (18,)
    ).fetchall()

    for row in rows:
        print(row["username"], row["email"])   # dict-like access

    # Fetch single row
    row: sqlite3.Row | None = conn.execute(
        "SELECT * FROM users WHERE id = ?", (1,)
    ).fetchone()

    # Iterate without loading all into memory
    cur = conn.execute("SELECT * FROM users")
    for row in cur:
        process(row)

    # Scalar value
    count: int = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
```

---

## UPDATE

```sql
UPDATE users SET email = 'new@example.com' WHERE id = 1;
UPDATE users SET age = age + 1;                                -- all rows
UPDATE users SET balance = balance * 1.05 WHERE is_active = 1;
UPDATE users SET bio = NULL WHERE bio = '';

-- Update with RETURNING (SQLite 3.35.0+)
UPDATE users SET is_active = 0 WHERE age < 18 RETURNING id, username;

-- Update from another table (SQLite 3.33.0+)
UPDATE products SET price = s.new_price
FROM price_updates s
WHERE products.id = s.product_id;
```

---

## DELETE

```sql
DELETE FROM users WHERE id = 1;
DELETE FROM users WHERE is_active = 0 AND created_at < datetime('now', '-1 year');
DELETE FROM logs;                                -- delete all rows (keeps table)

-- Delete with RETURNING (SQLite 3.35.0+)
DELETE FROM sessions WHERE expires_at < datetime('now') RETURNING id, user_id;
```

---

## Transactions

```sql
BEGIN TRANSACTION;               -- or just BEGIN
    INSERT INTO accounts ...;
    UPDATE balances ...;
COMMIT;                          -- persist changes

-- Or abort
ROLLBACK;

-- Savepoints (nested transactions)
SAVEPOINT my_save;
    INSERT INTO ...;
RELEASE my_save;                 -- commit savepoint
-- or
ROLLBACK TO my_save;             -- undo back to savepoint
```

### Python Transaction Handling

```python
conn = sqlite3.connect("app.db")
try:
    conn.execute("BEGIN")
    conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = ?", (1,))
    conn.execute("UPDATE accounts SET balance = balance + 100 WHERE id = ?", (2,))
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

---

## Views

```sql
CREATE VIEW active_user_orders AS
    SELECT u.username, o.id AS order_id, o.total
    FROM users u
    JOIN orders o ON u.id = o.user_id
    WHERE u.is_active = 1;

-- Temporary view (session-scoped)
CREATE TEMP VIEW my_view AS SELECT ...;

-- Query it like a table
SELECT * FROM active_user_orders WHERE total > 50;

DROP VIEW active_user_orders;
DROP VIEW IF EXISTS active_user_orders;
```

---

## Date and Time Functions

SQLite stores dates as TEXT, REAL, or INTEGER — there is no native datetime type.

```sql
-- Current timestamps
datetime('now')                            -- '2026-04-17 12:00:00'
date('now')                                -- '2026-04-17'
time('now')                                -- '12:00:00'
strftime('%Y-%m-%d %H:%M:%S', 'now')       -- formatted

-- Modifiers
datetime('now', '+7 days')
datetime('now', '-1 month')
datetime('now', 'start of month')
datetime('now', 'start of year', '+6 months')
date('now', 'weekday 0')                   -- next Sunday

-- Extract components
strftime('%Y', created_at)                 -- year
strftime('%m', created_at)                 -- month
strftime('%W', created_at)                 -- week number

-- Unix timestamps
unixepoch()                                -- current unix timestamp (3.38.0+)
datetime(1681750000, 'unixepoch')          -- unix -> datetime
strftime('%s', '2026-04-17')               -- datetime -> unix
```

---

## String Functions

```sql
length('hello')                     -- 5
upper('hello')                      -- 'HELLO'
lower('HELLO')                      -- 'hello'
trim('  hello  ')                   -- 'hello'
ltrim('  hello')                    -- 'hello'
rtrim('hello  ')                    -- 'hello'
replace('hello', 'l', 'r')         -- 'herro'
substr('hello', 2, 3)              -- 'ell'  (1-indexed)
instr('hello', 'ell')              -- 2      (position, 0 if not found)
'hello' || ' ' || 'world'          -- concatenation
printf('%d items at $%.2f', 3, 9.5) -- '3 items at $9.50'
hex(X)                             -- hex encoding
quote(X)                           -- SQL-safe quoting
```

---

## Other Useful Functions

```sql
-- Conditional
COALESCE(bio, 'No bio')                         -- first non-NULL
NULLIF(value, 0)                                 -- returns NULL if value = 0
IIF(age >= 18, 'adult', 'minor')                 -- inline if (3.32.0+)
CASE status
    WHEN 'A' THEN 'Active'
    WHEN 'I' THEN 'Inactive'
    ELSE 'Unknown'
END

-- Type checking
typeof(column)                                   -- 'integer','real','text','blob','null'
CAST(value AS INTEGER)
CAST(value AS TEXT)

-- Math
abs(-5)                                          -- 5
max(a, b, c)                                     -- greatest value
min(a, b, c)                                     -- least value
random()                                         -- random integer
round(3.14159, 2)                                -- 3.14

-- JSON (SQLite 3.38.0+ has -> and ->> operators)
json('{"a":1}')                                  -- validate/normalize JSON
json_extract('{"a":{"b":2}}', '$.a.b')           -- 2
'{"a":1}' -> '$.a'                               -- JSON fragment
'{"a":1}' ->> '$.a'                              -- SQL value
json_array(1, 2, 3)                              -- '[1,2,3]'
json_object('key', 'value')                      -- '{"key":"value"}'
json_group_array(column)                         -- aggregate into JSON array
json_group_object(key_col, val_col)              -- aggregate into JSON object
json_each('{"a":1,"b":2}')                       -- table-valued: iterate pairs
```

---

## Schema Inspection

```sql
-- List all tables
SELECT name FROM sqlite_master WHERE type = 'table';

-- Table schema
SELECT sql FROM sqlite_master WHERE name = 'users';

-- Column info
PRAGMA table_info(users);          -- name, type, notnull, dflt_value, pk
PRAGMA table_xinfo(users);         -- extended (includes hidden/generated cols)

-- List indexes for a table
PRAGMA index_list(users);
PRAGMA index_info(idx_users_email);

-- Foreign keys for a table
PRAGMA foreign_key_list(orders);

-- Database stats
PRAGMA page_count;
PRAGMA page_size;
PRAGMA database_list;
```

---

## Full Python Example

```python
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class User:
    id: int
    username: str
    email: str
    age: int | None


@contextmanager
def get_db(path: str | Path = "app.db") -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            email    TEXT    NOT NULL,
            age      INTEGER CHECK(age >= 0)
        );
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """)


def insert_user(conn: sqlite3.Connection, username: str, email: str, age: int | None = None) -> int:
    cur: sqlite3.Cursor = conn.execute(
        "INSERT INTO users (username, email, age) VALUES (?, ?, ?) RETURNING id",
        (username, email, age),
    )
    row: sqlite3.Row = cur.fetchone()
    return int(row["id"])


def get_user(conn: sqlite3.Connection, user_id: int) -> User | None:
    row: sqlite3.Row | None = conn.execute(
        "SELECT id, username, email, age FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    return User(id=row["id"], username=row["username"], email=row["email"], age=row["age"])


def search_users(conn: sqlite3.Connection, *, min_age: int = 0, limit: int = 50) -> list[User]:
    rows: list[sqlite3.Row] = conn.execute(
        "SELECT id, username, email, age FROM users WHERE age >= ? ORDER BY username LIMIT ?",
        (min_age, limit),
    ).fetchall()
    return [User(id=r["id"], username=r["username"], email=r["email"], age=r["age"]) for r in rows]


def delete_user(conn: sqlite3.Connection, user_id: int) -> bool:
    cur: sqlite3.Cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return cur.rowcount > 0


if __name__ == "__main__":
    with get_db() as conn:
        init_db(conn)
        uid: int = insert_user(conn, "alice", "alice@example.com", 30)
        user: User | None = get_user(conn, uid)
        print(user)
```
