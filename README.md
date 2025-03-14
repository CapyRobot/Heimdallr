# Heimdallr

Heimdallr, the watchman of the gods, is also a CLI tool that uses AI to generate commands for the user.

## Installation and Setup

The installation script will create a virtual environment and install the necessary dependencies in the project directory.
Note that the project directory cannot be deleted after installation.

```bash
cd path/to/heimdallr
./install.sh
```

Create a `.env` file in the project directory with the following variables or set them in your environment.

```bash
OPENAI_API_KEY="..."
OPENAI_BASE_URL="https://api.openai.com/v1"
```

## Usage

See `heimdallr --help` for more information.

Sample usage:
```bash
erocha@erocha-mlt:~$ heimdallr    
Heim > What command are you looking for?
> get GPU info                
Heim >
system_profiler SPDisplaysDataType
```

## TODO

See [use cases](./docs/use_case.md)
