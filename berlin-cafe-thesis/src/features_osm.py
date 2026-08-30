import osmnx as ox
import geopandas as gpd

# UTM zone 33N - the correct metric CRS for Berlin. Buffers (500m, 800m etc.)
# only make sense in a metric CRS, not in lat/lon degrees.
METRIC_CRS = "EPSG:25833"


def fetch_pois(boundary_geom, tags, exclude=None):
    """Download OSM features matching `tags` inside `boundary_geom`.

    boundary_geom: a shapely geometry in EPSG:4326 (lat/lon) - same as berlin_boundary from notebook 01.tags: an OSM tag dict, e.g. {"shop": True} or {"amenity": "restaurant"}.
    exclude: optional {column: value} pairs to drop before returning,
    e.g. {"shop": "vacant"} to exclude vacant storefronts.

    OSM features can be points, lines, or polygons (a bus stop is a point, a park is a polygon). We convert everything to a single representative point (its centroid) so every feature type can be counted the same way.
    """
    raw = ox.features_from_polygon(boundary_geom, tags)

    if exclude:
        for col, bad_value in exclude.items():
            if col in raw.columns:
                raw = raw[raw[col] != bad_value]

    raw = raw.copy()
    raw["geometry"] = raw["geometry"].apply(
        lambda geom: geom if geom.geom_type == "Point" else geom.centroid
    )
    return raw[["geometry"]]


def count_in_buffer(grid, pois, buffer_m, col_name):
    """Add a column to `grid` counting how many `pois` fall within
    `buffer_m` metres of each hexagon's centroid.

    Uses centroid-based buffering
    """
    grid_m = grid.to_crs(METRIC_CRS)
    pois_m = pois.to_crs(METRIC_CRS)

    centroids = grid_m.geometry.centroid
    buffers = gpd.GeoDataFrame(
        {"h3_index": grid_m["h3_index"]},
        geometry=centroids.buffer(buffer_m),
        crs=METRIC_CRS,
    )

    joined = gpd.sjoin(pois_m, buffers, predicate="within", how="inner")
    counts = joined.groupby("h3_index").size()

    grid[col_name] = grid["h3_index"].map(counts).fillna(0).astype(int)
    return grid