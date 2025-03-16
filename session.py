import json
import os
import logging

from common import Color, colored
from config import SessionAction

LOGGER = logging.getLogger(__name__)

"""
Sessions are managed by the session.sh script.
"""


# Session Runtime - to be used by other commands to interact with the active session


def is_active() -> bool:
    session_id = os.environ.get("HEIMDALLR_SESSION_ID")
    if session_id is None:
        LOGGER.debug("No session ID found")
        return False
    LOGGER.debug(f"Session {session_id} is active")
    return True


def extract_commands_from_session_log(file_path: str) -> list[dict]:
    with open(file_path, "r") as f:
        lines = f.readlines()
        commands = []
        parsing = None

        def empty_command():
            return {
                "command": None,
                "output": "",
                "start timestamp": None,
                "working directory": None,
            }

        cmd = empty_command()
        for line in lines:
            # ignore iterm2 escape sequences
            # e.g., ]633;E;;378ffb94-ac7d-4776-b99d-f0aef65636fd]633;C]633;D]633;P;Cwd=/Users/erocha/dev/heimdallr
            # https://iterm2.com/documentation-escape-codes.html
            if line.startswith("]633;"):
                continue

            if line.startswith("$"):
                parsing = "command"
                cmd["command"] = line[2:]
            elif parsing == "command":
                if line.strip().startswith("metadata: "):
                    metadata = line.strip().split("metadata: ")[1].split(",")
                    cmd["working directory"] = metadata[0].strip()
                    cmd["start timestamp"] = metadata[1].strip()
                    parsing = "output"
                else:
                    cmd["command"] += line
            elif parsing == "output":
                if line.strip().startswith("--------------"):
                    parsing = None
                    commands.append(cmd)
                    cmd = empty_command()
                else:
                    cmd["output"] += line
        return commands


# # TODO: does openai have a schema for this?
# @dataclass
# class ChatMessage:
#     role: str
#     content: str


# class ChatLog:
#     def __init__(self, file_path: str):
#         self.file_path = file_path

#     def get_log(self) -> list[ChatMessage]:
#         with open(self.file_path, "r") as f:
#             history = json.load(f)
#             return [ChatMessage(message["role"], message["content"]) for message in history]

#     def add_message(self, message: ChatMessage):
#         with open(self.file_path, "r") as f:
#             history = json.load(f)
#         history.append({"role": message.role, "content": message.content})
#         with open(self.file_path, "w") as f:
#             json.dump(history, f)

#     def get_number_of_messages(self) -> int:
#         with open(self.file_path, "r") as f:
#             history = json.load(f)
#             return len(history)


class Runtime:
    def __init__(self):
        assert is_active(), "No active session"

        self.commands_file = os.environ.get("HEIMDALLR_SESSION_CMDS_FILE")
        self.chat_file = os.environ.get("HEIMDALLR_SESSION_CHAT_FILE")

        self.session_id = os.environ.get("HEIMDALLR_SESSION_ID")
        # self.chat_log = ChatLog(os.environ.get("HEIMDALLR_SESSION_CHAT_HISTORY_FILE"))

    def get_command_history(self, number_of_commands: int | None) -> list[dict]:
        all_cmds = extract_commands_from_session_log(self.commands_file)
        if number_of_commands is None:
            return all_cmds
        return all_cmds[-number_of_commands:]

    # def get_chat_log(self) -> ChatLog:
    #     return self.chat_log


def get_session_runtime() -> Runtime | None:
    if not is_active():
        return None
    return Runtime()


def execute_session_command(_: SessionAction):
    print(colored(f"heimdallr > deprecated. Use the shell script instead.", Color.RED))
    print(colored(f"$ source heim_session start", Color.RED))
    print(colored(f"$ source heim_session stop", Color.RED))
    print(colored(f"$ heim_session status", Color.RED))


if __name__ == "__main__":
    # pretty print the commands
    runtime = Runtime()
    commands = runtime.get_command_history(None)
    print(json.dumps(commands, indent=4))
