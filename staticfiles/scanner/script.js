// Camera initialization moved to scan.html

let stream = null;
let videoTrack = null;
let isScanning = false;
let scanInterval = null;
let scanOverlay = null;
let successBeep = null;
let errorBeep = null;
let resultContainer = null;
let scanningStatus = null;

// Helper function to safely play audio without console errors
function playSound(audioElement) {
    if (audioElement && audioElement.play) {
        const playPromise = audioElement.play();
        if (playPromise !== undefined) {
            playPromise.catch(() => {
                // Silently ignore audio playback errors
            });
        }
    }
}

async function checkCameraAvailable() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return false;
        const devices = await navigator.mediaDevices.enumerateDevices();
        return devices.some(d => d.kind === 'videoinput');
    } catch {
        return false;
    }
}

async function startCamera() {
    try {
        const constraints = {
            video: {
                facingMode: 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30 }
            }
        };

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        const videoElement = document.getElementById('videoElement');
        videoElement.srcObject = stream;
        videoElement.style.display = 'block';
        videoTrack = stream.getVideoTracks()[0];

        await new Promise((resolve) => {
            videoElement.onloadedmetadata = () => { videoElement.play(); resolve(); };
        });

        return true;
    } catch (error) {
        const msg = error.name === 'NotFoundError'
            ? 'No camera detected on this device. Use manual entry or upload an image below.'
            : 'Could not access camera: ' + error.message;
        showCameraUnavailable(msg);
        return false;
    }
}

function showCameraUnavailable(msg) {
    const cameraSection = document.getElementById('cameraSection');
    if (cameraSection) {
        cameraSection.innerHTML = `
            <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:10px;padding:20px;text-align:center;color:#856404;">
                <i class="fas fa-video-slash" style="font-size:2rem;margin-bottom:10px;"></i>
                <p style="margin:0;font-size:1rem;">${msg}</p>
            </div>`;
    }
}

function stopCamera() {
    if (videoTrack) {
        videoTrack.stop();
        const videoElement = document.getElementById('videoElement');
        videoElement.style.display = 'none';
        videoElement.srcObject = null;
        stream = null;
        videoTrack = null;
        isScanning = false;
    }
}

async function captureAndScan() {
    if (!videoTrack || !isScanning) return;

    const videoElement = document.getElementById('videoElement');
    const canvas = document.createElement('canvas');
    // Use higher resolution for better OCR
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const context = canvas.getContext('2d');
    
    // Apply sharpening filter
    context.filter = 'contrast(1.4) brightness(1.2) saturate(1.3)';
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    context.filter = 'none';

    canvas.toBlob(async (blob) => {
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const imageData = e.target.result;
                const response = await fetch('/scan_plate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                    body: JSON.stringify({ image: imageData })
                });
                const data = await response.json();
                
                const plateNumber = document.getElementById('plateNumber');
                const insuranceStatus = document.getElementById('insuranceStatus');
                const statusBadge = document.getElementById('statusBadge');
                const resultContainer = document.querySelector('.result-container');
                const scanningStatus = document.getElementById('scanningStatus');
                
                if (data.status === 'success') {
                    plateNumber.textContent = data.plate_number;
                    resultContainer.style.display = 'block';
                    
                    if (data.found) {
                        insuranceStatus.textContent = data.is_insured ? 'Insured' : 'Not Insured';
                        statusBadge.className = data.is_insured ? 'status-badge insured' : 'status-badge not-insured';
                        statusBadge.textContent = data.is_insured ? '✅ Valid' : '❌ Uninsured';
                        
                        if (data.insurance_expiry) {
                            document.getElementById('insuranceExpiry').textContent = data.insurance_expiry;
                            document.getElementById('expiryInfo').style.display = 'block';
                        }
                        
                        // Play success sound
                        playSound(successBeep);
                    } else {
                        insuranceStatus.textContent = 'Not Found';
                        statusBadge.className = 'status-badge not-insured';
                        statusBadge.textContent = '⚠️ Unregistered';
                        playSound(errorBeep);
                    }
                    
                    // Update scan overlay
                    scanOverlay.className = 'scan-overlay detected';
                    setTimeout(() => {
                        scanOverlay.classList.remove('detected');
                    }, 2000);
                    
                } else {
                    scanningStatus.textContent = data.message || 'No license plate detected';
                    scanOverlay.className = 'scan-overlay not-detected';
                    setTimeout(() => {
                        scanOverlay.classList.remove('not-detected');
                    }, 2000);
                }
            } catch (error) {
                console.error('Error processing image:', error);
                scanningStatus.textContent = 'Error: Could not process image';
            }
        };
        reader.readAsDataURL(blob);
    }, 'image/jpeg', 0.95);  // Increased quality to 95%
}

function handleKeyPress(event) {
    if (event.key.toLowerCase() === 'q' && isScanning) {
        document.getElementById('stopScan').click();
    }
}

// Initialize scanning when document is ready
document.addEventListener('DOMContentLoaded', () => {
    scanOverlay = document.querySelector('.scan-overlay');
    resultContainer = document.querySelector('.result-container');
    loadingSpinner = document.querySelector('.loading-spinner');
    scanningStatus = document.getElementById('scanningStatus');
    successBeep = document.getElementById('successBeep');
    errorBeep = document.getElementById('errorBeep');

    // Auto-check camera availability on load
    checkCameraAvailable().then(available => {
        if (!available) showCameraUnavailable('No camera detected on this device. Use manual entry or upload an image below.');
    });
    const startButton = document.getElementById('startScan');
    const stopButton = document.getElementById('stopScan');
    const manualPlateInput = document.getElementById('manualPlateInput');
    const scanManualBtn = document.getElementById('scanManualBtn');

    // Handle manual plate submission
    async function submitManualPlate() {
        const plateNumber = manualPlateInput.value.trim().toUpperCase();
        
        if (!plateNumber) {
            alert('Please enter a license plate number');
            return;
        }
        
        // Show loading state
        scanManualBtn.disabled = true;
        scanManualBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Scanning...';
        
        try {
            const response = await fetch('/scan_manual_plate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify({ plate_number: plateNumber })
            });
            
            const data = await response.json();
            
            const plateNumberEl = document.getElementById('plateNumber');
            const insuranceStatus = document.getElementById('insuranceStatus');
            const statusBadge = document.getElementById('statusBadge');
            
            if (data.status === 'success') {
                plateNumberEl.textContent = data.plate_number;
                resultContainer.style.display = 'block';
                
                if (data.found) {
                    insuranceStatus.textContent = data.is_insured ? 'Insured' : 'Not Insured';
                    statusBadge.className = data.is_insured ? 'status-badge insured' : 'status-badge not-insured';
                    statusBadge.textContent = data.is_insured ? '✅ Valid' : '❌ Uninsured';
                    
                    if (data.insurance_expiry) {
                        document.getElementById('insuranceExpiry').textContent = data.insurance_expiry;
                        document.getElementById('expiryInfo').style.display = 'block';
                    }
                    
                    playSound(successBeep);
                } else {
                    insuranceStatus.textContent = 'Not Found';
                    statusBadge.className = 'status-badge not-insured';
                    statusBadge.textContent = '⚠️ Unregistered';
                    playSound(errorBeep);
                }
            } else {
                alert('Error: ' + data.message);
                playSound(errorBeep);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error submitting plate number');
            playSound(errorBeep);
        } finally {
            scanManualBtn.disabled = false;
            scanManualBtn.innerHTML = '<i class="fas fa-search me-2"></i>Scan';
        }
    }
    
    // Add event listeners
    scanManualBtn.addEventListener('click', submitManualPlate);
    manualPlateInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            submitManualPlate();
        }
    });

    // Add keyboard event listener
    document.addEventListener('keypress', handleKeyPress);

    startButton.addEventListener('click', async () => {
        const success = await startCamera();
        if (success) {
            isScanning = true;
            startButton.style.display = 'none';
            stopButton.style.display = 'block';
            scanningStatus.textContent = 'Camera started. Scanning... (Press Q to stop)';
            scanInterval = setInterval(captureAndScan, 2000);
        }
    });

    stopButton.addEventListener('click', () => {
        if (scanInterval) {
            clearInterval(scanInterval);
            scanInterval = null;
        }
        stopCamera();
        stopButton.style.display = 'none';
        startButton.style.display = 'block';
        resultContainer.style.display = 'none';
        scanningStatus.textContent = '';
    });
});