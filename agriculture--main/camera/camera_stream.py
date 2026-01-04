import cv2
import time


class CameraStream:
    """
    CameraStream
    -------------
    Responsible ONLY for:
    - Opening the camera
    - Reading frames safely
    - Optional FPS calculation
    - Releasing resources
    """

    def __init__(self, camera_index=0, width=640, height=480):
        """
        Initialize the camera.
        This runs ONCE.
        """
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise RuntimeError("ERROR: Camera not accessible")

        # Set resolution (performance friendly)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # FPS tracking
        self.prev_time = time.time()
        self.fps = 0

    def read_frame(self):
        """
        Read a single frame from the camera.
        Returns:
            frame (numpy array) or None if failed
        """
        ret, frame = self.cap.read()
        if not ret:
            return None

        # FPS calculation
        current_time = time.time()
        self.fps = 1 / (current_time - self.prev_time)
        self.prev_time = current_time

        return frame

    def get_fps(self):
        """
        Returns current FPS (integer)
        """
        return int(self.fps)

    def release(self):
        """
        Release camera and destroy windows
        """
        self.cap.release()
        cv2.destroyAllWindows()
