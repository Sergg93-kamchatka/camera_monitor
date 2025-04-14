import os
from config_manager import ConfigManager
from video_stream_handler import VideoStreamHandler
from motion_detector import MotionDetector
from roi_manager import ROIManager
from image_saver import ImageSaver
from gui_handler import GUIHandler

def main():
    config_file_path = os.path.join(os.getcwd(), 'config.ini') # Получаем полный путь к config.ini в текущей рабочей директории
    config = ConfigManager(config_file_path)
    print(f"Попытка чтения конфигурации из файла: {config_file_path}") # Для отладки
    print(f"Прочитанный RTSP URL из config.ini: {config.get('RTSP', 'url')}")
    video_handler = VideoStreamHandler(config.get('RTSP', 'url'))
    motion_detector = MotionDetector(config.get_list_int('MotionDetection', 'motion_rect1'),
                                     config.get_list_int('MotionDetection', 'motion_rect2'),
                                     config.get_int('MotionDetection', 'threshold'),
                                     config.get_float('MotionDetection', 'delay'))
    roi_manager = ROIManager(config.get_list_int('ROICheck', 'roi_rect'),
                             config.get_float('ROICheck', 'presence_threshold_percent'))
    image_saver = ImageSaver(config.get('Directories', 'save_dir'),
                             config.get_float('ROICheck', 'min_save_interval'))
    gui_handler = GUIHandler(video_handler, motion_detector, roi_manager, image_saver, config)
    gui_handler.run()

if __name__ == "__main__":
    main()