# SQLite for metric storage

We store sealed-month data in SQLite files. The schema is simple (three tables: `prs`, `reviews`, `sealed_months`) and accessed via raw SQL with `executemany`. No ORM.

SQLite was chosen for zero-setup: no server, no config, ships with Python. The schema is deliberately flat — the data shape matches GitHub's API response shape. We can evaluate other stores (Postgres, Parquet files) in the future if the project outgrows SQLite.
