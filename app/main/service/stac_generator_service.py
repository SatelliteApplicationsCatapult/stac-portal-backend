from datetime import datetime

import pystac
from rasterio.warp import calculate_default_transform
from shapely.geometry import Polygon, mapping

def create_STAC_Item(metadata):

    geom = return_geom_from_multiple_geom(metadata["geom"])
    src_crs = metadata["crs"]
    destination_crs = "epsg:4326"
    bbox = return_bbox_from_geom(geom)
    id = 'cool_id'    
    time_acquired = datetime.today()

    # Instantiate pystac item
    item = pystac.Item(id=id,
                geometry=geom,
                bbox=bbox,
                datetime = time_acquired,
                properties={
                })

    # Then add the assets
    for asset in metadata['assets']:
        continue

    return "cool"


def return_geom_from_multiple_geom(geom):
    """Return a single geometry from a list of geometries"""
    if len(geom) == 1:
        return geom[0]
    else:
        return geom

def return_bbox_from_geom(geom):
    """Return a bbox from a geometry"""
    return Polygon(geom).bounds
