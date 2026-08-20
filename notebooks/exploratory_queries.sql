-- ========================================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM — EXPLORATORY SQL QUERIES
-- Deliverable: notebooks/exploratory_queries.sql
-- ========================================================================

-- Query 1: Sector Composition & Weight Distribution
SELECT 
    broad_sector,
    COUNT(company_id) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_weight_pct,
    ROUND(AVG(index_weight_pct), 2) AS avg_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY total_weight_pct DESC;

-- Query 2: Top 10 Companies by Latest Market Capitalization
SELECT 
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    mc.year,
    mc.market_cap_crore
FROM market_cap mc
JOIN companies c ON mc.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE mc.year = (SELECT MAX(year) FROM market_cap)
ORDER BY mc.market_cap_crore DESC
LIMIT 10;

-- Query 3: Top 10 by Net Profit (Latest FY: 2024-03)
SELECT 
    c.id AS ticker,
    c.company_name,
    p.year,
    p.sales,
    p.net_profit,
    p.opm_percentage
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
WHERE p.year = '2024-03'
ORDER BY p.net_profit DESC
LIMIT 10;

-- Query 4: Top 10 Lowest Positive P/E Multiples (Value Screen)
SELECT 
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    mc.pe_ratio,
    mc.pb_ratio,
    mc.dividend_yield_pct
FROM market_cap mc
JOIN companies c ON mc.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE mc.year = (SELECT MAX(year) FROM market_cap)
  AND mc.pe_ratio > 0
ORDER BY mc.pe_ratio ASC
LIMIT 10;

-- Query 5: Top 10 Operating Profit Margins (Non-Financials)
SELECT 
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    p.year,
    p.sales,
    p.operating_profit,
    p.opm_percentage
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE p.year = '2024-03'
  AND s.broad_sector != 'Financials'
  AND p.opm_percentage IS NOT NULL
  AND p.opm_percentage BETWEEN 0 AND 100
ORDER BY p.opm_percentage DESC
LIMIT 10;

-- Query 6: Top 10 Dividend Yield Leaders
SELECT 
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    mc.year,
    mc.dividend_yield_pct,
    mc.pe_ratio,
    mc.pb_ratio
FROM market_cap mc
JOIN companies c ON mc.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE mc.year = (SELECT MAX(year) FROM market_cap)
  AND mc.dividend_yield_pct IS NOT NULL
ORDER BY mc.dividend_yield_pct DESC
LIMIT 10;

-- Query 7: Top 10 Highest Debt-Holding Companies (Crores, Non-Financials)
SELECT 
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    b.year,
    b.borrowings,
    b.reserves,
    b.total_liabilities
FROM balancesheet b
JOIN companies c ON b.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE b.year = '2024-03'
  AND s.broad_sector != 'Financials'
ORDER BY b.borrowings DESC
LIMIT 10;

-- Query 8: Cash Flow Quality (CFO to Net Profit Conversion)
SELECT 
    p.company_id AS ticker,
    c.company_name,
    s.broad_sector,
    p.year,
    p.net_profit,
    cf.operating_activity AS operating_cash_flow,
    ROUND(cf.operating_activity / NULLIF(p.net_profit, 0), 2) AS cfo_to_pat_ratio
FROM profitandloss p
JOIN cashflow cf ON p.company_id = cf.company_id AND p.year = cf.year
JOIN companies c ON p.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE p.year = '2024-03'
  AND p.net_profit > 1000
ORDER BY cfo_to_pat_ratio DESC
LIMIT 10;

-- Query 9: 5-Year Price Volatility & High-Low Range
SELECT 
    sp.company_id AS ticker,
    c.company_name,
    s.broad_sector,
    ROUND(MIN(sp.low_price), 2) AS min_5yr_low,
    ROUND(MAX(sp.high_price), 2) AS max_5yr_high,
    ROUND((MAX(sp.high_price) - MIN(sp.low_price)) / MIN(sp.low_price) * 100, 2) AS price_range_pct
FROM stock_prices sp
JOIN companies c ON sp.company_id = c.id
JOIN sectors s ON c.id = s.company_id
GROUP BY sp.company_id
ORDER BY price_range_pct DESC
LIMIT 10;

-- Query 10: 3-Year Sales Compound Annual Growth Rate (FY21 to FY24)
WITH sales_fy21 AS (
    SELECT company_id, sales AS sales_2021
    FROM profitandloss
    WHERE year = '2021-03' AND sales > 0
),
sales_fy24 AS (
    SELECT company_id, sales AS sales_2024
    FROM profitandloss
    WHERE year = '2024-03' AND sales > 0
)
SELECT 
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    s21.sales_2021,
    s24.sales_2024,
    ROUND((POW(s24.sales_2024 / s21.sales_2021, 1.0 / 3.0) - 1.0) * 100, 2) AS sales_cagr_3yr_pct
FROM sales_fy21 s21
JOIN sales_fy24 s24 ON s21.company_id = s24.company_id
JOIN companies c ON s21.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE s.broad_sector != 'Financials'
ORDER BY sales_cagr_3yr_pct DESC
LIMIT 10;
