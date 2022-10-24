import re
from datetime import datetime

import pystac
from pyproj import CRS
from rasterio.warp import transform_bounds
from shapely.geometry import Polygon

stac_extensions = {
    "eo": "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
    "proj": "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
    "view": "https://stac-extensions.github.io/view/v1.0.0/schema.json",
}


def create_STAC_Item(metadata):
    # EPSG (Source and destination)
    src_crs = return_epsg_from_wkt(metadata["staticVariables"]["wkt"])
    destination_crs = "epsg:4326"  # All STAC Items are in EPSG:4326

    # Converted Geoms
    wgs84_grouped_geom = return_geom_from_multiple_geom(
        metadata["groupedVariables"]["wgs84_geom"]
    )
    wgs84_bbox = return_bbox_from_geom(wgs84_grouped_geom, src_crs, destination_crs)
    wgs84_geom = return_geom_from_bbox(wgs84_bbox)

    # Original Geoms
    original_grouped_geom = return_geom_from_multiple_geom(
        metadata["groupedVariables"]["proj_geom"]
    )
    original_bbox = return_bbox_from_coordinates(
        original_grouped_geom, src_crs, src_crs
    )

    # Required fields
    id = metadata["staticVariables"]["id"]
    time_acquired = datetime.strptime(
        metadata["staticVariables"]["time_acquired"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    # Properties
    properties = {
        "proj:bbox": original_bbox,
        "proj:epsg": src_crs,
    }
    # Call the appropriate parser to extend the properties
    if metadata["staticVariables"]["provider"] == "Planet":
        planet_stac_parser(properties, metadata["additional"])
    elif metadata["staticVariables"]["provider"] == "Maxar":
        maxar_stac_parser(properties, metadata["additional"])

    # Instantiate pystac item
    item = pystac.Item(
        id=id,
        geometry=wgs84_geom,
        bbox=wgs84_bbox,
        datetime=time_acquired,
        properties=properties,
    )

    for asset in metadata["assets"]:
        # Remove extension from asset name
        name = re.sub(r"\.[^.]*$", "", asset["filename"])
        item.add_asset(
            key=name,
            asset=pystac.Asset(
                href=asset["href"],
                media_type=asset["type"],  # TODO: Convert to pystac.MediaType
                extra_fields={
                    "eo:bands": asset["bands"],
                    "proj:shape": asset["shape"],
                    "proj:transform": asset["transform"],
                },
            ),
        )

    for other_asset in metadata["otherAssets"]:
        url = metadata["staticVariables"]["url"].split("/")[0:-1]
        href = "/".join(url) + "/" + other_asset["name"]
        item.add_asset(
            key=other_asset["name"],
            asset=pystac.Asset(
                href=href,
                media_type=other_asset["type"],  # TODO: Convert to pystac.MediaType
            ),
        )

    # Configure extensions
    configure_extensions(item, properties)

    item.set_self_href("item.json")

    item.validate()
    item.save_object()

    item_json = item.to_dict()
    return item_json


def return_geom_from_multiple_geom(geom):
    """Return a single geometry from a list of geometries"""
    # For now, just return the first geom and convert to geometry obect
    return geom[0]


def return_bbox_from_geom(geom, src_crs, destination_crs):
    """
    Return a bbox from a geometry
    """
    geom = Polygon(geom["coordinates"][0])
    left, bottom, right, top = transform_bounds(
        "epsg:4326", destination_crs, *geom.bounds
    )
    return [left, bottom, right, top]


def return_geom_from_bbox(bbox):
    """Return a geometry from a bbox"""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [bbox[0], bbox[1]],
                [bbox[2], bbox[1]],
                [bbox[2], bbox[3]],
                [bbox[0], bbox[3]],
                [bbox[0], bbox[1]],
            ]
        ],
    }


def return_epsg_from_wkt(wkt):
    """Return an EPSG code from a WKT"""
    src_crs = CRS.from_wkt(wkt)
    return src_crs.to_epsg()


def return_bbox_from_coordinates(geom, src_crs, destination_crs):
    """Return a bbox from mapped coorindates"""
    left, bottom, right, top = transform_bounds(
        src_crs,
        destination_crs,
        geom["lowerLeft"][0],
        geom["lowerLeft"][1],
        geom["lowerRight"][0],
        geom["upperLeft"][1],
    )
    return [left, bottom, right, top]


def planet_stac_parser(properties, metadata):
    """Parse Planet STAC metadata"""
    planet_properties = metadata["properties"]
    if planet_properties.get("gsd"):
        properties["gsd"] = planet_properties["gsd"]

    # EO Additions
    if planet_properties.get("cloud_cover") != None:
        properties["eo:cloud_cover"] = planet_properties["cloud_cover"]

    # View Additions
    if planet_properties.get("sun_elevation"):
        properties["view:sun_elevation"] = planet_properties["sun_elevation"]
    if planet_properties.get("sun_azimuth"):
        properties["view:sun_azimuth"] = planet_properties["sun_azimuth"]
    if planet_properties.get("view_angle"):
        properties["view:off_nadir"] = planet_properties["view_angle"]

    # Thumbnail


def maxar_stac_parser(properties, metadata):
    """Parse Maxar STAC metadata"""
    # Cloud Cover
    if metadata["README"].get("CLOUDCOVER") != None:
        properties["eo:cloud_cover"] = float(metadata["README"]["CLOUDCOVER"])

    # Thumbnail

    # View additions
    try:
        if metadata["delivery"]["message"]["DeliveryMetadata"]["product"]["sunAzimuth"]:
            properties["view:sun_azimuth"] = float(
                metadata["delivery"]["message"]["DeliveryMetadata"]["product"][
                    "sunAzimuth"
                ]
            )
    except:
        pass

    try:
        if metadata["delivery"]["message"]["DeliveryMetadata"]["product"][
            "sunElevation"
        ]:
            properties["view:sun_elevation"] = float(
                metadata["delivery"]["message"]["DeliveryMetadata"]["product"][
                    "sunElevation"
                ]
            )
    except:
        pass

    try:
        if metadata["delivery"]["message"]["DeliveryMetadata"]["product"][
            "offNadirAngle"
        ]:
            properties["view:off_nadir"] = float(
                metadata["delivery"]["message"]["DeliveryMetadata"]["product"][
                    "offNadirAngle"
                ]
            )
    except:
        pass


# Function that checkswhat extensions are present and adds them to the item
def configure_extensions(item, properties):
    if any(key.startswith("eo:") for key in properties):
        item.stac_extensions.append(stac_extensions["eo"])
    if any(key.startswith("view:") for key in properties):
        item.stac_extensions.append(stac_extensions["view"])
    if any(key.startswith("proj:") for key in properties):
        item.stac_extensions.append(stac_extensions["proj"])
