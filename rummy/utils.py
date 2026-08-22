def str_list(lst):
    return list(map(str, lst))


def format_list_of_str(lst):
    if not lst:
        return ""
    if not isinstance(lst[0], str):
        lst = str_list(lst)
    return ", ".join(lst)
