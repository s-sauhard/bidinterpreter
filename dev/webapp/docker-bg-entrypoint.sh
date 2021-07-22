#!/bin/bash

cd /app/

# Apply database migrations
# echo "Checking for database migrations"
# python manage.py makemigrations

# Apply database migrations
# echo "Apply database migrations"
# python manage.py migrate

# Start Python Kafka worker
# echo "Starting Kafka Python worker"
# /app/start-worker.sh &

# Setting environment variables
source .env

# Start server
echo "Starting background server"
python manage.py process_tasks
