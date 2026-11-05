# Research decision — November 5, 2026

## Decision

Finish a descriptive local portfolio demo now. Preserve the October 30 freeze, show the November 5 revisions separately, and defer models and buying-strategy claims. More bulk collection is not necessary for this deliverable. No searches or paid services were used during this implementation.

## What the evidence supports

The frozen study has 167 usable histories from 168 planned route/date queries, 10,282 observations, and 9,113 exact seven-day pairs. The refresh check adds six dates to each of three selected trips, but revises two prices at overlapping timestamps. These are 18 new trip/date observations, not 18 new independent histories. The six oldest timestamps drop from each refreshed window; raw snapshots retain them.

The new same-trip sensitivity compares the 21 trips eligible in both 8–14 and 31–60 starting-lead bins. Equal-trip seven-day rise frequencies are 82.4% and 29.8%, respectively; mean changes are +$67.12 and −$3.84. This reduces changes in trip composition but still confounds lead time with market calendar dates. It was chosen after seeing the original results and is explicitly exploratory. Reproduce with `.venv/bin/python -m flights.robustness`.

All 183 flagged jumps remain in the original analysis. Their presence is not proof of a provider error; no flight-level explanation or realized purchase is established. No optimal booking time or causal weekday advice is claimed.

## Sources reviewed and what they do not establish

- [SerpApi Price Insights](https://serpapi.com/google-flights-price-insights), reviewed November 5: describes timestamp/price pairs and defines current lowest price among returned flights. It does not establish point-in-time immutability, full historical filter semantics, or a redistribution license for this project. Our revisions are empirical evidence against assuming immutability.
- [SerpApi terms](https://serpapi.com/legal), reviewed November 5 (page updated August 27, 2026): sections 1, 2, and 8 contain use restrictions and third-party-material caveats. The public page does not resolve permission to redistribute these collected histories or display our specific derived artifacts. This is an unresolved permissions assessment, not a legal conclusion that every research use is prohibited. The prepared provider inquiry asks about individual curves, aggregates, raw exports, and attribution separately; it has not been sent.
- [Scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) explains why information unavailable at prediction time invalidates an evaluation. [Its cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html) distinguishes correlated time-series data and untouched evaluation data. These principles reinforce the decision not to train on revised later-retrieved histories and call the result a prospective forecast.

## Framework choice

The existing `site/` is a separate placeholder with synthetic data and its own repository/hosting metadata. It is left unchanged. The local real-data demo retains its neutral design direction in `demo/`, with generated output in ignored `artifacts/demo/`.

A static browser demo is a bounded exception to the initial Streamlit preference: there is already a working static design, only 167 small histories, and no validated model needing Python inference. Python remains the reproducible research/export pipeline. The generated bundle is about 300 KB, uses no third-party JavaScript libraries or external assets, requires no credentials, and needs no application server in deployment. This avoids maintaining a second app framework. Node is only an optional development-test dependency.

The outcome explorer is labeled retrospective, leaves the full curve visible, and never displays a model probability. It compares exact observed pairs and explains the no-change benchmark on one pair without presenting that as model evaluation.

## What would justify modeling later

1. Resolve what the histories represent and preserve immutable retrieval snapshots; revisions remain explicit.
2. Write a dated evaluation protocol before selecting models or looking at future labels. Choose a prediction timestamp, exact horizon, and purchase deadline if evaluating policies. Train labels must already be observable at the cutoff.
3. Collect sufficient independent route/date groups over several future market periods. Reserve whole trip groups and a final period, with chronological label availability checks and no overlapping query variants across splits. Sampling and interval estimates must respect common calendar shocks.
4. Compare training-only majority/route-lead baselines and zero change before a modest model. Report MAE, class balance, Brier/calibration if probabilities are used, and route/lead breakdowns. Evaluate strategies on the same eligible histories without future decisions.

There is no defensible universal minimum sample size from these three checks. Ten remaining project attempts (190 used of 200) cannot establish broad forecasting performance. The account has 61 free searches as last verified November 5, but the stricter project cap and 40-search reserve still govern. Do not silently raise either cap or spend the remaining budget to force a model.

## Completion and remaining external dependency

Local demo, reproducible export, actual-data reconciliation, synthetic horizon tests, and research documentation are implemented. Public release remains contingent on data-display/redistribution clarification and a review of exactly which artifacts may be uploaded. Source code can be separated from data; source-only cloning does not reproduce private collected results until the user collects their own permitted dataset.
