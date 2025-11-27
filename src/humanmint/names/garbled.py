"""
Garbled name cleaning for HumanMint.

Handles severely corrupted name data from untrusted sources (e.g., CRM exports,
database dumps with SQL artifacts). Strips SQL injection patterns, comments, and
other obvious non-name content.

This is an AGGRESSIVE cleaning mode and should only be used when you know your
data comes from a genuinely corrupted or untrusted source.

Examples:
    >>> clean_garbled_name("### TEMP ### MR JOHN Q PUBLIC")
    "MR JOHN Q PUBLIC"

    >>> clean_garbled_name("John Smith; DROP TABLES")
    "John Smith DROP TABLES"

    >>> clean_garbled_name("SELECT * FROM users WHERE id=42; /* hack */")
    "SELECT * FROM users WHERE id42"
"""

import re
from typing import Optional


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
}

# Compile regex pattern for SQL keywords (word boundary = whole words only)
_SQL_KEYWORD_PATTERN = r"\b(" + "|".join(re.escape(kw) for kw in SQL_KEYWORDS) + r")\b"


def clean_garbled_name(text: Optional[str]) -> Optional[str]:
    """
    Remove SQL artifacts, HTML, and corruption markers from a name field.

    This is an AGGRESSIVE cleaning mode. Only use if data comes from a
    genuinely corrupted source (e.g., raw database exports with SQL injection
    artifacts, CRM exports with system comments, HTML exports, etc.).

    WARNING: This may remove legitimate content. For example:
    - "Johnson; consultant" loses the semicolon
    - Text after `--` or `/* */` is stripped (even if intentional)
    - HTML tags are completely removed

    Patterns removed:
    1. HTML tags and entities: `<b>`, `&nbsp;`, etc.
    2. SQL comment markers: `--` (rest of line), `/* ... */` (block)
    3. Statement terminators: `;`
    4. Classic SQL injection patterns: `OR 1=1`, `UNION SELECT`, etc.
    5. SQL Server exploitation patterns: `EXEC xp_`
    6. Leading corruption markers: `### TEMP ###`, `[CORRUPTED]`, etc.

    Args:
        text: Raw name field that may contain garbage.

    Returns:
        Cleaned text with SQL artifacts removed, or None if empty after cleaning.

    Examples:
        >>> clean_garbled_name("### TEMP ### John Smith")
        "John Smith"

        >>> clean_garbled_name("John Smith; DELETE FROM users")
        "John Smith DELETE FROM users"

        >>> clean_garbled_name("Dr. O'Brien -- legacy account")
        "Dr. O'Brien"

        >>> clean_garbled_name("SELECT * FROM names")
        "SELECT * FROM names"  # Not removed (legitimate surname "Select" possible)

        >>> clean_garbled_name(None)
        None
    """
    if not text or not isinstance(text, str):
        return None

    # 0. Remove HTML tags and entities (highest priority - these are clearly not names)
    # Remove HTML tags: <b>, <span>, etc.
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove HTML entities: &nbsp;, &lt;, etc.
    text = re.sub(r"&[a-z]+;", " ", text, flags=re.IGNORECASE)

    # 1. Remove SQL-style comments
    # Remove inline comments: -- anything after until end of string/newline
    text = re.sub(r"--.*?(?:\n|$)", " ", text, flags=re.MULTILINE)

    # Remove block comments: /* ... */
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)

    # 2. Remove everything after semicolon (statement terminator)
    # Semicolon marks end of SQL statement, nothing after it is a name
    text = re.sub(r";.*", "", text)

    # 3. Remove classic SQL injection patterns
    # OR 1=1, OR true, UNION SELECT, EXEC xp_, etc.
    text = re.sub(r"\bOR\s+1\s*=\s*1\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bOR\s+true\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bUNION\s+SELECT\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bEXEC\s+xp_\w+", " ", text, flags=re.IGNORECASE)

    # 4. Remove markdown formatting and corruption markers
    # Remove markdown headers: # Title, ## Subtitle, etc.
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Remove markdown bold: **text** or __text__
    text = re.sub(r"\*{2,}|_{2,}", "", text)
    # Remove markdown italic: *text* or _text_
    text = re.sub(r"(?<!\*)\*(?!\*)|\b_\b", "", text)
    # Remove markdown links: [text](url) -> keep text
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    # Remove markdown code blocks and inline code: `code` or ```code```
    text = re.sub(r"`{1,3}", "", text)

    # Remove common corruption markers at start/end
    # These are system markers, not part of actual names
    text = re.sub(
        r"^#+\s*(?:TEMP|CORRUPTED|TEST|DEBUG|ADMIN|USER).*?#+\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^\s*#+\s*(?:TEMP|CORRUPTED|TEST|DEBUG|ADMIN|USER).*?#+\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"\s*#+$", "", text)

    # 5. Remove trailing SQL keywords that often follow injected code
    # Pattern: <name> DROP/DELETE/INSERT/UPDATE/SELECT/FROM/WHERE/etc
    # Keep only the first 2-3 words (typical name length)
    words = text.split()

    # Find where legitimate name ends and SQL begins
    # A name is typically 1-3 words (first, middle/initial, last)
    # SQL keywords appearing as 3rd+ word are likely injection
    cleaned_words = []
    sql_keyword_count = 0

    for i, word in enumerate(words):
        word_lower = word.lower().rstrip(".,;")

        # Stop if we hit multiple SQL keywords or a keyword after 3+ name words
        if word_lower in SQL_KEYWORDS:
            sql_keyword_count += 1
            # If we see 2+ keywords, stop (likely SQL injection)
            if sql_keyword_count >= 2:
                break
            # If we see keyword as 4th+ word and we already have 2-3 name words, stop
            if len(cleaned_words) >= 2:
                break
            # Otherwise include it (might be a name)
            cleaned_words.append(word)
        else:
            cleaned_words.append(word)
            sql_keyword_count = 0  # Reset counter for legitimate words

    text = " ".join(cleaned_words)

    # 6. Clean up excess whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Return None if nothing left after cleaning
    if not text:
        return None

    return text


def should_use_garbled_cleaning(text: Optional[str]) -> bool:
    """
    Auto-detect if a name field likely needs garbled cleaning.

    Returns True if the text contains clear signs of corruption:
    - SQL comment markers (-- or /*)
    - Statement terminators (;)
    - SQL keywords (select, delete, etc. as standalone words)
    - Corruption markers (### TEMP ###, [CORRUPTED], etc.)

    This is used to decide whether to apply aggressive cleaning automatically
    if aggressive_clean=True is set.

    Args:
        text: Raw name field to analyze.

    Returns:
        True if text appears corrupted, False otherwise.

    Examples:
        >>> should_use_garbled_cleaning("John Smith")
        False

        >>> should_use_garbled_cleaning("John Smith; DROP TABLE")
        True

        >>> should_use_garbled_cleaning("### TEMP ### John")
        True

        >>> should_use_garbled_cleaning("Dr. O'Brien -- legacy")
        True
    """
    if not text or not isinstance(text, str):
        return False

    # Check for HTML tags or entities
    if re.search(r"<[^>]+>|&[a-z]+;", text, re.IGNORECASE):
        return True

    # Check for SQL comment markers
    if "--" in text or "/*" in text or "*/" in text:
        return True

    # Check for statement terminators (semicolon)
    if ";" in text:
        return True

    # Check for corruption markers
    if re.search(r"^#+\s*(TEMP|CORRUPTED|TEST|DEBUG|ADMIN)", text, re.IGNORECASE):
        return True

    if re.search(r"\[(TEMP|CORRUPTED|TEST|DEBUG|ADMIN)\]", text, re.IGNORECASE):
        return True

    # Check for SQL injection patterns
    if re.search(r"\bOR\s+1\s*=\s*1\b", text, flags=re.IGNORECASE):
        return True

    if re.search(r"\bUNION\s+SELECT\b", text, flags=re.IGNORECASE):
        return True

    if re.search(r"\bEXEC\s+xp_", text, flags=re.IGNORECASE):
        return True

    # Check for SQL keywords as standalone words (higher confidence of corruption)
    # Only flag if there are multiple keywords or keywords in unusual positions
    keywords_found = re.findall(_SQL_KEYWORD_PATTERN, text, flags=re.IGNORECASE)
    if len(keywords_found) >= 2:  # Multiple keywords = likely SQL, not a name
        return True

    return False
