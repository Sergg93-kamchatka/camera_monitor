import cv2
import numpy as np
import time

class MotionDetector:
    def __init__(self, motion_rect1, motion_rect2, threshold, delay):
        self.motion_rect1 = motion_rect1
        self.motion_rect2 = motion_rect2
        self.threshold = threshold
        self.delay = delay
        self.last_motion_time = None
        self.last_motion_frame = None

    def detect(self, frame_gray):
        motion_detected = False
        current_time = time.time()

        if self.last_motion_frame is not None:
            # Детекция движения в первой зоне
            x1, y1, w1, h1 = self.motion_rect1
            diff1 = cv2.absdiff(frame_gray[y1:y1 + h1, x1:x1 + w1],
                                self.last_motion_frame[y1:y1 + h1, x1:x1 + w1])
            _, thresh1 = cv2.threshold(diff1, 30, 255, cv2.THRESH_BINARY)
            motion_pixels1 = np.sum(thresh1 > 0)

            # Детекция движения во второй зоне
            x2, y2, w2, h2 = self.motion_rect2
            diff2 = cv2.absdiff(frame_gray[y2:y2 + h2, x2:x2 + w2],
                                self.last_motion_frame[y2:y2 + h2, x2:x2 + w2])
            _, thresh2 = cv2.threshold(diff2, 30, 255, cv2.THRESH_BINARY)
            motion_pixels2 = np.sum(thresh2 > 0)

            if motion_pixels1 > self.threshold or motion_pixels2 > self.threshold:
                motion_detected = True
                self.last_motion_time = current_time
            elif self.last_motion_time is not None and (current_time - self.last_motion_time) > self.delay:
                motion_detected = False  # Сбрасываем, если прошло время задержки и движения нет
                self.last_motion_time = None

        self.last_motion_frame = frame_gray.copy()
        return motion_detected