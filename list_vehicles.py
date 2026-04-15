import os
import django
from datetime import datetime
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LicensePlateApp.settings')
django.setup()

from scanner.models import Vehicle, ScanRecord

def list_vehicles():
    print("\n=== Registered Vehicles ===")
    print("=" * 50)
    print(f"{'Plate Number':<15} {'Type':<15} {'Insurance Status':<15}")
    print("-" * 50)
    
    vehicles = Vehicle.objects.all().order_by('plate_number')
    
    for vehicle in vehicles:
        # Determine vehicle type based on plate format
        if vehicle.plate_number.startswith('GK'):
            vehicle_type = "Government"
        elif any(comm in vehicle.plate_number for comm in ['KCT', 'KDH']):
            vehicle_type = "Commercial"
        else:
            vehicle_type = "Private"
        
        # Format status
        status = "[VALID]" if vehicle.is_insured else "[EXPIRED]"
        
        print(f"{vehicle.plate_number:<15} {vehicle_type:<15} {status}")
    
    print("\n=== Recent Scans ===")
    print("=" * 50)
    print(f"{'Plate Number':<15} {'Scan Date':<20} {'Insurance Status':<15}")
    print("-" * 50)
    
    scans = ScanRecord.objects.all().order_by('-scan_date')[:5]
    for scan in scans:
        status = "[VALID]" if scan.insurance_status else "[EXPIRED]"
        print(f"{scan.plate_number:<15} {scan.scan_date.strftime('%Y-%m-%d %H:%M'):<20} {status}")
    
    print("\n=== Summary ===")
    print(f"Total Vehicles: {vehicles.count()}")
    print(f"Insured: {vehicles.filter(is_insured=True).count()}")
    print(f"Not Insured: {vehicles.filter(is_insured=False).count()}")
    print("-" * 50)

if __name__ == '__main__':
    list_vehicles()
