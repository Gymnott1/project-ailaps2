from django.core.management.base import BaseCommand
from scanner.models import Vehicle
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Adds sample vehicles to the database'

    def handle(self, *args, **kwargs):
        # Sample vehicle data
        vehicles = [
            {
                'plate_number': 'KAA 123A',
                'owner_name': 'John Doe',
                'owner_phone': '0712345678',
                'vehicle_model': 'Toyota Camry',
                'year': 2020,
                'color': 'Silver',
                'is_insured': True,
                'insurance_expiry': date.today() + timedelta(days=30),
                'insurance_company': 'Jubilee Insurance',
                'insurance_policy_number': 'JUB123456'
            },
            {
                'plate_number': 'KAB 456B',
                'owner_name': 'Jane Smith',
                'owner_phone': '0723456789',
                'vehicle_model': 'Honda Civic',
                'year': 2021,
                'color': 'Black',
                'is_insured': True,
                'insurance_expiry': date.today() + timedelta(days=60),
                'insurance_company': 'CIC Insurance',
                'insurance_policy_number': 'CIC789012'
            },
            {
                'plate_number': 'KAC 789C',
                'owner_name': 'Robert Johnson',
                'owner_phone': '0734567890',
                'vehicle_model': 'Nissan Altima',
                'year': 2019,
                'color': 'White',
                'is_insured': False,
                'insurance_expiry': None,
                'insurance_company': None,
                'insurance_policy_number': None
            },
            {
                'plate_number': 'KAD 012D',
                'owner_name': 'Mary Wilson',
                'owner_phone': '0745678901',
                'vehicle_model': 'Mazda CX-5',
                'year': 2022,
                'color': 'Red',
                'is_insured': True,
                'insurance_expiry': date.today() - timedelta(days=10),
                'insurance_company': 'UAP Insurance',
                'insurance_policy_number': 'UAP345678'
            },
            {
                'plate_number': 'KAE 345E',
                'owner_name': 'David Brown',
                'owner_phone': '0756789012',
                'vehicle_model': 'Subaru Forester',
                'year': 2021,
                'color': 'Blue',
                'is_insured': True,
                'insurance_expiry': date.today() + timedelta(days=90),
                'insurance_company': 'APA Insurance',
                'insurance_policy_number': 'APA901234'
            }
        ]

        # Add vehicles to database
        for vehicle_data in vehicles:
            try:
                Vehicle.objects.create(**vehicle_data)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully added vehicle {vehicle_data["plate_number"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to add vehicle {vehicle_data["plate_number"]}: {str(e)}')
                ) 