"""PNG output entrypoint; shares layout via `compose_panel()`."""

from compose import compose_panel

def generate_image(save_path="main.png"):
    image = compose_panel()
    image.save(save_path)
    return image

if __name__ == "__main__":
    generate_image()
