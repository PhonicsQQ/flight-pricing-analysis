# Run the finished local demo

From the repository root:

```sh
python3 -m flights.export_demo
python3 -m flights.serve_demo
```

Open http://127.0.0.1:4174. Stop the server with Ctrl-C. It binds only to loopback and serves `artifacts/demo/`, not the workspace or `.env`. No credentials or flight requests are used. The build requires the existing frozen study plus saved analysis results; missing inputs cause an explicit error, never a synthetic fallback. Source-only users must first reproduce collection and analysis with their own local credentials and permitted use.

To reproduce the full analysis/export:

```sh
.venv/bin/python -m flights.analyze
.venv/bin/python -m flights.robustness
python3 -m flights.refresh_report
python3 -m flights.export_demo
.venv/bin/python -m unittest discover -s tests -v
node --test tests/demo.test.mjs
```

The refresh report is offline and requires the three already collected refreshed snapshots. Do not rerun live searches just to launch the demo. Browser calculation checks compare against the saved Python results. CSS responds to narrow screens; final visual QA dimensions and any limits are recorded in `docs/demo-verification.md`.

## Runtime and storage

`artifacts/demo/build.json` records per-file sizes and SHA-256 hashes. The first complete build is about 300 KB across a handful of HTML/CSS/JavaScript/JSON files. There are no package installs or server-side model computations for visitors. Python's local HTTP server is a preview convenience, not a production application service. Browser memory and local server measurements are machine-specific, not a promise about hosting limits.

No framework-specific Python hosting is required. [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud) is currently free and GitHub-connected, but adopting it here would require replacing the already working static UI without an inference need. [Cloudflare Pages' published free limits](https://developers.cloudflare.com/pages/platform/limits/) include 500 builds/month, 20,000 files/site, and 25 MiB/file (reviewed November 5, 2026). The measured bundle fits far below these size limits. This is a feasibility assessment only: no account, upload, plan, or deployment was created.

## Publication, after permissions are resolved

1. Obtain clarity for the intended individual histories, aggregates, and any screenshots. Record permitted attribution, retention, and export conditions. If only aggregates are allowed, replace the individual-history export before upload. Do not assume ignoring files in Git grants permission to host them.
2. Rebuild and review `artifacts/demo/` alone. All browser-delivered JSON is downloadable by visitors; a hidden UI does not protect the underlying data. Do not upload `.env`, ledger, raw responses, whole workspace, or analysis caches.
3. Recheck the chosen host's free plan and limits. Deploy only the approved static files, using a provided subdomain, with no functions, paid overages, or paid custom domain. Do not enable paid services without explicit approval.
4. Verify route/date selection, missing history, unavailable exact horizon, counts, mobile layout, attribution, and dataset dates at the deployed URL.

Local operation remains the $0 fallback. No publishing is required for the user to review the finished project.
