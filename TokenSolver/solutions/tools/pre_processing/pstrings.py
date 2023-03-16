from itertools import product, combinations
from ..pre_processing import plist
import re
from typing import Any


class Grep:
    """ Get content from string """

    def __init__(self, string):
        self.string = string

    def ints(self) -> list:
        """
        Grab integer from given string
        :return: list[ints]
        """

        return [int(x) for x in re.findall(r"[-+]?\d+", self.string)]

    def floats(self) -> list:
        """
        Get float from string
        :return: list[floats]
        """

        return [float(x) for x in re.findall(r"[-+]?\d*\.\d+", self.string)]

    def domain(self, include_protocol: bool = False, include_subdomain=False, include_tld=True) -> dict or str:
        """
        Grab domain from given url
        :param include_tld: choose whether to include top level domain like .com, .org, .io
        :param include_subdomain: choose whether to include subdomain i.e www
        :param include_protocol: include domain protocol i.e http | https | ftp etc
        :return: domain of url or json
        """

        url = self.string
        protocol, domain = url[:url.find("/") - 1], url[url.find("/") + 2:]
        if domain.find("/") == -1:
            domain = domain[:]
        else:
            domain = domain[:domain.find("/")]

        dnc = domain.split('.')
        tld = f".{dnc[-1]}"
        if include_protocol:
            domain = f"{protocol}://{domain}"
        if not include_tld:
            domain = domain.replace(tld, '')
        if not include_subdomain:
            domain = domain.replace('www.', '')
        return domain

    def __len__(self, int_only=False):
        if int_only:
            return len([x for x in self.string if x.isdigit()])
        else:
            return len(self.string)


def insert(string, insert_str, interval=1, reversed=False) -> str:
    """
    Insert some string at every interval
        example: insert('10000', ',', interval=3, reversed=True) -> 10,000
    :param string: input string
    :param insert_str: string to insert in input str
    :param interval: when to insert insert_str in str
    :param reversed: reverse string before insertion
    :return: new_str
    """

    if reversed:
        ts = []
        for x in range(len(string), 0, -interval):
            val = string[x - interval:x]
            if val:
                ts.append(val)
            else:
                ts.append(string[:x])
        ts.reverse()
        return f'{insert_str}'.join(ts)
    else:
        return f'{insert_str}'.join(string[x:x + interval] for x in range(0, len(string), interval))


def find_all(string, word_in_str) -> list:
    """
    Grab the indexes of the given word found in line
    :type string: str
    :param string: Any line from where the word is needed to grab
    :type word_in_str: str
    :param word_in_str: The word which index is required
    :return: List of indexes of the given word found in string
    """

    return [match.start() for match in re.finditer(word_in_str, string)]


def enclose_text(text: str, encloserS, encloserE) -> str:
    """
    Add parentheses to text for repeat stance
    :param text: input string
    :param encloserS: insert on start of text
    :param encloserE: insert on end of text
    :return: Text in enclosed str
    """

    return f"{encloserS}{text}{encloserE}"


def evaluate(expression: str) -> Any or None:
    """
    Solve any mathematical equation like calculator
    :param expression: a + b
    :return: result of expression
    """

    if is_arbitrary(expression):
        return None

    try:
        return eval(expression)
    except:
        return None


def replace_all(text: str, __old: list, __new: list) -> str:
    """
    Replace all old values with new ones
    :param text: input string
    :param __old: list of old texts to be replaced
    :param __new: list of new texts
    :return: text in str
    """

    assert len(__old) == len(__new)
    replaced = text
    for i in range(len(__new)):
        replaced = replaced.replace(__old[i], __new[i])
    return replaced


def text_augmentation(
text: str,
        augmented_letters: dict,
        flip: bool = False,
        include_self: bool = True,
        include_single_level: bool = True,
        include_multi_level: bool = True) -> list:
    """
    Text transformations
    :param text: text to be augmented
    :param augmented_letters: dictionary of transformations
    :param flip: if true inverse transformations are also included
    :param include_single_level:transformations including one letter at a time
    :param include_multi_level: transformations including all letter at a time
    :return: list of augmented text
    """

    augmented_results = [] if not include_self else [text]
    originals = list(augmented_letters.keys())
    replacements = list(augmented_letters.values())

    # Lose unused keys/values
    pending_removal = []
    for o in range(len(originals)):
        if originals[o] not in text:
            pending_removal.append(o)
    originals = [originals[x] for x in range(len(originals)) if x not in pending_removal]
    replacements = [replacements[x] for x in range(len(replacements)) if x not in pending_removal]

    # Single level replacements
    if include_single_level:
        for o in range(len(originals)):
            for x in replacements[o]:
                augmented_results.append(text.replace(originals[o], x))

    # Multi level replacements
    if len(originals) > 1:
        if include_multi_level:
            for r in range(2, len(replacements) + 1):
                val_combs = list(combinations(replacements, r))
                key_combs = list(combinations(originals, r))
                for c in range(len(key_combs)):
                    cartesian_product = product(*val_combs[c])
                    for p in cartesian_product:
                        augmented_results.append(replace(text, __old=key_combs[c], __new=p))
    if flip:
        augmented_results += [x[::-1] for x in augmented_results]
    return augmented_results


def reverse_augmentation(text: str, augmented_letters: dict) -> str:
    """
    Recover text
    :param text: input string
    :param augmented_letters: dictionary of augmented letters
    :return: text in str
    """

    replaced = list(augmented_letters.values())
    originals = list(augmented_letters.keys())

    for o in range(len(originals)):
        for letter in replaced[o]:
            if letter in text:
                text = text.replace(letter, originals[o])
    return text


def maximum_splittedN(string: str, splitters: list or tuple, count: bool = False) -> tuple or int:
    """
    Split a string to a given list of splitters, then grab the max key
    :param string: input string
    :param splitters: list of splitters | ['+', '-', '/', '*']
    :param count: also count the max length
    :return: maximum occuring splitter or (len, op)
    """

    splitted = [{len(string.split(s)): s} for s in splitters]
    max_n = max([list(s.keys()) for s in splitted])[0]
    return [s[max_n] for s in splitted if s.get(max_n)][0] if not count else \
        [list(s.items())[0] for s in splitted if s.get(max_n)][0]


def is_arbitrary(string: str) -> bool:
    """
    Check whether the given string is arbitrary::
        -> str is arbitrary if no operator is inside it or str == '' or str == ' '
    :param string: input string
    :return: bool
    """

    max_n = maximum_splittedN(string, plist.operators, count=True)
    return False if string and max_n[0] != 1 and not string.isspace() else True
