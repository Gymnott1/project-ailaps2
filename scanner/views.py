from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vehicle, ScanRecord
from .plate_detector import get_detector
import cv2
import numpy as np
from PIL import Image
import io
from datetime import datetime
import os
import base64
import json

def home(request):
    """Home page view"""
    return render(request, 'scanner/home.html')

def scan(request):
    """Camera scanning view"""
    return render(request, 'scanner/scan.html')

def scan_plate(request):
    """API endpoint for scanning license plates"""
    if request.method == 'POST':
        try:
            # Get the image data from the request
            data = json.loads(request.body)
            image_data = data.get('image').split(',')[1]
            image_bytes = base64.b64decode(image_data)
            
            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Detect license plate
            plate_text = detect_license_plate(image)
            
            if plate_text:
                # Check if vehicle exists in database
                try:
                    vehicle = Vehicle.objects.get(license_plate=plate_text)
                    is_insured = vehicle.is_insured
                    insurance_expiry = vehicle.insurance_expiry.strftime('%Y-%m-%d') if vehicle.insurance_expiry else None
                    
                    # Record the scan
                    ScanRecord.objects.create(
                        license_plate=plate_text,
                        is_insured=is_insured,
                        vehicle=vehicle
                    )
                    
                    return JsonResponse({
                        'status': 'success',
                        'plate_number': plate_text,
                        'is_insured': is_insured,
                        'insurance_expiry': insurance_expiry,
                        'found': True
                    })
                except Vehicle.DoesNotExist:
                    # Record unregistered vehicle scan
                    ScanRecord.objects.create(
                        license_plate=plate_text,
                        is_insured=False
                    )
                    
                    return JsonResponse({
                        'status': 'success',
                        'plate_number': plate_text,
                        'is_insured': False,
                        'found': False,
                        'message': 'Vehicle not found in database'
                    })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No license plate detected'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def detect_license_plate(image):
    """
    Detect and extract license plate from image using improved detector
    
    Args:
        image: Input image as numpy array (BGR format)
        
    Returns:
        Detected license plate text or None
    """
    try:
        detector = get_detector()
        detections = detector.process_frame(image)
        
        if detections:
            plate_text = detections[0]['text']
            print(f"✓ Detected plate: {plate_text}")
            return plate_text
        else:
            print("No license plate detected")
            return None
            
    except Exception as e:
        print(f"Error in detect_license_plate: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def scan_manual_plate(request):
    """API endpoint for manually entered license plates"""
    if request.method == 'POST':
        try:
            # Get the plate number from the request
            data = json.loads(request.body)
            plate_number = data.get('plate_number', '').strip().upper()
            
            if not plate_number:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please enter a plate number'
                })
            
            # Check if vehicle exists in database
            try:
                vehicle = Vehicle.objects.get(plate_number=plate_number)
                is_insured = vehicle.is_insured
                insurance_expiry = vehicle.insurance_expiry.strftime('%Y-%m-%d') if vehicle.insurance_expiry else None
                
                # Record the scan
                ScanRecord.objects.create(
                    plate_number=plate_number,
                    is_registered=True,
                    insurance_status='Valid' if is_insured else 'Invalid',
                    vehicle=vehicle
                )
                
                return JsonResponse({
                    'status': 'success',
                    'plate_number': plate_number,
                    'is_insured': is_insured,
                    'insurance_expiry': insurance_expiry,
                    'found': True
                })
            except Vehicle.DoesNotExist:
                # Record unregistered vehicle scan
                ScanRecord.objects.create(
                    plate_number=plate_number,
                    is_registered=False,
                    insurance_status='Unknown'
                )
                
                return JsonResponse({
                    'status': 'success',
                    'plate_number': plate_number,
                    'is_insured': False,
                    'found': False,
                    'message': 'Vehicle not found in database'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request format'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def stop_camera(request):
    """API endpoint for stopping the camera"""
    return JsonResponse({'status': 'success'})

def list_plates(request):
    """View to list all scanned plates"""
    vehicles = Vehicle.objects.all()
    return render(request, 'scanner/list_plates.html', {'vehicles': vehicles})

def process_image(request):
    """API endpoint for processing uploaded images"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Get the image from the request
        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({'success': False, 'error': 'No image provided'})
        
        print("Received image file for processing")
        
        # Read the image
        image_data = image_file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print("Failed to decode image")
            return JsonResponse({'success': False, 'error': 'Invalid image data'})
        
        # Log image dimensions
        height, width = image.shape[:2]
        print(f"Processing image with dimensions: {width}x{height}")
        
        # Resize image if too large for better performance
        max_dimension = 1280
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            print(f"Resized image to: {image.shape[1]}x{image.shape[0]}")
        
        # Enhance image quality
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Save debug image
        debug_dir = os.path.join(os.path.dirname(__file__), 'static', 'scanner', 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = os.path.join('scanner', 'debug', f'debug_{timestamp}.jpg')
        cv2.imwrite(os.path.join(debug_dir, f'debug_{timestamp}.jpg'), enhanced)
        print(f"Saved debug image: {image_path}")
        
        # Detect license plate
        print("Starting plate detection...")
        plate_number = detect_license_plate(enhanced)
        
        if not plate_number:
            print("No plate detected in the image")
            # Create scan record for failed detection
            scan_record = ScanRecord.objects.create(
                plate_number='Not detected',
                is_registered=False,
                insurance_status='Unknown',
                image_path=image_path
            )
            print(f"Created scan record for failed detection: {scan_record}")
            return JsonResponse({
                'success': True,
                'registered': False,
                'license_plate': 'Not detected',
                'insurance_status': 'Unknown',
                'detected': False
            })
        
        print(f"Detected plate number: {plate_number}")
        
        # Check if vehicle exists in database
        try:
            vehicle = Vehicle.objects.get(plate_number=plate_number)
            print(f"Found vehicle in database: {vehicle.owner_name}")
            insurance_status = 'Valid' if vehicle.is_insured else 'Invalid'
            
            # Create scan record
            scan_record = ScanRecord.objects.create(
                plate_number=plate_number,
                is_registered=True,
                insurance_status=insurance_status,
                vehicle=vehicle,
                image_path=image_path
            )
            print(f"Created scan record for registered vehicle: {scan_record}")
            
            return JsonResponse({
                'success': True,
                'registered': True,
                'license_plate': plate_number,
                'insurance_status': insurance_status,
                'detected': True,
                'vehicle_details': {
                    'owner': vehicle.owner_name,
                    'model': vehicle.vehicle_model,
                    'year': vehicle.year
                }
            })
        except Vehicle.DoesNotExist:
            print(f"Vehicle not found in database for plate: {plate_number}")
            # Create scan record for unregistered vehicle
            scan_record = ScanRecord.objects.create(
                plate_number=plate_number,
                is_registered=False,
                insurance_status='Unknown',
                image_path=image_path
            )
            print(f"Created scan record for unregistered vehicle: {scan_record}")
            
            return JsonResponse({
                'success': True,
                'registered': False,
                'license_plate': plate_number,
                'insurance_status': 'Unknown',
                'detected': True
            })
            
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def admin_login(request):
    """Admin login view"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('scanner:admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password')
            return render(request, 'scanner/admin/login.html')
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff:  # Check if user is staff/admin
                login(request, user)
                messages.success(request, 'Successfully logged in')
                return redirect('scanner:admin_dashboard')
            else:
                messages.error(request, 'You do not have admin privileges')
        else:
            messages.error(request, 'Invalid username or password')
            
    return render(request, 'scanner/admin/login.html')

def admin_logout(request):
    """Admin logout view"""
    logout(request)
    return redirect('scanner:home')

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('scanner:home')
        
    try:
        # Get all vehicles ordered by date added
        vehicles = Vehicle.objects.all().order_by('-date_added')
        
        # Get recent scan records
        scan_records = ScanRecord.objects.all().order_by('-scan_time')[:20]  # Get last 20 scans
        
        # Calculate statistics
        total_vehicles = vehicles.count()
        insured_vehicles = vehicles.filter(is_insured=True).count()
        uninsured_vehicles = total_vehicles - insured_vehicles
        
        # Get vehicles with expired insurance
        today = datetime.now().date()
        expired_insurance = vehicles.filter(
            is_insured=True,
            insurance_expiry__lt=today
        ).count()
        
        # Get vehicles added today
        today_vehicles = vehicles.filter(
            date_added__date=today
        ).count()
        
        context = {
            'vehicles': vehicles,
            'scan_records': scan_records,
            'total_vehicles': total_vehicles,
            'insured_vehicles': insured_vehicles,
            'uninsured_vehicles': uninsured_vehicles,
            'expired_insurance': expired_insurance,
            'today_vehicles': today_vehicles,
            'today': today
        }
        return render(request, 'scanner/admin/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('scanner:home')

@login_required
def add_vehicle(request):
    """Add new vehicle view"""
    if request.method == 'POST':
        try:
            plate_number = request.POST.get('plate_number')
            owner_name = request.POST.get('owner_name')
            owner_phone = request.POST.get('owner_phone')
            is_insured = request.POST.get('is_insured') == 'on'
            insurance_expiry = request.POST.get('insurance_expiry')
            
            # Check if plate number already exists
            if Vehicle.objects.filter(plate_number=plate_number).exists():
                messages.error(request, 'A vehicle with this plate number already exists')
                return redirect('scanner:add_vehicle')
            
            # Create new vehicle
            vehicle = Vehicle.objects.create(
                plate_number=plate_number,
                owner_name=owner_name,
                owner_phone=owner_phone,
                is_insured=is_insured,
                insurance_expiry=insurance_expiry if insurance_expiry else None
            )
            
            messages.success(request, 'Vehicle added successfully')
            return redirect('scanner:admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding vehicle: {str(e)}')
    
    return render(request, 'scanner/admin/add_vehicle.html')

@login_required
def edit_vehicle(request, vehicle_id):
    """Edit vehicle view"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        try:
            plate_number = request.POST.get('plate_number')
            owner_name = request.POST.get('owner_name')
            owner_phone = request.POST.get('owner_phone')
            is_insured = request.POST.get('is_insured') == 'on'
            insurance_expiry = request.POST.get('insurance_expiry')
            
            # Check if plate number already exists (excluding current vehicle)
            if Vehicle.objects.filter(plate_number=plate_number).exclude(id=vehicle_id).exists():
                messages.error(request, 'A vehicle with this plate number already exists')
                return redirect('scanner:edit_vehicle', vehicle_id=vehicle_id)
            
            # Update vehicle
            vehicle.plate_number = plate_number
            vehicle.owner_name = owner_name
            vehicle.owner_phone = owner_phone
            vehicle.is_insured = is_insured
            vehicle.insurance_expiry = insurance_expiry if insurance_expiry else None
            vehicle.save()
            
            messages.success(request, 'Vehicle updated successfully')
            return redirect('scanner:admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating vehicle: {str(e)}')
    
    return render(request, 'scanner/admin/edit_vehicle.html', {'vehicle': vehicle})

@login_required
def delete_vehicle(request, vehicle_id):
    """Delete vehicle view"""
    try:
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        vehicle.delete()
        messages.success(request, 'Vehicle deleted successfully')
    except Exception as e:
        messages.error(request, f'Error deleting vehicle: {str(e)}')
    
    return redirect('scanner:admin_dashboard')

def get_vehicles_api(request):
    """API endpoint to get all vehicles"""
    vehicles = Vehicle.objects.all()
    data = [{'id': v.id, 'plate_number': v.plate_number} for v in vehicles]
    return JsonResponse({'vehicles': data})
