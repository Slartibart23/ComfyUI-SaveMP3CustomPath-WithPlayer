from .save_mp3_custom_path import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
)

# Weist ComfyUI an, die JavaScript-Extension aus dem ./js Ordner
# an das Frontend auszuliefern. Dort wird der Audio-Player-Widget
# in den Node eingehaengt.
WEB_DIRECTORY = "./js"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
