# SQL — Retail Forensic Benford Analysis

SQL companion to the UCI Online Retail II investigation. The queries assume the raw retail transaction data has been loaded into a table named `online_retail` with fields such as `invoice_no`, `quantity`, `unit_price`, `invoice_date`, `customer_id`, and `country`.

The SQL constructs positive completed invoice totals, extracts leading digits, compares empirical first-digit frequencies with Benford expectations, and surfaces high-value invoices for follow-up. It is intended to demonstrate how the same forensic logic can be moved from pandas into a relational analytical workflow.
