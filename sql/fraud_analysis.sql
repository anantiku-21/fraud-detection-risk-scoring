-- Q1. Portfolio overview: volume, fraud count, fraud rate and value lost
SELECT
    COUNT(*)                                                   AS total_transactions,
    SUM(isFraud)                                               AS fraud_transactions,
    ROUND(100.0 * AVG(isFraud), 2)                             AS fraud_rate_pct,
    ROUND(SUM(TransactionAmt), 0)                              AS total_amount,
    ROUND(SUM(CASE WHEN isFraud = 1 THEN TransactionAmt END), 0) AS fraud_amount,
    ROUND(100.0 * SUM(CASE WHEN isFraud = 1 THEN TransactionAmt END) / SUM(TransactionAmt), 2) AS fraud_value_pct
FROM transactions;


-- Q2. Fraud rate by product segment, ranked
SELECT
    ProductCD,
    COUNT(*)                        AS transactions,
    SUM(isFraud)                    AS fraud_transactions,
    ROUND(100.0 * AVG(isFraud), 2)  AS fraud_rate_pct,
    RANK() OVER (ORDER BY AVG(isFraud) DESC) AS risk_rank
FROM transactions
GROUP BY ProductCD
ORDER BY risk_rank;


-- Q3. Alternate data: fraud rate by email provider and device type (segments with at least 500 transactions)
SELECT
    email_group,
    DeviceType,
    COUNT(*)                        AS transactions,
    ROUND(100.0 * AVG(isFraud), 2)  AS fraud_rate_pct
FROM transactions
GROUP BY email_group, DeviceType
HAVING COUNT(*) >= 500
ORDER BY fraud_rate_pct DESC;


-- Q4. Fraud rate by amount band
SELECT
    CASE
        WHEN TransactionAmt < 25   THEN '1. under 25'
        WHEN TransactionAmt < 100  THEN '2. 25-100'
        WHEN TransactionAmt < 500  THEN '3. 100-500'
        WHEN TransactionAmt < 1000 THEN '4. 500-1000'
        ELSE '5. 1000+'
    END                             AS amount_band,
    COUNT(*)                        AS transactions,
    ROUND(100.0 * AVG(isFraud), 2)  AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN isFraud = 1 THEN TransactionAmt ELSE 0 END), 0) AS fraud_amount
FROM transactions
GROUP BY amount_band
ORDER BY amount_band;


-- Q5. Weekly fraud trend with week-on-week change
WITH weekly AS (
    SELECT
        day / 7                         AS week,
        COUNT(*)                        AS transactions,
        ROUND(100.0 * AVG(isFraud), 2)  AS fraud_rate_pct
    FROM transactions
    GROUP BY day / 7
)
SELECT
    week,
    transactions,
    fraud_rate_pct,
    ROUND(fraud_rate_pct - LAG(fraud_rate_pct) OVER (ORDER BY week), 2) AS change_vs_last_week
FROM weekly
ORDER BY week;


-- Q6. Customers with unusually many transactions in a single day
WITH daily_activity AS (
    SELECT uid, day, COUNT(*) AS txns_that_day, SUM(isFraud) AS fraud_that_day
    FROM transactions
    GROUP BY uid, day
)
SELECT uid, day, txns_that_day, fraud_that_day
FROM daily_activity
WHERE txns_that_day >= 10
ORDER BY txns_that_day DESC
LIMIT 20;


-- Q7. Does fraud repeat on the same customer? Customers grouped by number of fraud cases
WITH customer_summary AS (
    SELECT uid, COUNT(*) AS transactions, SUM(isFraud) AS fraud_cases
    FROM transactions
    GROUP BY uid
)
SELECT
    CASE
        WHEN fraud_cases = 0 THEN '0 fraud'
        WHEN fraud_cases = 1 THEN '1 fraud'
        WHEN fraud_cases <= 5 THEN '2-5 fraud'
        ELSE '6+ fraud'
    END                         AS customer_group,
    COUNT(*)                    AS customers,
    SUM(transactions)           AS transactions,
    SUM(fraud_cases)            AS fraud_cases
FROM customer_summary
GROUP BY customer_group
ORDER BY MIN(fraud_cases);


-- Q8. High-value suspicious transactions: more than 5x the customer's average of EARLIER transactions
WITH with_history AS (
    SELECT
        TransactionID, uid, TransactionDT, TransactionAmt, isFraud,
        AVG(TransactionAmt) OVER (
            PARTITION BY uid ORDER BY TransactionDT
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS avg_prior_amt
    FROM transactions
)
SELECT
    COUNT(*)                        AS flagged_transactions,
    SUM(isFraud)                    AS fraud_among_flagged,
    ROUND(100.0 * AVG(isFraud), 2)  AS fraud_rate_pct
FROM with_history
WHERE avg_prior_amt IS NOT NULL
  AND TransactionAmt > 5 * avg_prior_amt;


-- Q9. Test period: risk tier summary joined with actual outcomes
SELECT
    r.risk_tier,
    COUNT(*)                                AS transactions,
    SUM(t.isFraud)                          AS actual_fraud,
    ROUND(100.0 * AVG(t.isFraud), 2)        AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN t.isFraud = 1 THEN t.TransactionAmt ELSE 0 END), 0) AS fraud_amount,
    ROUND(100.0 * SUM(t.isFraud) / SUM(SUM(t.isFraud)) OVER (), 1)       AS share_of_all_fraud_pct
FROM risk_scores r
JOIN transactions t ON t.TransactionID = r.TransactionID
GROUP BY r.risk_tier
ORDER BY MIN(r.risk_score) DESC;


-- Q10. Alert queue: the 20 highest-risk test transactions
SELECT
    r.TransactionID, t.TransactionAmt, t.ProductCD, t.email_group, t.DeviceType,
    r.risk_score, r.risk_tier, t.isFraud AS actual_fraud
FROM risk_scores r
JOIN transactions t ON t.TransactionID = r.TransactionID
ORDER BY r.risk_score DESC
LIMIT 20;
