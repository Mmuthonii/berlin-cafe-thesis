# Decision Log

Track major methodological pivots here as they happen — this becomes
direct source material for your Methodology and Discussion chapters
(e.g. "the study initially considered X, but Y was chosen because Z").

| Date | Decision | Reasoning |
|---|---|---|
| — | Switched square grid → H3 hexagons | No edge distortion, uniform neighbor distances, native buffer approximation |
| — | Switched binary target → count target | Preserves clustering intensity, needed for opportunity-gap residual analysis |
| — | Café data sourced from internship company (Google Places API) instead of self-collected | Avoids API cost/quota constraints; same legitimate source, pre-collected |
| — | Predictor features kept independent (OSM/Eurostat) rather than reusing company dataset | Avoids circularity/bias between target and features; supports reproducibility |
| — | Competition saturation adjustment parked | Simplifies scope; revisit as future work if time allows |
| — | Opportunity-gap exact definition deferred to post-Study 1 | Should be grounded in observed residual distribution, not fixed in advance |
