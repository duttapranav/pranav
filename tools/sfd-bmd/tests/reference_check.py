"""Cross-check the browser solver's published benchmark cases with anaStruct.

anaStruct is installed only in the CI validation environment; it is not shipped
to users and is not part of the browser application.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from anastruct import SystemElements

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "benchmark-cases.json"
TOL = 2e-4


def close(actual: float, expected: float, label: str, case_id: str) -> None:
    if not math.isclose(actual, expected, rel_tol=TOL, abs_tol=TOL):
        raise AssertionError(
            f"{case_id}: {label}: anaStruct={actual:.9g}, "
            f"benchmark={expected:.9g}, tolerance={TOL}"
        )


def run_case(case: dict) -> dict:
    length = float(case["beam_length"])
    supports = case["supports"]
    points = case.get("point_loads", [])
    udls = case.get("udls", [])

    coordinates = {0.0, length}
    coordinates.update(float(s["x"]) for s in supports)
    coordinates.update(float(p["x"]) for p in points)
    for load in udls:
        coordinates.add(float(load["start"]))
        coordinates.add(float(load["end"]))
    coordinates.update(float(m["x"]) for m in case.get("moments", []))
    anchors = sorted(coordinates)
    # Subdivide each load/support interval so linearly varying loads can be
    # represented by midpoint-intensity uniform element loads. Midpoint
    # integration preserves each linear region's total force and first moment.
    xs_set = set(anchors)
    for left, right in zip(anchors, anchors[1:]):
        for j in range(1, 101):
            xs_set.add(left + (right - left) * j / 100)
    xs = sorted(xs_set)

    # Large EA/EI values keep this comparison focused on beam response.
    model = SystemElements(EA=1.0e9, EI=1.0e6, mesh=1000)
    element_for_interval = {}
    for x0, x1 in zip(xs, xs[1:]):
        model.add_element(location=[[x0, 0.0], [x1, 0.0]])
        element_for_interval[(x0, x1)] = len(element_for_interval) + 1

    node_for_x = {x: model.find_node_id(vertex=[x, 0.0]) for x in anchors}

    for support in supports:
        node_id = node_for_x[float(support["x"])]
        kind = support["type"]
        if kind == "fixed":
            model.add_support_fixed(node_id)
        elif kind == "pin":
            model.add_support_hinged(node_id)
        elif kind == "roller":
            # A horizontal roller plane restrains vertical translation and
            # leaves beam rotation free, matching the browser model.
            model.add_support_roll(node_id, direction="x")
        else:
            raise ValueError(f"Unsupported support type: {kind}")

    for load in points:
        model.point_load(
            node_id=node_for_x[float(load["x"])],
            Fy=float(load["magnitude"]),
        )

    for moment in case.get("moments", []):
        model.moment_load(
            node_id=node_for_x[float(moment["x"])],
            Ty=float(moment["magnitude_clockwise_positive"]),
        )

    for load in udls:
        start, end = float(load["start"]), float(load["end"])
        q0 = float(load.get("start_intensity", load.get("intensity", 0.0)))
        q1 = float(load.get("end_intensity", load.get("intensity", q0)))
        for (x0, x1), element_id in element_for_interval.items():
            midpoint = (x0 + x1) / 2
            if midpoint >= start - 1e-10 and midpoint <= end + 1e-10:
                intensity = q0 + (q1 - q0) * (midpoint - start) / (end - start)
                if intensity:
                    model.q_load(q=intensity, element_id=element_id)

    model.solve()

    reactions = []
    for support in supports:
        result = model.get_node_results_system(node_for_x[float(support["x"])])
        reactions.append({
            "x": float(support["x"]),
            "type": support["type"],
            "vertical": float(result["Fy"]),
            # anaStruct's nodal reaction moment is opposite to the browser
            # application's applied-support-moment sign convention.
            "browser_moment_sign": -float(result["Tz"]),
        })

    element_results = [
        model.get_element_results(element_id)
        for element_id in sorted(element_for_interval.values())
    ]
    return {
        "reactions": reactions,
        "max_sagging": max(float(r["Mmax"]) for r in element_results),
        "min_hogging": min(float(r["Mmin"]) for r in element_results),
        "elements": element_results,
    }


def verify(case: dict) -> None:
    case_id = case["id"]
    expected = case["expected"]
    actual = run_case(case)

    expected_reactions = expected.get("reactions")
    if expected_reactions is None:
        expected_reactions = expected.get("vertical_reactions")
    if expected_reactions is not None:
        for i, target in enumerate(expected_reactions):
            close(actual["reactions"][i]["vertical"], target,
                  f"support {i + 1} vertical reaction", case_id)

    if "max_sagging_moment" in expected:
        close(actual["max_sagging"], expected["max_sagging_moment"],
              "maximum sagging moment", case_id)
    if "min_hogging_moment" in expected:
        close(actual["min_hogging"], expected["min_hogging_moment"],
              "minimum hogging moment", case_id)

    if "fixed_end_moment" in expected:
        fixed = next(r for r in actual["reactions"] if r["type"] == "fixed")
        close(fixed["browser_moment_sign"], expected["fixed_end_moment"],
              "fixed-end moment (browser sign convention)", case_id)

    if "fixed_support_reaction_moment_clockwise_positive" in expected:
        fixed = next(r for r in actual["reactions"] if r["type"] == "fixed")
        close(fixed["browser_moment_sign"],
              expected["fixed_support_reaction_moment_clockwise_positive"],
              "fixed-support reaction moment", case_id)

    if "end_moments" in expected:
        # The fixture records internal end moments. anaStruct exposes the
        # opposite support-reaction moment at the restrained nodes.
        fixed = [r for r in actual["reactions"] if r["type"] == "fixed"]
        for i, target in enumerate(expected["end_moments"]):
            # Internal end-moment sign reverses between the left and right
            # element ends, while anaStruct reports nodal support actions.
            internal_end_moment = (
                fixed[i]["browser_moment_sign"] if i == 0
                else -fixed[i]["browser_moment_sign"]
            )
            close(internal_end_moment, target,
                  f"fixed end {i + 1} internal moment", case_id)

    if "interior_support_moment" in expected:
        # Element envelopes include the internal support hogging extremum.
        candidates = [
            float(r[k]) for r in actual["elements"] for k in ("Mmin", "Mmax")
        ]
        close(min(candidates), expected["interior_support_moment"],
              "interior support moment", case_id)

    print(f"PASS {case_id}: anaStruct cross-check")


def main() -> None:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    for case in data["cases"]:
        verify(case)
    print(f"All {len(data['cases'])} benchmark cases cross-checked with anaStruct.")


if __name__ == "__main__":
    main()
