#!/usr/bin/env python3
"""Closed-form reference checks for prescribed support settlement cases.

Sign convention: downward settlement and downward applied load are positive;
sagging bending moment is positive. These checks are independent of the
browser finite-element assembly and use classical equal-span compatibility.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

FIXTURES = Path(__file__).with_name("settlement-cases.json")


def close(actual: float, expected: float, label: str, case_id: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8):
        raise AssertionError(
            f"{case_id}: {label}: actual={actual:.10g}, "
            f"expected={expected:.10g}"
        )


def main() -> None:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    for case in data["cases"]:
        case_id = case["id"]
        ei = float(case["E_kN_m2"]) * float(case["I_m4"])
        delta = float(case["settlement_mm"]) / 1000.0
        span = float(case["span_m"])
        if case["type"] == "two_equal_spans_middle_support_settlement":
            outer = 3.0 * ei * delta / span**3
            middle = -2.0 * outer
            peak = 3.0 * ei * delta / span**2
            close(outer, case["expected"]["outer_reaction_kN"],
                  "outer support reaction", case_id)
            close(middle, case["expected"]["middle_reaction_kN"],
                  "middle support reaction", case_id)
            close(peak, case["expected"]["middle_sagging_kNm"],
                  "middle support sagging moment", case_id)
        elif case["type"] == "equal_settlement_simple_span":
            close(0.0, case["expected"]["reaction_each_kN"],
                  "support reaction", case_id)
            close(0.0, case["expected"]["bending_moment_kNm"],
                  "bending moment", case_id)
            close(delta * 1000.0, case["expected"]["midspan_deflection_mm"],
                  "midspan displacement", case_id)
        else:
            raise ValueError(f"Unknown settlement case type: {case['type']}")
        print(f"PASS {case_id}: closed-form settlement benchmark")


if __name__ == "__main__":
    main()
