#!/bin/sh
# DictCreator - Launcher Script for Linux, macOS & iOS iSH
set -e

# Move to the script's directory
cd "$(dirname "$0")"

# Check if python3 is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "\033[1;31m[Error] Python 3 is not installed!\033[0m"
    if [ -f /etc/alpine-release ] || [ -e /dev/location ]; then
        echo "\033[1;33mTo install Python on iSH (Alpine Linux), run:\033[0m"
        echo "  apk update && apk add python3"
    else
        echo "Please install python3 using your package manager."
    fi
    exit 1
fi

# Map simple shorthand commands (e.g. ./run.sh web -> python3 main.py --web)
case "$1" in
    web|--web|-w)
        shift
        exec python3 main.py --web "$@"
        ;;
    cli|--cli|-c)
        shift
        exec python3 main.py --cli "$@"
        ;;
    manage|--manage|-m)
        shift
        exec python3 main.py --manage "$@"
        ;;
    *)
        exec python3 main.py "$@"
        ;;
esac
