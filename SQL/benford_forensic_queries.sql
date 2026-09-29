-- UCI Online Retail II: forensic Benford analysis in PostgreSQL-style SQL.
-- Benford deviations are screening signals, not conclusions of fraud.

WITH clean_lines AS (
    SELECT
        CAST(invoice_no AS text) AS invoice_no,
        invoice_date,
        customer_id,
        country,
        quantity,
        unit_price,
        quantity * unit_price AS line_amount
    FROM online_retail
    WHERE UPPER(CAST(invoice_no AS text)) NOT LIKE 'C%'
      AND quantity > 0
      AND unit_price > 0
),
invoice_totals AS (
    SELECT
        invoice_no,
        MIN(invoice_date) AS invoice_date,
        MAX(customer_id) AS customer_id,
        MAX(country) AS country,
        SUM(line_amount) AS invoice_total
    FROM clean_lines
    GROUP BY invoice_no
),
first_digits AS (
    SELECT
        *,
        FLOOR(invoice_total / POWER(10, FLOOR(LOG(10, invoice_total))))::int AS first_digit
    FROM invoice_totals
    WHERE invoice_total > 0
),
observed AS (
    SELECT first_digit, COUNT(*) AS n
    FROM first_digits
    GROUP BY first_digit
),
total AS (
    SELECT SUM(n)::numeric AS n_total FROM observed
),
benford AS (
    SELECT d AS first_digit, LOG(10, 1 + 1.0 / d) AS expected_prop
    FROM generate_series(1, 9) AS d
)
SELECT
    b.first_digit,
    COALESCE(o.n, 0) AS observed_count,
    COALESCE(o.n, 0) / t.n_total AS observed_prop,
    b.expected_prop,
    (COALESCE(o.n, 0) / t.n_total) - b.expected_prop AS deviation
FROM benford b
LEFT JOIN observed o USING (first_digit)
CROSS JOIN total t
ORDER BY b.first_digit;

-- High-value invoices for contextual review; not an accusation of wrongdoing.
SELECT invoice_no, invoice_date, customer_id, country, invoice_total
FROM (
    SELECT
        CAST(invoice_no AS text) AS invoice_no,
        MIN(invoice_date) AS invoice_date,
        MAX(customer_id) AS customer_id,
        MAX(country) AS country,
        SUM(quantity * unit_price) AS invoice_total
    FROM online_retail
    WHERE UPPER(CAST(invoice_no AS text)) NOT LIKE 'C%'
      AND quantity > 0
      AND unit_price > 0
    GROUP BY invoice_no
) x
ORDER BY invoice_total DESC
LIMIT 100;
