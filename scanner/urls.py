from django.urls import path
from . import views
from scanner.views import home,scan

app_name = 'scanner'

urlpatterns = [
    path('', views.home, name='home'),
    path('scan/', views.scan, name='scan'),
    path('scan_plate/', views.scan_plate, name='scan_plate'),
    path('scan_manual_plate/', views.scan_manual_plate, name='scan_manual_plate'),
    path('stop_camera/', views.stop_camera, name='stop_camera'),
    path('list_plates/', views.list_plates, name='list_plates'),
    path('process_image/', views.process_image, name='process_image'),
    
    # Admin URLs
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Vehicle management
    path('admin/vehicle/add/', views.add_vehicle, name='add_vehicle'),
    path('admin/vehicle/edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('admin/vehicle/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    
    # API endpoints
    path('api/vehicles/', views.get_vehicles_api, name='get_vehicles_api'),
]
