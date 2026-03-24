"""Seed DuckDB with synthetic e-commerce data.

Run with: python -m app.db.seed
"""

from __future__ import annotations

import random
from datetime import date, timedelta

import duckdb
from faker import Faker

from app.config import settings

SEED = 42
fake = Faker()
Faker.seed(SEED)
random.seed(SEED)

REGIONS = ["Northeast", "Southeast", "Midwest", "West", "Southwest"]
CHANNELS = ["organic", "paid_search", "social", "email", "referral", "direct"]
SEGMENTS = ["premium", "standard", "basic"]
CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Sports", "Books", "Beauty"]
SUBCATEGORIES = {
    "Electronics": ["Phones", "Laptops", "Tablets", "Headphones", "Cameras"],
    "Clothing": ["Shirts", "Pants", "Dresses", "Shoes", "Accessories"],
    "Home & Kitchen": ["Appliances", "Furniture", "Cookware", "Decor", "Storage"],
    "Sports": ["Fitness", "Outdoor", "Team Sports", "Cycling", "Swimming"],
    "Books": ["Fiction", "Non-Fiction", "Technical", "Self-Help", "Children"],
    "Beauty": ["Skincare", "Makeup", "Haircare", "Fragrance", "Tools"],
}
ORDER_STATUSES = ["completed", "pending", "cancelled", "refunded"]
DEVICES = ["desktop", "mobile", "tablet"]
DATE_START = date(2024, 1, 1)
DATE_END = date(2025, 12, 31)
DATE_RANGE_DAYS = (DATE_END - DATE_START).days

NUM_CUSTOMERS = 2000
NUM_PRODUCTS = 500
NUM_ORDERS = 15000
NUM_ORDER_ITEMS = 30000
NUM_SESSIONS = 20000
NUM_MARKETING_SPEND = 1000


def _random_date() -> date:
    return DATE_START + timedelta(days=random.randint(0, DATE_RANGE_DAYS))


DDL = """
CREATE OR REPLACE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    name          VARCHAR NOT NULL,
    email         VARCHAR NOT NULL,
    segment       VARCHAR NOT NULL,
    region        VARCHAR NOT NULL,
    created_at    DATE NOT NULL
);

CREATE OR REPLACE TABLE products (
    product_id    INTEGER PRIMARY KEY,
    name          VARCHAR NOT NULL,
    category      VARCHAR NOT NULL,
    subcategory   VARCHAR NOT NULL,
    price         DOUBLE NOT NULL,
    cost          DOUBLE NOT NULL
);

CREATE OR REPLACE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date    DATE NOT NULL,
    status        VARCHAR NOT NULL,
    channel       VARCHAR NOT NULL
);

CREATE OR REPLACE TABLE order_items (
    item_id       INTEGER PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id),
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL,
    unit_price    DOUBLE NOT NULL,
    discount      DOUBLE NOT NULL
);

CREATE OR REPLACE TABLE sessions (
    session_id    INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    session_date  DATE NOT NULL,
    device        VARCHAR NOT NULL,
    source        VARCHAR NOT NULL,
    pages_viewed  INTEGER NOT NULL,
    converted     BOOLEAN NOT NULL
);

CREATE OR REPLACE TABLE marketing_spend (
    spend_id      INTEGER PRIMARY KEY,
    channel       VARCHAR NOT NULL,
    spend_date    DATE NOT NULL,
    amount        DOUBLE NOT NULL,
    impressions   INTEGER NOT NULL,
    clicks        INTEGER NOT NULL
);
"""


def _generate_customers() -> list[tuple]:
    rows = []
    for i in range(1, NUM_CUSTOMERS + 1):
        rows.append((
            i,
            fake.name(),
            fake.email(),
            random.choice(SEGMENTS),
            random.choice(REGIONS),
            _random_date(),
        ))
    return rows


def _generate_products() -> list[tuple]:
    rows = []
    for i in range(1, NUM_PRODUCTS + 1):
        category = random.choice(CATEGORIES)
        subcategory = random.choice(SUBCATEGORIES[category])
        price = round(random.uniform(5.0, 500.0), 2)
        cost = round(price * random.uniform(0.3, 0.7), 2)
        rows.append((
            i,
            f"{fake.word().title()} {subcategory} {fake.word().title()}",
            category,
            subcategory,
            price,
            cost,
        ))
    return rows


def _generate_orders() -> list[tuple]:
    rows = []
    status_weights = [0.70, 0.12, 0.10, 0.08]
    for i in range(1, NUM_ORDERS + 1):
        rows.append((
            i,
            random.randint(1, NUM_CUSTOMERS),
            _random_date(),
            random.choices(ORDER_STATUSES, weights=status_weights, k=1)[0],
            random.choice(CHANNELS),
        ))
    return rows


def _generate_order_items(products: list[tuple]) -> list[tuple]:
    product_prices = {p[0]: p[4] for p in products}
    rows = []
    for i in range(1, NUM_ORDER_ITEMS + 1):
        product_id = random.randint(1, NUM_PRODUCTS)
        base_price = product_prices[product_id]
        quantity = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3], k=1)[0]
        discount = round(base_price * random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20]), 2)
        rows.append((
            i,
            random.randint(1, NUM_ORDERS),
            product_id,
            quantity,
            base_price,
            discount,
        ))
    return rows


def _generate_sessions() -> list[tuple]:
    rows = []
    for i in range(1, NUM_SESSIONS + 1):
        rows.append((
            i,
            random.randint(1, NUM_CUSTOMERS),
            _random_date(),
            random.choice(DEVICES),
            random.choice(CHANNELS),
            random.randint(1, 30),
            random.random() < 0.12,
        ))
    return rows


def _generate_marketing_spend() -> list[tuple]:
    rows = []
    for i in range(1, NUM_MARKETING_SPEND + 1):
        impressions = random.randint(1000, 100000)
        ctr = random.uniform(0.005, 0.08)
        rows.append((
            i,
            random.choice(CHANNELS),
            _random_date(),
            round(random.uniform(50.0, 5000.0), 2),
            impressions,
            int(impressions * ctr),
        ))
    return rows


def seed(db_path: str | None = None) -> None:
    path = db_path or str(settings.duckdb_abs_path)
    settings.duckdb_abs_path.parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(path)

    conn.execute("BEGIN TRANSACTION")
    try:
        conn.execute(DDL)

        customers = _generate_customers()
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers)

        products = _generate_products()
        conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)", products)

        orders = _generate_orders()
        conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)

        order_items = _generate_order_items(products)
        conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)", order_items)

        sessions = _generate_sessions()
        conn.executemany("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)", sessions)

        marketing = _generate_marketing_spend()
        conn.executemany("INSERT INTO marketing_spend VALUES (?, ?, ?, ?, ?, ?)", marketing)

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()

    print(f"Seeded {path}:")
    print(f"  customers:       {NUM_CUSTOMERS:,}")
    print(f"  products:        {NUM_PRODUCTS:,}")
    print(f"  orders:          {NUM_ORDERS:,}")
    print(f"  order_items:     {NUM_ORDER_ITEMS:,}")
    print(f"  sessions:        {NUM_SESSIONS:,}")
    print(f"  marketing_spend: {NUM_MARKETING_SPEND:,}")


if __name__ == "__main__":
    seed()
