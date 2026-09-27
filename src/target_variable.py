"""
src/target_variable.py

Assigns cafes to their H3 hexagon and counts popular cafes per hexagon. 
"""

import h3
import pandas as pd


def add_hex_id(cafes, lat_col="latitude", lng_col="longitude", resolution=8):
    # tagging each cafe with the hexagon it falls inside
    cafes = cafes.copy()
    cafes["h3_index"] = cafes.apply(
        lambda row: h3.latlng_to_cell(row[lat_col], row[lng_col], resolution),
        axis=1
    )
    return cafes


def count_cafes_per_hex(cafes, grid, hex_id_col="h3_index"):
    # count cafes by hexagon, then merge onto the full grid so empty hexagons show up as 0
    counts = cafes.groupby(hex_id_col).size().reset_index(name="popular_cafe_count")

    grid = grid.merge(counts, on=hex_id_col, how="left")
    grid["popular_cafe_count"] = grid["popular_cafe_count"].fillna(0).astype(int)

    return grid