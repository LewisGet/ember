import cv2
import numpy as np
import subprocess


class Ember:
    def __init__(self, config):
        self.adb_path = config.adb_path
        self.screen_cache_path = config.screen_cache_path

    def get_screen(self):
        p = subprocess.Popen([self.adb_path, "exec-out", "screencap", "-p", ">", self.screen_cache_path])
        p.wait()

        return cv2.imread(self.screen_cache_path)

    def touch_screen(self, x, y):
        p = subprocess.Popen([self.adb_path, "shell", "input", "tap", str(x), str(y)])
        p.wait()

    def swipe(self, x_start, y_start, x_end, y_end, duration=30):
        p = subprocess.Popen([self.adb_path, "shell", "input", "swipe", str(x_start), str(y_start), str(x_end), str(y_end), str(duration)])
        p.wait()

    def get_images_location(self, target_image_path, similarity):
        screen = self.get_screen()
        target_image_array = cv2.imread(target_image_path)
        w, h = target_image_array.shape[:-1]

        res = cv2.matchTemplate(screen, target_image_array, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= similarity)

        xs, ys = locations

        return [[x + int(w / 2), y + int(h / 2)] for x, y in zip(xs, ys)]
