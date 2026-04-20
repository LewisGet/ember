import cv2
import numpy as np
import subprocess


class Location:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, location):
        return ((self.x - location.x) ** 2 + (self.y - location.y) ** 2) ** 0.5


class Image:
    def __init__(self, image):
        self.org_path = None

        if type(image) == str:
            self.org_path = image
            self.Main = cv2.imread(image)
            self.Offset = Location(0, 0)
            self.Similarity = 0.85

        if type(image) == Image:
            self.Main = image.Main
            self.Offset = image.Offset
            self.Similarity = image.Similarity

    def set_offset(self, location):
        self.Offset = location
        return self

    def set_similarity(self, value):
        self.Similarity = value
        return self


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

    def get_images_location(self, img, min_distance=5):
        screen = self.get_screen()
        img = Image(img)
        h, w = img.Main.shape[:-1]

        res = cv2.matchTemplate(screen, img.Main, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= img.Similarity)

        ys, xs = locations

        return_locations = []

        for x, y in zip(xs, ys):
            this_location = Location(x + int(w / 2), y + int(h / 2))

            have_same_location = False

            for save_location in return_locations:
                if this_location.distance(save_location) < min_distance:
                    have_same_location = True

            if have_same_location is False:
                return_locations.append(this_location)

        return return_locations

    def touch_first_image_find(self, image):
        targets = self.get_images_location(image)

        try:
            self.touch_screen(targets[0].x + image.Offset.x, targets[0].y + image.Offset.y)
        except IndexError:
            raise Exception(image.org_path + " not found")


class WindowsEmber(Ember):
    def __init__(self, config):
        self.screen_region = getattr(config, "screen_region", None)

    def get_screen(self):
        import mss

        with mss.mss() as sct:
            if self.screen_region:
                left, top, width, height = self.screen_region
                monitor = {"left": left, "top": top, "width": width, "height": height}
            else:
                monitor = sct.monitors[1]

            raw = sct.grab(monitor)
            img = np.array(raw)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def touch_screen(self, x, y):
        import ctypes

        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)

        norm_x = int(x * 65535 / screen_w)
        norm_y = int(y * 65535 / screen_h)

        user32.mouse_event(0x0001 | 0x8000, norm_x, norm_y, 0, 0)
        user32.mouse_event(0x0002 | 0x8000, norm_x, norm_y, 0, 0)
        user32.mouse_event(0x0004 | 0x8000, norm_x, norm_y, 0, 0)

    def swipe(self, x_start, y_start, x_end, y_end, duration=30):
        import ctypes
        import time

        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)

        steps = 20
        delay = (duration / 1000.0) / steps

        def to_norm(x, y):
            return int(x * 65535 / screen_w), int(y * 65535 / screen_h)

        nx, ny = to_norm(x_start, y_start)
        user32.mouse_event(0x0001 | 0x8000, nx, ny, 0, 0)
        user32.mouse_event(0x0002 | 0x8000, nx, ny, 0, 0)

        for i in range(1, steps + 1):
            ix = x_start + (x_end - x_start) * i // steps
            iy = y_start + (y_end - y_start) * i // steps
            nx, ny = to_norm(ix, iy)
            user32.mouse_event(0x0001 | 0x8000, nx, ny, 0, 0)
            time.sleep(delay)

        user32.mouse_event(0x0004 | 0x8000, nx, ny, 0, 0)
