import io
from PIL import Image, ImageChops
import random


def glitch_image(image_bytes: Image, max_offset=20, glitch_lines=30):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = img.size

    result = Image.new("RGB", (width, height), "black")
    result.paste(img)

    for _ in range(glitch_lines):
        line_height = random.randint(1, height // 20)
        y = random.randint(0, height - line_height)
        offset = random.randint(-max_offset, max_offset)

        band = img.crop((0, y, width, y + line_height))

        r, g, b = band.split()

        r = ImageChops.offset(r, offset, 0)
        g = ImageChops.offset(g, -offset, 0)
        b = ImageChops.offset(b, offset // 2, 0)

        band = Image.merge("RGB", (r, g, b))
        result.paste(band, (0, y))

    output_buffer = io.BytesIO()
    result.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return output_buffer
