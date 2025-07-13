from flask import Flask, render_template, Response, jsonify, request
from camera import init_camera, get_camera
import cv2
import os
import time

# Initialize the Flask app
app = Flask(__name__)

# We'll use a global camera variable
camera = None

def get_or_init_camera():
    """Get the current camera instance or initialize it if not yet created"""
    global camera
    if camera is None:
        camera = init_camera()
    return camera

@app.route('/')
def index():
    """Home page with webcam feed and controls"""
    # Ensure camera is initialized when accessing the home page
    get_or_init_camera()
    return render_template('index.html')

@app.route('/about')
def about():
    """About page with project information"""
    return render_template('about.html')

@app.route('/settings')
def settings():
    """Settings page for configuring gesture recognition parameters"""
    return render_template('settings.html')

@app.route('/api/status')
def status():
    """API endpoint for checking system status"""
    cam = get_or_init_camera()
    
    return jsonify({
        'status': 'online',
        'webcam_available': True,
        'gesture_system': 'ready',
        'fps': cam.fps
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update camera and detection settings"""
    cam = get_or_init_camera()
    
    try:
        data = request.json
        if 'camera' in data:
            # This would require restarting the camera
            # Simplified for now
            pass
        
        if 'detectionConfidence' in data:
            cam.min_detection_confidence = float(data['detectionConfidence'])
            
        if 'trackingConfidence' in data:
            cam.min_tracking_confidence = float(data['trackingConfidence'])
            
        if 'displayLandmarks' in data:
            cam.show_landmarks = bool(data['displayLandmarks'])
            
        if 'mirrorMode' in data:
            cam.mirror = bool(data['mirrorMode'])
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def gen_frames():
    """Generator function for video streaming"""
    cam = get_or_init_camera()
    
    while True:
        frame = cam.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            # If frame is None, yield an empty image or placeholder
            time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    """Route for streaming video content"""
    # Return a multipart response with MJPEG content type
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/shutdown')
def shutdown():
    """Shutdown the camera and application"""
    global camera
    if camera:
        camera.stop()
        camera = None
    return "Camera has been shut down."

@app.teardown_appcontext
def shutdown_camera(exception=None):
    """Ensure camera is shut down when the application context ends"""
    global camera
    if camera:
        camera.stop()
        camera = None

if __name__ == '__main__':
    try:
        app.run(debug=True, threaded=True)
    finally:
        # Ensure camera is properly released when the app exits
        if camera:
            camera.stop()
