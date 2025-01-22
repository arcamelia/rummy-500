"""
Return a list where each element in the given list is transformed into a string.
"""
def str_list(lst):
    return list(map(str, lst))

"""
Return a string of a list, formatted nicely.
"""
def format_list_of_str(lst):
    if not isinstance(lst[0], str):
        lst = str_list(lst)
    return ", ".join(lst)