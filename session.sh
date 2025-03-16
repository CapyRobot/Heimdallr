#!/usr/bin/env zsh

# only zsh is supported for now
# TODO: add support for bash
if [ -z "$ZSH_VERSION" ]; then
    echo_red "zsh is required to use heimdallr_session"
    return 1
fi

LOG_DIR="$HOME/.cache/heimdallr/sessions"
ARCHIVE_DIR="$LOG_DIR/archive"
mkdir -p "$LOG_DIR"
mkdir -p "$ARCHIVE_DIR"

echo_red() {
    echo $1
}

echo_blue() {
    echo $1
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
        echo_blue "heimdallr > deleting sessions older than 7 days..."
        find "$ARCHIVE_DIR" -type f -mtime +7 -exec sh -c 'echo "Deleting $1" && rm -rf "$1"' _ {} \;
    fi
}
cleanup_old_sessions

start_session() {
    if is_session_active; then
        echo_red "Session already active. Stop it first before starting a new one."
        echo_red "Run 'source heimdallr_session stop' to stop the current session."
        echo_red "See 'heimdallr_session status' for more session information."
        return
    fi

    session_id=$(date '+%Y-%m-%d-%H-%M-%S')
    log_path="$LOG_DIR/session_$session_id.log"

    export HEIMDALLR_SESSION_ID="$session_id"
    export HEIMDALLR_SESSION_CMDS_FILE="$log_path"
    export HEIMDALLR_SESSION_CHAT_FILE="$log_path"
    echo_blue "heimdallr > Starting session $session_id..."
    echo_blue "heimdallr > Session history: $log_path"

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
    }

    # Enable `preexec` and `precmd` hooks
    autoload -Uz add-zsh-hook
    add-zsh-hook -d preexec my_preexec 2>/dev/null
    add-zsh-hook preexec my_preexec

    # Start logging output - add indentation
    exec > >(tee -a "$log_path") 2>&1
}

stop_session() {
    log_stop() {
        echo "----------------------------------------"
        echo "Session ended"
        echo "(timestamp: $(date '+%Y-%m-%d %H:%M:%S'))"
    }

    # Restore output to normal (detach from tee)
    exec >/dev/tty 2>&1

    # Remove logging hooks
    autoload -Uz add-zsh-hook
    add-zsh-hook -d preexec my_preexec 2>/dev/null

    # Clear preexec_functions if used
    unset preexec_functions

    mv "$HEIMDALLR_SESSION_CMDS_FILE" "$ARCHIVE_DIR/session_$HEIMDALLR_SESSION_ID.log"
    log_stop >> "$ARCHIVE_DIR/session_$HEIMDALLR_SESSION_ID.log"

    echo_blue "heimdallr > Session $HEIMDALLR_SESSION_ID stopped."
    echo_blue "heimdallr > Archived session at $ARCHIVE_DIR/session_$HEIMDALLR_SESSION_ID.log"

    unset HEIMDALLR_SESSION_ID
    unset HEIMDALLR_SESSION_CMDS_FILE
    unset HEIMDALLR_SESSION_CHAT_FILE
}

report_status() {
    if is_session_active; then
        echo_blue "heimdallr > Session $HEIMDALLR_SESSION_ID is active."
        echo_blue "heimdallr > Session history: $HEIMDALLR_SESSION_CMDS_FILE"
        lines=$(wc -l < "$HEIMDALLR_SESSION_CMDS_FILE" | tr -d ' ')
        cmd_count=$(grep -c "^$ " "$HEIMDALLR_SESSION_CMDS_FILE" || echo 0)
        size=$(ls -lh "$HEIMDALLR_SESSION_CMDS_FILE" | awk '{print $5}')
        echo_blue "heimdallr > History size: $lines lines, $cmd_count commands, $size"
    else
        echo_red "heimdallr > No active session."
    fi
}

if [ "$1" = "start" ]; then
    start_session
elif [ "$1" = "stop" ]; then
    stop_session
elif [ "$1" = "status" ]; then
    report_status
else
    echo "Usage: $0 start | stop | status"
fi
