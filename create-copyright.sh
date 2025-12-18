# First, define the source file and target parent directory for clarity
SOURCE_LICENSE_FILE="COPYRIGHT"
TARGET_PARENT_DIR="/opt/docker/odoo18/ez_addons"

# Find 1st level directories under TARGET_PARENT_DIR and copy the SOURCE_LICENSE_FILE into each
find "${TARGET_PARENT_DIR}" -maxdepth 1 -mindepth 1 -type d -exec cp "${SOURCE_LICENSE_FILE}" {} \;
