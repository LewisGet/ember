## What is `Ember`

`Embers` is an `android` automation tool,
It can operate the interface through basic image comparison.
used by adb and openCV

## Getting started

### Android

```pydocstring
# create config with adb path, and android screen file cache
class config:
    def __init__(self):
        self.adb_path = "path"
        self.screen_cache_path = "path"

# init with config
init = ember.Ember(config())
```

### Android server

```pydocstring
init = ember.AccessibilityEmber("ws://android_ip:8765")
```

### Windows

```pydocstring
class config:
    def __init__(self):
        self.screen_region = "window region size or None"


# init with ember
init = ember.WindowsEmber(config())
```

## Classes

### `Location`
A simple (x, y) coordinate. Has a `.distance(other)` method.

### `Image`
Wraps an image file for template matching.

```python
img = ember.Image("button.png")
img.set_similarity(0.9) # default 0.85
img.set_offset(ember.Location(5, 5))  # tap offset from match center
```

### `UINode`
Represents one node from a `uiautomator dump`. Returned by all `find_nodes_*` methods.

| Attribute | Type | Description |
|---|---|---|
| `.text` | str | Visible text of the element |
| `.class_name` | str | e.g. `android.widget.TextView` |
| `.resource_id` | str | e.g. `com.app:id/message` |
| `.content_desc` | str | Accessibility description |
| `.clickable` | bool | Whether the element accepts taps |
| `.enabled` | bool | Whether the element is enabled |
| `.bounds()` | dict or None | `{"x1", "y1", "x2", "y2"}` |
| `.center()` | Location or None | Center point, ready for `touch_screen` |

---

## Methods

### Screen / image

```python
e.get_screen()                        # returns OpenCV image (numpy array)
e.get_images_location(img)            # returns list of Location for all template matches
e.touch_first_image_find(img)         # tap the first match; raises if not found
```

### Touch / gesture

```python
e.touch_screen(x, y)
e.swipe(x_start, y_start, x_end, y_end, duration=30)  # duration in ms
```

> `swipe` 會執行兩次 `swipe_arc` 讓他有顫動感
> `swipe_arc` 路徑為 `A → M+c → B`
> - `M` = midpoint of AB
> - `P1` = perpendicular offset of A→M midpoint by `c` pixels
> - `P2` = perpendicular offset of M→B midpoint by `c` pixels

### Text input

```python
e.input_text("hello world")           # types text into the focused field
e.key_event(66)                       # send keycode by number (66 = Enter)
e.key_event("KEYCODE_CTRL_A")         # or by name
```

> `input_text` uses `adb shell input text` which does not support newlines (`\n`).
> Replace newlines with spaces before calling, or send `key_event(66)` manually per line.

### UI text reading (uiautomator)

```python
# Raw XML string from the device
xml = e.dump_ui()

# All nodes (list of UINode)
nodes = e.get_ui_nodes()

# Filtered — pass any lambda
inputs = e.get_ui_nodes(lambda n: n.clickable and n.enabled)

# Shortcuts
e.find_nodes_by_text("Send", exact=True)   # exact match on .text
e.find_nodes_by_text("Send", exact=False)  # substring match
e.find_nodes_by_class("android.widget.EditText")
e.find_nodes_by_resource_id("com.app:id/input")
```

Example — type into the first input field then tap Enter:

```python
inputs = e.find_nodes_by_class("android.widget.EditText")
c = inputs[0].center()
e.touch_screen(c.x, c.y)
e.key_event("KEYCODE_CTRL_A")
e.key_event("KEYCODE_DEL")
e.input_text("your message here")
e.key_event(66)
```

Example — read all visible text views:

```python
nodes = e.find_nodes_by_class("android.widget.TextView")
for n in nodes:
    print(n.text)
```
