import os
import logging
import sys
from dataclasses import dataclass
import platform
from openai import OpenAI

from config import AppConfig, Command, LLMQueryArgs, load_config
from common import Color, colored


############################################################################
# Setup

# Logging
DEFAULT_LOG_LEVEL = logging.ERROR  # will be overridden by config.py if verbose is set
logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
LOGGER = logging.getLogger(__name__)


# get useful environment info from the system like OS, shell type, etc.
# things that might help the AI to generate a better command
@dataclass
class EnvironmentInfo:
    os: str
    shell: str
    user: str
    home: str

    def __str__(self):
        return f"OS: {self.os}, Shell: {self.shell}, User: {self.user}, Home: {self.home}"


def get_os_info() -> str:
    os_name = platform.system()
    if os_name == "Darwin":
        try:
            mac_ver = platform.mac_ver()[0]
            if mac_ver:
                os_name = f"macOS {mac_ver}"
        except:
            pass
    return os_name


def get_environment_info() -> EnvironmentInfo:
    return EnvironmentInfo(
        os=get_os_info(),
        shell=os.environ.get("SHELL", "unknown"),
        user=os.environ.get("USER", "unknown"),
        home=os.environ.get("HOME", "unknown"),
    )


ENV_INFO = get_environment_info()
LOGGER.debug(f"Environment info: {ENV_INFO}")


############################################################################


class AIClient:
    def __init__(self, llm_query_args: LLMQueryArgs):
        self._load_env()
        self.client = OpenAI(base_url=self.url, api_key=self.key)
        self.model = llm_query_args.model

    def _load_env(self):
        self.key = os.getenv("OPENAI_API_KEY")
        if not self.key:
            LOGGER.error("OPENAI_API_KEY is not set")
            raise ValueError("OPENAI_API_KEY is not set")
        self.url = os.getenv("OPENAI_BASE_URL")
        if not self.url:
            LOGGER.error("OPENAI_BASE_URL is not set")
            raise ValueError("OPENAI_BASE_URL is not set")
        LOGGER.debug("Environment variables successfully loaded")

    def get_command_suggestion(self, prompt):
        system_message = f"""
        You are a helpful terminal assistant. When users ask for help with command-line tasks,
        provide only the exact command they should run, with no additional explanation unless they specifically ask for it.
        Make sure the command is correct and efficient for their needs.
        Do not wrap the command in backticks or any other formatting.
        Here is some useful information about the environment: {ENV_INFO}
        """

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,  # Lower temperature for more precise responses
            top_p=0.7,
            max_tokens=2096,  # Reduced as we only need short commands
            stream=False,  # Changed to False for simpler handling
        )

        return completion.choices[0].message.content


def execute_llm_command(command: Command, config: LLMQueryArgs):
    ai_client = AIClient(config)

    if command == "suggest":
        try:
            prompt = config.query
            if prompt.strip():
                command = ai_client.get_command_suggestion(prompt)
                command = command.strip("`")  # remove leading and trailing backticks
                print(command)
            else:
                print("No prompt provided.")
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            LOGGER.error(f"An error occurred: {str(e)}")
            sys.exit(1)

    elif command == "answer":
        raise NotImplementedError("Answer command not implemented")


def main():
    config: AppConfig = load_config()

    if config.command == "suggest" or config.command == "answer":
        execute_llm_command(config.command, config.llm_query_args)
    elif config.command == "exec":
        raise NotImplementedError("Exec command not implemented")
    elif config.command == "session":
        raise NotImplementedError("Session command not implemented")


if __name__ == "__main__":
    main()
