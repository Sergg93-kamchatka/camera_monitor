import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading
import time

class GUIHandler:
    def __init__(self, video_handler, motion_detector, roi_manager, image_saver, config):
        self.video_handler = video_handler
        self.motion_detector = motion_detector
        self.roi_manager = roi_manager
        self.image_saver = image_saver
        self.config = config

        self.root = tk.Tk()
        self.root.title("Camera Monitor")
        self.root.geometry("1280x720")
        self.panel = tk.Label(self.root)
        self.panel.pack(fill="both", expand=True)

        self.motion_rect1 = self.config.get_list_int('MotionDetection', 'motion_rect1')
        self.motion_rect2 = self.config.get_list_int('MotionDetection', 'motion_rect2')
        self.roi_rect = self.config.get_list_int('ROICheck', 'roi_rect')
        self.resize_handle_size = self.config.get_int('UI', 'resize_handle_size')

        self.dragging_motion1 = False
        self.drag_offset_motion1 = [0, 0]
        self.resizing_motion1 = None

        self.dragging_motion2 = False
        self.drag_offset_motion2 = [0, 0]
        self.resizing_motion2 = None

        self.dragging_roi = False
        self.drag_offset_roi = [0, 0]
        self.resizing_roi = None

        self.mouse_x, self.mouse_y = -1, -1
        self.stream_active = True
        self.show_handles_motion1 = False
        self.show_handles_motion2 = False
        self.show_handles_roi = False

        self.panel.bind("<Button-1>", self.on_mouse_press)
        self.panel.bind("<Motion>", self.on_mouse_move)
        self.panel.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.last_frame = None
        self.update_frame()

    def on_closing(self):
        print("Закрытие приложения...")
        self.stream_active = False
        self.video_handler.release()
        self.root.destroy()

    def check_resize_handle(self, rect, x, y):
        rx, ry, rw, rh = rect
        h = self.resize_handle_size // 2
        if rx - h < x < rx + h and ry - h < y < ry + h: return 'nw'
        if rx + rw - h < x < rx + rw + h and ry - h < y < ry + h: return 'ne'
        if rx - h < x < rx + h and ry + rh - h < y < ry + rh + h: return 'sw'
        if rx + rw - h < x < rx + rw + h and ry + rh - h < y < ry + rh + h: return 'se'
        if rx - h < x < rx + h and ry < y < ry + rh: return 'w'
        if rx + rw - h < x < rx + rw + h and ry < y < ry + rh: return 'e'
        if rx < x < rx + rw and ry - h < y < ry + h: return 'n'
        if rx < x < rx + rw and ry + rh - h < y < ry + rh + h: return 's'
        return None

    def on_mouse_press(self, event):
        self.resizing_motion1 = self.check_resize_handle(self.motion_rect1, event.x, event.y)
        self.resizing_motion2 = self.check_resize_handle(self.motion_rect2, event.x, event.y)
        self.resizing_roi = self.check_resize_handle(self.roi_rect, event.x, event.y)

        if self.resizing_motion1:
            self.show_handles_motion1 = True
        elif self.resizing_motion2:
            self.show_handles_motion2 = True
        elif self.resizing_roi:
            self.show_handles_roi = True

        if not self.resizing_motion1:
            rx, ry, rw, rh = self.motion_rect1
            if rx < event.x < rx + rw and ry < event.y < ry + rh:
                self.dragging_motion1 = True
                self.show_handles_motion1 = True
                self.drag_offset_motion1 = [event.x - rx, event.y - ry]

        if not self.resizing_motion2:
            rx, ry, rw, rh = self.motion_rect2
            if rx < event.x < rx + rw and ry < event.y < ry + rh:
                self.dragging_motion2 = True
                self.show_handles_motion2 = True
                self.drag_offset_motion2 = [event.x - rx, event.y - ry]

        if not self.resizing_roi:
            rx, ry, rw, rh = self.roi_rect
            if rx < event.x < rx + rw and ry < event.y < ry + rh:
                self.dragging_roi = True
                self.show_handles_roi = True
                self.drag_offset_roi = [event.x - rx, event.y - ry]

    def on_mouse_move(self, event):
        self.mouse_x, self.mouse_y = event.x, event.y

        if self.dragging_motion1:
            self.motion_rect1[0] = event.x - self.drag_offset_motion1[0]
            self.motion_rect1[1] = event.y - self.drag_offset_motion1[1]
        elif self.dragging_motion2:
            self.motion_rect2[0] = event.x - self.drag_offset_motion2[0]
            self.motion_rect2[1] = event.y - self.drag_offset_motion2[1]
        elif self.dragging_roi:
            self.roi_rect[0] = event.x - self.drag_offset_roi[0]
            self.roi_rect[1] = event.y - self.drag_offset_roi[1]
        elif self.resizing_motion1:
            r = list(self.motion_rect1)
            if self.resizing_motion1 == 'nw': self.motion_rect1 = [event.x, event.y, r[0] + r[2] - event.x, r[1] + r[3] - event.y]
            elif self.resizing_motion1 == 'ne': self.motion_rect1 = [r[0], event.y, event.x - r[0], r[1] + r[3] - event.y]
            elif self.resizing_motion1 == 'sw': self.motion_rect1 = [event.x, r[1], r[0] + r[2] - event.x, event.y - r[1]]
            elif self.resizing_motion1 == 'se': self.motion_rect1 = [r[0], r[1], event.x - r[0], event.y - r[1]]
            elif self.resizing_motion1 == 'n': self.motion_rect1 = [r[0], event.y, r[2], r[1] + r[3] - event.y]
            elif self.resizing_motion1 == 's': self.motion_rect1 = [r[0], r[1], r[2], event.y - r[1]]
            elif self.resizing_motion1 == 'e': self.motion_rect1 = [r[0], r[1], event.x - r[0], r[3]]
            elif self.resizing_motion1 == 'w': self.motion_rect1 = [event.x, r[1], r[0] + r[2] - event.x, r[3]]
            self.motion_rect1[2] = max(1, self.motion_rect1[2])
            self.motion_rect1[3] = max(1, self.motion_rect1[3])
        elif self.resizing_motion2:
            r = list(self.motion_rect2)
            if self.resizing_motion2 == 'nw': self.motion_rect2 = [event.x, event.y, r[0] + r[2] - event.x, r[1] + r[3] - event.y]
            elif self.resizing_motion2 == 'ne': self.motion_rect2 = [r[0], event.y, event.x - r[0], r[1] + r[3] - event.y]
            elif self.resizing_motion2 == 'sw': self.motion_rect2 = [event.x, r[1], r[0] + r[2] - event.x, event.y - r[1]]
            elif self.resizing_motion2 == 'se': self.motion_rect2 = [r[0], r[1], event.x - r[0], event.y - r[1]]
            elif self.resizing_motion2 == 'n': self.motion_rect2 = [r[0], event.y, r[2], r[1] + r[3] - event.y]
            elif self.resizing_motion2 == 's': self.motion_rect2 = [r[0], r[1], r[2], event.y - r[1]]
            elif self.resizing_motion2 == 'e': self.motion_rect2 = [r[0], r[1], event.x - r[0], r[3]]
            elif self.resizing_motion2 == 'w': self.motion_rect2 = [event.x, r[1], r[0] + r[2] - event.x, r[3]]
            self.motion_rect2[2] = max(1, self.motion_rect2[2])
            self.motion_rect2[3] = max(1, self.motion_rect2[3])
        elif self.resizing_roi:
            r = list(self.roi_rect)
            if self.resizing_roi == 'nw': self.roi_rect = [event.x, event.y, r[0] + r[2] - event.x, r[1] + r[3] - event.y]
            elif self.resizing_roi == 'ne': self.roi_rect = [r[0], event.y, event.x - r[0], r[1] + r[3] - event.y]
            elif self.resizing_roi == 'sw': self.roi_rect = [event.x, r[1], r[0] + r[2] - event.x, event.y - r[1]]
            elif self.resizing_roi == 'se': self.roi_rect = [r[0], r[1], event.x - r[0], event.y - r[1]]
            elif self.resizing_roi == 'n': self.roi_rect = [r[0], event.y, r[2], r[1] + r[3] - event.y]
            elif self.resizing_roi == 's': self.roi_rect = [r[0], r[1], r[2], event.y - r[1]]
            elif self.resizing_roi == 'e': self.roi_rect = [r[0], r[1], event.x - r[0], r[3]]
            elif self.resizing_roi == 'w': self.roi_rect = [event.x, r[1], r[0] + r[2] - event.x, r[3]]
            self.roi_rect[2] = max(1, self.roi_rect[2])
            self.roi_rect[3] = max(1, self.roi_rect[3])

    def on_mouse_release(self, event):
        self.dragging_motion1 = False
        self.dragging_motion2 = False
        self.dragging_roi = False
        self.resizing_motion1 = None
        self.resizing_motion2 = None
        self.resizing_roi = None
        self.show_handles_motion1 = False
        self.show_handles_motion2 = False
        self.show_handles_roi = False
        self.save_zone_config()

    def save_zone_config(self):
        self.config.config['MotionDetection']['motion_rect1'] = ', '.join(map(str, self.motion_rect1))
        self.config.config['MotionDetection']['motion_rect2'] = ', '.join(map(str, self.motion_rect2))
        self.config.config['ROICheck']['roi_rect'] = ', '.join(map(str, self.roi_rect))
        self.config.save_config()

    def draw_zones(self, frame):
        frame_height, frame_width = frame.shape[:2]
        for rect in [self.motion_rect1, self.motion_rect2, self.roi_rect]:
            rect[0] = max(0, min(rect[0], frame_width - rect[2]))
            rect[1] = max(0, min(rect[1], frame_height - rect[3]))
            rect[2] = max(1, min(rect[2], frame_width - rect[0]))
            rect[3] = max(1, min(rect[3], frame_height - rect[1]))

        x1, y1, w1, h1 = map(int, self.motion_rect1)
        x2, y2, w2, h2 = map(int, self.motion_rect2)
        rx, ry, rw, rh = map(int, self.roi_rect)
        # Красный для motion_rect1 (BGR: 0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (0, 0, 255), 2)
        # Синий для motion_rect2 (BGR: 255, 0, 0)
        cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (255, 0, 0), 2)
        # Зелёный для ROI (оставляем как есть, BGR: 0, 255, 0)
        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (0, 255, 0), 2)

        if self.show_handles_motion1:
            self.draw_resize_handles(frame, self.motion_rect1)
        if self.show_handles_motion2:
            self.draw_resize_handles(frame, self.motion_rect2)
        if self.show_handles_roi:
            self.draw_resize_handles(frame, self.roi_rect)

        return frame

    def draw_resize_handles(self, frame, rect):
        rx, ry, rw, rh = map(int, rect)
        h = self.resize_handle_size // 2
        handles = [
            (rx - h, ry - h), (rx + rw - h, ry - h),
            (rx - h, ry + rh - h), (rx + rw - h, ry + rh - h)
        ]
        for hx, hy in handles:
            cv2.rectangle(frame, (hx, hy), (hx + self.resize_handle_size, hy + self.resize_handle_size), (0, 255, 255), -1)

    def update_frame(self):
        if not self.stream_active:
            return

        frame_rgb = self.video_handler.get_frame_rgb()
        if frame_rgb is None:
            if self.last_frame is not None:
                frame_pil = Image.fromarray(self.last_frame)
                imgtk = ImageTk.PhotoImage(image=frame_pil)
                self.panel.imgtk = imgtk
                self.panel.config(image=imgtk)
            self.root.after(100, self.update_frame)
            return

        self.last_frame = self.draw_zones(frame_rgb.copy())
        frame_pil = Image.fromarray(self.last_frame)
        imgtk = ImageTk.PhotoImage(image=frame_pil)
        self.panel.imgtk = imgtk
        self.panel.config(image=imgtk)

        frame_gray = self.video_handler.get_frame_grayscale()
        if frame_gray is not None:
            motion_detected = self.motion_detector.detect(frame_gray)
            if motion_detected:
                if self.motion_detector.last_motion_time is not None and \
                   (time.time() - self.motion_detector.last_motion_time) > self.motion_detector.delay:
                    if self.roi_manager.is_object_present(frame_rgb):
                        self.image_saver.save(frame_rgb)

        self.root.after(50, self.update_frame)

    def run(self):
        self.root.mainloop()