
def surroundedwith(string: str, start: str, end: Optional[str] = None) -> bool:
    """Return a boolean representing whether 'string' argument starts with
    'start' substring and ends with 'end' substring.

    If end is not provided, 'start' is used in its place.
    """
    return string.startswith(start) and string.endswith(end if end is not None else start)
