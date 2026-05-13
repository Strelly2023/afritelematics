def next_attempt(current_attempt, total_drivers):
    """
    Returns next attempt index or None if exhausted
    """
    if current_attempt + 1 >= total_drivers:
        return None
    return current_attempt + 1