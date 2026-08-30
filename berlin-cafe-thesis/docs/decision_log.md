# Decision Log

A running record of the key methodological and technical decisions made during this thesis,
and the reasoning behind each - kept for transparency and reproducibility.


## Spatial unit

**D1 - Hexagonal grid (H3) instead of a square grid**
Decision: Represent Berlin as Uber H3 hexagons rather than the square grid originally proposed in the exposé.
Rationale: Each hexagon has six equidistant neighbours sharing a full edge, giving unambiguous adjacency for proximity-based features.
Status: Locked. Supersedes the square-grid design in the exposé.

**D2 - Resolution 8**
Decision: Use H3 resolution 8 (edge length ~460m, average area ~0.7 km²).
Rationale: Comparable in scale to the 500m square originally proposed in the exposé.
Status: Locked. Resolution 9 was not revisited — resolution 8 held up through EDA and modelling.

**D3 - Berlin boundary source**
Decision: Load the Berlin boundary from the supervisor-provided WKT CSV using `shapely.wkt.loads()`.
Status: Done. 1,353 resolution-8 hexagons generated and verified visually in Kepler.gl.

**D3.2 - H3 grid containment method & hexagon count**
Decision: Fill Berlin's boundary using `h3.polygon_to_cells`, which assigns a hexagon to the study area only if its centroid falls within the boundary polygon.
Result: 1,353 resolution-8 hexagons, aligning tightly with the official boundary.
Status: Locked. (See O1 for a related, unresolved discrepancy against a supervisor reference count.)

## Target variable

**D4 - Count regression, not binary classification**
Decision: Model the count of popular cafés per hexagon, rather than a binary "contains a popular café / does not" label.
Rationale: A count preserves more information (five popular cafés differs meaningfully from one) and suits the opportunity-gap framing in Study 2. Supersedes the binary classification design in the exposé.
Status: Locked.

**D5 - "Popular café" threshold**
Decision: A café is "popular" if its Google rating is ≥4.2 and it has ≥100 reviews.
Rationale: Direct success measures (revenue, footfall) aren't public, so rating and review count serve as a proxy. The review threshold sits close to the sample median (~96 reviews) — a defensible cut, not an arbitrary one.
Status: Locked. EDA (notebook 06) confirmed these thresholds produce a sensible, strongly zero-inflated target suited to a Poisson-objective model; thresholds unchanged from the original proposal.

**D6 - Café definition ("Moderate")**
Decision: Count as a café: coffee-first venues (Cafe, Coffee shop, Coffee roasters, Coffee store, Espresso bar, Art cafe, Chocolate cafe, Children's cafe, Vegetarian cafe and deli, Restaurant or cafe, Cafeteria) plus bakeries, pastry shops, patisseries, donut shops, and cake shops.
Excluded: internet cafés, ice-cream shops, bubble-tea and dessert venues, standalone delis, bars, restaurants, gas stations, and other non-café categories.
Rationale: Reflects German Bäckerei-with-seating culture, where bakeries function as café spaces.
Status: Locked.

**D7 - Remove permanently closed venues; keep temporarily closed**
Decision: Drop permanently closed cafés (928 rows); keep temporarily closed cafés with a flag column.
Rationale: Permanently closed cafés no longer represent real supply and would distort the target. Temporarily closed cafés still exist, and flagging (rather than dropping) keeps the choice reversible.
Status: Locked.

**D8 - Defer spatial (Berlin) filtering to hexagon assignment**
Decision: Don't filter cafés to Berlin with a bounding box during cleaning; instead drop cafés that fall outside the Berlin hexagon grid at the assignment step (notebook 03, via `h3.latlng_to_cell()`).
Rationale: Hexagon membership is a more precise "is it in Berlin?" test than a rectangular cut-off.
Status: Locked.

**D18 - Out-of-boundary cafés excluded from the target variable**
Decision: Exclude the 79 provisionally popular cafés whose coordinates don't match any hexagon in the 1,353-hexagon Berlin grid from the target variable.
Context: Notebook 02 flagged 923 cafés as provisionally popular (rating ≥4.2, ≥100 reviews). When assigning these to the grid in notebook 03, only 844 matched a hexagon; the remaining 79 cluster in Potsdam, Schönefeld, and other Brandenburg towns just outside Berlin, likely picked up because the original scrape used a "Berlin" search radius wide enough to reach neighbouring towns.
Rationale: Excluding them correctly enforces the study's Berlin-only scope, consistent with D8.
Status: Locked. Final target: 844 popular cafés assigned across 268 hexagons.

## Features

**D9 - Predictor features from separate sources (avoid circularity)**
Decision: Draw all predictor features from OpenStreetMap (via osmnx) and Eurostat population data — never from the café dataset itself.
Rationale: Using café data to predict café popularity would be circular. Keeping predictor and target sources fully separate avoids this and keeps the pipeline reproducible from open data.
Status: Locked. Core methodological principle.

**D10 - Final feature groups (5 groups, H1-H5)**
Decision: The original three-group plan (transport, commercial/POI density, population density) was expanded during feature engineering (notebooks 04-05) into five groups, matching the final hypothesis structure:
- H1 - Transport access: `transit_stops_500m`, `rail_stations_800m`
- H2 - Commercial & leisure activity: `shops_500m`, `food_500m`, `culture_700m`
- H3 - Institutional & workplace density: `offices_500m`, `universities_800m`, `coworking_500m`
- H4 - Green space: `green_spaces_800m`
- H5 - Population density: `population_density_per_km2`
Rationale: Splitting the original "commercial/POI density" group into commercial & leisure vs. institutional & workplace gave a cleaner conceptual separation once OSM tag exploration showed how different these categories actually are.
Status: Done. See `src/features_osm.py` and notebooks 04-05.

**D11 - Supervisor parquet files are reference schema only**
Decision: Treat the supervisor-provided parquet files (resolutions 7/8/9, ~1,649 columns) as a reference for expected feature schema, not as inputs. `reca_cafe` columns are a target-leakage risk and must not be used as predictors.
Status: Locked.

## Modelling & evaluation

**D12 - Models: Linear Regression baseline + XGBoost (Poisson)**
Decision: Use Linear Regression as an interpretable baseline and XGBoost with a Poisson objective as the main model.
Rationale: The target is count data, which the Poisson objective models appropriately; the linear baseline makes the case concrete, since it produces negative predictions, which don't make sense for a count.
Status: Locked. See notebook 07.

**D13 - Evaluation metrics**
Decision: Headline metric is Spearman rank correlation, reported alongside RMSE and MAE.
Rationale: The practical aim is to rank hexagons by predicted popularity, so a rank-based metric is the most meaningful headline; RMSE/MAE describe error magnitude.
Status: Locked.

**D14 - Interpretability via SHAP**
Decision: Use SHAP (TreeExplainer) to identify which feature groups drive predictions, computed globally across all 1,353 hexagons.
Status: Done. See notebook 08. Note: because SHAP is computed on the full dataset (including the 929 hexagons used to train the model), the resulting ranking partly reflects patterns the model was fit to see — noted as a limitation.

**D15 - Spatial train/test split**
Decision: Split by H3 resolution-6 parent hexagon ("block"), not by individual hexagon, to avoid spatial leakage from overlapping feature buffers between neighbouring train/test hexagons.
Rationale: Two greedy assignment strategies (balancing on hexagon count, then on café count) both failed, since one block alone holds ~25% of all cafés. A random-search approach (20,000 trials) was used instead, to find a block combination balancing both hexagon share and café share near the 80/20 target simultaneously. Train-side hexagons directly bordering the test set are additionally dropped to reduce residual buffer overlap.
Status: Locked. See notebook 07.

## Scope

**D16 - Study 2: opportunity gap via prediction vs. actual divergence**
Decision: Define opportunity gaps as predicted minus actual popular-café count, using a model refit on the full 1,353-hexagon dataset (rather than the notebook 07 train/test model), so every hexagon is scored consistently.
Status: Done. See notebook 09. Note: because the scoring model is fit on the same data it evaluates, gap magnitudes are likely conservative relative to a fully held-out estimate — noted as a limitation.

**D17 — Competition saturation deferred / out of scope**
Decision: The explicit competition-saturation scoring described in the exposé is not part of the final scope; the opportunity-gap formulation (D16) replaces it.
Status: Deferred — out of final scope; not revisited.

## Open technical items

**O1 - Hexagon count discrepancy**
1,353 hexagons generated vs. a supervisor reference example of 1,541. Likely a boundary-containment difference (e.g. buffering the polygon before generation).
Status: Accepted as-is. The fix (buffering the boundary by 300-500m before regenerating) wasn't pursued given time constraints; all downstream analysis consistently uses the same 1,353-hexagon grid, so the discrepancy doesn't affect internal consistency, but is noted here for transparency.

**O2 - Project folder nesting**
Notebooks originally ran from a doubled path (`berlin-cafe-thesis\berlin-cafe-thesis\notebooks`), with hardcoded absolute paths in early versions of notebook 02.
Status: Resolved. All notebooks now use relative paths (`../data/...`) anchored to the project's own folder structure, so the outer folder nesting no longer affects reproducibility, even though the nested folder itself was never renamed.

## Data quality notes (for the Limitations section)

- The café scrape spans multiple dates (2022-2026), so it isn't a single-point-in-time snapshot; ratings and review counts were captured at different times for different venues.
- Ratings and review counts are popularity proxies, not direct measures of business success. The absence of a popular café in a hexagon doesn't necessarily mean the location is unsuitable — it could reflect missing supply or unmeasured factors instead.
- Because SHAP importance and opportunity-gap scores are both computed from models fit on the full dataset, both should be read as descriptive rather than fully out-of-sample findings (see D14, D16).