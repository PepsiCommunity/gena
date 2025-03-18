from PIL import Image, ImageFont, ImageDraw
import math


def generate_mi(text: str):
    fnt = ImageFont.truetype("./mi/res/geist.ttf", 150)

    left: Image.Image = Image.open('./mi/res/mi_1.png').convert('RGBA')
    right: Image.Image = Image.open('./mi/res/mi_2.png').convert('RGBA')
    mid: Image.Image = Image.open('./mi/res/mi_3.png').convert('RGBA')
    text_size = fnt.getbbox(text)

    new = Image.new(
        "RGBA",
        (left.width + right.width + text_size[2], left.height)
    )
    new.paste(left, (0, 0), left)
    new.paste(right, (new.width - right.width - 1, 0), right)

    new_mid = Image.new("RGBA", (text_size[2], left.width))
    for x in range(max(1, math.ceil(new_mid.width / mid.width))):
        new_mid.paste(mid, (x * mid.width, 0), mid)

    new.paste(new_mid, (left.width - 1, 0), new_mid)
    draw = ImageDraw.Draw(new)
    draw.text((left.width, (left.height // 2 -
              (text_size[1] + text_size[3]) // 2)), text, font=fnt)
    return new
