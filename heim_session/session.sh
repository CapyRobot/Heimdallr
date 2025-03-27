
# This script requires the following platform-specific functions to be defined prior to being used:
# - is_sourced: returns true if the script is being sourced
# - set-preexec-hook: sets a function as the preexec hook
# - set-precmd-hook: sets a function as the precmd hook
# - cleanup-hooks: removes the preexec and precmd hooks
assert_required_functions_exist() {
    assert_function_exists() {
        fn_name="$1"
        if ! command -v "$fn_name" >/dev/null 2>&1; then
                    echo "Required function '$func' not found."
                    echo "Use the entrypoint scripts provided, do not use this script directly."
                    exit 1
        fi
    }

    local required_functions=("is_sourced" "set-preexec-hook" "set-precmd-hook" "cleanup-hooks")
    for func in "${required_functions[@]}"; do
        assert_function_exists "$func"
    done
}
assert_required_functions_exist

LOG_DIR="$HOME/.cache/heimdallr/sessions"
ARCHIVE_DIR="$LOG_DIR/archive"
mkdir -p "$LOG_DIR"
mkdir -p "$ARCHIVE_DIR"

echo_heimdallr() {
    echo "heimdallr > $1"
}

assert_script_is_sourced() {
    if ! is_sourced; then
        echo_heimdallr "This script must be sourced, not executed"
        exit 1
    fi
}

is_session_active() {
    if [ -z "$HEIMDALLR_SESSION_ID" ]; then
        return 1
    fi
    return 0
}

cleanup_old_sessions() {
    # TODO: add policy config
    # Deleting sessions older than 7 days and echoing the deleted sessions
    # if there are sessions older than 7 days
    if [ -n "$(find "$ARCHIVE_DIR" -type f -mtime +7)" ]; then
        echo_heimdallr "deleting sessions older than 7 days..."
        find "$ARCHIVE_DIR" -type f -mtime +7 -exec sh -c 'echo "Deleting $1" && rm -rf "$1"' _ {} \;
    fi
}
cleanup_old_sessions

# Returns true if the command is TTY-sensitive or uses a terminal UI,
# and should be excluded from output redirection to avoid breaking behavior.
_should_skip_output_logging() {
    local cmd="$1"
    [[ "$cmd" =~ ^(scp|ssh|rsync|sftp|top|htop|less|more|man|vim|nano|emacs|watch|tmux|screen|fzf|peco|dialog|whiptail|sshpass) ]]
}

start_session() {
    assert_script_is_sourced

    if is_session_active; then
        echo_heimdallr "Session already active. Stop it first before starting a new one."
        echo_heimdallr "Run 'source heimdallr_session stop' to stop the current session."
        echo_heimdallr "See 'heimdallr_session status' for more session information."
        return
    fi

    session_id=$(date '+%Y-%m-%d-%H-%M-%S')
    log_path="$LOG_DIR/session_$session_id.log"

    export HEIMDALLR_SESSION_ID="$session_id"
    export HEIMDALLR_SESSION_CMDS_FILE="$log_path"
    export HEIMDALLR_SESSION_CHAT_FILE="$log_path"
    echo_heimdallr "Starting session $session_id..."
    echo_heimdallr "Session history: $log_path"

    log_start() {
        echo "New session"
        echo "(timestamp: $(date '+%Y-%m-%d %H:%M:%S'))"
    }
    log_start >"$log_path"

    log_command() {
        echo
        echo "----------------------------------------"
        echo "$ $1"
        echo "metadata: $(pwd),$(date '+%Y-%m-%d %H:%M:%S')"
    }

    my_preexec() {
        log_command "$1" >>"$log_path"
        if _should_skip_output_logging "$1"; then
            echo_heimdallr "Disabling output tracking for TTY-sensitive command: $1"
            echo_heimdallr "This command's output will not be logged."
            exec >/dev/tty 2>&1
        fi
    }

    my_precmd() {
        # Restore output to tee in case it was disabled for a TTY-sensitive command
        exec >/dev/tty 2>&1
        exec > >(tee -a "$log_path") 2>&1
    }

    # Enable `preexec` and `precmd` hooks
    set-preexec-hook my_preexec
    set-precmd-hook my_precmd

    # Start logging output - add indentation
    exec > >(tee -a "$log_path") 2>&1
}

stop_session() {
    assert_script_is_sourced

    log_stop() {
        echo "----------------------------------------"
        echo "Session ended"
        echo "(timestamp: $(date '+%Y-%m-%d %H:%M:%S'))"
    }

    # Restore output to normal (detach from tee)
    exec >/dev/tty 2>&1

    # Remove logging hooks
    cleanup-hooks

    mv "$HEIMDALLR_SESSION_CMDS_FILE" "$ARCHIVE_DIR/session_$HEIMDALLR_SESSION_ID.log"
    log_stop >> "$ARCHIVE_DIR/session_$HEIMDALLR_SESSION_ID.log"

    echo_heimdallr "Session $HEIMDALLR_SESSION_ID stopped."
    echo_heimdallr "Archived session at $ARCHIVE_DIR/session_$HEIMDALLR_SESSION_ID.log"

    unset HEIMDALLR_SESSION_ID
    unset HEIMDALLR_SESSION_CMDS_FILE
    unset HEIMDALLR_SESSION_CHAT_FILE
}

report_status() {
    if is_session_active; then
        echo_heimdallr "Session $HEIMDALLR_SESSION_ID is active."
        echo_heimdallr "Session history: $HEIMDALLR_SESSION_CMDS_FILE"
        lines=$(wc -l < "$HEIMDALLR_SESSION_CMDS_FILE" | tr -d ' ')
        cmd_count=$(grep -c "^$ " "$HEIMDALLR_SESSION_CMDS_FILE" || echo 0)
        size=$(ls -lh "$HEIMDALLR_SESSION_CMDS_FILE" | awk '{print $5}')
        echo_heimdallr "History size: $lines lines, $cmd_count commands, $size"
    else
        echo_heimdallr "No active session."
    fi
}

report_history() {
    if is_session_active; then
        echo_heimdallr "Session $HEIMDALLR_SESSION_ID command history:"
        # replace "$ " with ">> " to not affect command history parsing later
        cat "$HEIMDALLR_SESSION_CMDS_FILE" | grep "^$ " | sed 's/^\$ />> /g'
    else
        echo_heimdallr "No active session."
    fi
}

print_usage() {
    echo
    echo "Usage:"
    echo "    source heim_session start | stop | restart"
    echo "    heim_session status | history"
    echo
}


if [ $# -eq 0 ]; then
    print_usage
    return 1
fi

if [ "$1" = "start" ]; then
    start_session
    return 0
elif [ "$1" = "stop" ]; then
    stop_session
    return 0
elif [ "$1" = "restart" ]; then
    stop_session
    clear
    start_session
    return 0
elif [ "$1" = "status" ]; then
    report_status
    return 0
elif [ "$1" = "history" ]; then
    report_history
    return 0
fi

echo_heimdallr "Invalid usage."
print_usage
return 1
