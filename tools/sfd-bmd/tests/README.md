# Beam calculator verification tests

This directory contains two independent verification layers:

1. `reference_check.py` builds the same benchmark geometries in anaStruct 1.7.1 and compares support reactions and selected bending-moment results. anaStruct is installed only in CI; it is not bundled into the public static application.
2. `beam.spec.js` runs Chromium browser regression checks against the actual `index.html`, including calculation display, SI unit switching, invalid support detection and CSV download.

Run locally:

```bash
python -m pip install anastruct==1.7.1
python tools/sfd-bmd/tests/reference_check.py
cd tools/sfd-bmd/tests
npm install
npx playwright install chromium
npm run test:e2e
```

The benchmark fixture source is `../benchmark-cases.json`. The test tolerances are intentionally explicit in the test code. A passing suite is evidence for the covered cases only; it is not a proof for every possible model or a substitute for design checks and professional review.

anaStruct is distributed under GPL-3.0-or-later. It is used as an external CI reference dependency and no anaStruct source code is copied into this browser application.
