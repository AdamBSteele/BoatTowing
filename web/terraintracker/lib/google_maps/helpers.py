from .constants import MAP_IMAGE_URL_TEMPLATE

from io import BytesIO
from PIL import Image
from urllib.request import urlopen

from terraintracker.config import GOOGLE_MAPS_KEY


def get_coordinates_color(lat, lon):
    """ Get RGB color of Google static map (1x1) """
    url = MAP_IMAGE_URL_TEMPLATE.format(lat=lat, lon=lon, key=GOOGLE_MAPS_KEY)
    with urlopen(url) as f:
        img = Image.open(BytesIO(f.read()))
    pix = img.convert('RGB').load()
    return pix[0, 0]


def color_distance(c1, c2):
    """
    Manhattan distance between colors.
    https://en.wikipedia.org/wiki/Taxicab_geometry
    """
    return sum([delta(x) for x in zip(c1, c2)])


def delta(x):
    return abs(x[0] - x[1])
