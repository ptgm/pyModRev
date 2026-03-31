"""
Utility functions for quoting/unquoting identifiers at the ASP boundary.

In Clingo's ASP, names starting with an uppercase letter are treated as
variables. To use them as constants, they must be wrapped in double quotes.
These helpers centralise that logic so the rest of the codebase works 
with plain, unquoted identifiers.
"""


def asp_quote(name: str) -> str:
    """
    Wraps an identifier in double quotes if it needs quoting for ASP/Clingo.

    An identifier needs quoting when it does NOT already start with:
      - a lowercase letter
      - a digit
      - a double-quote (already quoted)

    Examples:
        asp_quote("egr1")   -> "egr1"      (no change)
        asp_quote("Egr1")   -> '"Egr1"'     (quoted)
        asp_quote('"Egr1"') -> '"Egr1"'     (already quoted, no change)
    """
    if not name:
        return name
    first = name[0]
    if first == '"' or first.islower() or first.isdigit():
        return name
    return f'"{name}"'


def asp_unquote(name: str) -> str:
    """
    Strips surrounding double quotes from an identifier if present.

    Examples:
        asp_unquote('"Egr1"') -> "Egr1"
        asp_unquote("egr1")   -> "egr1"    (no change)
    """
    if name and len(name) >= 2 and name[0] == '"' and name[-1] == '"':
        return name[1:-1]
    return name
