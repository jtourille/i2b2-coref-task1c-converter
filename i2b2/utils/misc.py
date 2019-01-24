
def find_ngrams(input_list: list, n: int) -> list:
    """
    Return a list of n_grams from a list

    Args:
        input_list (list): list from which n_grams are extracted
        n (int): n gram length

    Returns:
        list: n-gram list

    """
    if n == 1:
        return input_list
    else:
        return list(zip(*[input_list[i:] for i in range(n)]))
