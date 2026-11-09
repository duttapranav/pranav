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

This benchmark set is a regression check, not third-party certification. The tool currently analyses vertical-plane bending of prismatic beams with linear-elastic Euler–Bernoulli behaviour. It does not replace a design-code check or independent engineering review. It does not currently model shear deformation, plasticity, geometric nonlinearity, settlement, temperature effects, axial-force interaction, or arbitrary applied point couples. Distributed loads may be uniform or vary linearly between their entered start and end intensities; curved/nonlinear load profiles are not supported.

## Unit equivalence

The metric pair kN–m and SI pair N–mm must give identical physical results. In particular, 1 kN/m is numerically equal to 1 N/mm. Point-force and moment display conversions differ and are handled separately.

## Verification run — 9 November 2026

The eight closed-form benchmark cases above were executed against the application calculation functions. All eight passed using a tolerance of 0.002 in the displayed engineering units. The largest absolute vertical-force equilibrium residual among those cases was below 0.000001 kN; the largest absolute moment-equilibrium residual was below 0.000001 kN·m.

An additional combined-load case (10 kN at x = 2 m plus 5 kN/m from x = 1–5 m on a 6 m simply supported beam) returned RA = 16.666667 kN, RB = 13.333333 kN and Mmax = 31.111112 kN·m, matching statics and the zero-shear location.

A unit-display regression check confirmed that a 10 kN/m UDL displays as 10 N/mm in the SI unit selection. This check caught and corrected a UDL conversion error in the first implementation.

The solver was subsequently cross-checked directly against anaStruct 1.7.1 using the same 11 reproducible benchmark fixtures in `benchmark-cases.json`. The independent reference job completed successfully for all 11 cases. The comparison checks support reactions and the relevant end-moment / maximum-moment results represented in each fixture. The reference runner constructs the beam in anaStruct from the fixture geometry and load regions; anaStruct is used only in CI and is not bundled into the browser application.

A Chromium browser regression suite completed successfully: 8 of 8 tests passed. It covers a simply supported central point load, SI-unit switching, a fixed-pinned UDL case, duplicate-support validation, CSV and PNG downloads, print-to-PDF rendering, and mobile viewport overflow. Subsequent cross-browser testing runs the same suite in Chromium, Firefox and WebKit; the PDF test is intentionally skipped outside Chromium because Playwright's page.pdf() is Chromium-only. In WebKit, the PNG test checks the first download exposed by a single user gesture; Chromium and Firefox verify all four PNG files.

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

- **Independent solver 1:** anaStruct 1.7.1 — 11/11 benchmark fixtures passed, including support reactions and applicable moment results.
- **Independent solver 2:** OpenSeesPy 3.8.0.0 — 11/11 benchmark fixtures passed for vertical support reactions and global vertical equilibrium; fixed-support reaction/end-moment sign checks are included where benchmark values are defined.
- **Browser regression:** Playwright 1.56.1 — 46 passed, 2 intentionally skipped, across 48 executions in Chromium, Firefox and WebKit. The skipped tests are the PDF-generation check in Firefox and WebKit because Playwright's `page.pdf()` is Chromium-only.
- **Diagram-level checks:** point-load shear jump and bending-moment continuity; partial-UDL shear slope and peak moment; cantilever hogging moment profile; and moment continuity plus shear jump at an interior support in a two-span continuous beam. These tests read the application's section inspector at selected beam positions. Three closed-form deflection cases and invalid E/I input handling also pass in all three browsers.
- **Exports and layout:** CSV download in all three browsers; all four PNG downloads in Chromium and Firefox; first diagram PNG download in WebKit; A4 PDF rendering in Chromium; narrow mobile viewport overflow check in all three browsers.
- **Workflow:** [GitHub Actions run 42588145386](https://github.com/duttapranav/pranav/actions/runs/42588145386) — independent anaStruct/OpenSeesPy checks and cross-browser regression completed successfully.
- **Test sources:** [anaStruct cross-check script](tests/reference_check.py), [OpenSeesPy cross-check script](tests/opensees_reference_check.py), [Playwright browser tests](tests/beam.spec.js), and [benchmark fixtures](benchmark-cases.json).
- Independent solver comparisons are additional evidence, not certification or proof of correctness for every possible input.

## Remaining verification scope

- The checks validate selected elastic beam response cases; they do not prove every possible input combination.
- Live GitHub Pages deployment, additional mobile devices/browsers, and broader export edge cases still require separate manual checks.
- The OpenSeesPy check compares vertical support reactions and global vertical equilibrium for all 11 fixtures, plus fixed-support reaction/end moments where fixture values are defined. It also independently compares three selected E-I deflections (simply supported point load, cantilever tip load and simply supported UDL) against closed-form values. Full diagram arrays and continuous deflection profiles have not yet been compared directly against OpenSeesPy or anaStruct.
- The current application does not yet support triangular/trapezoidal distributed loads, externally applied concentrated couples, settlement, elastic supports, shear deformation, axial force or geometric/material nonlinearity.
- The tool remains an educational and preliminary-analysis application, not a substitute for design-code checks or independent professional review.


## Elastic deflection module — 9 November 2026

The application now calculates vertical displacement using the same Euler–Bernoulli finite-element model as the force and moment analysis. Users enter Young's modulus, E, in GPa and the second moment of area, I, in m⁴. The default values (200 GPa and 8.0 × 10⁻⁴ m⁴) are illustrative steel-like inputs only; they must be replaced with the actual material and section properties before interpreting a result.

- The element stiffness matrix is multiplied by the constant flexural rigidity EI, with E converted from GPa to kN/m² for the application's kN–m solver.
- Cubic Hermite interpolation reconstructs vertical displacement between beam nodes.
- Candidate extrema are found from the derivative of each element's cubic displacement polynomial, rather than relying only on sampled plot points.
- The inspector reports local vertical displacement; the deflection plot and maximum absolute deflection are displayed in mm, with downward positive.
- CSV export now includes a `Deflection_mm` column; the deflection plot is included in the PNG diagram export.
- The model assumes constant E and I along the beam, linear elasticity, small displacement, and Euler–Bernoulli kinematics. It does not include shear deformation, variable sections/materials, support settlement, temperature effects, or geometric/material nonlinearity.

### Closed-form deflection benchmarks

For E = 200 GPa, I = 8.0 × 10⁻⁴ m⁴ and L = 6 m:

| Case | Analytical result | Expected maximum displacement |
|---|---|---:|
| Simply supported, P = 20 kN at midspan | PL³/(48EI) | 0.5625 mm downward at midspan |
| Cantilever, P = 20 kN at free end | PL³/(3EI) | 9.0000 mm downward at free end |
| Simply supported, q = 10 kN/m over full span | 5qL⁴/(384EI) | 1.0546875 mm downward at midspan |

The Playwright browser tests exercise these results in Chromium, Firefox and WebKit. The OpenSeesPy reference script builds independent elasticBeamColumn models using the same E and I, and compares nodal vertical displacement for all three cases. OpenSees reports upward-positive displacement; the verification runner changes sign when comparing with the application's downward-positive convention.

These are focused elastic beam benchmarks, not a general validation of all deflection cases. Deflection output is intended for preliminary analysis and education; it must be checked against an independent model and applicable serviceability criteria for engineering decisions.


## Linearly varying distributed-load verification — 9 November 2026

The distributed-load input now accepts an intensity at the start and end of each load region. Equal values represent a UDL; one zero end represents a triangular load; two nonzero unequal values represent a trapezoidal load. Intensities vary linearly between the two positions, and multiple load regions may overlap.

The finite-element solver uses the consistent nodal load vector for a linearly varying load with endpoint intensities q₀ and q₁ over element length ℓ:

- Vertical nodal forces: ℓ(7q₀ + 3q₁)/20 and ℓ(3q₀ + 7q₁)/20.
- Nodal moments: ℓ²(3q₀ + 2q₁)/60 and −ℓ²(2q₀ + 3q₁)/60.

The shear-force function integrates the linear load intensity exactly, producing a quadratic shear function. Bending-moment extrema are therefore evaluated using the quadratic roots of V(x) = 0, rather than a linear interpolation between shear samples. Resultant load and first moment are also integrated analytically for equilibrium reporting.

### New closed-form benchmarks

| Case | Load | Reactions (left, right) | Maximum sagging moment |
|---|---|---:|---:|
| Simply supported, 6 m, triangular | 0 to 10 kN/m | 10.000, 20.000 kN | 23.0940 kN·m |
| Simply supported, 6 m, trapezoidal | 2 to 8 kN/m | 12.000, 18.000 kN | 22.7207 kN·m |
| Simply supported, 6 m, partial triangular | 0 to 8 kN/m over x = 1–5 m | 6.2222, 9.7778 kN | 16.5695 kN·m |

Browser tests also verify the varying-load input fields, moment-extremum locations, and preservation of physical results when switching to SI display units. The independent anaStruct and OpenSeesPy reference runners subdivide each varying-load region and apply midpoint-intensity element loads; midpoint integration preserves the total force and first moment of a linearly varying load. This is a mesh-based independent cross-check, while the browser solver uses exact consistent element loading.
