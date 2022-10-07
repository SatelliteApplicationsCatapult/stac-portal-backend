from datetime import datetime

import pystac
from rasterio.warp import calculate_default_transform
from shapely.geometry import Polygon, mapping
from rasterio.warp import calculate_default_transform, transform_bounds
import pyproj
from pyproj import CRS
import json
import uuid


def create_STAC_Item(metadata):
    geom = return_geom_from_multiple_geom(metadata["groupedVariables"]["geom"])
    src_crs = return_epsg_from_wkt(metadata["staticVariables"]["wkt"])
    destination_crs = "epsg:4326"

    bbox = return_bbox_from_geom(geom, src_crs, destination_crs)
    geom = return_geom_from_bbox(bbox)

    id = metadata["staticVariables"]["id"]
    time_acquired = datetime.strptime(
        metadata["staticVariables"]["time_acquired"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    # # Instantiate pystac item
    item = pystac.Item(
        id=id, geometry=geom, bbox=bbox, datetime=time_acquired, properties={}
    )

    for asset in metadata["assets"]:
        random_id = str(uuid.uuid4())
        item.add_asset(
            key=random_id,
            asset=pystac.Asset(
                href=asset["href"],
                media_type=asset["type"],
                extra_fields={
                    "shape": asset["shape"],
                    "transform": asset["transform"],
                },
            ),
        )
    return item


def return_geom_from_multiple_geom(geom):
    """Return a single geometry from a list of geometries"""
    if len(geom) == 1:
        return geom[0]
    else:
        return geom


def return_bbox_from_geom(geom, src_crs, destination_crs):
    """Return a bbox from a geometry"""
    left, bottom, right, top = transform_bounds(
        src_crs,
        destination_crs,
        geom[0]["lowerLeft"][0],
        geom[0]["lowerLeft"][1],
        geom[0]["lowerRight"][0],
        geom[0]["upperLeft"][1],
    )
    return [left, bottom, right, top]


def return_geom_from_bbox(bbox):
    """Return a geometry from a bbox"""
    return Polygon(
        [[bbox[0], bbox[1]], [bbox[0], bbox[3]], [bbox[2], bbox[3]], [bbox[2], bbox[1]]]
    )


def return_epsg_from_wkt(wkt):
    """Return an EPSG code from a WKT"""
    src_crs = CRS.from_wkt(wkt)
    return src_crs.to_epsg()
