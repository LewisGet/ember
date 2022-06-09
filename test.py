import ember


class config:
    def __init__(self):
        self.adb_path = "C:\\Users\\Lewis\\Desktop\\tools\\scrcpy\\adb.exe"
        self.screen_cache_path = "F:\\code\\ember\\tmp.png"


init = ember.Ember(config())
init.touch_first_image_find("test_target.png", 0.8)
