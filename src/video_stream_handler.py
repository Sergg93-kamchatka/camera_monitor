import cv2
import numpy as np
import ffmpeg
import threading
import time
import subprocess

class VideoStreamHandler:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.process = None
        self.width = None
        self.height = None
        self._frame = None
        self._gray_frame = None
        self._lock = threading.Lock()
        self._running = True
        self._start_stream()

    def _start_stream(self):
        while self._running:
            try:
                # Проверка доступности потока
                probe = ffmpeg.probe(self.rtsp_url, timeout=15)
                video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                if not video_stream:
                    raise Exception("Не найден видеопоток.")
                
                self.width = video_stream['width']
                self.height = video_stream['height']
                print(f"Ширина видеопотока: {self.width}, Высота видеопотока: {self.height}")

                # Настройка FFmpeg с явным форматом пикселей
                command = (
                    ffmpeg
                    .input(self.rtsp_url, rtsp_transport='tcp', timeout='15000000', re=None)
                    .output('pipe:', format='rawvideo', pix_fmt='bgr24', vsync='0')
                    .compile()
                )

                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=10**7,  # Увеличенный буфер
                    universal_newlines=False
                )

                threading.Thread(target=self._read_frames, daemon=True).start()
                threading.Thread(target=self._read_stderr, args=(self.process.stderr,), daemon=True).start()

                # Ожидание первого кадра
                start_time = time.time()
                while self._frame is None and time.time() - start_time < 15 and self._running:
                    time.sleep(0.1)
                if self._frame is None:
                    print("Не удалось получить первый кадр за 15 секунд.")
                    self.release()
                    time.sleep(3)
                    continue

                print("Поток успешно запущен.")
                break  # Успешное подключение

            except ffmpeg.Error as e:
                print(f"Ошибка FFmpeg (probe): {e}")
                self.release()
                time.sleep(3)
            except FileNotFoundError:
                print("Ошибка: FFmpeg не найден. Убедитесь, что FFmpeg установлен и добавлен в PATH.")
                self._running = False
                break
            except Exception as e:
                print(f"Произошла ошибка при запуске потока: {e}")
                self.release()
                time.sleep(3)

    def _read_frames(self):
        while self.process and self.process.poll() is None and self._running:
            try:
                raw_frame = self.process.stdout.read(self.width * self.height * 3)
                if len(raw_frame) != self.width * self.height * 3:
                    print("FFmpeg: Неполный кадр, попытка переподключения...")
                    break
                frame_np = np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
                gray_frame = cv2.cvtColor(frame_np, cv2.COLOR_BGR2GRAY)
                with self._lock:
                    self._frame = frame_np
                    self._gray_frame = gray_frame
                time.sleep(0.001)
            except Exception as e:
                print(f"Ошибка при чтении кадра: {e}")
                break
        self.release()
        if self._running:
            print("Переподключение потока...")
            time.sleep(1)
            self._start_stream()

    def _read_stderr(self, stderr):
        for line in iter(lambda: stderr.readline(), b''):
            print(f"FFmpeg stderr: {line.decode('utf-8', errors='ignore').strip()}")
        stderr.close()

    def read_frame(self):
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def get_frame_grayscale(self):
        with self._lock:
            return self._gray_frame.copy() if self._gray_frame is not None else None

    def get_frame_rgb(self):
        frame = self.read_frame()
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame is not None else None

    def release(self):
        if self.process:
            print("Завершение процесса FFmpeg...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process.stdout.close()
            print("Процесс FFmpeg завершен.")
            self.process = None
            with self._lock:
                self._frame = None
                self._gray_frame = None