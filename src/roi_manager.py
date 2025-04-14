import cv2
import numpy as np

class ROIManager:
    def __init__(self, roi_rect, presence_threshold_percent):
        self.roi_rect = roi_rect
        self.presence_threshold_percent = presence_threshold_percent

    def is_object_present(self, frame_rgb):
        x, y, w, h = self.roi_rect
        roi_zone = frame_rgb[y:y + h, x:x + w]
        gray_roi = cv2.cvtColor(roi_zone, cv2.COLOR_BGR2GRAY)
        _, binary_roi = cv2.threshold(gray_roi, 200, 255, cv2.THRESH_BINARY)
        white_pixels_roi = np.sum(binary_roi > 0)
        total_pixels_roi = roi_zone.shape[0] * roi_zone.shape[1]

        if total_pixels_roi > 0 and (white_pixels_roi / total_pixels_roi) > self.presence_threshold_percent:
            return True
        return False