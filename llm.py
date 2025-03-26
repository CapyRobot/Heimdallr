from dataclasses import dataclass
import platform
import logging
import os
import sys
from openai import OpenAI

from common import exit_with_error
from config import LLMQueryArgs, Command
from session import get_session_runtime, print_session_usage

LOGGER = logging.getLogger(__name__)

############################################################################
# Environment info / Context


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


def get_piped_input() -> str | None:
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def get_piped_input_message() -> dict | None:
    piped_input = get_piped_input()
    if piped_input is None:
        return None
    return {"role": "user", "content": f"User provided data: {piped_input}"}


def get_file_content(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def get_multiline_input() -> str:
    print("Input your text. Type 'EOF' on a new line when done:", flush=True)
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "EOF":
                break
            lines.append(line)
        except EOFError:
            break
    print(f"--- EOF received ---", flush=True)
    user_input = '\n'.join(lines)
    LOGGER.debug(f"Multiline user input: {user_input}")
    return user_input


############################################################################


class AIClient:
    def __init__(self, llm_query_args: LLMQueryArgs):
        LOGGER.debug(f"Environment info: {ENV_INFO}")
        self.config = llm_query_args
        self.client = OpenAI(base_url=llm_query_args.openai_base_url, api_key=llm_query_args.openai_api_key)
        self.session_runtime = get_session_runtime()
        if self.session_runtime is None:
            for context in llm_query_args.context:
                if context.type == "chat" or context.type == "commands":
                    print_session_usage()
                    exit_with_error("Terminal history is not supported when no session is active.", LOGGER)

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
        messages = [{"role": "system", "content": self._get_system_instructions(command)}]

        piped_input_message = get_piped_input_message()
        if piped_input_message is not None:
            messages.append(piped_input_message)

        for context in self.config.context:
            if context.type == "chat":
                raise NotImplementedError("Chat history is not supported yet")
            elif context.type == "commands":
                messages.append(
                    {
                        "role": "user",
                        "content": f"Here is the terminal history: {self.session_runtime.get_command_history(context.data)}",
                    }
                )
            elif context.type == "file":
                messages.append(
                    {
                        "role": "user",
                        "content": f"User provided data from file {context.data}: {get_file_content(context.data)}",
                    }
                )
            elif context.type == "input":
                data = get_multiline_input()
                messages.append({"role": "user", "content": f"User provided input: {data}"})

        messages.append({"role": "user", "content": prompt})

        print("... thinking ...", flush=True)
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
        exit_with_error("No prompt provided.", LOGGER)
