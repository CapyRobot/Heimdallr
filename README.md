# Heimdallr (Heim)

Heimdallr, the watchman of the gods, is also an AI CLI tool.

## Installation and Setup

The installation script will create a virtual environment and install the necessary dependencies in the project directory.
Note that the project directory cannot be deleted after installation as of now we use symlinks pointing to the project directory.

```bash
cd path/to/heimdallr
./install.sh
```

Create a `.env` file in the project directory with your OpenAI API key.

```bash
OPENAI_API_KEY="..."
```

Customize the [config.json](./config.json) to match your OpenAI API base URL and available models.

## Usage examples

See `heim --help` for more information.

Ask Heim to suggest a command to get the GPU info:
```bash
erocha@erocha-mlt:~$ heim suggest "get GPU info"
[1] system_profiler SPDisplaysDataType
```

Ask Heimdallr a question:
```bash
erocha@erocha-mlt:~$ heim answer "what is the capital of France?"
The capital of France is Paris.
```

Include terminal history as context:
```bash
erocha@erocha-mlt:~$ source heim_session start  # start a session, this can be added to your .bashrc/.zshrc

... executed commands are logged ...

erocha@erocha-mlt:~$ my_command
ERROR: ...
erocha@erocha-mlt:~$ heim answer --history 1-commands "help" # include last 1 command as context
It seems... heim answer ...

erocha@erocha-mlt:~/dev/heimdallr$ heim_session status
heimdallr > Session 2025-03-16-16-26-40 is active.
heimdallr > Session history: /Users/erocha/.cache/heimdallr/sessions/session_2025-03-16-16-26-40.log
heimdallr > History size: 368 lines, 13 commands, 20.8K
...
erocha@erocha-mlt:~$ source heim_session stop
```

Piping data to Heimdallr:
```bash
erocha@erocha-mlt:~$ cat /my/file/path | heim answer "explain the content of the file"
...

erocha@erocha-mlt:~$ cat /my/file/path | heim answer "reformat the content to a more readable format"
...
```
