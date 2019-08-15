from . import helpers
from .constants import AVERAGE_WATER_COLOR, MAXIMUM_WATER_COLOR_DISTANCE

import logging

logger = logging.getLogger(__name__)


def get_color_and_isWater(lat, lon):
    color = helpers.get_coordinates_color(lat, lon)
    this_color_distance = helpers.color_distance(color, AVERAGE_WATER_COLOR)
    is_water = this_color_distance < MAXIMUM_WATER_COLOR_DISTANCE
    logger.debug("Color: {}, Color Distance: {}, Lat: {}, Lon: {}, is_water: {}".format(
        color, this_color_distance, lat, lon, is_water))
    return color, is_water
