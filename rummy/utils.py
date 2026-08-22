def str_list(lst):
    """
    Return a list where each element in the given list is transformed into a string.
    """
    return list(map(str, lst))


def format_list_of_str(lst):
    """
    Return a nicely formatted string representation of the given list of objects.
    """
    if not lst:
        return ""
    if not isinstance(lst[0], str):
        lst = str_list(lst)
    return ", ".join(lst)
