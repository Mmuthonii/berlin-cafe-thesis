"""
Central config for the Berlin café thesis project.
Change values here — everything else (notebooks, src/) reads from this file,
so you never have hard-coded thresholds scattered across notebooks.
"""

# --- Spatial unit ---
H3_RESOLUTION = 8  # ~500m hexagons

# --- Target variable ---
POPULAR_RATING_THRESHOLD = 4.2
POPULAR_REVIEW_THRESHOLD = 100
# NOTE: revisit after EDA (Phase 2) 

# --- Feature buffer distances (meters) ---
BUFFER_TRANSPORT = 500
BUFFER_COMMERCIAL = 500
BUFFER_CULTURAL = 700
BUFFER_PARK = 800

# --- Reproducibility ---
RANDOM_SEED = 42
TRAIN_TEST_SPLIT = 0.8

# --- CRS ---
CRS_GEOGRAPHIC = "EPSG:4326"
CRS_PROJECTED = "EPSG:25833"  # ETRS89 / UTM zone 33N — standard for Berlin, needed for accurate buffer/distance calcs
