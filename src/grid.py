"""
H3 hexagon grid generation for Berlin.

Loads Berlin's boundary from a pre-saved WKT CSV (rather than a live OSM
geocoding call, for reproducibility) and generates an H3 hexagon grid
covering it at a specified resolution.
"""

import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Polygon
import h3


def load_boundary_from_csv(csv_path, location_column="location"):
    """
    Load a city boundary from a CSV containing a WKT geometry column.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file.
    location_column : str
        Name of the column containing the WKT geometry text.

    Returns
    -------
    shapely.geometry.base.BaseGeometry
        The parsed boundary geometry (Polygon or MultiPolygon).
    """
    boundary_df = pd.read_csv(csv_path)
    boundary_wkt_text = boundary_df[location_column].iloc[0]
    return wkt.loads(boundary_wkt_text)


def generate_h3_grid(boundary_geom, resolution):
    """
    Generate an H3 hexagon grid covering a given boundary geometry.

    Parameters
    ----------
    boundary_geom : shapely.geometry.base.BaseGeometry
        A Polygon or MultiPolygon representing the area to cover.
    resolution : int
        H3 resolution level (e.g. 8 for ~500m hexagons).

    Returns
    -------
    geopandas.GeoDataFrame
        One row per hexagon, with columns: h3_index, resolution, geometry.
    """
    if boundary_geom.geom_type == "MultiPolygon":
        polygons = list(boundary_geom.geoms)
    else:
        polygons = [boundary_geom]

    hex_cells = set()
    for poly in polygons:
        # Shapely stores (lon, lat); H3 expects (lat, lon)
        coords = [(lat, lon) for lon, lat in poly.exterior.coords]
        h3_poly = h3.LatLngPoly(coords)
        cells = h3.polygon_to_cells(h3_poly, resolution)
        hex_cells.update(cells)

    hex_ids = sorted(hex_cells)  # sorted for reproducible output order

    hex_geometries = []
    for cell in hex_ids:
        boundary_coords = h3.cell_to_boundary(cell)  # returns (lat, lon) pairs
        lon_lat_coords = [(lon, lat) for lat, lon in boundary_coords]
        hex_geometries.append(Polygon(lon_lat_coords))

    return gpd.GeoDataFrame(
        {"h3_index": hex_ids, "resolution": resolution},
        geometry=hex_geometries,
        crs="EPSG:4326",
    )


def generate_and_save_h3_grid(csv_path, resolution, output_path, location_column="location"):
    """
    Full pipeline: load boundary from CSV, generate H3 grid, save as GeoJSON.

    Parameters
    ----------
    csv_path : str
        Path to the boundary CSV (WKT format).
    resolution : int
        H3 resolution level.
    output_path : str
        Path to save the resulting GeoJSON file.
    location_column : str
        Name of the WKT geometry column in the CSV.

    Returns
    -------
    geopandas.GeoDataFrame
        The generated hexagon grid.
    """
    boundary_geom = load_boundary_from_csv(csv_path, location_column)
    hex_gdf = generate_h3_grid(boundary_geom, resolution)
    hex_gdf.to_file(output_path, driver="GeoJSON")
    print(f"Saved {len(hex_gdf)} resolution-{resolution} hexagons to {output_path}")
    return hex_gdf


if __name__ == "__main__":
    generate_and_save_h3_grid(
        csv_path="../data/external/berlin_boundary.csv",
        resolution=8,
        output_path="../data/external/berlin_h3_res8.geojson",
    )