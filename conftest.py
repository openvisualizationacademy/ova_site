# Use pysqlite3 if available (CI bundles a modern SQLite via pysqlite3-binary,
# needed because Django 5.2 generates JSON_VALID() constraints that older
# system SQLite versions don't support).
try:
    import pysqlite3
    import sys

    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass