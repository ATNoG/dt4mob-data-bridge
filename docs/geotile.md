
# Geotile Implementation Guide

# Introduction

Geotiles are a method used in geographic information systems (GIS) for dividing the Earth's surface into a hierarchical grid of tiles. Each tile corresponds to a defined geographic area, making geotiles essential for spatial indexing. Their primary function is to aid in the efficient search for objects or regions within a specified area by reducing the geographic search space.

Geotiles are particularly useful for applications that handle large volumes of geospatial data, as they enable fast querying, filtering, and zooming to smaller areas of interest.

## Overview

In this implementation, geotiles are calculated using a hierarchical grid system known as QuadTiles. These tiles are used for geospatial data storage and indexing, and the algorithm allows efficient spatial queries by breaking the Earth's surface into recursive quadrants. The geotile information is encoded as a 64-bit signed integer for compactness and ease of manipulation.

---

## The Algorithm

Geotiles are calculated based on latitude, longitude, and zoom level. The algorithm follows these steps:

1. **Convert Latitude and Longitude to Tile Coordinates:**
   - Convert the longitude to an `x` coordinate.
   - Convert the latitude to a `y` coordinate using the Mercator projection.
   - Map these coordinates onto a grid defined by the zoom level.

2. **Encode Coordinates into a Single Quadkey:**
   - For each level of zoom:
     - Determine the quadrant of the current point.
     - Encode the quadrant as a combination of `x` and `y` bits.
   - This step results in a compact integer representation of the tile (quadkey).

### Function Definition

```python
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
```

---

## Packaging as Signed Integer

The geotile quadkey is represented using a signed 64-bit integer, where:

- **Even bits** represent the x-coordinate (longitude) at each zoom level.
- **Odd bits** represent the y-coordinate (latitude) at each zoom level.

This gives us a unique index for each tile based on its spatial positioning. The algorithm supports up to a maximum zoom level of 31 to comply with the constraints of a signed 64-bit integer.

---

## Searching Geotiles

Efficient searching for geotiles within a specific zoom level and area (bounds) is enabled via the `get_tile_bounds` function.

### How Bounds are Calculated
Given a latitude, longitude, and zoom level:
1. Compute the geotile (quadkey) for the tile containing the point.
2. Adjust the bounds based on the desired zoom level.

```python
def get_tile_bounds(lat: float, lng: float, tile_zoom: int, max_zoom: int = 31):
    tile_qk = get_geotile(lat, lng, tile_zoom)
    shift_bits = 2 * (max_zoom - tile_zoom)
    lower_bound = tile_qk << shift_bits
    upper_bound = (tile_qk + 1) << shift_bits

    return lower_bound, upper_bound
```

### Example Query for Eclipse Ditto

The lower and upper bounds computed by `get_tile_bounds` can be used in Resource Query Language (RQL). The following query retrieves all resources within the computed geotile bounds:

```text
and(ge(attributes/geotile,<lower_bound>),le(attributes/geotile,<upper_bound>))
```
