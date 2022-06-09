## What is `Ember`

`Embers` is an `android` automation tool,
It can operate the interface through basic image comparison.
used by adb and openCV

## Getting started

```pydocstring
# create config with adb path, and android screen file cache
class config:
    def __init__(self):
        self.adb_path = "path"
        self.screen_cache_path = "path"

# init with config
init = ember.Ember(config())
```
