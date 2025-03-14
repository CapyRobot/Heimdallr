from dataclasses import dataclass
import platform
from openai import OpenAI

import os
import logging
from dotenv import load_dotenv
import sys
import argparse

from common import Color, colored


# See build.nvidia.com for more models
MODEL_MAP = {
    "deepseek-large": "deepseek-ai/deepseek-r1-distill-qwen-32b",
    "deepseek-small": "deepseek-ai/deepseek-r1-distill-qwen-7b",
    "llama-3.2-3b": "meta/llama-3.2-3b-instruct",
    "llama-3.3-70b": "meta/llama-3.3-70b-instruct",
}
DEFAULT_MODEL = "llama-3.3-70b"


############################################################################
# Setup

load_dotenv()

_epilog = "Available models:\n\t{models}".format(
    models="\n\t".join([f"{k}: {v}" for k, v in MODEL_MAP.items()])
)

# CLI args
_parser = argparse.ArgumentParser(
    description="Heimdallr, the watchman of the gods, and the AI CLI assistant.",
    epilog=_epilog,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
_parser.add_argument(
    "model",
    nargs="?",
    default=DEFAULT_MODEL,
    help=f"The AI model to use [default: {DEFAULT_MODEL}]",
)
_parser.add_argument(
    "-v", "--verbose", action="store_true", default=False, help="Enable verbose logging"
)
ARGS = _parser.parse_args()

# Logging
_level = logging.DEBUG if ARGS.verbose else logging.ERROR
logging.basicConfig(
    level=_level,
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
        return (
            f"OS: {self.os}, Shell: {self.shell}, User: {self.user}, Home: {self.home}"
        )


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
    def __init__(self):
        self._load_env()
        self.client = OpenAI(base_url=self.url, api_key=self.key)
        self.model = MODEL_MAP[ARGS.model]

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

def main():
    ai_client = AIClient()
    try:
        prompt = input(colored("Heim > What command are you looking for?", Color.BLUE) + "\n> ")
        if prompt.strip():
            print(colored("Heim >", Color.BLUE))
            command = ai_client.get_command_suggestion(prompt)
            # remove leading and trailing backticks
            command = command.strip("`")
            print(colored(command, Color.GREEN))
        else:
            print("No prompt provided.")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        LOGGER.error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
