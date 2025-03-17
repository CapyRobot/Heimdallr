from enum import Enum
import logging


class Color(Enum):
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"


def colored(text, color: Color):
    return f"{color.value}{text}\033[0m"


def exit_with_error(message: str, logger: logging.Logger, exit_code: int = 1):
    logger.error(colored(message, Color.RED))
    exit(exit_code)
