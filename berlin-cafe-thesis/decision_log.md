Decision Log

This is a running record of the key methodological and technical decisions made during this thesis, with the reasoning behind each one. The purpose is transparency and
reproducibility

Log created 2026-07-12. Entries dated earlier than this were recorded
retrospectively on that date.

Spatial unit

D1 — Hexagonal grid (H3) instead of a square grid

Decision: Represent Berlin as Uber H3 hexagons rather than the square grid originally proposed in the exposé.
Rationale: Each hexagon has six neighbours that lie at an equal distance and each share a full edge, giving unambiguous adjacency for proximity-based features. 
Status: Locked. Supersedes the square-grid design in the exposé.

D2 — Resolution 8

Decision: Use H3 resolution 8 (edge length ~460 m, average area ~0.7 km²).
Rationale: Its ~460 m edge length is comparable to the 500 m square proposed in the exposé.
Status: Locked. Resolution 9 may be revisited in sensitivity analysis if EDA suggests it.

D3 — Berlin boundary source

Decision: Load the Berlin boundary from the supervisor-provided WKT CSV using shapely.wkt.loads().
Status: Done. 1,353 resolution-8 hexagons generated and verified in Kepler.gl.

D3.2 H3 grid containment method & hexagon count
Berlin's boundary was filled using h3.polygon_to_cells, which assigns a hexagon to the study area only if its centroid falls within the Berlin polygon. This produced 1,353 resolution-8 hexagons, which align tightly with the official boundary (verified visually in Kepler.gl).

Target variable

D4 — Count regression, not binary classification

Decision: Model the count of popular cafés per hexagon (a count target), rather than a binary "contains a popular café / does not" label.
Rationale: A count preserves more information (a hexagon with five popular cafés differs from one with one) and suits the opportunity-gap framing in Study 2. Supersedes the binary classification design in the exposé.
Status: Locked.

D5 — "Popular café" threshold (provisional)

Decision: A café is provisionally "popular" if its Google rating is ≥ 4.2 and it has ≥ 100 reviews.
Rationale: Direct success measures (revenue, footfall) are not public, so rating and review count serve as a popularity proxy. On the cleaned data the review threshold sits near the median (~96 reviews), a defensible starting point.
Status: Provisional — to be finalised after EDA (notebook 04).

D6 — Café definition ("Moderate")

Decision: Count as a café: coffee-first venues (Cafe, Coffee shop, Coffee roasters, Coffee store, Espresso bar, Art cafe, Chocolate cafe, Children's cafe, Vegetarian cafe and deli, Restaurant or cafe, Cafeteria) plus bakeries, pastry shops, patisseries, donut shops, and cake shops.
Excluded: internet cafés, ice-cream shops, bubble-tea and dessert venues, delis, bars, restaurants, gas stations, and other non-café categories.
Rationale: Reflects German Bäckerei-with-seating culture, where bakeries function as café spaces. The set is deliberately adjustable if EDA shows the bakery group behaves differently from cafés.
Status: Locked, revisitable.

D7 — Remove permanently closed venues; keep temporarily closed

Decision: Drop permanently closed cafés (928 rows); keep temporarily closed cafés but retain a flag column.
Rationale: Permanently closed cafés no longer represent real supply and would distort the target. Temporarily closed cafés still exist and are flagged so the choice can be reversed.
Status: Locked.

D8 — Defer spatial (Berlin) filtering to hexagon assignment

Decision: Do not filter cafés to Berlin with a bounding box during cleaning. Instead, drop cafés that fall outside the Berlin hexagon grid at the assignment step (notebook 03, via h3.latlng_to_cell()).
Rationale: Hexagon membership is a more precise "is it in Berlin?" test than a
rectangular cut-off.
Status: Locked.


Features

D9 — Predictor features from separate sources (avoid circularity)

Decision: Draw all predictor features from OpenStreetMap (via osmnx) and Eurostat population data — never from the company café dataset.
Rationale: Using café data to predict café popularity would be circular. Keeping feature sources fully separate from the target source makes the model honest and the pipeline reproducible from open data.
Status: Locked. Core methodological principle.

D10 — Feature groups

Decision: Initial feature groups are transport access (H1), commercial/POI density (H2), and population density, computed with buffer/aggregation logic (e.g. counts within 500m).
Status: Planned. Extraction not yet started.

D11 — Supervisor parquet files are reference schema only

Decision: Treat the supervisor-provided parquet files (res 7/8/9, ~1,649 columns) as a reference for expected feature schema, not as inputs. reca_cafe columns are a target-leakage risk and must not be used as predictors.
Status: Locked.


Modelling & evaluation

D12 — Models: Linear Regression baseline + XGBoost (Poisson)

Decision: Use Linear Regression as an interpretable baseline and XGBoost with a Poisson objective as the main model.
Rationale: The target is count data, which the Poisson objective models appropriately; the linear baseline gives an interpretable reference point.
Status: Locked.

D13 — Evaluation metrics

Decision: Headline metric is Spearman rank correlation, reported alongside RMSE and MAE.
Rationale: The practical aim is to rank hexagons by predicted popularity, so a rank-based metric is the most meaningful headline; RMSE/MAE describe error magnitude.
Status: Locked.

D14 — Interpretability via SHAP

Decision: Use SHAP values to identify which feature groups drive predictions.
Status: Planned (approx. week 5).

D15 — Spatial train/test split

Decision: Consider a spatially-aware train/test split, since neighbouring hexagons share overlapping buffer features and a naive random split risks spatial leakage.
Status: Open — approach to be decided before modelling.


Scope

D16 — Study 2: opportunity-gap via prediction vs. actual divergence

Decision: Define opportunity gaps from the divergence between predicted and actual popular-café density (Study 1 residuals).
Status: Planned. Deferred until Study 1 residuals exist.

D17 — Competition saturation deferred / out of scope for now

Decision: The explicit competition-saturation scoring described in the exposé is not part of the current scope; the opportunity-gap formulation (D16) replaces it and is deferred until residuals are available.
Status: Deferred. Revisit if time allows.


Open technical items

O1 — Hexagon count discrepancy

1,353 hexagons generated vs. a supervisor reference example of 1,541. Likely a boundary-containment difference. Planned fix: buffer the Berlin polygon by 300–500 m before regenerating. Unresolved.

O2 — Project folder nesting

Notebook running from a doubled path
(berlin-cafe-thesis\berlin-cafe-thesis\notebooks); data/ may live in a
different copy. To be resolved so paths and version control point at a single
project root. Unresolved (identified 2026-07-12).


Data quality notes (for the Limitations section)


The café scrape spans multiple dates (2022–2026), so it is not a single-point snapshot; ratings and review counts were captured at different times.
Ratings and review counts are popularity proxies, not direct measures of business success. The absence of a popular café in a hexagon does not necessarily mean the location is unsuitable (could reflect missing supply or unmeasured factors).