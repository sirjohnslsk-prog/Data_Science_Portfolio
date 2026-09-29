"""Core Benford-law and forensic statistical utilities.

Benford tests are screening procedures, not proof of fraud. The functions in
this module separate digit extraction, expected distributions, goodness-of-fit
statistics, and bootstrap uncertainty so the analysis is auditable and reusable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class BenfordResult:
    test: str
    n: int
    chi_square: float
    chi_square_p: float
    mad: float
    ks_distance: float
    monte_carlo_p: float


def _positive_finite(values: Iterable[float]) -> np.ndarray:
    arr = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=float)
    arr = np.abs(arr[np.isfinite(arr)])
    return arr[arr > 0]


def first_digit(values: Iterable[float]) -> np.ndarray:
    x = _positive_finite(values)
    if x.size == 0:
        return np.array([], dtype=int)
    scaled = x / np.power(10.0, np.floor(np.log10(x)))
    return np.floor(scaled + 1e-12).astype(int)


def first_two_digits(values: Iterable[float]) -> np.ndarray:
    x = _positive_finite(values)
    if x.size == 0:
        return np.array([], dtype=int)
    scaled = x / np.power(10.0, np.floor(np.log10(x)))
    return np.floor(scaled * 10 + 1e-10).astype(int)


def second_digit(values: Iterable[float]) -> np.ndarray:
    ft = first_two_digits(values)
    return ft % 10


def expected_probabilities(test: str) -> tuple[np.ndarray, np.ndarray]:
    if test == "first_digit":
        digits = np.arange(1, 10)
        probs = np.log10(1 + 1 / digits)
    elif test == "second_digit":
        digits = np.arange(0, 10)
        probs = np.array([
            sum(np.log10(1 + 1 / (10 * d + k)) for d in range(1, 10))
            for k in digits
        ])
    elif test == "first_two_digits":
        digits = np.arange(10, 100)
        probs = np.log10(1 + 1 / digits)
    else:
        raise ValueError(f"Unsupported test: {test}")
    return digits, probs / probs.sum()


def observed_counts(values: Iterable[float], test: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    digits, probs = expected_probabilities(test)
    if test == "first_digit":
        extracted = first_digit(values)
    elif test == "second_digit":
        extracted = second_digit(values)
    else:
        extracted = first_two_digits(values)
    counts = pd.Series(extracted).value_counts().reindex(digits, fill_value=0).to_numpy(dtype=int)
    return digits, counts, probs


def mad_threshold_label(test: str, mad: float) -> str:
    # Common Nigrini-style interpretive bands; these are heuristics, not formal tests.
    bands = {
        "first_digit": (0.006, 0.012, 0.015),
        "second_digit": (0.008, 0.010, 0.012),
        "first_two_digits": (0.0012, 0.0018, 0.0022),
    }
    a, b, c = bands[test]
    if mad <= a:
        return "close conformity"
    if mad <= b:
        return "acceptable conformity"
    if mad <= c:
        return "marginal conformity"
    return "nonconformity"


def benford_test(values: Iterable[float], test: str = "first_digit", simulations: int = 2000, seed: int = 42) -> BenfordResult:
    digits, counts, probs = observed_counts(values, test)
    n = int(counts.sum())
    if n == 0:
        return BenfordResult(test, 0, np.nan, np.nan, np.nan, np.nan, np.nan)

    obs = counts / n
    exp_counts = probs * n
    chi = float(((counts - exp_counts) ** 2 / exp_counts).sum())
    chi_p = float(stats.chi2.sf(chi, df=len(digits) - 1))
    mad = float(np.mean(np.abs(obs - probs)))
    ks = float(np.max(np.abs(np.cumsum(obs) - np.cumsum(probs))))

    rng = np.random.default_rng(seed)
    sims = rng.multinomial(n, probs, size=simulations)
    sim_chi = ((sims - exp_counts) ** 2 / exp_counts).sum(axis=1)
    mc_p = float((np.count_nonzero(sim_chi >= chi) + 1) / (simulations + 1))
    return BenfordResult(test, n, chi, chi_p, mad, ks, mc_p)


def digit_table(values: Iterable[float], test: str) -> pd.DataFrame:
    digits, counts, probs = observed_counts(values, test)
    n = counts.sum()
    observed = counts / n if n else np.zeros_like(probs)
    z = np.divide(observed - probs, np.sqrt(probs * (1 - probs) / max(n, 1)), out=np.zeros_like(probs), where=probs > 0)
    p = 2 * stats.norm.sf(np.abs(z))
    # Benjamini-Hochberg FDR adjustment.
    order = np.argsort(p)
    ranked = p[order]
    adj_ranked = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    adj = np.empty_like(adj_ranked)
    adj[order] = np.minimum(adj_ranked, 1.0)
    return pd.DataFrame({
        "digit": digits,
        "count": counts,
        "observed_pct": observed,
        "expected_pct": probs,
        "difference_pp": (observed - probs) * 100,
        "z_score": z,
        "p_value": p,
        "fdr_p_value": adj,
    })


def applicability_metrics(values: Iterable[float]) -> dict[str, float]:
    x = _positive_finite(values)
    if x.size == 0:
        return {"n_positive": 0, "min": np.nan, "max": np.nan, "orders_of_magnitude": np.nan, "unique_values": 0}
    return {
        "n_positive": int(x.size),
        "min": float(x.min()),
        "max": float(x.max()),
        "orders_of_magnitude": float(np.log10(x.max() / x.min())) if x.min() > 0 else np.nan,
        "unique_values": int(np.unique(x).size),
    }
