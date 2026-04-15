"""
Improved License Plate Detector using Haar Cascade and EasyOCR
Based on: https://github.com/Brian412M/NumberPlateRecog
"""

import cv2
import numpy as np
import easyocr
import os
from pathlib import Path

class LicensePlateDetector:
    """
    Detects license plates in images using Haar cascade classifier
    and extracts text using EasyOCR
    """
    
    def __init__(self, cascade_path=None):
        """
        Initialize the detector with Haar cascade classifier
        
        Args:
            cascade_path: Path to the haarcascade XML file
        """
        # Initialize EasyOCR reader globally for efficiency
        print("Initializing EasyOCR reader...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        
        # Set cascade path
        if cascade_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cascade_path = os.path.join(base_dir, 'model', 'haarcascade_russian_plate_number.xml')
        
        # Load cascade classifier
        self.plate_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.plate_cascade.empty():
            raise ValueError(f"Failed to load cascade classifier from {cascade_path}")
        
        print(f"✓ Cascade classifier loaded from: {cascade_path}")
        self.min_area = 500
        
    def detect_plates(self, image):
        """
        Detect license plates in image
        
        Args:
            image: Input image (BGR)
            
        Returns:
            List of detected plate regions as (x, y, w, h) tuples
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect plates using cascade classifier
            # Adjusted parameters for better detection:
            # scaleFactor: 1.1 - smaller scale step for more thorough detection
            # minNeighbors: 4 - fewer neighbors required for detection
            # minSize: (30, 30) - smaller minimum size
            plates = self.plate_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30),
                maxSize=(300, 100)
            )
            
            if len(plates) == 0:
                return []
            
            # Sort plates by area (largest first)
            plates = sorted(plates, key=lambda x: x[2] * x[3], reverse=True)
            
            return plates
        except Exception as e:
            print(f"Error detecting plates: {str(e)}")
            return []
    
    def extract_text(self, plate_image):
        """
        Extract text from license plate image using EasyOCR
        
        Args:
            plate_image: Cropped license plate image
            
        Returns:
            Extracted plate text string
        """
        try:
            if plate_image.size == 0:
                return None
            
            # Convert BGR to RGB for EasyOCR
            if len(plate_image.shape) == 3:
                plate_rgb = cv2.cvtColor(plate_image, cv2.COLOR_BGR2RGB)
            else:
                plate_rgb = plate_image
            
            # Read text using EasyOCR
            results = self.reader.readtext(plate_rgb, detail=1)
            
            if not results:
                return None
            
            # Extract text with confidence filtering
            plate_text = ''.join([text[1] for text in results if text[2] > 0.3])
            
            # Clean the text
            plate_text = ''.join(e for e in plate_text if e.isalnum() or e.isspace()).strip().upper()
            
            # Validate: typical plates have 4-10 characters
            if len(plate_text) >= 4:
                return plate_text
            
            return None
            
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            return None
    
    def process_frame(self, image):
        """
        Process a single frame to detect and extract license plates
        
        Args:
            image: Input image (BGR numpy array)
            
        Returns:
            List of dicts with detected plate info:
            [
                {
                    'text': 'KAX003S',
                    'roi': (x, y, w, h),
                    'plate_image': cropped_image
                },
                ...
            ]
        """
        results = []
        
        try:
            # Detect plates
            plates = self.detect_plates(image)
            
            if len(plates) == 0:
                return results
            
            # Process each detected plate
            for (x, y, w, h) in plates:
                area = w * h
                
                if area < self.min_area:
                    continue
                
                # Ensure coordinates are within bounds
                y = max(0, y)
                x = max(0, x)
                y_end = min(image.shape[0], y + h)
                x_end = min(image.shape[1], x + w)
                
                # Crop plate region
                plate_roi = image[y:y_end, x:x_end]
                
                if plate_roi.size == 0:
                    continue
                
                # Preprocess plate image for better OCR
                # Resize for better OCR recognition
                plate_processed = cv2.resize(plate_roi, None, fx=2.5, fy=2.5, 
                                            interpolation=cv2.INTER_CUBIC)
                
                # Apply threshold for binary image
                _, plate_binary = cv2.threshold(
                    cv2.cvtColor(plate_processed, cv2.COLOR_BGR2GRAY),
                    0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                
                # Extract text
                plate_text = self.extract_text(plate_processed)
                
                if plate_text:
                    results.append({
                        'text': plate_text,
                        'roi': (x, y, w, h),
                        'plate_image': plate_roi,
                        'confidence': 'high'
                    })
            
            return results
            
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            import traceback
            traceback.print_exc()
            return results
    
    def draw_detections(self, image, detections):
        """
        Draw rectangles and text on image showing detected plates
        
        Args:
            image: Input image (BGR)
            detections: List of detection dicts from process_frame()
            
        Returns:
            Image with drawn rectangles and text
        """
        result_image = image.copy()
        
        for detection in detections:
            x, y, w, h = detection['roi']
            plate_text = detection['text']
            
            # Draw green rectangle
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Put text
            cv2.putText(result_image, f"Plate: {plate_text}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return result_image


# Global detector instance
_detector = None

def get_detector():
    """Get or create global detector instance"""
    global _detector
    if _detector is None:
        _detector = LicensePlateDetector()
    return _detector


def detect_license_plate(image):
    """
    Standalone function to detect license plate from image
    
    Args:
        image: Input image (BGR numpy array)
        
    Returns:
        License plate text string or None
    """
    detector = get_detector()
    detections = detector.process_frame(image)
    
    if detections:
        return detections[0]['text']
    return None
