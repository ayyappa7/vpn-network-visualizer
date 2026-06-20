#!/bin/sh
set -e

echo "Running database migrations..."
max_retries=5
retry_delay=2
retry=0

until python manage.py migrate --noinput || [ $retry -ge $max_retries ]; do
    retry=$((retry + 1))
    echo "Migration failed (attempt $retry/$max_retries), retrying in ${retry_delay}s..."
    sleep $retry_delay
done

if [ $retry -ge $max_retries ]; then
    echo "Failed to apply migrations after $max_retries attempts"
    exit 1
fi

echo "Starting application..."
exec "$@"