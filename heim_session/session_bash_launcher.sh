#! /usr/bin/env bash

# This is an execution helper for the session.sh script using bash.
# In here, we add the bash shebang line and platform-specific features.

if [ -z "$BASH_VERSION" ]; then
    echo "bash is required to use this script."
    return 1
fi

TOP_IS_SOURCED=$([[ $BASH_SOURCE == $0 ]] && echo false || echo true)
is_sourced() {
    [[ $TOP_IS_SOURCED == true ]]
}

set-preexec-hook() {
    local hook_function="$1"
    trap '$hook_function "$BASH_COMMAND"' DEBUG
}

set-precmd-hook() {
    local hook_function="$1"
    if [[ -z "$PROMPT_COMMAND" ]]; then
        PROMPT_COMMAND="$hook_function"
    else
        PROMPT_COMMAND="$hook_function; $PROMPT_COMMAND"
    fi
}

cleanup-hooks() {
    trap - DEBUG      # Remove the DEBUG trap
    PROMPT_COMMAND="" # Clear PROMPT_COMMAND
}

# We must always source the session.sh script so that it runs in the current shell
# where the functions above are defined.
THIS_SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
source "$THIS_SCRIPT_DIR/session.sh" "$@"
