#!/usr/bin/env bash

echo "Cleaning Docker..."
docker system prune -af
docker volume prune -f

echo "Disk usage:"
df -h /