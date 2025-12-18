#!/bin/bash

# Script to copy a LICENSE file to all main directories (immediate subdirectories)
# under a specified root path.

# --- Configuration ---
# Default source LICENSE file (can be overridden with -l)
DEFAULT_LICENSE_FILE="/opt/docker/odoo18/LICENSE" # Assuming this is the main license
# Default target root directory (e.g., your addons directory)
DEFAULT_TARGET_ROOT_DIR="/opt/docker/odoo18/ez_addons"

# --- Functions ---
usage() {
    echo "Usage: $0 [-l <license_file>] [-t <target_root_dir>]"
    echo "  -l <license_file>      Path to the LICENSE file to copy."
    echo "                         (Default: $DEFAULT_LICENSE_FILE)"
    echo "  -t <target_root_dir>   Path to the root directory containing the main directories."
    echo "                         (Default: $DEFAULT_TARGET_ROOT_DIR)"
    echo "  -h                     Show this help message."
    exit 1
}

# --- Argument Parsing ---
LICENSE_FILE="$DEFAULT_LICENSE_FILE"
TARGET_ROOT_DIR="$DEFAULT_TARGET_ROOT_DIR"

while getopts "l:t:h" opt; do
    case ${opt} in
        l )
            LICENSE_FILE="$OPTARG"
            ;;
        t )
            TARGET_ROOT_DIR="$OPTARG"
            ;;
        h )
            usage
            ;;
        \? )
            usage
            ;;
    esac
done

# --- Validation ---
if [ ! -f "$LICENSE_FILE" ]; then
    echo "Error: LICENSE file '$LICENSE_FILE' not found."
    exit 1
fi

if [ ! -d "$TARGET_ROOT_DIR" ]; then
    echo "Error: Target root directory '$TARGET_ROOT_DIR' not found."
    exit 1
fi

# --- Main Logic ---
echo "Source LICENSE file: $LICENSE_FILE"
echo "Target root directory: $TARGET_ROOT_DIR"
echo "Copying LICENSE to main directories..."

# Use find to get the list of target directories
# -maxdepth 1: Don't go into sub-subdirectories
# -mindepth 1: Don't include the TARGET_ROOT_DIR itself
# -name .git -prune: If a directory is named .git, don't process it further (and don't print it due to -o)
# -o: OR operator
# -type d: Select only directories
# -print: Print the found directory path
find "$TARGET_ROOT_DIR" -maxdepth 1 -mindepth 1 -name .git -prune -o -type d -print | while IFS= read -r main_dir; do
    echo "Copying to ${main_dir}/LICENSE"
    cp "$LICENSE_FILE" "${main_dir}/LICENSE"
done

echo "Operation complete."