MAP_IMAGE_URL_TEMPLATE = (
    'https://maps.googleapis.com/maps/api/staticmap?'
    'center={lat},{lon}&'
    'zoom=19&'
    'size=1x1&'
    'maptype=roadmap&'
    'key={key}'
)

# average water color is obtained with sample points and ``get_color_stats.py`` script
AVERAGE_WATER_COLOR = (163, 204, 255)
MAXIMUM_WATER_COLOR_DISTANCE = 5
