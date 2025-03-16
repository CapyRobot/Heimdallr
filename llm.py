from dataclasses import dataclass
import platform
import logging
import os
from openai import OpenAI

from config import LLMQueryArgs, Command
from session import get_session_runtime

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
        self.config = llm_query_args
        self.client = OpenAI(base_url=llm_query_args.openai_base_url, api_key=llm_query_args.openai_api_key)
        self.session_runtime = get_session_runtime()
        if self.session_runtime is None:
            if llm_query_args.history_type is not None:
                raise ValueError("History context is not supported when no session is active")

    def _get_system_instructions(self, command: Command) -> str:
        template = """
            You are a helpful terminal assistant to help users with command-line tasks.
            {command_specific_instructions}
            {how_to_suggest_commands}
            """
        how_to_suggest_commands = """
            For any suggested commands, make sure the command is correct and efficient for their needs.
            To facilitate copy-paste, do not wrap suggested commands in backticks or any other formatting,
            and do not include any other text or formatting in the line of the command.
            Always suggest command with the format [<suggestion_number>] <command> so the user can easily
            reference the command.
            """
        command_specific_instructions = ""
        if command == "suggest":
            command_specific_instructions = """
            When users ask for help with command-line suggestions, provide only the exact command they should run
            with no additional explanation unless they specifically ask for it.
            Only provide multiple suggestions if the user asks for them.
            """
        elif command == "answer":
            command_specific_instructions = """
            Answer the user's question based on the information provided.
            When appropriate, suggest commands to help the user.
            """
        else:
            raise ValueError(f"Invalid command: {command}")
        instructions = template.format(
            command_specific_instructions=command_specific_instructions,
            how_to_suggest_commands=how_to_suggest_commands,
        )
        return " ".join(instructions.replace("\n", " ").split())

    def get_response(self, prompt, command: Command):
        system_message = self._get_system_instructions(command)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

        if self.config.history_type == "chat":
            raise NotImplementedError("Chat history is not supported yet")
        elif self.config.history_type == "commands":
            messages.append(
                {
                    "role": "user",
                    "content": f"Here is the terminal history: {self.session_runtime.get_command_history(self.config.history_length)}",
                }
            )

        completion = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=0.2,  # Lower temperature for more precise responses
            top_p=0.7,
            max_tokens=2096,  # Reduced as we only need short commands
            stream=False,  # Changed to False for simpler handling
        )

        return completion.choices[0].message.content


def execute_llm_command(command: Command, config: LLMQueryArgs):
    ai_client = AIClient(config)
    prompt = config.query
    if prompt.strip():
        answer = ai_client.get_response(prompt, command)
        print(answer)
    else:
        answer = ai_client.get_response(prompt, command)
        print("No prompt provided.")
