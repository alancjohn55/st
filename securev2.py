import os
from datetime import datetime
import cv2
import numpy as np
from time import sleep
from api_wh import API

greenAPI = API.GreenAPI("7103150461", "4c8cf4dbada046e7b69cdcac79b03b163e7590cf013646d0ac")

class SecurityCamera:
    def __init__(self):
        # Video parameters
        self.base_path = os.path.join(os.getcwd(), 'surveillance_footage')
        self.recording_time = 10  # seconds
        self.motion_threshold = 2.5  # Adjust this value based on sensitivity needs
        
        # Initialize camera
        self.camera = cv2.VideoCapture(0)  # Try 1 or 2 if camera not found
        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera")
        
        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        self.previous_frame = None
        self.setup_storage()
    
    def setup_storage(self):
        """Setup directory structure for video storage"""
        # Create main surveillance directory
        os.makedirs(self.base_path, exist_ok=True)
        
        # Create date-based directory
        current_date = datetime.now().strftime('%Y-%m-%d')
        self.current_storage_path = os.path.join(self.base_path, current_date)
        os.makedirs(self.current_storage_path, exist_ok=True)
    
    def detect_motion(self):
        """Detect motion using frame differencing"""
        ret, frame = self.camera.read()
        if not ret:
            return False
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Initialize previous frame
        if self.previous_frame is None:
            self.previous_frame = gray
            return False
        
        # Calculate absolute difference between frames
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        
        # Update previous frame
        self.previous_frame = gray
        
        # Calculate the percentage of changed pixels
        motion_pixels = np.sum(thresh > 0)
        total_pixels = thresh.size
        motion_percentage = (motion_pixels / total_pixels) * 100
        
        return motion_percentage > self.motion_threshold
    
    def capture_video(self):
        """Record video for specified duration"""
        # Check if we need to create a new date directory
        current_date = datetime.now().strftime('%Y-%m-%d')
        if not os.path.basename(self.current_storage_path) == current_date:
            self.setup_storage()
        
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%H-%M-%S')
        filename = f"motion_detected_{timestamp}.mp4"
        filepath = os.path.join(self.current_storage_path, filename)
        
        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, 20.0, (640, 480))
        
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < self.recording_time:
            ret, frame = self.camera.read()
            if ret:
                out.write(frame)
        
        out.release()
        return filepath, filename
    
    def run(self):
        """Main loop"""
        print("Security system started. Press Ctrl+C to stop.")
        print(f"Footage will be saved to: {self.base_path}")
        
        try:
            while True:
                if self.detect_motion():
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"Motion Detected at {current_time}")
                    
                    # Send WhatsApp notification
                    response = greenAPI.sending.sendMessage(
                        "918943815982@c.us", 
                        f"Motion detected at {current_time}"
                    )
                    print(f"Notification sent: {response.data}")
                    
                    # Capture and save video
                    filepath, filename = self.capture_video()
                    print(f"Video saved: {filename}")
                    
                    sleep(2)  # Brief pause before next detection
                sleep(0.1)
        except KeyboardInterrupt:
            print("\nSecurity system stopped")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Release camera and cleanup"""
        if self.camera.isOpened():
            self.camera.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    # Create and run security camera system
    security_system = SecurityCamera()
    security_system.run()
