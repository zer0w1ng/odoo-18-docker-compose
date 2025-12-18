# Use the official Odoo 18 image as the base
FROM odoo:18

# Switch to root to install system packages
USER root

# Update the package list and install paramiko
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-paramiko && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch back to the 'odoo' user for security
USER odoo

