# # # from flask import Flask, render_template, Response, jsonify, request
# # # from camera import init_camera, get_camera
# # # import cv2
# # # import os
# # # import time

# # # # Initialize the Flask app
# # # app = Flask(__name__)

# # # # We'll use a global camera variable
# # # camera = None

# # # def get_or_init_camera():
# # #     """Get the current camera instance or initialize it if not yet created"""
# # #     global camera
# # #     if camera is None:
# # #         camera = init_camera()
# # #     return camera

# # # @app.route('/')
# # # def index():
# # #     """Home page with webcam feed and controls"""
# # #     # Ensure camera is initialized when accessing the home page
# # #     get_or_init_camera()
# # #     return render_template('index.html')

# # # @app.route('/about')
# # # def about():
# # #     """About page with project information"""
# # #     return render_template('about.html')

# # # @app.route('/settings')
# # # def settings():
# # #     """Settings page for configuring gesture recognition parameters"""
# # #     return render_template('settings.html')

# # # @app.route('/api/status')
# # # def status():
# # #     """API endpoint for checking system status"""
# # #     cam = get_or_init_camera()
    
# # #     return jsonify({
# # #         'status': 'online',
# # #         'webcam_available': True,
# # #         'gesture_system': 'ready',
# # #         'fps': cam.fps
# # #     })

# # # @app.route('/api/settings', methods=['POST'])
# # # def update_settings():
# # #     """Update camera and detection settings"""
# # #     cam = get_or_init_camera()
    
# # #     try:
# # #         data = request.json
# # #         if 'camera' in data:
# # #             # This would require restarting the camera
# # #             # Simplified for now
# # #             pass
        
# # #         if 'detectionConfidence' in data:
# # #             cam.min_detection_confidence = float(data['detectionConfidence'])
            
# # #         if 'trackingConfidence' in data:
# # #             cam.min_tracking_confidence = float(data['trackingConfidence'])
            
# # #         if 'displayLandmarks' in data:
# # #             cam.show_landmarks = bool(data['displayLandmarks'])
            
# # #         if 'mirrorMode' in data:
# # #             cam.mirror = bool(data['mirrorMode'])
        
# # #         return jsonify({'success': True})
# # #     except Exception as e:
# # #         return jsonify({'success': False, 'error': str(e)})

# # # def gen_frames():
# # #     """Generator function for video streaming"""
# # #     cam = get_or_init_camera()
    
# # #     while True:
# # #         frame = cam.get_frame()
# # #         if frame is not None:
# # #             yield (b'--frame\r\n'
# # #                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
# # #         else:
# # #             # If frame is None, yield an empty image or placeholder
# # #             time.sleep(0.1)

# # # @app.route('/video_feed')
# # # def video_feed():
# # #     """Route for streaming video content"""
# # #     # Return a multipart response with MJPEG content type
# # #     return Response(gen_frames(),
# # #                     mimetype='multipart/x-mixed-replace; boundary=frame')

# # # @app.route('/shutdown')
# # # def shutdown():
# # #     """Shutdown the camera and application"""
# # #     global camera
# # #     if camera:
# # #         camera.stop()
# # #         camera = None
# # #     return "Camera has been shut down."

# # # @app.teardown_appcontext
# # # def shutdown_camera(exception=None):
# # #     """Ensure camera is shut down when the application context ends"""
# # #     global camera
# # #     if camera:
# # #         camera.stop()
# # #         camera = None

# # # if __name__ == '__main__':
# # #     try:
# # #         app.run(debug=True, threaded=True)
# # #     finally:
# # #         # Ensure camera is properly released when the app exits
# # #         if camera:
# # #             camera.stop()
# # from flask import Flask, render_template, Response, jsonify, request
# # from camera import init_camera, get_camera
# # import cv2
# # import os
# # import time
# # import traceback

# # # Initialize the Flask app
# # app = Flask(__name__)

# # # Initialize camera when the app starts
# # camera = None

# # @app.route('/')
# # def index():
# #     """Home page with webcam feed and controls"""
# #     return render_template('index.html')

# # @app.route('/about')
# # def about():
# #     """About page with project information"""
# #     return render_template('about.html')

# # @app.route('/settings')
# # def settings():
# #     """Settings page for configuring gesture recognition parameters"""
# #     return render_template('settings.html')

# # @app.route('/api/status')
# # def status():
# #     """API endpoint for checking system status"""
# #     cam = get_camera()
# #     if cam is None:
# #         return jsonify({
# #             'status': 'offline',
# #             'webcam_available': False,
# #             'gesture_system': 'not initialized',
# #             'error': 'Camera not initialized'
# #         })
    
# #     cam_status = cam.get_status()
    
# #     return jsonify({
# #         'status': 'online' if cam_status['running'] else 'offline',
# #         'webcam_available': cam_status['running'],
# #         'gesture_system': 'ready' if cam_status['running'] else 'not ready',
# #         'fps': cam_status['fps'],
# #         'camera_id': cam_status['camera_id'],
# #         'last_error': cam_status['error']
# #     })

# # @app.route('/api/settings', methods=['POST'])
# # def update_settings():
# #     """Update camera and detection settings"""
# #     cam = get_camera()
# #     if cam is None:
# #         return jsonify({'success': False, 'error': 'Camera not initialized'})
    
# #     try:
# #         data = request.json
# #         if 'camera' in data:
# #             # This would require restarting the camera
# #             camera_id = int(data['camera'])
# #             if camera_id != cam.camera_id:
# #                 # Initialize a new camera with the selected ID
# #                 init_camera(camera_id)
            
# #         if 'detectionConfidence' in data:
# #             cam.min_detection_confidence = float(data['detectionConfidence'])
            
# #         if 'trackingConfidence' in data:
# #             cam.min_tracking_confidence = float(data['trackingConfidence'])
            
# #         if 'displayLandmarks' in data:
# #             cam.show_landmarks = bool(data['displayLandmarks'])
            
# #         if 'mirrorMode' in data:
# #             cam.mirror = bool(data['mirrorMode'])
        
# #         return jsonify({'success': True})
# #     except Exception as e:
# #         error_details = traceback.format_exc()
# #         print(f"Error in settings update: {error_details}")
# #         return jsonify({'success': False, 'error': str(e), 'details': error_details})

# # @app.route('/diagnostic')
# # def diagnostic():
# #     """Diagnostic page to check system status"""
# #     cam = get_camera()
# #     if cam is None:
# #         camera_info = "No camera initialized"
# #         camera_status = "Not available"
# #     else:
# #         status = cam.get_status()
# #         camera_info = f"Camera ID: {status['camera_id']}"
# #         camera_status = "Running" if status['running'] else "Stopped"
# #         if status['error']:
# #             camera_info += f" | Error: {status['error']}"

# #     opencv_version = cv2.__version__
    
# #     return render_template(
# #         'diagnostic.html',
# #         camera_status=camera_status,
# #         camera_info=camera_info,
# #         opencv_version=opencv_version
# #     )

# # def gen_frames():
# #     """Generator function for video streaming"""
# #     try:
# #         cam = get_camera()
# #         if cam is None:
# #             yield _generate_error_frame("Camera not initialized")
# #             return
            
# #         while True:
# #             try:
# #                 frame = cam.get_frame()
# #                 if frame is not None:
# #                     yield (b'--frame\r\n'
# #                            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
# #                 else:
# #                     yield _generate_error_frame("No frame available")
# #                     time.sleep(0.1)
# #             except Exception as e:
# #                 print(f"Error in frame generation: {str(e)}")
# #                 yield _generate_error_frame(f"Frame error: {str(e)}")
# #                 time.sleep(0.5)  # Prevent rapid error loops
# #     except Exception as e:
# #         print(f"Stream error: {str(e)}")
# #         yield _generate_error_frame(f"Stream error: {str(e)}")

# # def _generate_error_frame(error_message):
# #     """Generate an error frame with message"""
# #     # Create a black frame with error text
# #     frame = np.zeros((480, 640, 3), dtype=np.uint8)
# #     # Add error message
# #     cv2.putText(
# #         frame, 
# #         "Stream Error", 
# #         (150, 200), 
# #         cv2.FONT_HERSHEY_SIMPLEX, 
# #         1, 
# #         (0, 0, 255), 
# #         2
# #     )
# #     cv2.putText(
# #         frame, 
# #         error_message, 
# #         (50, 250), 
# #         cv2.FONT_HERSHEY_SIMPLEX, 
# #         0.8, 
# #         (255, 255, 255), 
# #         1
# #     )
    
# #     # Encode the error frame
# #     ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
# #     if ret:
# #         return (b'--frame\r\n'
# #                b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
# #     else:
# #         return (b'--frame\r\n'
# #                b'Content-Type: text/plain\r\n\r\n'
# #                b'Error generating error frame\r\n')

# # @app.route('/video_feed')
# # def video_feed():
# #     """Route for streaming video content"""
# #     # Return a multipart response with MJPEG content type
# #     return Response(gen_frames(),
# #                     mimetype='multipart/x-mixed-replace; boundary=frame')

# # @app.route('/restart_camera')
# # def restart_camera():
# #     """Restart the camera with the current settings"""
# #     try:
# #         cam = get_camera()
# #         camera_id = 0 if cam is None else cam.camera_id
# #         init_camera(camera_id)
# #         return jsonify({'success': True})
# #     except Exception as e:
# #         return jsonify({'success': False, 'error': str(e)})

# # @app.route('/shutdown')
# # def shutdown():
# #     """Shutdown the camera and application"""
# #     global camera
# #     if camera:
# #         camera.stop()
# #         camera = None
# #     return "Camera has been shut down."

# # @app.teardown_appcontext
# # def shutdown_camera(exception=None):
# #     """Ensure camera is shut down when the application context ends"""
# #     global camera
# #     if camera:
# #         camera.stop()
# #         camera = None

# # if __name__ == '__main__':
# #     try:
# #         print("Starting GestureDrive application")
# #         app.run(debug=True, threaded=True, host='0.0.0.0')
# #     except Exception as e:
# #         print(f"Error starting application: {str(e)}")
# #     finally:
# #         # Ensure camera is properly released when the app exits
# #         if camera:
# #             camera.stop()
# from flask import Flask, render_template, Response, jsonify, request, g
# import cv2
# import os
# import time
# import traceback
# import logging
# import numpy as np
# import atexit
# from camera import init_camera, get_camera, cleanup_camera

# # Configure logging
# logging.basicConfig(level=logging.INFO, 
#                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger('app')

# # Initialize the Flask app
# app = Flask(__name__)

# @app.before_request
# def before_request():
#     """Set start time for request timing"""
#     g.start_time = time.time()
    
# @app.after_request
# def after_request(response):
#     """Log request timing and perform cleanup if needed"""
#     if hasattr(g, 'start_time'):
#         elapsed = time.time() - g.start_time
#         logger.debug(f"Request processed in {elapsed:.4f} seconds")
    
#     # Special handling for streaming endpoints to ensure proper cleanup
#     if request.endpoint == 'video_feed' and response.status_code != 200:
#         logger.info("Video feed request terminated. Checking camera state.")
#         cam = get_camera()
#         if cam and not cam.is_running:
#             logger.warning("Camera stopped unexpectedly. Attempting restart.")
#             init_camera(cam.camera_id)
    
#     return response

# @app.route('/')
# def index():
#     """Home page with webcam feed and controls"""
#     return render_template('index.html')

# @app.route('/about')
# def about():
#     """About page with project information"""
#     return render_template('about.html')

# @app.route('/settings')
# def settings():
#     """Settings page for configuring gesture recognition parameters"""
#     return render_template('settings.html')

# @app.route('/api/status')
# def status():
#     """API endpoint for checking system status"""
#     cam = get_camera()
#     if cam is None:
#         return jsonify({
#             'status': 'offline',
#             'webcam_available': False,
#             'gesture_system': 'not initialized',
#             'error': 'Camera not initialized'
#         })
    
#     cam_status = cam.get_status()
    
#     return jsonify({
#         'status': 'online' if cam_status['running'] else 'offline',
#         'webcam_available': cam_status['running'],
#         'gesture_system': 'ready' if cam_status['running'] else 'not ready',
#         'fps': cam_status['fps'],
#         'camera_id': cam_status['camera_id'],
#         'last_error': cam_status['error']
#     })

# @app.route('/api/settings', methods=['POST'])
# def update_settings():
#     """Update camera and detection settings"""
#     cam = get_camera()
#     if cam is None:
#         return jsonify({'success': False, 'error': 'Camera not initialized'})
    
#     try:
#         data = request.json
#         if 'camera' in data:
#             # This would require restarting the camera
#             camera_id = int(data['camera'])
#             if camera_id != cam.camera_id:
#                 logger.info(f"Changing camera from ID {cam.camera_id} to {camera_id}")
#                 # Initialize a new camera with the selected ID
#                 init_camera(camera_id)
            
#         if 'detectionConfidence' in data:
#             cam.min_detection_confidence = float(data['detectionConfidence'])
            
#         if 'trackingConfidence' in data:
#             cam.min_tracking_confidence = float(data['trackingConfidence'])
            
#         if 'displayLandmarks' in data:
#             cam.show_landmarks = bool(data['displayLandmarks'])
            
#         if 'mirrorMode' in data:
#             cam.mirror = bool(data['mirrorMode'])
        
#         return jsonify({'success': True})
#     except Exception as e:
#         error_details = traceback.format_exc()
#         logger.error(f"Error in settings update: {error_details}")
#         return jsonify({'success': False, 'error': str(e), 'details': error_details})

# @app.route('/diagnostic')
# def diagnostic():
#     """Diagnostic page to check system status"""
#     cam = get_camera()
#     if cam is None:
#         camera_info = "No camera initialized"
#         camera_status = "Not available"
#     else:
#         status = cam.get_status()
#         camera_info = f"Camera ID: {status['camera_id']}"
#         camera_status = "Running" if status['running'] else "Stopped"
#         if status['error']:
#             camera_info += f" | Error: {status['error']}"

#     opencv_version = cv2.__version__
    
#     return render_template(
#         'diagnostic.html',
#         camera_status=camera_status,
#         camera_info=camera_info,
#         opencv_version=opencv_version,
#         now=time.time()  # Cache-busting parameter
#     )

# def gen_frames():
#     """Generator function for video streaming"""
#     try:
#         logger.info("Starting video streaming")
#         cam = get_camera()
#         if cam is None:
#             yield _generate_error_frame("Camera not initialized")
#             return
            
#         while True:
#             try:
#                 frame = cam.get_frame()
#                 if frame is not None:
#                     yield (b'--frame\r\n'
#                            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#                 else:
#                     yield _generate_error_frame("No frame available")
#                     time.sleep(0.1)
#             except Exception as e:
#                 logger.error(f"Error in frame generation: {str(e)}")
#                 yield _generate_error_frame(f"Frame error: {str(e)}")
#                 time.sleep(0.5)  # Prevent rapid error loops
#     except GeneratorExit:
#         # This is called when the client disconnects
#         logger.info("Client disconnected from video stream")
#     except Exception as e:
#         logger.error(f"Stream error: {str(e)}")
#         yield _generate_error_frame(f"Stream error: {str(e)}")

# def _generate_error_frame(error_message):
#     """Generate an error frame with message"""
#     # Create a black frame with error text
#     frame = np.zeros((480, 640, 3), dtype=np.uint8)
#     # Add error message
#     cv2.putText(
#         frame, 
#         "Stream Error", 
#         (150, 200), 
#         cv2.FONT_HERSHEY_SIMPLEX, 
#         1, 
#         (0, 0, 255), 
#         2
#     )
#     cv2.putText(
#         frame, 
#         error_message, 
#         (50, 250), 
#         cv2.FONT_HERSHEY_SIMPLEX, 
#         0.8, 
#         (255, 255, 255), 
#         1
#     )
    
#     # Encode the error frame
#     ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
#     if ret:
#         return (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
#     else:
#         return (b'--frame\r\n'
#                b'Content-Type: text/plain\r\n\r\n'
#                b'Error generating error frame\r\n')

# @app.route('/video_feed')
# def video_feed():
#     """Route for streaming video content"""
#     # Return a multipart response with MJPEG content type
#     return Response(
#         gen_frames(),
#         mimetype='multipart/x-mixed-replace; boundary=frame'
#     )

# @app.route('/restart_camera')
# def restart_camera():
#     """Restart the camera with the current settings"""
#     try:
#         cam = get_camera()
#         camera_id = 0 if cam is None else cam.camera_id
#         logger.info(f"Manual camera restart requested for camera ID: {camera_id}")
#         init_camera(camera_id)
#         return jsonify({'success': True})
#     except Exception as e:
#         logger.error(f"Error restarting camera: {e}")
#         return jsonify({'success': False, 'error': str(e)})

# @app.route('/shutdown')
# def shutdown():
#     """Shutdown the camera and application"""
#     logger.info("Manual shutdown requested")
#     cleanup_camera()
#     return "Camera has been shut down."

# @app.teardown_appcontext
# def shutdown_camera_context(exception=None):
#     """Ensure camera is properly managed between requests"""
#     # We don't want to shut down the camera after every request,
#     # but we can use this to log exceptions
#     if exception:
#         logger.error(f"Exception during request: {exception}")
        
#         # Check if camera is still running
#         cam = get_camera()
#         if cam and not cam.is_running:
#             logger.warning("Camera stopped unexpectedly during request handling")

# # Clean up when Flask is shutting down
# @atexit.register
# def shutdown_on_exit():
#     """Ensure all resources are released when the application exits"""
#     logger.info("Application shutting down, cleaning up resources")
#     cleanup_camera()
#     cv2.destroyAllWindows()

# def handle_exception(exc_type, exc_value, exc_traceback):
#     """Handle uncaught exceptions"""
#     if issubclass(exc_type, KeyboardInterrupt):
#         # Call the original handler for KeyboardInterrupt
#         import sys
#         sys.__excepthook__(exc_type, exc_value, exc_traceback)
#         return
        
#     logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
#     cleanup_camera()

# # Set our custom exception handler
# import sys
# sys.excepthook = handle_exception

# if __name__ == '__main__':
#     try:
#         logger.info("Starting GestureDrive application")
#         # Register a function to be called when the application exits
#         atexit.register(cleanup_camera)
        
#         # Also handle signals for more robust cleanup
#         import signal
#         signal.signal(signal.SIGINT, lambda s, f: (cleanup_camera(), sys.exit(0)))
#         signal.signal(signal.SIGTERM, lambda s, f: (cleanup_camera(), sys.exit(0)))
        
#         app.run(debug=True, threaded=True, host='0.0.0.0', use_reloader=False)
#     except Exception as e:
#         logger.error(f"Error starting application: {str(e)}")
#         cleanup_camera()
#     finally:
#         # Final cleanup attempt
#         logger.info("Application main block exiting, final cleanup")
#         cleanup_camera()
#         cv2.destroyAllWindows()
from flask import Flask, Response, render_template, jsonify
import time
import atexit
import threading

from camera import Camera
from gesture_recognizer import GestureRecognizer
from gesture_file_controller import GestureFileController
app = Flask(__name__)

# Global instances
camera = None
recognizer = None
camera_lock = threading.Lock()
file_controller = GestureFileController()
def get_camera():
    global camera
    with camera_lock:
        if camera is None:
            # Lazy initialization
            camera = Camera(camera_id=0, width=640, height=480)
            camera.start()
    return camera

def get_recognizer():
    global recognizer
    if recognizer is None:
        recognizer = GestureRecognizer(buffer_size=5)
    return recognizer

@app.route('/api/gestures')
def api_gestures():
    """API endpoint to get current gesture data including selection gestures"""
    gesture_data = {
        'gesture': camera.current_gesture,
        'motion': camera.current_motion,
        'selection_gesture': camera.current_selection_gesture
    }
    return jsonify(gesture_data)

@app.route('/files')
def files():
    """File browser page with gesture-based navigation and selection"""
    return render_template('files.html')

@app.route('/api/directory')
def api_directory():
    """API endpoint to get current directory information"""
    return jsonify(file_controller.get_directory_info())

@app.route('/api/navigate')
def api_navigate():
    """API endpoint for directory navigation"""
    direction = request.args.get('direction', '')
    success = file_controller.navigate_directory(direction)
    
    return jsonify({
        'success': success,
        'directory': file_controller.get_directory_info()
    })

# Add API endpoint for selection navigation
@app.route('/api/select')
def api_select():
    """API endpoint for file selection navigation"""
    action = request.args.get('action', '')
    
    if action == 'next':
        success = file_controller.select_next()
    elif action == 'previous':
        success = file_controller.select_previous()
    else:
        success = False
    
    return jsonify({
        'success': success,
        'directory': file_controller.get_directory_info()
    })

# Add API endpoint for processing selection gestures
@app.route('/api/process_selection')
def api_process_selection():
    """API endpoint for processing selection gestures"""
    gesture = request.args.get('gesture', '')
    result = file_controller.process_selection_gesture(gesture)
    
    # Add directory info to the response
    result['directory'] = file_controller.get_directory_info()
    
    return jsonify(result)

def gesture_processor():
    """Background thread to process gestures and update file selection"""
    last_update_time = 0
    cooldown = 0.5  # seconds between updates
    
    while True:
        current_time = time.time()
        
        if current_time - last_update_time > cooldown:
            # Process motion gestures for navigation
            if camera.current_motion == "swipe_up":
                file_controller.select_previous()
                last_update_time = current_time
            elif camera.current_motion == "swipe_down":
                file_controller.select_next()
                last_update_time = current_time
            elif camera.current_motion == "swipe_left":
                file_controller.navigate_directory("up")
                last_update_time = current_time
            elif camera.current_motion == "swipe_right":
                file_controller.navigate_directory("down")
                last_update_time = current_time
                
            # Process selection gestures
            if camera.current_selection_gesture:
                file_controller.process_selection_gesture(camera.current_selection_gesture)
                last_update_time = current_time
        
        time.sleep(0.1)  # Sleep to avoid excessive CPU usage

# Start gesture processor thread when app starts
import threading
from werkzeug.serving import is_running_from_reloader

@app.before_first_request
def start_gesture_thread():
    """Start the background gesture processing thread"""
    if not is_running_from_reloader() or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=gesture_processor, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route for MJPEG."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames():
    """Generate MJPEG frames for streaming."""
    cam = get_camera()
    while True:
        # Get JPEG encoded frame
        frame = cam.get_jpeg_frame(processed=True)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/api/status')
def api_status():
    """API endpoint to get system status."""
    cam = get_camera()
    rec = get_recognizer()
    
    status = {
        'fps': cam.fps,
        'camera_running': cam.is_running,
        'current_gesture': rec.current_gesture,
        'current_command': rec.get_command()
    }
    return jsonify(status)

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """API endpoint to get/update settings."""
    # Implementation depends on your specific requirements
    pass

@app.route('/api/current_gestures', methods=['GET'])
def get_current_gestures():
    """API endpoint to get the current gestures with validation status"""
    camera = current_app.config.get('camera')
    
    if not camera:
        return jsonify({
            'error': 'Camera not initialized'
        }), 503
    
    # Get gesture data including validation status
    gesture_data = camera.get_current_gestures()
    
    return jsonify(gesture_data)

@app.route('/api/navigate', methods=['POST'])
def navigate():
    """API endpoint to process validated navigation gestures"""
    data = request.json
    gesture = data.get('gesture')
    motion_gesture = data.get('motion_gesture')
    
    if not gesture and not motion_gesture:
        return jsonify({'error': 'No gesture provided'}), 400
    
    # Get the navigator instance
    navigator = current_app.config.get('gesture_navigator')
    if not navigator:
        return jsonify({'error': 'Navigator not initialized'}), 500
    
    # Use validated gestures for navigation (prioritizing motion gestures)
    if motion_gesture and motion_gesture != 'stationary':
        state = navigator.process_gesture(motion_gesture)
    elif gesture:
        state = navigator.process_gesture(gesture)
    else:
        state = navigator.get_current_state()
        
    return jsonify(state)

@app.route('/api/toggle_validation_display', methods=['POST'])
def toggle_validation_display():
    """Toggle the display of validation information on the video feed"""
    camera = current_app.config.get('camera')
    
    if not camera:
        return jsonify({'error': 'Camera not initialized'}), 503
    
    # Toggle debug display
    show_status = camera.toggle_validation_display()
    
    return jsonify({
        'show_validation_status': show_status
    })

def cleanup_resources():
    """Ensure proper cleanup of resources when Flask shuts down."""
    global camera
    if camera:
        print("Shutting down camera...")
        camera.stop()
        camera = None

# Register cleanup function
atexit.register(cleanup_resources)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)