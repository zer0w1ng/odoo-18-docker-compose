# Use the official Odoo 18 image as the base
FROM postgres:17

# Switch to root to install system packages
USER root

# Update the package list and install paramiko
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgis postgresql-17-postgis-3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

