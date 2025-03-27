#!/usr/bin/env zsh

# This is an execution helper for the session.sh script using zsh.
# In here, we add the zsh shebang line and platform-specific features.

if [ -z "$ZSH_VERSION" ]; then
    echo "zsh is required to use this script."
    return 1
fi

TOP_IS_SOURCED=$([[ $ZSH_EVAL_CONTEXT == *:file:* ]] && echo true || echo false)
is_sourced() {
    [[ $TOP_IS_SOURCED == true ]]
}

_set-zsh-hook() {
    local hook_name="$1"
    local hook_function="$2"
    autoload -Uz add-zsh-hook
    add-zsh-hook -d "$hook_name" "$hook_function"
    add-zsh-hook "$hook_name" "$hook_function"
}

set-preexec-hook() {
    _set-zsh-hook preexec "$1"
}

set-precmd-hook() {
    _set-zsh-hook precmd "$1"
}

cleanup-hooks() {
    autoload -Uz add-zsh-hook
    add-zsh-hook -d preexec my_preexec 2>/dev/null
    add-zsh-hook -d precmd my_precmd 2>/dev/null
    unset preexec_functions
    unset precmd_functions
}

# We must always source the session.sh script so that it runs in the current shell
# where the functions above are defined.
THIS_SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${(%):-%x}")")" && pwd)"
source "$THIS_SCRIPT_DIR/session.sh" "$@"
