# Heimdallr (Heim)

Heimdallr, the watchman of the gods, is also an AI CLI tool.

## Usage examples

See `heim --help` for more information.

Ask Heimdallr any question:
```bash
erocha@erocha-mlt:~$ heim what is the capital of France?
The capital of France is Paris.
```

Ask Heim to suggest a command to get the GPU info. `--suggest` (`-s`) will instruct Heim to suggest a command without explanations.
```bash
erocha@erocha-mlt:~$ heim --suggest get GPU info
[1] system_profiler SPDisplaysDataType
```

Include context:
```bash
erocha@erocha-mlt:~$ heim -f /my/file/path -- explain the content of the file
...
erocha@erocha-mlt:~$ cat /my/file/path | heim explain the content of the file
...
erocha@erocha-mlt:~$ heim --input -- explain this error message
input context > ... user input ...
```

Include terminal history as context:
```bash
erocha@erocha-mlt:~$ heim_session

Usage:
    source heim_session start | stop | restart
    heim_session status | history

erocha@erocha-mlt:~$ source heim_session start  # start a session, this can be added to your .bashrc/.zshrc

... executed commands are logged ...

erocha@erocha-mlt:~$ my_command
ERROR: ...
erocha@erocha-mlt:~$ heim --commands 1 -- explain this error # include last 1 command as context
It seems... heim answer ...

erocha@erocha-mlt:~$ heim --chat all -- explain this error # include all chat history as context
It seems... heim answer ...

erocha@erocha-mlt:~$ heim_session status
heimdallr > Session 2025-03-16-16-26-40 is active.
heimdallr > Session history: /Users/erocha/.cache/heimdallr/sessions/session_2025-03-16-16-26-40.log
heimdallr > History size: 368 lines, 13 commands, 20.8K
...
erocha@erocha-mlt:~$ source heim_session stop  # stop the session and archive the log files
```

Execute a suggestion:
```bash
erocha@erocha-mlt:~$ heim --suggest -- get GPU info. provide multiple suggestions.
[1] system_profiler SPDisplaysDataType
[2] lspci | grep -i nvidia
erocha@erocha-mlt:~$ heim --exec 2  # execute the second suggestion
... heim will execute the command and show the output ...
```

## Installation and Setup

> The installation is currently hacky and should be improved. It will simply download requirements and create symlinks in `/usr/local/bin` that point to the project directory.

The installation script will create a virtual environment and install the necessary dependencies in the project directory.
Note that the project directory cannot be deleted after installation as of now we use symlinks pointing to the project directory.

```bash
cd path/to/heimdallr
./install.sh
```

Create a `.env` file in the project directory with your OpenAI API key or export the key as an environment variable of same name.

```bash
OPENAI_API_KEY="..."
```

Customize the [config.json](./config.json) to match your OpenAI API base URL and available models.

# TODO / Help wanted

1. Refactor project structure to align with the standard python project structure.
2. Improve installation (see note above).
3. Add linux support (currently only MacOS/zsh is supported).
