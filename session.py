from dataclasses import dataclass
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta
import logging
from strip_ansi import strip_ansi

from common import Color, colored
from config import SessionAction

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.expanduser("~/.cache/heimdallr/sessions")
ARCHIVE_DIR = os.path.expanduser("~/.cache/heimdallr/sessions/archive")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR, exist_ok=True)


def _check_prerequisites():
    script_paths = ["/usr/bin/script", "/bin/script", "/usr/local/bin/script"]
    if not any(os.path.exists(path) for path in script_paths):
        raise ValueError("script command not found")

    if os.environ.get("HEIMDALLR_SESSION_ID"):
        LOGGER.error(
            "There is an active session already running. To exit it, run `exit`."
            " See the env vars `HEIMDALLR_SESSION_*` for more information."
        )
        raise ValueError("There is an active session already running.")


def _cleanup_old_sessions():
    # TODO: add policy config
    for dir in os.listdir(ARCHIVE_DIR):
        dir_path = os.path.join(ARCHIVE_DIR, dir)
        if os.path.isdir(dir_path):
            # get the timestamp from the directory name
            timestamp_str = dir.split("_")[-1]
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d-%H-%M-%S")
            if timestamp < datetime.now() - timedelta(days=7):
                shutil.rmtree(dir_path)


def _start_session():
    _cleanup_old_sessions()
    _check_prerequisites()

    session_id = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    session_dir = os.path.join(LOG_DIR, f"session_{session_id}")
    archive_dir = os.path.join(ARCHIVE_DIR, f"session_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    terminal_history_file = os.path.join(session_dir, "terminal_history.txt")
    chat_history_file = os.path.join(session_dir, "chat_history.json")

    with open(chat_history_file, "w") as f:
        f.write("[]")

    # Export the log file name as an environment variable
    os.environ["HEIMDALLR_SESSION_ID"] = session_id
    os.environ["HEIMDALLR_SESSION_TERMINAL_HISTORY_FILE"] = terminal_history_file
    os.environ["HEIMDALLR_SESSION_CHAT_HISTORY_FILE"] = chat_history_file

    print(colored(f"heimdallr > Starting session {session_id}...", Color.BLUE))
    print(colored(f"heimdallr > Terminal history: {terminal_history_file}", Color.BLUE))
    print(colored(f"heimdallr > Chat history: {chat_history_file}", Color.BLUE))

    # Start the script session in the current terminal
    subprocess.run(
        f"export SCRIPT_LOG_FILE={terminal_history_file}; exec script -qF {terminal_history_file}",
        shell=True,
        executable="/bin/bash",
    )

    print(colored(f"heimdallr > Session {session_id} ended.", Color.BLUE))
    print(colored(f"heimdallr > Archiving session...", Color.BLUE))
    shutil.move(session_dir, archive_dir)
    print(colored(f"heimdallr > Session archived at {archive_dir}.", Color.BLUE))


def _report_status():
    session_id = os.environ.get("HEIMDALLR_SESSION_ID")
    terminal_history_file = os.environ.get("HEIMDALLR_SESSION_TERMINAL_HISTORY_FILE")
    chat_history_file = os.environ.get("HEIMDALLR_SESSION_CHAT_HISTORY_FILE")

    terminal_history_number_of_lines = TerminalLog(terminal_history_file).get_number_of_lines()
    chat_history_number_of_messages = ChatLog(chat_history_file).get_number_of_messages()

    print(colored(f"heimdallr > Session {session_id} is active.", Color.BLUE))
    print(
        colored(
            f"heimdallr > Terminal history: {terminal_history_file} ({terminal_history_number_of_lines} lines)",
            Color.BLUE,
        )
    )
    print(
        colored(
            f"heimdallr > Chat history: {chat_history_file} ({chat_history_number_of_messages} messages)", Color.BLUE
        )
    )


def execute_session_command(action: SessionAction):
    if action == "start":
        _start_session()
        return

    # the commands below are only relevant if there is an active session
    if not is_active():
        print(colored("heimdallr > No active session.", Color.RED))
        return

    if action == "status":
        _report_status()
    elif action == "end":
        # it is harder than I expected to implement this.
        # `exit` is good enough for now.
        print(colored("heimdallr > `session end` not implemented yet.", Color.RED))
        print(colored("heimdallr > use `exit` to end the session instead.", Color.RED))


###################################################################################################
# Session Runtime - to be used by other commands to interact with the active session


def is_active() -> bool:
    return os.environ.get("HEIMDALLR_SESSION_ID") is not None


class TerminalLog:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_last_n_lines(self, n: int) -> list[str]:
        with open(self.file_path, "r") as f:
            return f.readlines()[-n:]

    def get_last_n_commands(self, n: int) -> list[str]:
        raise NotImplementedError("Not implemented")

    def get_number_of_lines(self) -> int:
        with open(self.file_path, "r") as f:
            return len(f.readlines())


# TODO: does openai have a schema for this?
@dataclass
class ChatMessage:
    role: str
    content: str


class ChatLog:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_log(self) -> list[ChatMessage]:
        with open(self.file_path, "r") as f:
            history = json.load(f)
            return [ChatMessage(message["role"], message["content"]) for message in history]

    def add_message(self, message: ChatMessage):
        with open(self.file_path, "r") as f:
            history = json.load(f)
        history.append({"role": message.role, "content": message.content})
        with open(self.file_path, "w") as f:
            json.dump(history, f)

    def get_number_of_messages(self) -> int:
        with open(self.file_path, "r") as f:
            history = json.load(f)
            return len(history)


class Runtime:
    def __init__(self):
        assert is_active(), "No active session"

        self.session_id = os.environ.get("HEIMDALLR_SESSION_ID")
        self.terminal_log = TerminalLog(os.environ.get("HEIMDALLR_SESSION_TERMINAL_HISTORY_FILE"))
        self.chat_log = ChatLog(os.environ.get("HEIMDALLR_SESSION_CHAT_HISTORY_FILE"))

    def get_terminal_log(self) -> TerminalLog:
        return self.terminal_log

    def get_chat_log(self) -> ChatLog:
        return self.chat_log


if __name__ == "__main__":
    action = input("Enter a command: ")
    execute_session_command(action)
