from django.contrib import admin
from .models import Vehicle, ScanRecord

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'owner_name', 'owner_phone', 'is_insured', 'insurance_expiry')
    list_filter = ('is_insured',)
    search_fields = ('plate_number', 'owner_name', 'owner_phone')
    readonly_fields = ('date_added', 'last_updated')
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('plate_number', 'owner_name', 'owner_phone', 'vehicle_model', 'year', 'color')
        }),
        ('Insurance Information', {
            'fields': ('is_insured', 'insurance_expiry', 'insurance_company', 'insurance_policy_number')
        }),
        ('System Information', {
            'fields': ('date_added', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    
    def save_model(self, request, obj, form, change):
        # Clean the plate number before saving
        if obj.plate_number:
            obj.plate_number = obj.plate_number.strip().upper()
        super().save_model(request, obj, form, change)

@admin.register(ScanRecord)
class ScanRecordAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'scan_time', 'is_registered', 'insurance_status', 'get_vehicle_details')
    list_filter = ('is_registered', 'insurance_status', 'scan_time')
    search_fields = ('plate_number', 'vehicle__owner_name')
    readonly_fields = ('scan_time', 'plate_number', 'is_registered', 'insurance_status', 'vehicle')
    ordering = ('-scan_time',)
    
    fieldsets = (
        ('Scan Information', {
            'fields': ('plate_number', 'scan_time', 'is_registered', 'insurance_status', 'vehicle')
        }),
        ('Additional Information', {
            'fields': ('image_path', 'confidence_score'),
            'classes': ('collapse',)
        }),
    )
    
    def get_vehicle_details(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.owner_name} - {obj.vehicle.vehicle_model}"
        return "Not Registered"
    get_vehicle_details.short_description = "Vehicle Details"
    
    def has_add_permission(self, request):
        # Prevent manual creation of scan records
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing of scan records
        return False
    
    list_per_page = 25
