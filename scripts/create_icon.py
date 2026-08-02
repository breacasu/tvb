#!/usr/bin/env python3
"""Generate transparent application icons from the TVB icon design."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build"


def gradient(size, start, end):
    image = Image.new("RGBA", (size, size))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            pixels[x, y] = tuple(round(start[i] * (1 - t) + end[i] * t) for i in range(4))
    return image


def create(size=1024):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = size / 256
    box = lambda values: tuple(round(value * scale) for value in values)

    frame = gradient(size, (139, 92, 246, 255), (6, 182, 212, 255))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box((23, 23, 233, 233)), radius=round(52 * scale), fill=255)
    image.alpha_composite(Image.composite(frame, Image.new("RGBA", (size, size)), mask))

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box((31, 31, 225, 225)), radius=round(46 * scale), fill=(11, 17, 32, 255))
    draw.rounded_rectangle(box((43, 43, 213, 213)), radius=round(35 * scale), fill=(17, 24, 39, 250))

    for x in (61, 195):
        for y in (76, 103, 153, 180):
            draw.ellipse(box((x - 6, y - 6, x + 6, y + 6)), fill=(103, 232, 249, 230))

    draw.polygon([box((101, 76))[:2], box((101, 180))[:2], box((179, 128))[:2]], fill=(236, 254, 255, 255))
    draw.arc(box((78, 78, 166, 178)), start=205, end=320, fill=(103, 232, 249, 255), width=round(7 * scale))
    draw.polygon([box((151, 77))[:2], box((158, 87))[:2], box((145, 88))[:2]], fill=(103, 232, 249, 255))
    return image


def main():
    icon = create()
    icon.save(OUT / "icon.png", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256), (512, 512)])
    icon.save(OUT / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    icon.save(OUT / "icon.icns", sizes=[(16, 16), (32, 32), (128, 128), (256, 256), (512, 512), (1024, 1024)])


if __name__ == "__main__":
    main()
