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
