Querysets for psycopg
=====================

This is a small wrapper of psycopg (3) to provide a queryset method.
Querysets are a way to chain queries in a more pythonic way. The API is inspired by Django and SQLAlchemy querysets.

This library deliberately focuses on raw SQL queries, and doesn't dream of becoming any kind of ORM. No model support is planned.

## Notes:

I didn't end up using this project, and probably won't develop it further.
I'm leaving it here in case it's useful to someone else. It will probably need further development to be useful. 

Good luck!

## Usage

```python
import psycopg
from psycopg_querysets import wrap_connection
with wrap_connection(psycopg.connect(DSN)) as conn:
    print(conn.queryset("SELECT * FROM users").filter("name = %s", ["John"]))
```
