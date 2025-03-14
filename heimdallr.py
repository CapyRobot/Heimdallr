import logging
import sys

from config import AppConfig, load_config
from llm import execute_llm_command
from session import execute_session_command

# Logging
DEFAULT_LOG_LEVEL = logging.ERROR  # will be overridden by config.py if verbose is set
logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
LOGGER = logging.getLogger(__name__)


def main():
    config: AppConfig = load_config()

    if config.command == "suggest" or config.command == "answer":
        execute_llm_command(config.command, config.llm_query_args)
    elif config.command == "exec":
        raise NotImplementedError("Exec command not implemented")
    elif config.command == "session":
        execute_session_command(config.session_action)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt... exiting...")
        sys.exit(1)
