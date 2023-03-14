from copy import deepcopy
from functools import lru_cache
import sqlparse
from psycopg.sql import SQL, Composable, Composed, quote


ParamsType = list | dict | None


class Queryset:
    def __init__(self, connection, sql: Composable, params: ParamsType = None):
        self.connection = connection
        self.sql = sql
        self.params = params

    @property
    @lru_cache(maxsize=1)
    def _parsed(self):
        sql = self._to_string()
        parsed = sqlparse.parse(sql)
        if len(parsed) != 1:
            raise ValueError("SQL must be a single statement")
        return parsed[0]

    def _to_string(self) -> str:
        """
        Returns the SQL string for this queryset, interpolated similarly to how the database would.
        Used for testing.
        """
        sql = self.sql.as_string(self.connection)
        if self.params is not None:
            if isinstance(self.params, dict):
                quoted_params = {
                    k: quote(v, self.connection) for k, v in self.params.items()
                }
            elif isinstance(self.params, (tuple, list)):
                quoted_params = tuple(quote(v, self.connection) for v in self.params)
            else:
                raise TypeError("params must be a dict, tuple or list")
            sql %= quoted_params
        return sql

    def _combine_params(self, new_params: ParamsType) -> ParamsType:
        """
        Returns a new set of parameters by merging new parameters with the old ones.
        """
        # TODO: avoid copying if possible (if params are immutable?)
        if new_params is None:
            return deepcopy(self.params)
        if self.params is None:
            return deepcopy(new_params)

        if isinstance(self.params, dict) and not isinstance(new_params, dict):
            raise TypeError("Cannot combine dict params with non-dict params")

        if isinstance(self.params, dict):
            return {**self.params, **new_params}
        else:
            return (*self.params, *new_params)

    def filter(self, sql, params: ParamsType = None) -> "Queryset":
        """
        Returns a new QuerySet by filtering this one.
        """
        parsed = self._parsed
        # TODO: handle pre-existing ORDER clauses (throw an error?)
        # TODO: handle pre-existing GROUP BY clauses (subquery?)
        if any(isinstance(t, sqlparse.sql.Where) for t in parsed.tokens):
            joiner = SQL(" AND ")
        else:
            joiner = SQL(" WHERE ")

        params = self._combine_params(params)

        return Queryset(
            self.connection,
            sql=Composed([self.sql, joiner, SQL(sql)]),
            params=params,
        )

    def __iter__(self):
        """
        Returns an iterator over the results of this queryset.
        """
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql, self.params)
            yield from cursor

    def __len__(self):
        return self.count()

    def count(self):
        """
        Counts the number of rows in this queryset.
        """
        query = Composed([SQL("SELECT COUNT(*) FROM ("), self.sql, SQL(") AS count")])

        with self.connection.cursor() as cursor:
            cursor.execute(query, self.params)
            yield cursor.fetchone()[0]

    ### TODO:
    # * Slice support (limit/offset)
    # * .scalar() method (use the slice support to get a single row)


class ConnectionWrapper:
    """
    Wraps a psycopg connection to provide a queryset method.
    """

    def __init__(self, connection):
        self.connection = connection

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def __enter__(self, *args, **kwargs):
        self.connection.__enter__(*args, **kwargs)
        return self

    def __exit__(self, *args, **kwargs):
        self.connection.__exit__(*args, **kwargs)

    def queryset(self, sql: str | Composable, params: ParamsType = None):
        """
        Returns a lazily evaluated QuerySet for the given SQL and parameters.
        No database query is sent or executed until the queryset is evaluated.
        """
        if isinstance(sql, str):
            sql = SQL(sql)
        return Queryset(self, sql, params)


def wrap_connection(conn):
    return ConnectionWrapper(conn)
