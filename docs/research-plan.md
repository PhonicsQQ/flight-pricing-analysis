# Research and demo gates

## Descriptive analysis after feasibility

Produce individual trajectories, route comparisons by lead-time bucket, exact 1/3/7-day changes in dollars and percentages, direction frequencies, and lowest observed fare/lead-time distributions with ties. Display denominators, independent trip counts, window lengths, and missingness next to summaries. Separate departure-weekday from observation-weekday associations. Recheck dates under UTC versus Baltimore before asserting weekday patterns.

Do not pool all rows as independent trips. Compare both observation-weighted and equal-trip summaries, and use trip-cluster bootstrap intervals only when enough independent trips exist; overlapping departure dates and shared market shocks can create additional dependence. Small pilot results should remain descriptive. Account for route, lead time, and calendar/holiday effects where supported. Do not claim weekday causality. Full-trajectory normalization and oracle minima are retrospective only.

## Modeling decision

First assess independent trips, complete horizon pairs, class balance, time span, revision evidence, and whether multiple nonoverlapping evaluation periods are possible. Record a go/no-go rationale before fitting. If meaningful blocked evaluation is impossible, finish as an exploratory tool.

If feasible, targets are 7-day direction and dollar change. Compare zero change, training-set majority direction, and adequately supported training-only route/lead-time buckets before regularized regression or modest boosting. Freeze all splits and the final test period in a manifest. Never use random row splits. Keep all variants of a route/departure together. Train labels must end before the test prediction cutoff; purge boundary overlaps and fit preprocessing only on training data. Group separation may require discarding otherwise available overlapping rows.

Retrospective provider histories are not necessarily point-in-time archives. A model trained on later revised history can only be described as a retrospective simulation unless historic availability is substantiated. For genuine forward evaluation, use snapshots actually available at prediction time. Do not backdate current metadata into features. Add leakage tests once the real split implementation exists, including label cutoffs, group disjointness, preprocessing fitting, and snapshot availability.

Use validation windows for selection, leaving the final test untouched. Report MAE, majority-baseline comparisons, balanced classification metrics, and Brier/calibration diagnostics if displaying probabilities, broken down by route and lead time with counts. Unseen-route claims require a separate route-held-out evaluation. Save metrics, split manifests, model/data versions, and feature schema. Report failure to beat a baseline honestly.

## Buying strategies, only if supported

Predeclare a shared starting lead time, final purchase deadline, and missing-data eligibility. Compare buy at first eligible date, buy at a fixed lead time, wait a fixed duration, and a model strategy using only available information. Every policy must use the same eligible histories/start/deadline; do not substitute the next available observation silently. Show savings and losses from waiting, coverage lost to missing data, and a clearly labeled hindsight oracle that cannot be implemented in advance.

## Demo after data and publication gates

Preferred implementation: Streamlit loading saved processed artifacts, with no collector imports, credentials, or outbound searches. Route/departure selector, actual history with visible missingness, exact observed changes, route summaries/counts, methods and limitations, collection dates/coverage, and intended versus verified fare definition. A model replay is optional and requires a saved evaluated model; hide future observations until outcome reveal. Do not render mock trajectories or probabilities as findings.

Before delivery, test empty/missing artifacts, supported selections, date filters, and operation with credentials absent and network blocked. Check the app visually. Keep public artifacts in an explicitly approved export directory, separate from ignored private data. Measure installed size, artifact size, startup latency, and memory, then research a currently free host. Document resource limits and a local fallback; no deployment or paid activation before these gates. These app/model tests are pending because neither component should be built before data feasibility.
