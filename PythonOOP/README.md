# PythonOOP — Reusable Benford Forensic Engine

This module contains the reusable statistical core used by the retail transaction investigation. `benford_analyzer.py` implements digit extraction and Benford expected distributions together with Pearson chi-square tests, Monte Carlo p-values, MAD, cumulative-distance diagnostics, per-digit z statistics, FDR adjustment, and basic applicability metrics.

The code is intentionally dataset-agnostic so the same forensic methods can be applied to invoice totals, expense claims, payment values, procurement transactions, or other appropriate naturally occurring monetary populations.

Run automated validation from this directory with:

```bash
python -m pytest tests -q
```

Benford tests are screening procedures and do not, by themselves, establish fraud.
