from enum import Enum


class Color(Enum):
    BLUE = "\033[94m"
    GREEN = "\033[92m"


def colored(text, color: Color):
    return f"{color.value}{text}\033[0m"
