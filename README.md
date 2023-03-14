Querysets for psycopg
=====================

This is a small wrapper of psycopg (3) to provide a queryset method.
Querysets are a way to chain queries in a more pythonic way. The API is inspired by Django and SQLAlchemy querysets.

This library deliberately focuses on raw SQL queries, and doesn't dream of becoming any kind of ORM. No model support is planned.

## Usage

```python
import psycopg
from psycopg_querysets import wrap_connection
with wrap_connection(psycopg.connect(DSN)) as conn:
    print(conn.queryset("SELECT * FROM users").filter("name = %s", ["John"]))
```

## Notes:

There are important TODOs in the code. This is a work in progress.
