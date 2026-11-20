"""Run on the notebook-loaded MySQL 8 database; fixtures are session-local."""
import csv
import os
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pymysql

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "sql/customer_behavior_sql_queries.sql").read_text()
QUESTIONS = re.split(r"^-- Q\d+\.[^\n]*\n", SQL, flags=re.M)[1:]


def check(cursor, number, expected):
    cursor.execute(QUESTIONS[number - 1])
    actual = list(cursor.fetchall())
    if actual != expected:
        raise AssertionError(f"Q{number}: {actual!r} != {expected!r}")
    print(f"Q{number} passed: {actual}")


def reference_checks(cursor):
    with (ROOT / "data/customer_shopping_behavior.csv").open(newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    ids = {r["Customer ID"] for r in rows}
    assert "" not in ids and len(ids) == len(rows) == 3900
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT customer_id) FROM mytable")
    assert cursor.fetchone() == (len(rows), len(ids))
    segments, products, groups = Counter(), defaultdict(Counter), defaultdict(list)
    for row in rows:
        prior = int(row["Previous Purchases"])
        segment = "New" if prior in (0, 1) else "Returning" if prior in range(2, 11) else "Loyal"
        segments[segment] += 1
        products[row["Category"]][row["Item Purchased"]] += 1
        groups["Repeat" if prior > 5 else "Non-repeat"].append(row["Subscription Status"])
    check(cursor, 7, sorted(segments.items()))
    ranks = []
    for category, items in sorted(products.items()):
        top = sorted(items.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
        ranks.extend((i, category, item, count) for i, (item, count) in enumerate(top, 1))
    check(cursor, 8, ranks)
    expected = []
    for group, statuses in sorted(groups.items()):
        yes = statuses.count("Yes")
        known = yes + statuses.count("No")
        pct = (Decimal(100 * yes) / known).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
        expected.append((group, len(statuses), yes, known, len(statuses) - known, pct))
    check(cursor, 9, expected)


def fixture_checks(cursor):
    cursor.execute("""CREATE TEMPORARY TABLE mytable (
        previous_purchases INT, subscription_status VARCHAR(12),
        category VARCHAR(12), item_purchased VARCHAR(12))""")
    rows = [(0, "Yes", "A"), (1, "No", "B"), (2, None, "C"), (5, "Other", "D"),
            (6, "No", "D"), (10, "Yes", "C"), (11, "Yes", "B"), (None, None, "A"),
            (-1, "Other", "E")]
    cursor.executemany("INSERT INTO mytable VALUES (%s, %s, 'Test', %s)", rows)
    check(cursor, 7, [("Loyal", 1), ("New", 2), ("Returning", 4), ("Unknown", 2)])
    check(cursor, 8, [(1, "Test", "A", 2), (2, "Test", "B", 2), (3, "Test", "C", 2)])
    check(cursor, 9, [("Non-repeat", 4, 1, 2, 2, Decimal("50.00")),
                      ("Repeat", 3, 2, 3, 0, Decimal("66.67")),
                      ("Unknown", 2, 0, 0, 2, None)])


if __name__ == "__main__":
    with pymysql.connect(host=os.getenv("CUSTOMER_DB_HOST", "127.0.0.1"),
                         port=int(os.getenv("CUSTOMER_DB_PORT", "3306")),
                         user=os.getenv("CUSTOMER_DB_USER", "root"),
                         password=os.environ["CUSTOMER_DB_PASSWORD"],
                         database=os.getenv("CUSTOMER_DB_NAME", "mydatabase")) as connection:
        with connection.cursor() as cur:
            assert len(QUESTIONS) == 10
            for query in QUESTIONS:
                cur.execute(query)
                cur.fetchall()
            print("All ten analysis queries executed")
            reference_checks(cur)
            fixture_checks(cur)
