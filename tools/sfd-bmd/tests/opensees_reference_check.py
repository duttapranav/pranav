"""Independent OpenSeesPy reference check for the beam benchmark fixtures.

This script is run only in CI. It creates a 2D elasticBeamColumn model for
each benchmark and compares vertical support reactions with the independently
maintained expected values. The browser application does not import OpenSees.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import openseespy.opensees as ops

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "benchmark-cases.json"
REL_TOL = 2.0e-5
ABS_TOL = 2.0e-5
SUBDIVISIONS_PER_EVENT_INTERVAL = 200


def close(actual: float, expected: float, label: str, case_id: str) -> None:
    if not math.isclose(actual, expected, rel_tol=REL_TOL, abs_tol=ABS_TOL):
        raise AssertionError(
            f"{case_id}: {label}: OpenSeesPy={actual:.10g}, "
            f"benchmark={expected:.10g}, tolerance rel={REL_TOL}, abs={ABS_TOL}"
        )


def build_mesh(case: dict) -> list[float]:
    length = float(case["beam_length"])
    events = {0.0, length}
    events.update(float(s["x"]) for s in case["supports"])
    events.update(float(p["x"]) for p in case.get("point_loads", []))
    for load in case.get("udls", []):
        events.add(float(load["start"]))
        events.add(float(load["end"]))
    anchors = sorted(events)
    mesh = set(anchors)
    for left, right in zip(anchors, anchors[1:]):
        for i in range(1, SUBDIVISIONS_PER_EVENT_INTERVAL):
            mesh.add(left + (right - left) * i / SUBDIVISIONS_PER_EVENT_INTERVAL)
    return sorted(mesh)


def run_case(case: dict) -> list[dict]:
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 3)

    # Arbitrary consistent elastic properties: reactions in this statically
    # determinate/indeterminate linear-elastic model are independent of scale.
    area, elastic_modulus, inertia = 1.0, 2.0e8, 1.0e6
    ops.geomTransf("Linear", 1)

    xs = build_mesh(case)
    node_at = {}
    for tag, x in enumerate(xs, start=1):
        ops.node(tag, x, 0.0)
        node_at[x] = tag

    for support in case["supports"]:
        tag = node_at[float(support["x"])]
        kind = support["type"]
        if kind == "fixed":
            ops.fix(tag, 1, 1, 1)
        elif kind == "pin":
            ops.fix(tag, 1, 1, 0)
        elif kind == "roller":
            # Horizontal beam: vertical restraint, axial translation and
            # section rotation remain free at the roller.
            ops.fix(tag, 0, 1, 0)
        else:
            raise ValueError(f"Unsupported support type {kind!r}")

    element_data = []
    for tag, (x0, x1) in enumerate(zip(xs, xs[1:]), start=1):
        n0, n1 = node_at[x0], node_at[x1]
        ops.element(
            "elasticBeamColumn", tag, n0, n1,
            area, elastic_modulus, inertia, 1,
        )
        element_data.append((tag, x0, x1))

    # Element and nodal loads must be created inside an active load pattern.
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for tag, x0, x1 in element_data:
        midpoint = (x0 + x1) / 2.0
        intensity = 0.0
        for load in case.get("udls", []):
            start, end = float(load["start"]), float(load["end"])
            if start - 1e-12 <= midpoint <= end + 1e-12:
                q0 = float(load.get("start_intensity", load.get("intensity", 0.0)))
                q1 = float(load.get("end_intensity", load.get("intensity", q0)))
                intensity += q0 + (q1 - q0) * (midpoint - start) / (end - start)
        if intensity:
            # OpenSees local y is upward for this left-to-right horizontal
            # element; the application fixture defines downward loads positive.
            ops.eleLoad("-ele", tag, "-type", "-beamUniform", -intensity)

    for load in case.get("point_loads", []):
        ops.load(
            node_at[float(load["x"])],
            0.0,
            -float(load["magnitude"]),
            0.0,
        )

    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.test("NormDispIncr", 1.0e-12, 20, 0)
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")
    code = ops.analyze(1)
    if code != 0:
        raise RuntimeError(f"OpenSees analysis failed with code {code}")

    ops.reactions()
    results = []
    for support in case["supports"]:
        tag = node_at[float(support["x"])]
        reaction = ops.nodeReaction(tag)
        if len(reaction) < 3 or not all(math.isfinite(float(v)) for v in reaction):
            raise AssertionError(f"{case['id']}: non-finite support reaction")
        results.append({
            "x": float(support["x"]),
            "type": support["type"],
            "vertical": float(reaction[1]),
            "moment_ccw": float(reaction[2]),
        })

    # Global vertical force equilibrium is checked independently from the
    # benchmark values, including uplift reactions at overhang supports.
    total_load = sum(
        float(p["magnitude"]) for p in case.get("point_loads", [])
    ) + sum(
        float(u["intensity"]) * (float(u["end"]) - float(u["start"]))
        for u in case.get("udls", [])
    )
    total_reaction = sum(r["vertical"] for r in results)
    close(total_reaction, total_load, "global vertical equilibrium", case["id"])

    ops.wipe()
    return results


def verify(case: dict) -> None:
    expected = case["expected"]
    targets = expected.get("reactions", expected.get("vertical_reactions"))
    if targets is None:
        raise AssertionError(f"{case['id']}: fixture has no expected reactions")
    actual = run_case(case)
    if len(actual) != len(targets):
        raise AssertionError(f"{case['id']}: reaction count mismatch")
    for i, target in enumerate(targets):
        close(
            actual[i]["vertical"],
            float(target),
            f"support {i + 1} vertical reaction",
            case["id"],
        )

    # The fixtures use clockwise-positive support moments / hogging-negative
    # internal end moments. OpenSees reports counter-clockwise-positive nodal
    # reaction moments, so convert explicitly at each end.
    clockwise_positive = [-r["moment_ccw"] for r in actual]
    if "support_reaction_moments_clockwise_positive" in expected:
        for i, target in enumerate(expected["support_reaction_moments_clockwise_positive"]):
            close(clockwise_positive[i], float(target),
                  f"support {i + 1} reaction moment", case["id"])

    fixed_indices = [
        i for i, support in enumerate(case["supports"])
        if support["type"] == "fixed"
    ]
    if "fixed_end_moment" in expected:
        if len(fixed_indices) != 1:
            raise AssertionError(f"{case['id']}: expected one fixed support")
        close(clockwise_positive[fixed_indices[0]],
              float(expected["fixed_end_moment"]),
              "fixed-end moment", case["id"])

    if "fixed_support_reaction_moment_clockwise_positive" in expected:
        if len(fixed_indices) != 1:
            raise AssertionError(f"{case['id']}: expected one fixed support")
        close(clockwise_positive[fixed_indices[0]],
              float(expected["fixed_support_reaction_moment_clockwise_positive"]),
              "fixed-support reaction moment", case["id"])

    if "end_moments" in expected:
        ordered = sorted(fixed_indices, key=lambda i: float(case["supports"][i]["x"]))
        internal_end_moments = []
        for i in ordered:
            x = float(case["supports"][i]["x"])
            # For a fixed end at the left, internal-end moment is minus the
            # nodal reaction moment; at the right it has the same sign.
            internal_end_moments.append(
                -actual[i]["moment_ccw"] if x <= 1e-12
                else actual[i]["moment_ccw"]
            )
        if len(internal_end_moments) != len(expected["end_moments"]):
            raise AssertionError(f"{case['id']}: fixed-end moment count mismatch")
        for i, target in enumerate(expected["end_moments"]):
            close(internal_end_moments[i], float(target),
                  f"fixed end {i + 1} internal moment", case["id"])

    if "fixed_end_internal_moment" in expected:
        if len(fixed_indices) != 1:
            raise AssertionError(f"{case['id']}: expected one fixed support")
        i = fixed_indices[0]
        x = float(case["supports"][i]["x"])
        internal = -actual[i]["moment_ccw"] if x <= 1e-12 else actual[i]["moment_ccw"]
        close(internal, float(expected["fixed_end_internal_moment"]),
              "fixed-end internal moment", case["id"])

    print(f"PASS {case['id']}: OpenSeesPy reactions, moments and equilibrium")



def verify_deflection_benchmarks() -> None:
    """Compare E-I beam displacements with independent OpenSeesPy models.

    Units: kN, m, kN/m², m⁴. OpenSees vertical displacement is upward
    positive, while the browser tool reports downward-positive deflection.
    """
    E = 200.0e6  # 200 GPa expressed as kN/m²
    I = 8.0e-4   # m⁴
    A = 1.0      # m²; axial stiffness does not affect these bending cases
    L = 6.0
    ndiv = 24
    xs = [L * i / ndiv for i in range(ndiv + 1)]
    node_at = {round(x, 10): i + 1 for i, x in enumerate(xs)}

    cases = [
        ("SS-DEF-POINT", "simply", "point", 0.5625, 3.0),
        ("CANT-DEF-POINT", "cantilever", "point", 9.0, 6.0),
        ("SS-DEF-UDL", "simply", "udl", 1.0546875, 3.0),
    ]
    for case_id, kind, load_kind, expected_mm, inspect_x in cases:
        ops.wipe()
        ops.model("basic", "-ndm", 2, "-ndf", 3)
        ops.geomTransf("Linear", 1)
        for tag, x in enumerate(xs, start=1):
            ops.node(tag, x, 0.0)
        for tag, (x0, x1) in enumerate(zip(xs, xs[1:]), start=1):
            ops.element("elasticBeamColumn", tag, node_at[round(x0, 10)],
                        node_at[round(x1, 10)], A, E, I, 1)

        if kind == "simply":
            ops.fix(node_at[0.0], 1, 1, 0)
            ops.fix(node_at[round(L, 10)], 0, 1, 0)
        else:
            ops.fix(node_at[0.0], 1, 1, 1)

        ops.timeSeries("Linear", 1)
        ops.pattern("Plain", 1, 1)
        if load_kind == "point":
            ops.load(node_at[round(inspect_x, 10)], 0.0, -20.0, 0.0)
        else:
            for tag in range(1, ndiv + 1):
                ops.eleLoad("-ele", tag, "-type", "-beamUniform", -10.0)

        ops.constraints("Transformation")
        ops.numberer("RCM")
        ops.system("BandGeneral")
        ops.test("NormDispIncr", 1.0e-12, 20, 0)
        ops.algorithm("Linear")
        ops.integrator("LoadControl", 1.0)
        ops.analysis("Static")
        code = ops.analyze(1)
        if code != 0:
            raise RuntimeError(f"{case_id}: OpenSeesPy analysis failed: {code}")

        node = node_at[round(inspect_x, 10)]
        # OpenSees uses upward-positive vertical displacement.
        downward_mm = -float(ops.nodeDisp(node, 2)) * 1000.0
        close(downward_mm, expected_mm, "maximum/section deflection (mm)", case_id)
        print(f"PASS {case_id}: OpenSeesPy deflection = {downward_mm:.8f} mm")
    ops.wipe()


def main() -> None:
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"]
    for case in cases:
        verify(case)
    print(f"All {len(cases)} benchmark cases cross-checked with OpenSeesPy.")
    verify_deflection_benchmarks()
    print("All 3 E-I deflection benchmarks cross-checked with OpenSeesPy.")


if __name__ == "__main__":
    main()
