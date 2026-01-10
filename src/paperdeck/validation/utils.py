"""Utility functions for LaTeX validation."""


def is_escaped(text: str, position: int) -> bool:
    """Check if character at position is escaped by backslash.

    Handles:
    - \\{ is escaped (literal brace)
    - \\\\{ is NOT escaped (double backslash then brace)
    - \\\\\\{ is escaped (triple backslash then brace)

    Count consecutive backslashes before position.
    Odd count = escaped, Even count = not escaped.

    Args:
        text: The text string
        position: Position of character to check (0-indexed)

    Returns:
        True if character at position is escaped
    """
    if position == 0:
        return False

    backslash_count = 0
    idx = position - 1
    while idx >= 0 and text[idx] == '\\':
        backslash_count += 1
        idx -= 1

    # Odd number of backslashes = escaped
    return backslash_count % 2 == 1


def strip_comments(line: str) -> str:
    """Remove comments from line while preserving escaped percent signs.

    Examples:
    - "\\begin{frame} % comment" -> "\\begin{frame} "
    - "value is 50\\% done" -> "value is 50\\% done"
    - "% full line comment" -> ""
    - "text \\% and % comment" -> "text \\% and "

    Args:
        line: Line of LaTeX text

    Returns:
        Line with comments removed
    """
    result = []
    i = 0
    while i < len(line):
        if line[i] == '%' and not is_escaped(line, i):
            # Found unescaped %, rest is comment
            break
        result.append(line[i])
        i += 1
    return ''.join(result)
