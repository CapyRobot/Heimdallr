import os
import subprocess
import logging
import sys

from common import Color, colored, exit_with_error
from session import get_session_runtime, print_session_usage

LOGGER = logging.getLogger(__name__)


def _extract_exec_command(last_heim_command: dict, command_number: int) -> str:
    for line in last_heim_command["output"].split("\n"):
        if line.startswith(f"[{command_number}] "):
            command = line.split(f"[{command_number}] ")[1]
            return command
    LOGGER.debug(f"Last heim command:\n{last_heim_command}")
    return None


def _execute_command(command: str):
    """Runs a shell command, streaming stdout & stderr in real-time, using the user's default shell."""
    user_shell = os.environ.get("SHELL", "/bin/sh")  # Get user's shell, fallback to /bin/sh
    LOGGER.info(f"Executing command: {command} with shell: {user_shell}")
    print(
        colored(f"heimdallr > executing command: ({user_shell}) {colored(command, Color.GREEN)}", Color.BLUE),
        flush=True,
    )

    process = subprocess.Popen(
        command, shell=True, stdout=sys.stdout, stderr=sys.stderr, universal_newlines=True, executable=user_shell
    )
    process.communicate()
    sys.exit(process.returncode)  # Exit with the command's actual return code


def _get_last_heim_command() -> dict:
    session_runtime = get_session_runtime()
    if session_runtime is None:
        print_session_usage()
        exit_with_error("No session is active.", LOGGER)
    cmd_history = session_runtime.get_command_history(None)
    for cmd in reversed(cmd_history):
        # find last heim command that is not an exec or session command
        if "heim" in cmd["command"] and not (
            "--exec" in cmd["command"] or "-e" in cmd["command"] or "heim_session" in cmd["command"]
        ):
            LOGGER.debug(f"Found last heim command: {cmd}")
            return cmd
    LOGGER.debug(f"Command history:\n{cmd_history}")
    exit_with_error("No Heimdallr command found in session history.", LOGGER)


def execute(command_number: int):
    assert command_number > 0, "Command number must be greater than 0"

    last_heim_command = _get_last_heim_command()
    command = _extract_exec_command(last_heim_command, command_number)
    if command is None:
        exit_with_error(
            f"Command of number {command_number} not found in output:\n{last_heim_command['output']}", LOGGER
        )
    _execute_command(command)


if __name__ == "__main__":
    _execute_command("ls -l asd")
