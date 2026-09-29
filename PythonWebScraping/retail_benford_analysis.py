"""Forensic Benford analysis of UCI Online Retail II transactions.

Benford's Law is used as a screening diagnostic, not proof of fraud. The
primary population is completed positive-value invoice totals; sales-line
amounts are a secondary population. All figures are rendered as PNG files so
the repository remains visual when viewed on GitHub.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "PythonOOP"))

from benford_analyzer import (  # noqa: E402
    applicability_metrics,
    benford_test,
    digit_table,
    expected_probabilities,
    first_digit,
    mad_threshold_label,
)

DATA_DIR = HERE / "data" / "raw"
OUT = HERE / "outputs"
FIG = OUT / "figures"
TAB = OUT / "tables"
PYTHON_BLUE = "#1f77b4"


def _find_data_file() -> Path:
    candidates = [
        DATA_DIR / "online_retail_II.xlsx",
        DATA_DIR / "online_retail_II.csv",
        DATA_DIR / "Online Retail II.xlsx",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"No Online Retail II file found in {DATA_DIR}. Run download_data.py or place the UCI file there."
    )


def load_retail() -> pd.DataFrame:
    path = _find_data_file()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, low_memory=False)
    else:
        sheets = pd.read_excel(path, sheet_name=None)
        frames = []
        for sheet_name, frame in sheets.items():
            frame = frame.copy()
            frame["SourceSheet"] = sheet_name
            frames.append(frame)
        df = pd.concat(frames, ignore_index=True)
    return df.rename(columns={"Invoice": "InvoiceNo", "Price": "UnitPrice", "Customer ID": "CustomerID"})


def prepare(df: pd.DataFrame):
    d = df.copy()
    d["InvoiceNo"] = d["InvoiceNo"].astype(str).str.strip()
    d["Quantity"] = pd.to_numeric(d["Quantity"], errors="coerce")
    d["UnitPrice"] = pd.to_numeric(d["UnitPrice"], errors="coerce")
    d["InvoiceDate"] = pd.to_datetime(d["InvoiceDate"], errors="coerce")
    d["is_cancellation"] = d["InvoiceNo"].str.upper().str.startswith("C")
    d["LineAmount"] = d["Quantity"] * d["UnitPrice"]

    quality = pd.DataFrame({
        "metric": ["raw_rows", "duplicate_rows", "missing_customer_id", "cancellation_rows",
                   "negative_quantity_rows", "zero_or_negative_price_rows", "missing_invoice_date_rows"],
        "value": [len(d), d.duplicated().sum(), d["CustomerID"].isna().sum(), d["is_cancellation"].sum(),
                  (d["Quantity"] < 0).sum(), (d["UnitPrice"] <= 0).sum(), d["InvoiceDate"].isna().sum()],
    })

    clean = d.loc[(~d["is_cancellation"]) & (d["Quantity"] > 0) & (d["UnitPrice"] > 0)
                  & d["InvoiceNo"].notna() & d["InvoiceDate"].notna()].copy()

    invoices = clean.groupby("InvoiceNo", as_index=False).agg(
        InvoiceTotal=("LineAmount", "sum"), InvoiceDate=("InvoiceDate", "min"),
        CustomerID=("CustomerID", "first"), Country=("Country", "first"), LineCount=("LineAmount", "size"),
    )
    invoices = invoices.loc[invoices["InvoiceTotal"] > 0].copy()
    return d, clean, invoices, quality


def save_benford_population(values: pd.Series, label: str) -> dict:
    results = {}
    for test in ("first_digit", "second_digit", "first_two_digits"):
        r = benford_test(values, test=test, simulations=2000, seed=42)
        results[test] = {**r.__dict__, "mad_interpretation": mad_threshold_label(test, r.mad)}
        digit_table(values, test).to_csv(TAB / f"{label}_{test}_detail.csv", index=False)
    return results


def _finish(fig, filename):
    fig.tight_layout()
    fig.savefig(FIG / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_first_digit(values, title, filename):
    tbl = digit_table(values, "first_digit")
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(tbl["digit"], tbl["observed_pct"] * 100, color=PYTHON_BLUE, alpha=.88, label="Observed")
    ax.plot(tbl["digit"], tbl["expected_pct"] * 100, color="black", marker="o", linewidth=1.8, label="Benford expected")
    ax.set(title=title, xlabel="First digit", ylabel="Frequency (%)")
    ax.set_xticks(range(1, 10)); ax.grid(axis="y", alpha=.2); ax.legend(frameon=False)
    _finish(fig, filename)


def plot_deviation(values, filename):
    tbl = digit_table(values, "first_digit")
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(tbl["digit"], tbl["difference_pp"], color=PYTHON_BLUE, alpha=.88)
    ax.axhline(0, color="black", linewidth=1)
    ax.set(title="Invoice-total deviation from Benford expectation", xlabel="First digit",
           ylabel="Observed - expected (percentage points)")
    ax.set_xticks(range(1, 10)); ax.grid(axis="y", alpha=.2)
    _finish(fig, filename)


def plot_first_two_digits(values, filename):
    tbl = digit_table(values, "first_two_digits")
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.bar(tbl["digit"].astype(str), tbl["observed_pct"] * 100, color=PYTHON_BLUE, alpha=.85, label="Observed")
    ax.plot(range(len(tbl)), tbl["expected_pct"] * 100, color="black", linewidth=1.5, label="Benford expected")
    ax.set(title="First-two-digit Benford profile — invoice totals", xlabel="First two digits", ylabel="Frequency (%)")
    ax.set_xticks(range(0, len(tbl), 5)); ax.set_xticklabels(tbl["digit"].astype(str).iloc[::5], rotation=0)
    ax.grid(axis="y", alpha=.2); ax.legend(frameon=False)
    _finish(fig, filename)


def plot_invoice_distribution(invoices, filename):
    x = invoices["InvoiceTotal"].clip(lower=.01)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.hist(np.log10(x), bins=50, color=PYTHON_BLUE, alpha=.88)
    ax.set(title="Distribution of completed invoice totals", xlabel="log10(invoice total, GBP)", ylabel="Invoices")
    ax.grid(axis="y", alpha=.2)
    _finish(fig, filename)


def plot_monthly_sales(invoices, filename):
    m = invoices.set_index("InvoiceDate")["InvoiceTotal"].resample("ME").sum()
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(m.index, m.values, color=PYTHON_BLUE, linewidth=2)
    ax.set(title="Monthly completed sales value", xlabel="Month", ylabel="Sales value (GBP)")
    ax.grid(alpha=.2)
    _finish(fig, filename)


def plot_country_sales(invoices, filename):
    c = invoices.groupby("Country")["InvoiceTotal"].sum().sort_values(ascending=False).head(10).sort_values()
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.barh(c.index.astype(str), c.values, color=PYTHON_BLUE, alpha=.88)
    ax.set(title="Top countries by completed invoice value", xlabel="Sales value (GBP)", ylabel="Country")
    ax.grid(axis="x", alpha=.2)
    _finish(fig, filename)


def plot_cancellation_rate(raw, filename):
    t = raw.dropna(subset=["InvoiceDate"]).copy()
    t["Year"] = t["InvoiceDate"].dt.year
    g = t.groupby("Year").agg(rows=("InvoiceNo", "size"), cancelled=("is_cancellation", "sum"))
    g["rate"] = 100 * g["cancelled"] / g["rows"]
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.bar(g.index.astype(str), g["rate"], color=PYTHON_BLUE, alpha=.88)
    ax.set(title="Cancellation rate by year", xlabel="Year", ylabel="Cancellation rate (%)")
    ax.grid(axis="y", alpha=.2)
    _finish(fig, filename)


def anomaly_screen(invoices):
    digits, probs = expected_probabilities("first_digit")
    pmap = dict(zip(digits, probs))
    x = invoices.copy(); x["FirstDigit"] = first_digit(x["InvoiceTotal"])
    x["BenfordExpectedProbability"] = x["FirstDigit"].map(pmap)
    x["DigitRarityScore"] = -np.log10(x["BenfordExpectedProbability"])
    x["AmountPercentile"] = x["InvoiceTotal"].rank(pct=True)
    x["ScreeningScore"] = x["DigitRarityScore"] * x["AmountPercentile"]
    return x.sort_values("ScreeningScore", ascending=False)


def plot_screening(screen, filename):
    s = screen.head(40).sort_values("ScreeningScore")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(s["InvoiceNo"].astype(str), s["ScreeningScore"], color=PYTHON_BLUE, alpha=.88)
    ax.set(title="Top invoice screening scores", xlabel="Screening score", ylabel="Invoice")
    ax.tick_params(axis="y", labelsize=7); ax.grid(axis="x", alpha=.2)
    _finish(fig, filename)


def main():
    FIG.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)
    raw = load_retail(); raw, clean, invoices, quality = prepare(raw)
    quality.to_csv(TAB / "data_quality_report.csv", index=False)
    invoices.to_csv(TAB / "invoice_population.csv", index=False)
    summary = {
        "dataset": "UCI Online Retail II", "primary_population": "positive completed invoice totals",
        "raw_rows": int(len(raw)), "clean_sales_lines": int(len(clean)), "invoice_count": int(len(invoices)),
        "invoice_total_applicability": applicability_metrics(invoices["InvoiceTotal"]),
        "invoice_total_tests": save_benford_population(invoices["InvoiceTotal"], "invoice_total"),
        "line_amount_tests": save_benford_population(clean["LineAmount"], "line_amount"),
    }
    (TAB / "analysis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    screen = anomaly_screen(invoices); screen.head(500).to_csv(TAB / "invoice_screening_top500.csv", index=False)

    plot_first_digit(invoices["InvoiceTotal"], "Benford First-Digit Test — Completed Invoice Totals", "01_invoice_total_first_digit_benford.png")
    plot_deviation(invoices["InvoiceTotal"], "02_invoice_total_deviation.png")
    plot_first_digit(clean["LineAmount"], "Benford First-Digit Test — Positive Sales Line Amounts", "03_line_amount_first_digit_benford.png")
    plot_first_two_digits(invoices["InvoiceTotal"], "04_invoice_first_two_digits.png")
    plot_invoice_distribution(invoices, "05_invoice_value_distribution.png")
    plot_monthly_sales(invoices, "06_monthly_sales_trend.png")
    plot_country_sales(invoices, "07_country_sales_profile.png")
    plot_cancellation_rate(raw, "08_cancellation_rate.png")
    plot_screening(screen, "09_invoice_screening_scores.png")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
