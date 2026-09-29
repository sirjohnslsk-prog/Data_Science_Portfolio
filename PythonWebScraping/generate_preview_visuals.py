"""Generate deterministic preview figures for repository presentation.

These previews use a synthetic retail population only so the repository is
visually complete before the large UCI workbook is downloaded. Running
retail_benford_analysis.py on the official UCI data writes the production
figures to outputs/figures/ using the same visual design.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "figures"
PREVIEW = HERE / "data" / "preview"
BLUE = "#1f77b4"
RNG = np.random.default_rng(42)
OUT.mkdir(parents=True, exist_ok=True)
PREVIEW.mkdir(parents=True, exist_ok=True)

# Synthetic but realistic transaction-like invoice population for previews.
# Log-uniform values are naturally Benford-compatible; small digit-specific
# perturbations create visible forensic deviations without pretending to be
# findings from the UCI dataset.
n = 30000
logv = RNG.uniform(np.log10(4.5), np.log10(75000), n)
amount = 10 ** logv
first = np.floor(amount / (10 ** np.floor(np.log10(amount)))).astype(int)
amount[first == 9] *= 1.06
amount[first == 4] *= 0.96

dates = pd.Timestamp("2009-12-01") + pd.to_timedelta(RNG.integers(0, 739, n), unit="D")
countries = RNG.choice(
    ["United Kingdom", "Germany", "France", "EIRE", "Netherlands", "Spain", "Belgium", "Switzerland", "Portugal", "Australia"],
    n,
    p=[.73,.055,.05,.035,.025,.025,.02,.018,.017,.025]
)
invoice = pd.DataFrame({"InvoiceNo":[f"P{i+1:06d}" for i in range(n)], "InvoiceDate":dates,
                        "Country":countries, "InvoiceTotal":amount})
invoice.to_csv(PREVIEW / "synthetic_preview_invoice_population.csv", index=False)

benford = np.log10(1 + 1/np.arange(1,10))
fd = np.array([int(str(f"{x:.12g}").lstrip("0.")[0]) for x in amount])
obs = np.array([(fd==d).mean() for d in range(1,10)])

# 1 First digit
fig, ax = plt.subplots(figsize=(9,5.2)); x=np.arange(1,10)
ax.bar(x, obs*100, color=BLUE, alpha=.88, label="Observed preview")
ax.plot(x, benford*100, color="black", marker="o", linewidth=1.8, label="Benford expected")
ax.set(title="Benford First-Digit Test — Invoice Totals (Preview)", xlabel="First digit", ylabel="Frequency (%)")
ax.set_xticks(x); ax.grid(axis="y", alpha=.2); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT/"preview_01_first_digit_benford.png", dpi=180); plt.close(fig)

# 2 deviation
fig, ax = plt.subplots(figsize=(9,5.2)); dev=(obs-benford)*100
ax.bar(x,dev,color=BLUE,alpha=.88); ax.axhline(0,color="black",linewidth=1)
ax.set(title="First-Digit Deviation from Benford (Preview)",xlabel="First digit",ylabel="Observed - expected (pp)")
ax.set_xticks(x); ax.grid(axis="y",alpha=.2); fig.tight_layout(); fig.savefig(OUT/"preview_02_deviation.png",dpi=180); plt.close(fig)

# 3 second digit
s = [str(f"{v:.12g}").replace(".","").lstrip("0") for v in amount]
sd = np.array([int(z[1]) if len(z)>1 else 0 for z in s])
sec_expected=np.array([sum(np.log10(1+1/(10*k+d)) for k in range(1,10)) for d in range(10)])
sec_obs=np.array([(sd==d).mean() for d in range(10)])
fig,ax=plt.subplots(figsize=(9,5.2)); xx=np.arange(10)
ax.bar(xx,sec_obs*100,color=BLUE,alpha=.88,label="Observed preview"); ax.plot(xx,sec_expected*100,color="black",marker="o",linewidth=1.6,label="Benford expected")
ax.set(title="Benford Second-Digit Test (Preview)",xlabel="Second digit",ylabel="Frequency (%)"); ax.set_xticks(xx); ax.grid(axis="y",alpha=.2); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT/"preview_03_second_digit.png",dpi=180); plt.close(fig)

# 4 first two digit
mant=amount/(10**np.floor(np.log10(amount))); f2=np.floor(mant*10).astype(int)
digs=np.arange(10,100); exp2=np.log10(1+1/digs); obs2=np.array([(f2==d).mean() for d in digs])
fig,ax=plt.subplots(figsize=(12,5.2)); ax.bar(digs,obs2*100,color=BLUE,alpha=.82,label="Observed preview"); ax.plot(digs,exp2*100,color="black",linewidth=1.4,label="Benford expected")
ax.set(title="First-Two-Digit Benford Profile (Preview)",xlabel="First two digits",ylabel="Frequency (%)"); ax.set_xticks(np.arange(10,100,5)); ax.grid(axis="y",alpha=.2); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT/"preview_04_first_two_digits.png",dpi=180); plt.close(fig)

# 5 amount distribution
fig,ax=plt.subplots(figsize=(9,5.2)); ax.hist(np.log10(amount),bins=50,color=BLUE,alpha=.88)
ax.set(title="Distribution of Invoice Totals (Preview)",xlabel="log10(invoice total, GBP)",ylabel="Invoices"); ax.grid(axis="y",alpha=.2); fig.tight_layout(); fig.savefig(OUT/"preview_05_invoice_distribution.png",dpi=180); plt.close(fig)

# 6 monthly trend with plausible seasonality
monthly=invoice.set_index("InvoiceDate")["InvoiceTotal"].resample("ME").sum(); seasonal=1+0.18*np.sin(np.arange(len(monthly))*2*np.pi/12); monthly=monthly*seasonal
fig,ax=plt.subplots(figsize=(11,5.2)); ax.plot(monthly.index,monthly.values,color=BLUE,linewidth=2)
ax.set(title="Monthly Completed Sales Value (Preview)",xlabel="Month",ylabel="Sales value (GBP)"); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(OUT/"preview_06_monthly_sales.png",dpi=180); plt.close(fig)

# 7 country profile
country=invoice.groupby("Country")["InvoiceTotal"].sum().sort_values().tail(10)
fig,ax=plt.subplots(figsize=(9,5.6)); ax.barh(country.index,country.values,color=BLUE,alpha=.88)
ax.set(title="Top Countries by Invoice Value (Preview)",xlabel="Sales value (GBP)",ylabel="Country"); ax.grid(axis="x",alpha=.2); fig.tight_layout(); fig.savefig(OUT/"preview_07_country_sales.png",dpi=180); plt.close(fig)

# 8 data quality profile illustrative counts
labels=["Completed","Cancellations","Returns","Zero price","Missing ID"]; vals=[88.4,3.0,2.2,.7,5.7]
fig,ax=plt.subplots(figsize=(9,5.2)); ax.bar(labels,vals,color=BLUE,alpha=.88); ax.set(title="Transaction Quality Profile (Preview)",ylabel="Share of rows (%)"); ax.tick_params(axis="x",rotation=20); ax.grid(axis="y",alpha=.2); fig.tight_layout(); fig.savefig(OUT/"preview_08_quality_profile.png",dpi=180); plt.close(fig)

# 9 screening scatter
rarity=-np.log10(np.array([benford[d-1] for d in fd])); pct=pd.Series(amount).rank(pct=True).to_numpy(); score=rarity*pct
idx=np.argsort(score)[-800:]
fig,ax=plt.subplots(figsize=(9,5.5)); ax.scatter(amount[idx],score[idx],s=14,alpha=.55,color=BLUE); ax.set_xscale("log")
ax.set(title="Forensic Screening: Materiality vs Digit Rarity (Preview)",xlabel="Invoice total (GBP, log scale)",ylabel="Screening score"); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(OUT/"preview_09_screening_scatter.png",dpi=180); plt.close(fig)

print(f"Generated {len(list(OUT.glob('preview_*.png')))} preview figures in {OUT}")
