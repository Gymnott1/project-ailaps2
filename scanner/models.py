from django.db import models
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    owner_name = models.CharField(max_length=100, null=True, blank=True)
    owner_phone = models.CharField(max_length=15, null=True, blank=True)
    vehicle_model = models.CharField(max_length=100, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    is_insured = models.BooleanField(default=False)
    insurance_expiry = models.DateField(null=True, blank=True)
    insurance_company = models.CharField(max_length=100, null=True, blank=True)
    insurance_policy_number = models.CharField(max_length=50, null=True, blank=True)
    date_added = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plate_number} - {self.owner_name or 'Unknown'}"

    class Meta:
        ordering = ['-date_added']
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

class ScanRecord(models.Model):
    plate_number = models.CharField(max_length=20)
    scan_time = models.DateTimeField(auto_now_add=True)
    is_registered = models.BooleanField(default=False)
    insurance_status = models.CharField(max_length=20, default='Unknown')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    image_path = models.CharField(max_length=255, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.plate_number} - {self.scan_time}"

    class Meta:
        ordering = ['-scan_time']
        verbose_name = 'Scan Record'
        verbose_name_plural = 'Scan Records'
