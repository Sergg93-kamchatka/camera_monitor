import configparser
import os

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        print(f"Попытка загрузить конфигурацию из файла: {self.config_file}") # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
        if os.path.exists(self.config_file):
            print(f"Файл конфигурации найден.") # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
            self.config.read(self.config_file)
            print(f"Конфигурация прочитана. Содержимое секции RTSP: {self.config.get('RTSP', 'url', fallback='не найдено')}") # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
        else:
            print(f"Файл конфигурации не найден. Создается конфигурация по умолчанию.") # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
            self.create_default_config()
            self.save_config()

    def create_default_config(self):
        self.config['RTSP'] = {'url': 'rtsp://your_rtsp_url'}
        self.config['Directories'] = {'save_dir': 'captured_cars', 'config_file': 'config.txt'}
        self.config['MotionDetection'] = {'threshold': '50', 'delay': '1.0', 'motion_rect1': '50, 50, 100, 80', 'motion_rect2': '150, 100, 120, 90'}
        self.config['ROICheck'] = {'presence_threshold_percent': '0.3', 'min_save_interval': '2.0', 'roi_rect': '200, 150, 120, 90'}
        self.config['UI'] = {'resize_handle_size': '8'}

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
            print(f"Конфигурация сохранена в файл: {self.config_file}") # <--- ДОБАВЬТЕ ЭТУ СТРОКУ

    def get(self, section, key):
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return None

    def get_int(self, section, key):
        value = self.get(section, key)
        return int(value) if value is not None else None

    def get_float(self, section, key):
        value = self.get(section, key)
        return float(value) if value is not None else None

    def get_list_int(self, section, key):
        value = self.get(section, key)
        return list(map(int, value.split(','))) if value else None