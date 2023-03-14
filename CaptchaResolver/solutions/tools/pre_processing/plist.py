def argmax(list_: list) -> int:
    """ Maximum value index in given list """
    return list_.index(max(list_))


def argmin(list_) -> int:
    """ Minimum value index in given list """
    return list_.index(min(list_))


def argmaxN(array, n) -> list:
    """
    Get argmax_n from given np.array
    *argmax specifies maximum value index
    :param array: np.array
    :param n: no of values
    :return: list of argmax values
    """

    return array.argsort()[-n:]


def argminN(array, n) -> list:
    """
    Get argmin_n from given np.array
    *argmin specifies lowest value index
    :param array: np.array
    :param n: no of values
    :return: list of argmin values
    """

    return array.argsort()[:n]


def maxN(array, n) -> list:
    """
    Get max_n from given np.array
    :param array: np.array
    :param n: no of values
    :return: list of max values
    """

    return [array[x] for x in argmaxN(array, n)]


def minN(array, n) -> list:
    """
    Get min_n from given np.array
    :param array: np.array
    :param n: no of values
    :return: list of min values
    """

    return [array[x] for x in argminN(array, n)]


def inN(strings, list_of_str, n=1) -> bool:
    """
    Is any str from list[str] in str(__y)?
    :param strings: list or tuple of strings to match in __y
    :param list_of_str: str or list which might contains any str from strings
    :param n: Atleast number of matches to return True
    :return: True if n matches else False
    """

    list_of_str = ''.join(list_of_str)
    for x in strings:
        if x in list_of_str:
            n -= 1
        if n == 0:
            return True
    return False


def inS(string, list_, reverse=True) -> bool:
    """
    Check whether the given string in any item of list or list_item in string
    :param string: input string
    :param list_: input list
    :param reverse: is list_item in string
    :return: bool
    """

    for l in list_:
        if string in l:
            return True
        elif reverse and l in string:
            return True
    return False


def indexN(list_: list, value, n=1, reversed: bool = False) -> list or int or str:
    """
    Find x without raising ValueError
    :param list_: list of items
    :param value: value to be found
    :return: indexes if n > 1 else indexes[0] if len(indexes) == 1 else 'Not Found'
    """

    if reversed:
        list_ = list_[::-1]

    indexes = []
    i = 0
    for _ in range(n):
        try:
            i = list_.index(value, i)
            indexes.append(i)
            i += 1
        except ValueError:
            pass

    if reversed:
        indexes = [len(list_) - 1 - y for y in indexes]

    return indexes if n > 1 else indexes[0] if len(indexes) == 1 else 'Not Found'


def split(list_: list, n: int, reverse: bool = False) -> list:
    """
    Split the given list in n order
    :param list_: input list
    :param n: order of splittion
    :param reverse: reverse list first
    :return: list of lists
    """

    out = []
    start, stop, step = (0, len(list_), n) if not reverse else ((len(list_) - 1), -1, -n)
    for i in range(start, stop, step):
        sub_array = []
        for _i in range(n):
            try:
                sub_array.append(list_[i + _i])
            except IndexError:
                break
        out.append(sub_array)
    return out


def transpose(list_: list) -> list:
    """ Transpose of given list """
    import itertools
    return list(map(list, itertools.zip_longest(*list_, fillvalue=None)))
