# Heimdallr

Heimdallr, the watchman of the gods, is also an AI CLI tool.

## Installation and Setup

The installation script will create a virtual environment and install the necessary dependencies in the project directory.
Note that the project directory cannot be deleted after installation.

```bash
cd path/to/heimdallr
./install.sh
```

Create a `.env` file in the project directory with your OpenAI API key.

```bash
OPENAI_API_KEY="..."
```

Customize the [config.json](./config.json) to match your OpenAI API base URL and available models.

## Usage

See `heimdallr --help` for more information.

Sample usage:
```bash
erocha@erocha-mlt:~$ heimdallr suggest "get GPU info"
system_profiler SPDisplaysDataType
```

## TODO

See [use cases](./docs/use_case.md)
