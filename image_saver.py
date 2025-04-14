import cv2
import os
from datetime import datetime
import time

class ImageSaver:
    def __init__(self, save_dir, min_save_interval):
        self.save_dir = save_dir
        self.min_save_interval = min_save_interval
        self.last_save_time = None
        os.makedirs(self.save_dir, exist_ok=True)

    def save(self, frame):
        current_time = time.time()
        if self.last_save_time is None or (current_time - self.last_save_time) > self.min_save_interval:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.save_dir, f"car_{timestamp}.png")
            cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)) # Сохраняем в BGR
            print(f"Сохранено изображение: {filename}")
            self.last_save_time = current_time