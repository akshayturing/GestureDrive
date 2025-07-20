// Main JavaScript for GestureDrive

// Check system status when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkSystemStatus();
});

// Function to check system status
function checkSystemStatus() {
    setInterval(function() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('current-gesture').textContent = data.current_gesture;
                document.getElementById('current-command').textContent = data.current_command;
            })
            .catch(error => console.error('Error fetching status:', error));
    }, 1000);
    // fetch('/api/status')
    //     .then(response => response.json())
    //     .then(data => {
    //         console.log('System status:', data);
    //         if (data.status === 'online') {
    //             console.log('GestureDrive system is online');
    //         }
    //     })
    //     .catch(error => {
    //         console.error('Error checking system status:', error);
    //     });
}

// Function to handle gesture validation UI
function updateGestureValidation(data) {
    // Find UI elements
    const gestureDisplay = document.getElementById('current-gesture');
    const statusDisplay = document.getElementById('validation-status');
    
    if (!gestureDisplay) return;
    
    // Prioritize validated motion gestures
    if (data.validated_motion) {
        gestureDisplay.textContent = `${data.validated_motion} ✓`;
        gestureDisplay.classList.add('validated');
        gestureDisplay.classList.remove('raw');
    }
    // Then validated static gestures
    else if (data.validated_gesture) {
        gestureDisplay.textContent = `${data.validated_gesture} ✓`;
        gestureDisplay.classList.add('validated');
        gestureDisplay.classList.remove('raw');
    }
    // Show raw (unvalidated) gestures differently if available
    else if (data.raw_motion && data.raw_motion !== 'stationary') {
        gestureDisplay.textContent = `${data.raw_motion} (validating...)`;
        gestureDisplay.classList.add('raw');
        gestureDisplay.classList.remove('validated');
    }
    else if (data.raw_gesture) {
        gestureDisplay.textContent = `${data.raw_gesture} (validating...)`;
        gestureDisplay.classList.add('raw');
        gestureDisplay.classList.remove('validated');
    }
    else {
        gestureDisplay.textContent = 'No gesture detected';
        gestureDisplay.classList.remove('validated', 'raw');
    }
    
    // Update validation status if element exists
    if (statusDisplay && data.debug) {
        let statusText = data.debug.posture_valid ? 
            `Posture valid, duration: ${Math.round(data.debug.tracking_duration * 100) / 100}s` :
            `Invalid: ${data.debug.validation_reason}`;
            
        statusDisplay.textContent = statusText;
        
        // Update status appearance
        if (data.validated_motion || data.validated_gesture) {
            statusDisplay.className = 'status-valid';
        } else if (data.debug.posture_valid) {
            statusDisplay.className = 'status-tracking';
        } else {
            statusDisplay.className = 'status-invalid';
        }
    }
}

// Poll for gestures including validation status
function startGestureTracking() {
    // Create validation status display if needed
    if (!document.getElementById('validation-status')) {
        const container = document.querySelector('.controls-container') || document.body;
        const statusElem = document.createElement('div');
        statusElem.id = 'validation-status';
        statusElem.className = 'status-waiting';
        statusElem.textContent = 'Waiting for gestures...';
        container.appendChild(statusElem);
        
        // Add debug toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'debug-toggle-btn';
        toggleBtn.textContent = 'Toggle Validation Display';
        toggleBtn.onclick = function() {
            fetch('/api/toggle_validation_display', {
                method: 'POST'
            }).then(response => response.json())
              .catch(error => console.error('Error:', error));
        };
        container.appendChild(toggleBtn);
    }

    // Start polling for gestures
    setInterval(() => {
        fetch('/api/current_gestures')
            .then(response => response.json())
            .then(data => {
                // Update UI with validation status
                updateGestureValidation(data);
                
                // Process navigation only with validated gestures
                if (data.validated_motion || data.validated_gesture) {
                    const gestureToUse = data.validated_motion || data.validated_gesture;
                    processNavigation(gestureToUse);
                }
            })
            .catch(error => console.error('Error fetching gestures:', error));
    }, 200);
}

// Process navigation with validated gestures
function processNavigation(gesture) {
    // Only process on file navigation pages
    if (!window.location.pathname.includes('/files')) return;
    
    fetch('/api/navigate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ gesture: gesture })
    })
    .then(response => response.json())
    .then(data => {
        // Update file list display
        updateFileDisplay(data);
    })
    .catch(error => console.error('Error navigating:', error));
}

// Add validation styles
const validationStyles = document.createElement('style');
validationStyles.textContent = `
.validated {
    color: #28a745;
    font-weight: bold;
}
.raw {
    color: #ffc107;
    font-style: italic;
}
#validation-status {
    margin-top: 10px;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 14px;
}
.status-valid {
    background-color: rgba(40, 167, 69, 0.2);
    color: #28a745;
}
.status-tracking {
    background-color: rgba(255, 193, 7, 0.2);
    color: #ffc107;
}
.status-invalid {
    background-color: rgba(220, 53, 69, 0.2);
    color: #dc3545;
}
.status-waiting {
    background-color: rgba(108, 117, 125, 0.2);
    color: #6c757d;
}
.debug-toggle-btn {
    margin-top: 10px;
    background-color: #17a2b8;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
}
`;
document.head.appendChild(validationStyles);

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    startGestureTracking();
});