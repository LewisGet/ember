import cv2
import numpy as np
import re
import subprocess
import xml.etree.ElementTree as ET


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


class UINode:
    def __init__(self, element):
        self.text         = element.get("text", "")
        self.resource_id  = element.get("resource-id", "")
        self.class_name   = element.get("class", "")
        self.content_desc = element.get("content-desc", "")
        self.clickable    = element.get("clickable") == "true"
        self.enabled      = element.get("enabled") == "true"
        self._bounds      = element.get("bounds", "")

    def bounds(self):
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', self._bounds)
        if not m:
            return None
        x1, y1, x2, y2 = map(int, m.groups())
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

    def center(self):
        b = self.bounds()
        if not b:
            return None
        return Location((b["x1"] + b["x2"]) // 2, (b["y1"] + b["y2"]) // 2)

    def __repr__(self):
        return f"UINode(class={self.class_name!r}, text={self.text!r})"


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

    def _execute_swipe(self, x_start, y_start, x_end, y_end, duration=30):
        p = subprocess.Popen([self.adb_path, "shell", "input", "swipe", str(x_start), str(y_start), str(x_end), str(y_end), str(duration)])
        p.wait()

    def swipe_arc(self, x_start, y_start, x_end, y_end, c, duration=30, damping=0.6):
        dx = x_end - x_start
        dy = y_end - y_start
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length == 0:
            self._execute_swipe(x_start, y_start, x_end, y_end, duration)
            return
        mx = (x_start + x_end) / 2
        my = (y_start + y_end) / 2
        px = int(mx + (-dy / length) * c)
        py = int(my + ( dx / length) * c)
        self._execute_swipe(x_start, y_start, px, py, int(duration * (1 - damping)))
        self._execute_swipe(px, py, x_end, y_end, int(duration * damping))

    def swipe(self, x_start, y_start, x_end, y_end, duration=30, c=20, damping=0.6):
        mx = int((x_start + x_end) / 2)
        my = int((y_start + y_end) / 2)
        self.swipe_arc(x_start, y_start, mx, my, c, int(duration * (1 - damping)), damping)
        self.swipe_arc(mx, my, x_end, y_end, c, int(duration * damping), damping)

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

    def input_text(self, text: str) -> None:
        p = subprocess.Popen([self.adb_path, "shell", "input", "text", text])
        p.wait()

    def key_event(self, keycode) -> None:
        p = subprocess.Popen([self.adb_path, "shell", "input", "keyevent", str(keycode)])
        p.wait()

    def dump_ui(self) -> str:
        result = subprocess.run(
            [self.adb_path, "shell", "uiautomator", "dump", "/dev/tty"],
            capture_output=True, text=True,
        )
        output = result.stdout
        end = output.rfind("</hierarchy>")
        if end < 0:
            raise RuntimeError("uiautomator dump returned no XML hierarchy")
        return output[: end + len("</hierarchy>")]

    def get_ui_nodes(self, filter_fn=None) -> list:
        root = ET.fromstring(self.dump_ui())
        nodes = [UINode(el) for el in root.iter("node")]
        if filter_fn is not None:
            nodes = [n for n in nodes if filter_fn(n)]
        return nodes

    def find_nodes_by_text(self, text: str, exact: bool = True) -> list:
        if exact:
            return self.get_ui_nodes(lambda n: n.text == text)
        return self.get_ui_nodes(lambda n: text in n.text)

    def find_nodes_by_class(self, class_name: str) -> list:
        return self.get_ui_nodes(lambda n: n.class_name == class_name)

    def find_nodes_by_resource_id(self, resource_id: str) -> list:
        return self.get_ui_nodes(lambda n: n.resource_id == resource_id)


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

    def _execute_swipe(self, x_start, y_start, x_end, y_end, duration=30):
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
