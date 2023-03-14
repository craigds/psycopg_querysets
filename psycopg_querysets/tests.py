import os

import psycopg
import pytest

from psycopg_querysets import wrap_connection


@pytest.fixture(scope="session", autouse=True)
def conn():
    dsn = os.environ.get("POSTGRES_DSN")
    if dsn is None:
        pytest.fail("POSTGRES_DSN not set")
    with wrap_connection(psycopg.connect(dsn)) as c:
        yield c


def test_wrap_conn(conn):
    assert hasattr(conn, "queryset")


def test_simple_queryset_no_params(conn):
    qs = conn.queryset("select 1")
    assert qs._to_string() == "select 1"


def test_simple_queryset_params(conn):
    qs = conn.queryset("select %s, %s", ["mystring", 3])
    assert qs._to_string() == "select 'mystring', 3"


def test_queryset_filter_without_existing_where(conn):
    qs = conn.queryset("select %s FROM def", ["abc"])
    qs = qs.filter("ghi = %s", ["jkl"])

    assert qs._to_string() == "select 'abc' FROM def WHERE ghi = 'jkl'"


def test_queryset_filter_with_existing_where(conn):
    qs = conn.queryset("select %s FROM def WHERE ghi = true", ["abc"])
    qs = qs.filter("mno = %s", ["pqr"])

    assert qs._to_string() == "select 'abc' FROM def WHERE ghi = true AND mno = 'pqr'"


def test_chained_filters(conn):
    qs = (
        conn.queryset("select %s FROM def", ["abc"])
        .filter("ghi = %s", ["jkl"])
        .filter("mno = %s", ["pqr"])
    )
    assert qs._to_string() == "select 'abc' FROM def WHERE ghi = 'jkl' AND mno = 'pqr'"
