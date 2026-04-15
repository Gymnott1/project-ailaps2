import os
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LicensePlateApp.settings')
django.setup()

from scanner.models import Vehicle

def add_test_vehicles():
    # Clear existing vehicles
    Vehicle.objects.all().delete()

    # Test vehicles data with Kenyan format
    vehicles = [
        # Valid Insurance (Private Vehicles)
        {
            'plate_number': 'KAY 851Q',
            'is_insured': True,
            'owner_email': 'Kiiruian15@gmail.com',
            'insurance_expiry': timezone.now() + timedelta(days=90),
            'owner_phone': '0790016072'
        },
        {
            'plate_number': 'KCA 321D',
            'is_insured': True,
            'owner_email': 'owner2@example.com',
            'insurance_expiry': timezone.now() + timedelta(days=60),
            'owner_phone': '0790016072'
        },
        {
            'plate_number': 'KBW 567F',
            'is_insured': True,
            'owner_email': 'owner3@example.com',
            'insurance_expiry': timezone.now() + timedelta(days=45),
            'owner_phone': '0790016072'
        },
        # Commercial Vehicles (Valid Insurance)
        {
            'plate_number': 'KCT 789G',
            'is_insured': True,
            'owner_email': 'fleet1@company.com',
            'insurance_expiry': timezone.now() + timedelta(days=120),
            'owner_phone': '0790016072'
        },
        {
            'plate_number': 'KDH 432J',
            'is_insured': True,
            'owner_email': 'fleet2@company.com',
            'insurance_expiry': timezone.now() + timedelta(days=100),
            'owner_phone': '0790016072'
        },
        # Expired Insurance
        {
            'plate_number': 'KCE 456B',
            'is_insured': False,
            'owner_email': 'expired1@example.com',
            'insurance_expiry': timezone.now() - timedelta(days=30),
            'owner_phone': '0790016072'
        },
        {
            'plate_number': 'KBZ 789C',
            'is_insured': False,
            'owner_email': 'expired2@example.com',
            'insurance_expiry': timezone.now() - timedelta(days=15),
            'owner_phone': '0790016072'
        },
        # No Insurance
        {
            'plate_number': 'KAY 234H',
            'is_insured': False,
            'owner_email': 'noinsurance1@example.com',
            'insurance_expiry': None,
            'owner_phone': '0790016072'
        },
        {
            'plate_number': 'KCM 876P',
            'is_insured': False,
            'owner_email': 'noinsurance2@example.com',
            'insurance_expiry': None,
            'owner_phone': '0790016072'
        },
        # Government Vehicles (Always Insured)
        {
            'plate_number': 'GK 123A',
            'is_insured': True,
            'owner_email': 'gov.fleet1@gov.ke',
            'insurance_expiry': timezone.now() + timedelta(days=180),
            'owner_phone': '0790016072'
        },
        {
            'plate_number': 'GK 456B',
            'is_insured': True,
            'owner_email': 'gov.fleet2@gov.ke',
            'insurance_expiry': timezone.now() + timedelta(days=180),
            'owner_phone': '0790016072'
        }
    ]

    # Add vehicles to database
    for vehicle_data in vehicles:
        try:
            vehicle = Vehicle.objects.create(**vehicle_data)
            status = "Insured" if vehicle.is_insured else "Not Insured"
            expiry = vehicle.insurance_expiry.strftime('%Y-%m-%d') if vehicle.insurance_expiry else "No expiry"
            print(f"Added vehicle {vehicle.plate_number} - Insurance: {status} (Expires: {expiry})")
        except Exception as e:
            print(f"Error adding vehicle {vehicle_data['plate_number']}: {str(e)}")

if __name__ == '__main__':
    print("Initializing database with test vehicles...")
    add_test_vehicles()
    print("Database initialization complete!")
