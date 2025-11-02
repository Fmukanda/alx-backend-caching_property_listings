from django.core.management.base import BaseCommand
from properties.models import Property

class Command(BaseCommand):
    help = 'Seed the database with sample properties'

    def handle(self, *args, **options):
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
            },
            {
                'title': 'Beachfront Condo',
                'description': 'Luxurious beachfront condo with direct beach access',
                'price': 750000.00,
                'location': 'San Diego, CA'
            },
            {
                'title': 'Mountain Cabin',
                'description': 'Cozy cabin in the mountains perfect for weekend getaways',
                'price': 280000.00,
                'location': 'Denver, CO'
            }
        ]

        for prop_data in properties:
            property, created = Property.objects.get_or_create(
                title=prop_data['title'],
                defaults=prop_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created property: {prop_data["title"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Property already exists: {prop_data["title"]}')
                )