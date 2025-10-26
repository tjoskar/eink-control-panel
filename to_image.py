"""Image output entrypoint.

Uses shared composition in `compose_panel` so layout stays identical to
hardware path (`to_disply.py`).
"""

from compose import compose_panel

def generate_image(save_path="main.png"):
    image = compose_panel()
    image.save(save_path)
    return image

if __name__ == "__main__":
    generate_image()
