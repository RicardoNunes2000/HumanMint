"""Constants for aggressive/garbled name detection."""

import re

# SQL keywords that when standalone indicate corruption
# Only matches whole words to avoid false positives like "selectric" or "dropbox"
SQL_KEYWORDS = {
    "select",
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "merge",
    "call",
    "grant",
    "revoke",
    "union",
    "intersect",
    "except",
    "from",
    "where",
    "join",
    "inner",
    "outer",
    "left",
    "right",
    "group",
    "order",
    "having",
    "into",
    "values",
    "table",
    "exec",
    "xp_",
    "declare",
    "begin",
    "end",
    "cursor",
    "procedure",
    "function",
    "trigger",
    "loop",
    "commit",
    "rollback",
    "benchmark",
    "sleep",
    "load_file",
    "outfile",
}

# Compile regex pattern for SQL keywords (word boundary = whole words only)
SQL_KEYWORD_PATTERN = r"\b(" + "|".join(re.escape(kw) for kw in SQL_KEYWORDS) + r")\b"
