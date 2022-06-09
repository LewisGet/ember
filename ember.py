import cv2
import numpy as np
import subprocess


class Ember:
    def __init__(self, config):
        self.adb_path = config.adb_path
        self.screen_cache_path = config.screen_cache_path

    def get_screen(self):
        f = open(self.screen_cache_path, "w")
        p = subprocess.Popen([self.adb_path, "exec-out", "screencap", "-p"], stdout=f)
        p.wait()
        f.close()

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

        ys, xs = locations

        return [[x + int(w / 2), y + int(h / 2)] for x, y in zip(xs, ys)]

    def touch_first_image_find(self, target_image_path, similarity):
        targets = self.get_images_location(target_image_path, similarity)

        self.touch_screen(targets[0][0], targets[0][1])
