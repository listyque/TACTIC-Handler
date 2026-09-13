"""Stable application colors without the vendored colorhash package."""

import colorsys
import zlib


def color_hash(value, lightness: float = 0.5, saturation: float = 0.3) -> str:
    hue = (zlib.crc32(str(value).encode("utf-8")) & 0xFFFFFFFF) % 359
    rgb = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(*(round(channel * 255) for channel in rgb))
