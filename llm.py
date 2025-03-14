from dataclasses import dataclass
import platform
import logging
import os
import sys
from openai import OpenAI

from config import LLMQueryArgs, Command

LOGGER = logging.getLogger(__name__)

############################################################################
# Environment info


# get useful environment info from the system like OS, shell type, etc.
# things that might help the LLM to generate a better command
@dataclass
class EnvironmentInfo:
    os: str
    shell: str
    user: str
    home: str
    current_working_directory: str

    def __str__(self):
        return f"OS: {self.os}, Shell: {self.shell}, User: {self.user}, Home: {self.home}, Current Working Directory: {self.current_working_directory}"


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
        current_working_directory=os.getcwd(),
    )


ENV_INFO = get_environment_info()


############################################################################


class AIClient:
    def __init__(self, llm_query_args: LLMQueryArgs):
        LOGGER.debug(f"Environment info: {ENV_INFO}")
        self.model = llm_query_args.model
        self.key = llm_query_args.openai_api_key
        self.url = llm_query_args.openai_base_url

        self.client = OpenAI(base_url=self.url, api_key=self.key)

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

        prompt = config.query
        if prompt.strip():
            command = ai_client.get_command_suggestion(prompt)
            command = command.strip("`")  # remove leading and trailing backticks
            print(command)
        else:
            print("No prompt provided.")

    elif command == "answer":
        raise NotImplementedError("Answer command not implemented")
