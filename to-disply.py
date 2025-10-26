from lib.waveshare_epd.epd7in5_V2 import EPD
from compose import compose_panel

def generate_display():
    """Render and push image buffer to the physical E-Ink display.

    Layout provided by compose_panel to stay consistent with image output.
    """
    epd = EPD()
    epd.init()
    epd.Clear()

    image = compose_panel()
    epd.display(epd.getbuffer(image))
    epd.sleep()

if __name__ == "__main__":
    generate_display()
