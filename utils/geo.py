import math


def get_geotile(lat: float, lng: float, zoom: int) -> int:
    x = int((lng + 180) / 360 * (1 << zoom))
    y = int(
        (
            1
            - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat)))
            / math.pi
        )
        / 2
        * (1 << zoom)
    )

    quadkey = 0
    for i in range(zoom, 0, -1):
        x_bit = (x >> i) & 1
        y_bit = (y >> i) & 1
        quadkey = (quadkey << 2) | (y_bit << 1) | x_bit
    return quadkey
