# Customer Shopping Behavior Analytics

How do product preferences and subscription rates vary across this retail dataset? The [source CSV](data/customer_shopping_behavior.csv) contains 3,900 purchase records and 3,900 distinct, non-missing customer IDs. Each row describes one observed purchase and reports the customer's previous purchase count. The file provides a snapshot, without a dated transaction history for each customer.

## Findings from MySQL

| Question | Result |
| --- | --- |
| Q7 · Purchase history | 83 records are New (0–1 previous purchases), 701 Returning (2–10) and 3,116 Loyal (11+). Missing or negative counts are Unknown. None occur in this file. These labels describe purchase frequency. |
| Q8 · Most purchased products | Accessories: Jewelry (171), Belt (161), Sunglasses (161). Clothing: Blouse (171), Pants (171), Shirt (169). Footwear: Sandals (160), Shoes (150), Sneakers (145). Outerwear has just two products: Jacket (163) and Coat (161). |
| Q9 · Subscription by purchase history | Among repeat buyers (>5 previous purchases), 958 of 3,476 subscribed (27.56%). Among buyers with 0–5 previous purchases, 95 of 424 subscribed (22.41%). This 5.15 percentage-point difference describes the sample and does not establish causation. |

Q8 sorts by purchase count descending, then product name ascending. Each category contributes up to three products, including when counts tie. Q9 divides Yes responses by all known Yes/No responses **within the same purchase-history group**. The query reports unknown subscription counts separately and returns NULL for a group with no known responses. Q7 and Q9 use different thresholds to answer different questions.

## Follow the analysis

1. Inspect the [pandas notebook](notebooks/customer_shopping_behavior_analysis.ipynb). It fills 37 missing review ratings with category medians, standardises column names, derives age quartiles and purchase-frequency intervals, and drops the redundant promo-code flag. It loads the resulting table into MySQL through SQLAlchemy and PyMySQL.
2. Read the [ten SQL queries](sql/customer_behavior_sql_queries.sql) for revenue, discounts, ratings, shipping, subscriptions, segments and rankings. The [regression script](tests/validate_sql.py) compares Q7–Q9 against an independent calculation from the CSV, then exercises missing values, boundary counts, tied products and empty denominators.
3. Inspect the existing [Power BI file](powerbi/customer_behavior_dashboard.pbix), [analysis report](reports/Customer%20Shopping%20Behavior%20Analysis.pdf), [business brief](reports/Business%20Problem%20%20Document.pdf) and [slides](presentation/Customer-Shopping-Behavior-Analysis.pptx). These are earlier deliverables. The MySQL results above were verified separately. The dashboard and presentation were not refreshed or revalidated against the revised queries.

## Reproduce locally

Use Python, Jupyter and MySQL 8. Create a disposable database named `mydatabase` and grant your local account permission to create and replace tables and create temporary tables there. The notebook **replaces `mytable`**. From the repository root, run:

```bash
python -m pip install -r requirements.txt
export CUSTOMER_DB_USER=your_local_user
read -rsp "Local MySQL password: " CUSTOMER_DB_PASSWORD
export CUSTOMER_DB_PASSWORD
jupyter notebook notebooks/customer_shopping_behavior_analysis.ipynb
```

Run the notebook from top to bottom. The connection defaults to 127.0.0.1, port 3306 and database `mydatabase`. Override these with `CUSTOMER_DB_HOST`, `CUSTOMER_DB_PORT` and `CUSTOMER_DB_NAME` if needed. From the same environment, run:

```bash
mysql -h "${CUSTOMER_DB_HOST:-127.0.0.1}" -P "${CUSTOMER_DB_PORT:-3306}" -u "$CUSTOMER_DB_USER" -p "${CUSTOMER_DB_NAME:-mydatabase}" < sql/customer_behavior_sql_queries.sql
python tests/validate_sql.py
```

The notebook load, all ten questions and both sets of Q7–Q9 checks were exercised on MySQL Community Server 8.0.46. The tests use a session-local temporary table for edge cases. The sample supports descriptive comparisons. It provides no evidence of measured business uplift or changes over time.
