# Beam calculator verification tests

This directory contains independent numerical and browser verification:

1. `reference_check.py` builds each fixture in anaStruct 1.7.1 and compares support reactions and selected moment results.
2. `opensees_reference_check.py` independently builds 2D elasticBeamColumn models in OpenSeesPy 3.8.0.0, compares all benchmark vertical support reactions, checks global vertical equilibrium, and verifies three E-I deflection cases against closed-form solutions.
3. `beam.spec.js` exercises the real application page in Playwright across Chromium, Firefox and WebKit. It includes section-inspector checks for point-load shear jumps and moment continuity, partial-UDL shear slope and peak moment, cantilever hogging moments, continuity at an interior support of a two-span beam, and closed-form deflection checks for a simply supported point load, cantilever point load and simply supported UDL. It also validates rejection of non-positive E and I inputs. Chromium additionally generates an A4 PDF because Playwright's `page.pdf()` is Chromium-specific. Chromium and Firefox are checked for all four PNG downloads; WebKit is checked for its first user-gesture download because WebKit limits multiple programmatic downloads from one gesture in this test environment.

The two reference solvers are installed only in CI; neither is bundled into the browser application.

Run locally:

```bash
python -m pip install anastruct==1.7.1 openseespy==3.8.0.0
python tools/sfd-bmd/tests/reference_check.py
python tools/sfd-bmd/tests/opensees_reference_check.py
cd tools/sfd-bmd/tests
npm install
npx playwright install chromium firefox webkit
npm run test:e2e
```

The benchmark fixture source is `../benchmark-cases.json`. Tolerances are explicit in each test script. A passing suite is evidence for the cases covered, not proof of correctness for every possible model or a substitute for design checks and professional review.

OpenSeesPy and anaStruct are external CI reference dependencies. Their source code is not copied into or shipped with the browser application. Review their respective licenses and usage terms before any separate commercial redistribution or integration.
