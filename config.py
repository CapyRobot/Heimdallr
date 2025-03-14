import os
from dotenv import load_dotenv
import json
import logging
from dataclasses import dataclass
import argparse
from typing import Literal

LOGGER = logging.getLogger(__name__)

Command = Literal["suggest", "answer", "exec", "session"]


def create_cli_args_parser():
    parser = argparse.ArgumentParser(description="Heimdallr, the watchman of the gods, and the AI CLI assistant.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_llm_query_args(parser: argparse.ArgumentParser):
        parser.add_argument("query", help="User query")
        parser.add_argument("--history", help="Type of history to include (chat/N-lines/N-commands)")
        parser.add_argument("--context", help="Path to file to use as context")
        parser.add_argument("--model", help="The model to use (within options defined in configuration)")

    # 'suggest' command
    suggest_parser = subparsers.add_parser("suggest", help="Get command suggestions")
    add_llm_query_args(suggest_parser)

    # 'answer' command
    answer_parser = subparsers.add_parser("answer", help="Get detailed answers")
    add_llm_query_args(answer_parser)

    # 'exec' command
    exec_parser = subparsers.add_parser("exec", help="Execute a suggested command")
    exec_parser.add_argument("suggestion_number", type=int, help="Number of the suggestion to execute")

    # 'session' command
    session_parser = subparsers.add_parser("session", help="Manage terminal recording sessions")
    session_parser.add_argument(
        "action",
        nargs="?",
        choices=["start", "status", "end"],
        default="start",
        help="Session action to perform",
    )

    return parser


def parse_cli_args() -> tuple[Command, argparse.Namespace]:
    parser = create_cli_args_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.command == "answer" or args.command == "suggest":
        LOGGER.debug(f"{args.command}ing for query: {args.query}")
        if args.history:
            LOGGER.debug(f"Using history: {args.history}")
            raise NotImplementedError("History feature not implemented")
        if args.context:
            LOGGER.debug(f"Using context from: {args.context}")
            raise NotImplementedError("Context feature not implemented")
        if args.model:
            LOGGER.debug(f"Using model: {args.model}")

    elif args.command == "exec":
        LOGGER.debug(f"Executing suggestion number: {args.suggestion_number}")

    elif args.command == "session":
        LOGGER.debug(f"Session action: {args.action}")

    LOGGER.info(f"Parsed CLI command: {args.command}")
    LOGGER.info(f"Parsed CLI other args: {args}")

    return args.command, args


HistoryType = Literal["chat", "lines", "commands"]


@dataclass
class LLMQueryArgs:
    query: str
    model: str
    openai_api_key: str
    openai_base_url: str
    history_type: HistoryType | None = None
    history_length: int | None = None
    context: str | None = None

    @staticmethod
    def history_from_str(history: str | None) -> tuple[HistoryType | None, int | None]:
        if history is None:
            return None, None

        # Validation: accept "chat", "{int>0}-lines", "{int>0}-commands"
        if history == "chat":
            return "chat", None

        if len(history.split("-")) == 2:
            [n, type] = history.split("-")
            if n.isdigit() and int(n) > 0 and type in ["lines", "commands"]:
                return type, int(n)

        raise ValueError(
            f"Invalid history: {history}. Acceptable values are: chat, N-lines, N-commands (where N is an integer > 0)."
        )


@dataclass
class AppConfig:
    command: Command
    llm_query_args: LLMQueryArgs | None = None  # Only used for the suggest, answer commands
    exec_suggestion_number: int | None = None  # Only used for the exec command
    session_action: str | None = None  # Only used for the session command


def load_config() -> AppConfig:
    command, cli_args = parse_cli_args()

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        file_config = json.load(f)
    LOGGER.debug(f"Loaded config: {file_config}")

    load_dotenv()
    env_config = {"openai_api_key": os.getenv("OPENAI_API_KEY")}
    LOGGER.debug(f"Loaded env config: {env_config}")
    if command == "suggest" or command == "answer":
        model_map = file_config["model_map"]
        try:
            model = model_map[cli_args.model if cli_args.model else file_config["default_model"]]
        except KeyError:
            LOGGER.error(f"Invalid model: {cli_args.model}. Acceptable values are: {model_map.keys()}")
            raise
        history_type, history_length = LLMQueryArgs.history_from_str(cli_args.history)
        llm_query_args = LLMQueryArgs(
            query=cli_args.query,
            model=model,
            openai_api_key=env_config["openai_api_key"],
            openai_base_url=file_config["openai_base_url"],
            history_type=history_type,
            history_length=history_length,
            context=cli_args.context,
        )
        config = AppConfig(command=command, llm_query_args=llm_query_args)

    elif command == "exec":
        config = AppConfig(command=command, exec_suggestion_number=cli_args.suggestion_number)

    elif command == "session":
        config = AppConfig(command=command, session_action=cli_args.action)

    else:
        raise ValueError(f"Invalid command: {command}")

    LOGGER.debug(f"Loaded config: {config}")
    return config


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    config = load_config()
