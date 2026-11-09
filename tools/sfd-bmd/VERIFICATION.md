# SFD & BMD Generator — Verification Record

This file records independent closed-form benchmark cases used to check the beam solver. Values below assume a prismatic, linear-elastic Euler–Bernoulli beam, small deflection, downward-positive loading, and sagging-positive bending moment.

## Benchmark cases

| Case | Input | Expected results |
|---|---|---|
| Simply supported, central point load | L = 6 m; P = 20 kN at x = 3 m | RA = RB = 10 kN; V = +10 kN immediately right of A and −10 kN immediately right of the load; Mmax = +30 kN·m at midspan |
| Cantilever, end point load | L = 6 m; P = 20 kN at free end | Vertical reaction = 20 kN; fixed-end reaction couple = −120 kN·m in the app's clockwise-positive reaction convention; internal M at fixed end = −120 kN·m; free-end M = 0 |
| Simply supported, full UDL | L = 6 m; q = 10 kN/m over 0–6 m | RA = RB = 30 kN; Mmax = +45 kN·m at midspan |
| Cantilever, full UDL | L = 6 m; q = 10 kN/m over 0–6 m | Vertical reaction = 60 kN; fixed-end reaction couple = −180 kN·m in the app's clockwise-positive reaction convention; internal M at fixed end = −180 kN·m; free-end M = 0 |
| Fixed-fixed, full UDL | L = 6 m; q = 10 kN/m over 0–6 m | RA = RB = 30 kN; end internal moments = −30 kN·m; midspan moment = +15 kN·m |
| Simply supported, eccentric point load | L = 6 m; P = 12 kN at x = 2 m | RA = 8 kN; RB = 4 kN; Mmax = +16 kN·m at x = 2 m |
| Simply supported, partial UDL | L = 6 m; q = 5 kN/m over x = 1–4 m | RA = 8.75 kN; RB = 6.25 kN; Mmax = +16.40625 kN·m at x = 2.75 m |
| Left overhang with tip load | L = 6 m; supports at x = 1 m and 5 m; P = 10 kN at x = 0 | RA = +12.5 kN; RB = −2.5 kN (uplift); moment at support A = −10 kN·m |

## Numerical method

- The beam is discretised into two-node Euler–Bernoulli beam elements with vertical displacement and rotation at each node.
- Mesh nodes are inserted at support positions, point-load positions and UDL boundaries.
- Uniformly distributed loads are applied using consistent element load vectors.
- Support restraints are applied to the relevant degrees of freedom, and reactions are recovered from restrained-degree-of-freedom residuals.
- The SFD is recovered from vertical equilibrium; the BMD is recovered from the applied loads and support actions.
- Diagram sampling includes left- and right-hand values at concentrated actions so shear jumps are not hidden.
- Maximum/minimum bending moments are checked at event locations and at zero-shear locations within each constant-load interval.

## Scope and limitations

This benchmark set is a regression check, not third-party certification. The tool currently analyses vertical-plane bending of prismatic beams with linear-elastic Euler–Bernoulli behaviour. It does not replace a design-code check or independent engineering review. It does not currently model shear deformation, plasticity, geometric nonlinearity, settlement, temperature effects, axial-force interaction, or arbitrary applied point couples.

## Unit equivalence

The metric pair kN–m and SI pair N–mm must give identical physical results. In particular, 1 kN/m is numerically equal to 1 N/mm. Point-force and moment display conversions differ and are handled separately.

## Verification run — 9 November 2026

The eight closed-form benchmark cases above were executed against the application calculation functions. All eight passed using a tolerance of 0.002 in the displayed engineering units. The largest absolute vertical-force equilibrium residual among those cases was below 0.000001 kN; the largest absolute moment-equilibrium residual was below 0.000001 kN·m.

An additional combined-load case (10 kN at x = 2 m plus 5 kN/m from x = 1–5 m on a 6 m simply supported beam) returned RA = 16.666667 kN, RB = 13.333333 kN and Mmax = 31.111112 kN·m, matching statics and the zero-shear location.

A unit-display regression check confirmed that a 10 kN/m UDL displays as 10 N/mm in the SI unit selection. This check caught and corrected a UDL conversion error in the first implementation.

The solver was subsequently cross-checked directly against anaStruct 1.7.1 using the same 11 reproducible benchmark fixtures in `benchmark-cases.json`. The independent reference job completed successfully for all 11 cases. The comparison checks support reactions and the relevant end-moment / maximum-moment results represented in each fixture. The reference runner constructs the beam in anaStruct from the fixture geometry and load regions; anaStruct is used only in CI and is not bundled into the browser application.

A Chromium browser regression suite also completed successfully: 8 of 8 tests passed. The tests cover a simply supported central point load, SI-unit switching, a fixed-pinned UDL case, duplicate-support validation, CSV and PNG downloads, print-to-PDF rendering, and mobile viewport overflow. The browser tests exercise the actual application page in a headless browser. PNG download, print-to-PDF output, mobile-device layout, and the live GitHub Pages deployment still require separate manual checks.

## Additional cross-checks — 9 November 2026

Further cases were run after reviewing the analytical validation suite in the open-source anaStruct project and external beam formula references.

| Additional case | Expected analytical response | Application response |
|---|---|---|
| Propped cantilever, L = 6 m, q = 10 kN/m | Fixed-end vertical reaction = 37.5 kN; prop reaction = 22.5 kN; fixed-end internal moment = −45 kN·m; maximum sagging = +25.3125 kN·m | Agreement within numerical tolerance |
| Two equal continuous spans, each 5 m, q = 1 kN/m over both spans | End reactions = 1.875 kN each; middle reaction = 6.25 kN; interior support moment = −3.125 kN·m; positive span maximum = +1.7578125 kN·m | Agreement within numerical tolerance |
| Fixed–pinned beam, L = 2 m, q = 1 kN/m | Pin reaction = 0.75 kN; fixed reaction = 1.25 kN; fixed-end hogging moment magnitude = 0.5 kN·m | Agreement within numerical tolerance |

The continuous-span case confirms that the solver can analyse a statically indeterminate multi-support arrangement when the user explicitly places multiple supports. The beam-type selector remains a preset arrangement selector; the actual calculation is driven by the support locations and types.

## Independent reference sources reviewed

- anaStruct project and its analytical validation tests: https://github.com/anastruct/anaStruct
- anaStruct analytical tests: https://github.com/anastruct/anaStruct/blob/master/tests/test_analytical.py
- anaStruct beam model documentation: https://anastruct-docs.readthedocs.io/en/latest/preprocessing_beams.html
- OpenSeesMatlab beam stresses and deflections verification example: https://openseesmatlab.readthedocs.io/en/latest/examples/verify/verify_beam/
- Steel Construction Institute, *Formulae for Beams*: https://www.steelconstruction.info/images/6/65/Handbook_of_Structural_Steelwork_EE_55-13.pdf

These are reference materials for independent verification. No third-party solver source code has been copied into this application. The anaStruct project is licensed under LGPL-3.0; this project currently uses its own JavaScript implementation.

## Automated verification record — 9 November 2026

- **Independent solver:** anaStruct 1.7.1 — 11/11 benchmark fixtures passed.
- **Browser regression:** Playwright 1.56.1 with Chromium — 5/5 tests passed.
- **Workflow:** [GitHub Actions run 42584859945](https://github.com/duttapranav/pranav/actions/runs/42584859945).
- **Test sources:** [anaStruct cross-check script](tests/reference_check.py), [Playwright browser tests](tests/beam.spec.js), and [benchmark fixtures](benchmark-cases.json).
- The independent anaStruct comparison is a separate numerical implementation, not a certification or a proof of correctness for every possible input.

## Remaining verification scope

- The checks validate selected elastic beam response cases; they do not prove every possible input combination.
- Live GitHub Pages deployment, additional mobile devices/browsers, and broader export edge cases still require separate manual checks.
- A direct OpenSees run using the identical fixture inputs has not yet been performed. OpenSees documentation and verification examples were reviewed as additional reference material.
- The current application does not yet support triangular/trapezoidal distributed loads, externally applied concentrated couples, settlement, elastic supports, shear deformation, axial force or geometric/material nonlinearity.
- The tool remains an educational and preliminary-analysis application, not a substitute for design-code checks or independent professional review.
