import cv2
import numpy as np
import ffmpeg
import threading
import time
import subprocess  # Импортируем subprocess

class VideoStreamHandler:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.process = None
        self.width = None
        self.height = None
        self._frame = None
        self._gray_frame = None
        self._lock = threading.Lock()
        self._start_stream()

    def _start_stream(self):
        try:
            probe = ffmpeg.probe(self.rtsp_url)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if video_stream:
                self.width = video_stream['width']
                self.height = video_stream['height']
                print(f"Ширина видеопотока: {self.width}, Высота видеопотока: {self.height}")
            else:
                raise Exception("Не найден видеопоток.")

            command = (
                ffmpeg
                .input(self.rtsp_url, format='rtsp')
                .output('pipe', format='rawvideo', pix_fmt='bgr24')
                .compile()
            )

            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1024 * 1024) # Увеличиваем bufsize

            threading.Thread(target=self._read_frames, daemon=True).start()
            threading.Thread(target=self._read_stderr, args=(self.process.stderr,), daemon=True).start()

        except ffmpeg.Error as e:
            print(f"Ошибка при запуске FFmpeg (probe): {e}")
            self.process = None
        except FileNotFoundError:
            print("Ошибка: Не найден FFmpeg. Убедитесь, что FFmpeg установлен и добавлен в PATH.")
            self.process = None
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            self.process = None

    def _read_frames(self):
        while self.process and self.process.poll() is None:
            try:
                raw_frame = self.process.stdout.read(self.width * self.height * 3)
                if not raw_frame:
                    print("FFmpeg: Пустой кадр, завершение (чтение stdout)...")
                    break
                frame_np = np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
                gray_frame = cv2.cvtColor(frame_np, cv2.COLOR_BGR2GRAY)
                with self._lock:
                    self._frame = frame_np
                    self._gray_frame = gray_frame
                time.sleep(0.001)
            except Exception as e:
                print(f"Ошибка при чтении кадра (stdout): {e}")
                break
            except BrokenPipeError:
                print("FFmpeg: Broken pipe (stdout). Завершение...")
                break

    def _read_stderr(self, stderr):
        for line in iter(stderr.readline, b''):
            print(f"FFmpeg stderr: {line.decode('utf8').strip()}")
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
            self.process.wait()
            print("Процесс FFmpeg завершен.")
            self.process = None