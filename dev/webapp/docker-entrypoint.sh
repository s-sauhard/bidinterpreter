#!/bin/bash

cd /app/

# Apply database migrations
echo "Checking for database migrations"
python manage.py makemigrations

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

echo "Starting background service"
python manage.py process_tasks &

# Start server
echo "Starting server"
python -u manage.py runserver 0.0.0.0:8002
