#!/usr/bin/env python3
"""Aggregate BMAT pairwise-debate outcomes into a single deterministic ranking.

Used by the idea-discovery hypothesis tournament (round type ``pairwise-debate``)
to turn a set of head-to-head debate verdicts into one ordered ranking with a
numeric rating per hypothesis. This reduces reliance on a model self-reporting a
final order and makes the ranking reproducible from the recorded matches.

The default method is Bradley-Terry maximum likelihood via the MM (Zermelo)
algorithm. It is order-independent and deterministic: the same match set always
yields the same ratings, regardless of the order matches were played. A classic
sequential Elo update is also available for compatibility with Elo-style logs.

This script is dependency-free (standard library only) so it runs in source
checkouts, marketplace sources, and installed cache roots without extra install.

Input JSON (``--matches PATH`` or stdin):

    {
      "tournament_id": "HT-20250102-001",
      "candidates": ["H-001", "H-002", "H-003"],   # optional; inferred if absent
      "matches": [
        {"a": "H-001", "b": "H-002", "winner": "a"},
        {"a": "H-001", "b": "H-003", "winner": "draw"},
        {"a": "H-002", "b": "H-003", "winner": "b", "weight": 2}
      ]
    }

``winner`` is one of ``a`` | ``b`` | ``draw`` (``tie`` accepted as an alias).
``weight`` is an optional positive multiplier for repeated or high-confidence
matches (default 1).

Output JSON:

    {
      "method": "bradley-terry",
      "ratings": {"H-001": 1547.2, ...},        # Elo-scaled, deterministic
      "matches_played": {"H-001": 2, ...},
      "matches_won": {"H-001": 1.5, ...},        # draws count as 0.5
      "final_ranking": [                          # hypothesis-tournament shape
        {"rank": 1, "hypothesis_id": "H-001", "elo_rating": 1547.2,
         "matches_played": 2, "matches_won": 1.5}
      ],
      "iterations": 37,
      "converged": true
    }
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ELO_BASE = 1500.0
ELO_SCALE = 400.0  # points per factor-of-10 strength ratio
DEFAULT_K = 24.0
MM_MAX_ITERS = 1000
MM_TOLERANCE = 1e-9
# Fractional prior win+loss vs a virtual average opponent. Keeps Bradley-Terry
# finite when a hypothesis wins or loses all of its matches.
PRIOR_STRENGTH = 0.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate pairwise debate outcomes into a ranking.")
    parser.add_argument("--matches", type=Path, help="Path to matches JSON. Reads stdin if omitted.")
    parser.add_argument("--out", type=Path, help="Write result JSON to this path instead of stdout.")
    parser.add_argument(
        "--method",
        choices=("bradley-terry", "elo"),
        default="bradley-terry",
        help="bradley-terry (default, order-independent) or elo (sequential).",
    )
    parser.add_argument("--k", type=float, default=DEFAULT_K, help="Elo K-factor (elo method only).")
    parser.add_argument("--selftest", action="store_true", help="Run built-in assertions and exit.")
    return parser.parse_args()


def normalize_winner(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"a", "b"}:
        return text
    if text in {"draw", "tie", "d"}:
        return "draw"
    raise ValueError(f"invalid winner value: {value!r} (expected a|b|draw)")


def load_matches(payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    raw_matches = payload.get("matches")
    if not isinstance(raw_matches, list) or not raw_matches:
        raise ValueError("payload.matches must be a non-empty array")

    matches: list[dict[str, Any]] = []
    inferred: list[str] = []
    for index, match in enumerate(raw_matches):
        if not isinstance(match, dict):
            raise ValueError(f"matches[{index}] must be an object")
        a = str(match.get("a", "")).strip()
        b = str(match.get("b", "")).strip()
        if not a or not b:
            raise ValueError(f"matches[{index}] must have non-empty 'a' and 'b'")
        if a == b:
            raise ValueError(f"matches[{index}] cannot pit a hypothesis against itself")
        winner = normalize_winner(match.get("winner"))
        weight = match.get("weight", 1)
        try:
            weight = float(weight)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"matches[{index}].weight must be numeric") from exc
        if weight <= 0:
            raise ValueError(f"matches[{index}].weight must be positive")
        matches.append({"a": a, "b": b, "winner": winner, "weight": weight})
        for candidate in (a, b):
            if candidate not in inferred:
                inferred.append(candidate)

    declared = payload.get("candidates")
    if isinstance(declared, list) and declared:
        candidates = [str(c).strip() for c in declared if str(c).strip()]
        for candidate in inferred:
            if candidate not in candidates:
                candidates.append(candidate)
    else:
        candidates = inferred
    return candidates, matches


def tally(candidates: list[str], matches: list[dict[str, Any]]) -> tuple[dict[str, float], dict[str, float]]:
    played = {c: 0.0 for c in candidates}
    won = {c: 0.0 for c in candidates}
    for match in matches:
        a, b, winner, weight = match["a"], match["b"], match["winner"], match["weight"]
        played[a] += weight
        played[b] += weight
        if winner == "a":
            won[a] += weight
        elif winner == "b":
            won[b] += weight
        else:  # draw
            won[a] += 0.5 * weight
            won[b] += 0.5 * weight
    return played, won


def strengths_to_elo(strengths: dict[str, float]) -> dict[str, float]:
    logs = [math.log(s) for s in strengths.values()]
    mean_log = sum(logs) / len(logs)
    ratings = {}
    for candidate, strength in strengths.items():
        ratings[candidate] = round(ELO_BASE + (ELO_SCALE / math.log(10.0)) * (math.log(strength) - mean_log), 1)
    return ratings


def bradley_terry(candidates: list[str], matches: list[dict[str, Any]]) -> tuple[dict[str, float], int, bool]:
    """Bradley-Terry strengths via the MM algorithm with a symmetric prior."""
    strength = {c: 1.0 for c in candidates}
    # wins[i] = fractional wins for i (draw = 0.5); pair_weight[(i,j)] = total games i vs j
    wins = {c: PRIOR_STRENGTH for c in candidates}
    pair_weight: dict[tuple[str, str], float] = {}
    for match in matches:
        a, b, winner, weight = match["a"], match["b"], match["winner"], match["weight"]
        key = (a, b) if a < b else (b, a)
        pair_weight[key] = pair_weight.get(key, 0.0) + weight
        if winner == "a":
            wins[a] += weight
        elif winner == "b":
            wins[b] += weight
        else:
            wins[a] += 0.5 * weight
            wins[b] += 0.5 * weight
    # Prior adds PRIOR_STRENGTH games vs a virtual average opponent per candidate.
    opponents: dict[str, list[tuple[str, float]]] = {c: [] for c in candidates}
    for (i, j), w in pair_weight.items():
        opponents[i].append((j, w))
        opponents[j].append((i, w))

    converged = False
    iterations = 0
    for iterations in range(1, MM_MAX_ITERS + 1):
        new_strength = {}
        for c in candidates:
            denom = PRIOR_STRENGTH / (strength[c] + 1.0)  # prior vs virtual average (strength 1)
            for opp, w in opponents[c]:
                denom += w / (strength[c] + strength[opp])
            new_strength[c] = wins[c] / denom if denom > 0 else strength[c]
        # normalize (geometric mean = 1) for numerical stability and determinism
        geo = math.exp(sum(math.log(v) for v in new_strength.values()) / len(new_strength))
        new_strength = {c: v / geo for c, v in new_strength.items()}
        delta = max(abs(new_strength[c] - strength[c]) for c in candidates)
        strength = new_strength
        if delta < MM_TOLERANCE:
            converged = True
            break
    return strength, iterations, converged


def sequential_elo(candidates: list[str], matches: list[dict[str, Any]], k: float) -> dict[str, float]:
    rating = {c: ELO_BASE for c in candidates}
    for match in matches:
        a, b, winner, weight = match["a"], match["b"], match["winner"], match["weight"]
        expected_a = 1.0 / (1.0 + 10 ** ((rating[b] - rating[a]) / ELO_SCALE))
        expected_b = 1.0 - expected_a
        if winner == "a":
            score_a, score_b = 1.0, 0.0
        elif winner == "b":
            score_a, score_b = 0.0, 1.0
        else:
            score_a, score_b = 0.5, 0.5
        rating[a] += k * weight * (score_a - expected_a)
        rating[b] += k * weight * (score_b - expected_b)
    return {c: round(v, 1) for c, v in rating.items()}


def build_result(payload: dict[str, Any], method: str, k: float) -> dict[str, Any]:
    candidates, matches = load_matches(payload)
    played, won = tally(candidates, matches)

    iterations = 0
    converged = True
    if method == "bradley-terry":
        strengths, iterations, converged = bradley_terry(candidates, matches)
        ratings = strengths_to_elo(strengths)
    else:
        ratings = sequential_elo(candidates, matches, k)

    ranking = sorted(candidates, key=lambda c: (-ratings[c], c))
    final_ranking = []
    for rank, c in enumerate(ranking, start=1):
        final_ranking.append(
            {
                "rank": rank,
                "hypothesis_id": c,
                "elo_rating": ratings[c],
                "matches_played": round(played[c], 3),
                "matches_won": round(won[c], 3),
            }
        )

    result: dict[str, Any] = {
        "method": method,
        "ratings": ratings,
        "matches_played": {c: round(played[c], 3) for c in candidates},
        "matches_won": {c: round(won[c], 3) for c in candidates},
        "final_ranking": final_ranking,
    }
    if payload.get("tournament_id"):
        result["tournament_id"] = payload["tournament_id"]
    if method == "bradley-terry":
        result["iterations"] = iterations
        result["converged"] = converged
    return result


def run_selftest() -> int:
    # 1) Transitive set A>B>C: ranking must be A, B, C for both methods.
    payload = {
        "candidates": ["A", "B", "C"],
        "matches": [
            {"a": "A", "b": "B", "winner": "a"},
            {"a": "B", "b": "C", "winner": "a"},
            {"a": "A", "b": "C", "winner": "a"},
        ],
    }
    bt = build_result(payload, "bradley-terry", DEFAULT_K)
    order = [row["hypothesis_id"] for row in bt["final_ranking"]]
    assert order == ["A", "B", "C"], f"BT order wrong: {order}"
    assert bt["converged"], "BT did not converge on simple transitive set"
    assert bt["ratings"]["A"] > bt["ratings"]["B"] > bt["ratings"]["C"], bt["ratings"]

    # 2) Order-independence: shuffling match order must not change ratings.
    shuffled = {"candidates": ["A", "B", "C"], "matches": list(reversed(payload["matches"]))}
    bt2 = build_result(shuffled, "bradley-terry", DEFAULT_K)
    assert bt["ratings"] == bt2["ratings"], "BT ratings changed with match order"

    # 3) Symmetry: a single draw yields equal ratings.
    draw = {"candidates": ["X", "Y"], "matches": [{"a": "X", "b": "Y", "winner": "draw"}]}
    bt3 = build_result(draw, "bradley-terry", DEFAULT_K)
    assert abs(bt3["ratings"]["X"] - bt3["ratings"]["Y"]) < 1e-6, bt3["ratings"]
    assert bt3["matches_won"]["X"] == 0.5 and bt3["matches_won"]["Y"] == 0.5

    # 4) Sweep winner beats never-winner even with all-win record (prior keeps it finite).
    sweep = {
        "candidates": ["W", "L", "M"],
        "matches": [
            {"a": "W", "b": "L", "winner": "a"},
            {"a": "W", "b": "M", "winner": "a"},
            {"a": "M", "b": "L", "winner": "a"},
        ],
    }
    bt4 = build_result(sweep, "bradley-terry", DEFAULT_K)
    assert all(math.isfinite(v) for v in bt4["ratings"].values()), bt4["ratings"]
    top = bt4["final_ranking"][0]["hypothesis_id"]
    assert top == "W", f"expected W on top, got {top}"

    # 5) Elo method runs and ranks the transitive set correctly.
    elo = build_result(payload, "elo", DEFAULT_K)
    elo_order = [row["hypothesis_id"] for row in elo["final_ranking"]]
    assert elo_order == ["A", "B", "C"], f"Elo order wrong: {elo_order}"

    # 6) Weight multiplier is honored in the tally.
    weighted = {"candidates": ["P", "Q"], "matches": [{"a": "P", "b": "Q", "winner": "a", "weight": 3}]}
    bt5 = build_result(weighted, "bradley-terry", DEFAULT_K)
    assert bt5["matches_played"]["P"] == 3.0, bt5["matches_played"]

    print("bmat_elo self-test passed.")
    return 0


def main() -> int:
    args = parse_args()
    if args.selftest:
        return run_selftest()

    if args.matches:
        payload = json.loads(args.matches.read_text(encoding="utf-8"))
    else:
        payload = json.loads(sys.stdin.read())

    result = build_result(payload, args.method, args.k)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
