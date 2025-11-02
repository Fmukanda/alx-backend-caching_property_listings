#!/bin/bash

set -e

echo "Waiting for PostgreSQL and Redis to be ready..."

# Wait for PostgreSQL
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (for development)
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
    print('Superuser created: admin/admin');
else:
    print('Superuser already exists');
"

# Seed sample properties if none exist
echo "Seeding sample properties..."
python manage.py shell -c "
from properties.models import Property;
if Property.objects.count() == 0:
    properties = [
        {
            'title': 'Luxury Villa in Miami',
            'description': 'Beautiful 4-bedroom villa with ocean view and private pool',
            'price': 1250000.00,
            'location': 'Miami, FL'
        },
        {
            'title': 'Downtown Apartment',
            'description': 'Modern 2-bedroom apartment in city center with amazing views',
            'price': 450000.00,
            'location': 'New York, NY'
        },
        {
            'title': 'Country House', 
            'description': 'Spacious country house with large garden and peaceful surroundings',
            'price': 320000.00,
            'location': 'Austin, TX'
        }
    ]
    for prop in properties:
        Property.objects.create(**prop)
    print('Sample properties created');
else:
    print('Properties already exist in database');
"

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --access-logfile - \
    --error-logfile - \
    alx-backend-caching_property_listings.wsgi:application