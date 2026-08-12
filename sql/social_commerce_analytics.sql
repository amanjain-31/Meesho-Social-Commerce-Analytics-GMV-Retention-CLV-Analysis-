/* ===============================================================================
   MEESHO SOCIAL COMMERCE ANALYTICS & CUSTOMER INTELLIGENCE SUITE
   Author: Aman Jain (amanjain-31)
   Repository: https://github.com/amanjain-31/Meesho-Social-Commerce-Analytics-GMV-Retention-CLV-Analysis-
   =============================================================================== */

-- -------------------------------------------------------------------------------
-- SECTION 1: EXECUTIVE REVENUE & FINANCIAL METRICS
-- -------------------------------------------------------------------------------

-- 1.1 Gross Merchandise Value (GMV) of Delivered Orders
SELECT 
    CAST(ROUND(SUM(total_amount), 2) AS DECIMAL(12, 2)) AS gross_merchandise_value_gmv
FROM orders
WHERE order_status = 'Delivered';

-- 1.2 Average Order Value (AOV) for Successful Transactions
SELECT 
    CAST(ROUND(AVG(total_amount), 2) AS DECIMAL(10, 2)) AS average_order_value_aov
FROM orders
WHERE order_status = 'Delivered';

-- 1.3 Monthly GMV Growth Trend & Month-over-Month (MoM) % Change
WITH MonthlyRevenue AS (
    SELECT 
        FORMAT(order_date, 'yyyy-MM') AS order_month,
        SUM(total_amount) AS monthly_gmv,
        COUNT(order_id) AS order_volume
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY FORMAT(order_date, 'yyyy-MM')
)
SELECT 
    order_month,
    CAST(ROUND(monthly_gmv, 2) AS DECIMAL(12, 2)) AS current_month_gmv,
    order_volume,
    LAG(monthly_gmv) OVER (ORDER BY order_month) AS prior_month_gmv,
    CAST(ROUND(
        100.0 * (monthly_gmv - LAG(monthly_gmv) OVER (ORDER BY order_month)) / 
        NULLIF(LAG(monthly_gmv) OVER (ORDER BY order_month), 0), 2
    ) AS DECIMAL(10, 2)) AS mom_growth_percentage
FROM MonthlyRevenue
ORDER BY order_month ASC;


-- -------------------------------------------------------------------------------
-- SECTION 2: CUSTOMER LIFETIME VALUE (CLV) & RFM SEGMENTATION
-- -------------------------------------------------------------------------------

-- 2.1 Repeat Customer Penetration Rate
WITH CustomerPurchaseCounts AS (
    SELECT 
        customer_id,
        COUNT(order_id) AS delivered_orders_count
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
)
SELECT 
    COUNT(customer_id) AS total_active_customers,
    SUM(CASE WHEN delivered_orders_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    CAST(ROUND(
        100.0 * SUM(CASE WHEN delivered_orders_count > 1 THEN 1 ELSE 0 END) / COUNT(customer_id), 2
    ) AS DECIMAL(10, 2)) AS repeat_customer_rate_percentage
FROM CustomerPurchaseCounts;

-- 2.2 Customer RFM (Recency, Frequency, Monetary) Value Matrix
WITH RawRFM AS (
    SELECT 
        o.customer_id,
        DATEDIFF(day, MAX(o.order_date), GETDATE()) AS recency_days,
        COUNT(o.order_id) AS frequency_orders,
        SUM(o.total_amount) AS monetary_spend
    FROM orders o
    WHERE o.order_status = 'Delivered'
    GROUP BY o.customer_id
),
RFMScores AS (
    SELECT 
        customer_id,
        recency_days,
        frequency_orders,
        monetary_spend,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency_orders ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary_spend ASC) AS m_score
    FROM RawRFM
)
SELECT 
    customer_id,
    recency_days,
    frequency_orders,
    CAST(ROUND(monetary_spend, 2) AS DECIMAL(10, 2)) AS total_monetary_spend,
    CONCAT(r_score, f_score, m_score) AS rfm_combined_code,
    CASE 
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal Customers'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At-Risk High-Value'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating / Churned'
        ELSE 'Promising'
    END AS customer_segment
FROM RFMScores
ORDER BY monetary_spend DESC;


-- -------------------------------------------------------------------------------
-- SECTION 3: COHORT RETENTION & CHURN ANALYSIS
-- -------------------------------------------------------------------------------

-- 3.1 Customer First Purchase Cohort Retention Base
WITH FirstPurchaseCohort AS (
    SELECT 
        customer_id,
        MIN(FORMAT(order_date, 'yyyy-MM')) AS cohort_month
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
),
CustomerActivity AS (
    SELECT 
        o.customer_id,
        fpc.cohort_month,
        FORMAT(o.order_date, 'yyyy-MM') AS activity_month,
        DATEDIFF(month, CAST(fpc.cohort_month + '-01' AS DATE), CAST(FORMAT(o.order_date, 'yyyy-MM') + '-01' AS DATE)) AS period_number
    FROM orders o
    JOIN FirstPurchaseCohort fpc ON o.customer_id = fpc.customer_id
    WHERE o.order_status = 'Delivered'
)
SELECT 
    cohort_month,
    period_number,
    COUNT(DISTINCT customer_id) AS active_retained_customers
FROM CustomerActivity
GROUP BY cohort_month, period_number
ORDER BY cohort_month ASC, period_number ASC;


-- -------------------------------------------------------------------------------
-- SECTION 4: PRODUCT CATEGORY & BASKET PERFORMANCE
-- -------------------------------------------------------------------------------

-- 4.1 Top Product Categories by Delivered Revenue & Volume
SELECT 
    p.category,
    COUNT(DISTINCT oi.order_id) AS total_orders_containing_category,
    SUM(oi.quantity) AS total_units_sold,
    CAST(ROUND(SUM(oi.quantity * oi.price_sold), 2) AS DECIMAL(12, 2)) AS category_total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Delivered'
GROUP BY p.category
ORDER BY category_total_revenue DESC;

-- 4.2 Cross-Selling Product Pair Analysis (Market Basket)
SELECT TOP 10
    p1.product_name AS product_a,
    p2.product_name AS product_b,
    COUNT(*) AS co_purchase_frequency
FROM order_items oi1
JOIN order_items oi2 ON oi1.order_id = oi2.order_id AND oi1.product_id < oi2.product_id
JOIN products p1 ON oi1.product_id = p1.product_id
JOIN products p2 ON oi2.product_id = p2.product_id
GROUP BY p1.product_name, p2.product_name
ORDER BY co_purchase_frequency DESC;


-- -------------------------------------------------------------------------------
-- SECTION 5: OPERATIONAL FRICTION ANALYSIS (RETURNS & COD)
-- -------------------------------------------------------------------------------

-- 5.1 Payment Method Share & Cash-on-Delivery (COD) Dependency
SELECT 
    payment_method,
    COUNT(order_id) AS order_count,
    CAST(ROUND(100.0 * COUNT(order_id) / (SELECT COUNT(*) FROM orders), 2) AS DECIMAL(5, 2)) AS payment_share_percentage
FROM orders
GROUP BY payment_method
ORDER BY order_count DESC;

-- 5.2 Order Fulfillment Breakdown (Delivered vs Returned vs Cancelled)
SELECT 
    order_status,
    COUNT(order_id) AS total_orders,
    CAST(ROUND(100.0 * COUNT(order_id) / (SELECT COUNT(*) FROM orders), 2) AS DECIMAL(5, 2)) AS status_percentage
FROM orders
GROUP BY order_status;


-- -------------------------------------------------------------------------------
-- SECTION 6: SUPPLIER QUALITY & RETURN RISK SCORING
-- -------------------------------------------------------------------------------

-- 6.1 Supplier Return Rate & Vendor Risk Assessment
WITH SupplierOrderStats AS (
    SELECT 
        p.supplier_id,
        COUNT(DISTINCT o.order_id) AS total_vendor_orders,
        SUM(CASE WHEN o.order_status = 'Returned' THEN 1 ELSE 0 END) AS returned_vendor_orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.supplier_id
)
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.supplier_tier,
    s.avg_rating,
    sos.total_vendor_orders,
    sos.returned_vendor_orders,
    CAST(ROUND(100.0 * sos.returned_vendor_orders / NULLIF(sos.total_vendor_orders, 0), 2) AS DECIMAL(5, 2)) AS vendor_return_rate_percentage,
    CASE 
        WHEN (100.0 * sos.returned_vendor_orders / NULLIF(sos.total_vendor_orders, 0)) > 15.0 THEN 'High Return Risk'
        WHEN (100.0 * sos.returned_vendor_orders / NULLIF(sos.total_vendor_orders, 0)) BETWEEN 8.0 AND 15.0 THEN 'Moderate Risk'
        ELSE 'Optimal Quality'
    END AS vendor_risk_score
FROM SupplierOrderStats sos
JOIN suppliers s ON sos.supplier_id = s.supplier_id
WHERE sos.total_vendor_orders >= 10
ORDER BY vendor_return_rate_percentage DESC;
