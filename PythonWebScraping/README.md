# PythonWebScraping — Retail Forensic Analysis

This section contains the reproducible UCI Online Retail II workflow and the project's visual evidence.

## Files

- `download_data.py` — downloads the official UCI workbook.
- `retail_benford_analysis.py` — cleans transactions, constructs invoice totals, executes forensic statistical tests and generates production charts.
- `generate_preview_visuals.py` — creates the deterministic **preview-only** gallery committed to GitHub.
- `Forensic_Benford_Retail_Analysis.ipynb` — notebook interface for reproducing and presenting the investigation.
- `visualizations/` — committed PNG gallery visible immediately on GitHub.
- `outputs/figures/` — production figures generated from the full UCI dataset.
- `outputs/tables/` — detailed statistical and anomaly-screening tables.

## Production visualizations generated from UCI data

Running `python retail_benford_analysis.py` creates:

1. Invoice-total first-digit observed vs expected Benford profile
2. First-digit percentage-point deviation chart
3. Positive line-amount first-digit profile
4. Invoice-total first-two-digit profile
5. Log-scale invoice-value distribution
6. Monthly completed-sales trend
7. Top-country sales profile
8. Cancellation-rate diagnostic
9. Invoice screening-score ranking

All visualizations use Matplotlib's standard Python blue (`#1f77b4`).

## Preview gallery

The committed preview gallery is deliberately labeled *Preview*: it demonstrates the finished visual design without claiming synthetic values are UCI findings. The full-data script replaces that presentation layer with results calculated from the official dataset.
