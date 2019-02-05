
def overlap(e1_start: int, e1_end: int, e2_start: int, e2_end: int) -> bool:
    """
    Check if two spans overlap with each other

    Args:
        e1_start (int): span 1 begin offset
        e1_end (int): span 1 end offset
        e2_start (int): span 2 begin offset
        e2_end (int): span 2 end offset

    Returns:
        bool: True if they overlap, False otherwise

    """

    if e1_start <= e2_start < e2_end <= e1_end:
        return True

    elif e2_start <= e1_start < e1_end <= e2_end:
        return True

    elif e1_start <= e2_start < e1_end <= e2_end:
        return True

    elif e2_start <= e1_start < e2_end <= e1_end:
        return True

    return False
