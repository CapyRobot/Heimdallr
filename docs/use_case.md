# What do I want to achieve?

## Basic usage

Ask Heimdallr to suggest a command.

```bash
$ heimdallr suggest "how to create a new directory called 'test'"
(1)
mkdir test
```

Ask Heimdallr a question.

```bash
$ heimdallr answer "why is the sky blue?"
> The sky is blue because of the Rayleigh scattering of sunlight by the atmosphere.
```

The difference between `answer` and `suggest` is the instructions given to the model.
For `answer`, the model will give a detailed **unstructured** answer.
For `suggest`, the model will be instructed to give a command suggestion(s) without explanation unless the user asks for it.

## Chat history as context

Add previous chat history as context.

```bash
$ heimdallr answer "why is the sky blue?"
> The sky is blue because of the Rayleigh scattering of sunlight by the atmosphere.
$ heimdallr answer --history chat "more details"
> ... more details ...
```

## Add previous terminal data as context

Add last N lines of terminal history as context.

```bash
$ command
ERROR: ...
$ heimdallr answer --history 2-lines "Help"
> Explanation of the error... suggestion ...
$ heimdallr suggest --history 4-lines "Fix the error"
(1)
suggestion
```

Add last N commands (+ output) as context.

```bash
$ command
ERROR: ...
$ heimdallr answer --history 1-command "Help"
> Explanation of the error...
```

## Add other data as context

```bash
$ heimdallr answer --context file/path "Give me a summary"
> Explanation of the error...
```

Extension: multiple files, directories, etc.

## Execute suggestions

```bash
$ heimdallr suggest "I want to create a new directory called 'test'"
(1)
mkdir test
$ heimdallr exec 1
# heimdallr will execute the command and show the output
```

# How will I achieve this?

## No context needed

If no context is needed, Heimdallr will simply send a request to the model and return the response. No more.

## File context

Load file to memory. Add to LLM request.

## Previous terminal history

- Last N lines.
- Last N commands.
- Chat history.

All of these depend on the capacity to access the terminal history. To do this, we will

1. Use `script` to record the terminal history into a file.
2. Save the chat history to another file.

A Session is started and stopped by the user.

```bash
# Start a session
$ heimdallr session
# same as `heimdallr session start`, `start` can be omitted
# in here we start recording the history...

$ heimdallr session status
> ... print session info ...

# Commands that use history will check if a session is active and use that as context, if not, error out

$ heimdallr session end

$ heimdallr session status
> No active session. Run `heimdallr session` to start a new session.
```

Starting a session:

1. Assert that there isn't an active session.
2. Cleanup old session files (policy: older than 7 days - or as configured)
3. Create a new session.
    3.1 Set env variables
    3.2 Create session directory in {heimdallr_data_dir}/session_{session_id}/
    3.3 Start recording the terminal history into {heimdallr_data_dir}/session_{session_id}/terminal_history.txt
    3.4 Start recording the chat history into {heimdallr_data_dir}/session_{session_id}/chat_history.json

Ending a session:

1. Assert that there is an active session.
2. Stop recording.
3. Move session files to {heimdallr_data_dir}/archive/session_{session_id}
4. Restore env variables
