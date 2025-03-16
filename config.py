import os
from dotenv import load_dotenv
import json
import logging
from dataclasses import dataclass, field
import argparse
from typing import Literal

LOGGER = logging.getLogger(__name__)

Command = Literal["suggest", "answer", "exec"]


def create_cli_args_parser():
    parser = argparse.ArgumentParser(
        description="Heimdallr, the watchman of the gods, and the AI CLI assistant.",
        usage="'heim [options] -- query' or 'heim --exec <suggestion_number>'",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    # Options for the 'suggest' and 'answer' commands
    parser.add_argument("-s", "--suggest", action="store_true", help="Get succint command suggestions, no explanations")
    parser.add_argument("-c", "--commands", help="include terminal command history as context [all, N (last N)]")
    parser.add_argument("--chat", help="include Heimdallr chat history as context [all, N (last N)]")
    parser.add_argument("-f", "--file", help="include file content as context")
    parser.add_argument("-i", "--input", action="store_true", help="request input from user to provide context")
    parser.add_argument("-m", "--model", help="The model to use (within options defined in configuration)")

    # Execute suggestion
    parser.add_argument("-e", "--exec", type=int, metavar="N", help="Execute suggestion number N")

    # Query will be everything after --
    parser.add_argument("query", nargs="*", help="The query to process")

    return parser


def parse_cli_args() -> tuple[Command, argparse.Namespace]:
    parser = create_cli_args_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.exec:
        command = "exec"
    else:
        command = "suggest" if args.suggest else "answer"
        args.query = " ".join(args.query)
        LOGGER.debug(f"{command}ing for query: {args.query}")

        if args.commands:
            LOGGER.debug(f"Using commands history: {args.commands}")
        if args.file:
            LOGGER.debug(f"Using file content: {args.file}")
        if args.input:
            LOGGER.debug(f"Requesting input from user")
        if args.chat:
            LOGGER.debug(f"Using chat history: {args.chat}")
        if args.model:
            LOGGER.debug(f"Using model: {args.model}")

    LOGGER.info(f"Parsed CLI command: {command}")
    LOGGER.info(f"Parsed CLI other args: {args}")

    return command, args


@dataclass
class Context:
    type: Literal["chat", "commands", "file", "input"]
    data: int | str | None = None


@dataclass
class LLMQueryArgs:
    query: str
    model: str
    openai_api_key: str
    openai_base_url: str
    context: list[Context] = field(default_factory=list)


@dataclass
class AppConfig:
    command: Command
    llm_query_args: LLMQueryArgs | None = None  # Only used for the suggest, answer commands
    exec_suggestion_number: int | None = None  # Only used for the exec command


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
        history = []
        if cli_args.commands:
            history.append(
                Context(type="commands", data=None if cli_args.commands == "all" else int(cli_args.commands))
            )
        if cli_args.chat:
            history.append(Context(type="chat", data=None if cli_args.chat == "all" else int(cli_args.chat)))
        if cli_args.file:
            history.append(Context(type="file", data=cli_args.file))
        if cli_args.input:
            history.append(Context(type="input"))
        llm_query_args = LLMQueryArgs(
            query=cli_args.query,
            model=model,
            openai_api_key=env_config["openai_api_key"],
            openai_base_url=file_config["openai_base_url"],
            context=history,
        )
        config = AppConfig(command=command, llm_query_args=llm_query_args)

    elif command == "exec":
        config = AppConfig(command=command, exec_suggestion_number=cli_args.exec)

    else:
        raise ValueError(f"Invalid command: {command}")

    LOGGER.debug(f"Loaded config: {config}")
    return config


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    config = load_config()
