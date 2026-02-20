# IAP Payouts — Table Logic & Calculation Reference

> **Purpose:** Document the data sources, formulas, and business rules behind the IAP Payouts page.
> Use this as the spec for building automated tests.

---

## 1. Data Sources (BigQuery)

All tables live in `rcwl-data.powerbi_dashboard`.

| Table | Description | Key Columns |
|---|---|---|
| `d1_appstore_sales` | Apple App Store Connect daily sales reports | `sku`, `report_date`, `units`, `customer_price`, `developer_proceeds`, `customer_currency`, `product_type_identifier`, `title`, `subscription`, `period` |
| `d1_google_earnings` | Google Play earnings reports (ingested from GCS CSVs) | `application_name`, `month`, `transaction_type`, `amount_buyer`, `buyer_currency`, `product_title`, `sku_id` |
| `d1_inapp_products` | Product catalog (SKU → app name mapping) | `product_id`, `application_name`, `plan_type` |
| `d1_app_fee_lookup` | Per-app KLIQ fee percentage | `application_name`, `kliq_fee_pct` |

### 1.1 FX Rates

All amounts are converted to USD using a hardcoded FX rate table (inline CTE in each query). Rates are approximate spot rates. The same rate table is used across all queries for consistency.

Key rates: `GBP → 1.27`, `EUR → 1.08`, `AUD → 0.64`, `CAD → 0.72`.

### 1.2 App Name Normalisation

Google earnings app names may differ in casing from Apple (e.g. `Ladies Who Crunch` vs `Ladies who Crunch`). After loading, Google names are normalised to match Apple's canonical names using case-insensitive matching. Apple names are the source of truth (via `d1_inapp_products`).

---

## 2. Data Loading Queries

### 2.1 Apple Monthly Sales — `load_apple_monthly()`

```
Source:  d1_appstore_sales
Filter:  product_type_identifier IN ('IA1', 'IAY') AND customer_price_usd > 0
Join:    d1_inapp_products (sku → application_name)
```

**Output columns:** `application_name`, `month`, `total_units`, `sales`, `proceeds`

- **sales** = `SUM(customer_price * units * fx_rate)` — gross amount the customer paid, in USD
- **proceeds** = `SUM(developer_proceeds * units * fx_rate)` — what Apple reports as developer proceeds
- **total_units** = `SUM(units)` — number of transactions
- Rows with `units < 0` (refunds) are excluded here (handled separately)

### 2.2 Google Monthly Sales — `load_google_monthly()`

```
Source:  d1_google_earnings
Filter:  transaction_type = 'Charge' AND application_name IS NOT NULL
```

**Output columns:** `application_name`, `month`, `total_units`, `sales`, `proceeds`

- **sales** = `SUM(amount_buyer * fx_rate)` — post-tax amount charged to buyer, in USD
- **proceeds** = `sales * 0.70` — estimated developer proceeds after 30% platform fee
- **total_units** = `COUNT(*)` — number of charge transactions
- Google `amount_buyer` is already the post-tax amount (tax is deducted before the charge)

### 2.3 Apple Refunds — `load_apple_refunds()`

```
Source:  d1_appstore_sales
Filter:  product_type_identifier IN ('IA1', 'IAY') AND units < 0
```

**Output columns:** `application_name`, `month`, `refund_units`, `refund_amount`

- **refund_units** = `SUM(units)` — negative values (count of refunded transactions)
- **refund_amount** = `ABS(SUM(customer_price * units * fx_rate))` — absolute USD value of refunds
- Identified by negative `units` in Apple sales reports

### 2.4 Google Refunds — `load_google_refunds()`

```
Source:  d1_google_earnings
Filter:  transaction_type = 'Charge refund' AND application_name IS NOT NULL
```

**Output columns:** `application_name`, `month`, `refund_units`, `refund_amount`

- **refund_units** = `COUNT(*)` — number of refund transactions
- **refund_amount** = `ABS(SUM(amount_buyer * fx_rate))` — absolute USD value of refunds
- Identified by `transaction_type = 'Charge refund'` in Google earnings

### 2.5 Fee Lookup — `load_fee_lookup()`

```
Source:  d1_app_fee_lookup
```

**Output columns:** `application_name`, `kliq_fee_pct`

- Each app has a configured KLIQ fee percentage (e.g. 35.0 means 35%)
- Apps not in this table default to 0% KLIQ fee

### 2.6 Apple Product Details — `load_apple_product_details()`

```
Source:  d1_appstore_sales
Filter:  product_type_identifier IN ('IA1', 'IAY') AND units > 0
Group:   application_name, month, sku, title, subscription, period
```

**Output columns:** `application_name`, `month`, `product_id`, `product_name`, `sub_type`, `period`, `units`, `revenue_usd`

- **sub_type** = `New` or `Renewal` (from Apple's `subscription` field)
- **period** = `1 Month`, `7 Days`, `6 Months`, `1 Year` etc.
- **revenue_usd** = `SUM(customer_price * units * fx_rate)`

### 2.7 Google Product Details — `load_google_product_details()`

```
Source:  d1_google_earnings
Filter:  transaction_type = 'Charge' AND application_name IS NOT NULL
Group:   application_name, month, sku_id, product_title
```

**Output columns:** `application_name`, `month`, `product_id`, `product_name`, `sub_type`, `period`, `units`, `revenue_usd`

- **sub_type** = always `'Purchase'` (Google doesn't distinguish new vs renewal in earnings)
- **period** = derived from SKU ID pattern: `%monthly%` → `1 Month`, `%quarterly%` → `3 Months`, `%yearly%` → `1 Year`, else `Other`
- **revenue_usd** = `SUM(amount_buyer * fx_rate)`

---

## 3. Calculation Logic — `compute_breakdown()`

This function takes raw sales data for one platform and computes the full financial breakdown.

**Inputs:**
- `df_platform` — raw sales data (from `load_apple_monthly` or `load_google_monthly`)
- `fee_lookup` — KLIQ fee percentages per app
- `platform_fee_pct` — platform fee percentage (30.0 for both Apple and Google)
- `platform_name` — `"Apple"` or `"Google"`
- `refunds_df` — refund data (optional)

**Steps:**

```
1. MERGE sales with fee_lookup on application_name (LEFT JOIN)
2. platform_fee     = sales × (platform_fee_pct / 100)         # 30% of gross sales
3. proceeds         = sales − platform_fee                      # net after platform fee
4. kliq_fee_pct     = from fee_lookup (default 0 if not found)
5. kliq_fee         = sales × (kliq_fee_pct / 100)             # KLIQ % of GROSS sales
6. refund_amount    = merged from refunds_df (default 0)
7. refund_units     = merged from refunds_df (default 0)
8. payout           = sales − platform_fee − kliq_fee − refund_amount
```

### Key Business Rules

| Rule | Detail |
|---|---|
| **Platform fee** | 30% for both Apple and Google, applied to gross sales |
| **KLIQ fee** | Calculated on **gross sales** (before platform fee deduction) |
| **Refunds** | Deducted from payout at face value |
| **Payout formula** | `Payout = Sales − Platform Fee − KLIQ Fee − Refunds` |

### Example Calculation

```
App:            Livinia
Month:          2026-01
Apple Sales:    $754.70  (23 units)
Google Sales:   $164.95  (5 units)
KLIQ Fee %:     35%

Apple Platform Fee:  $754.70 × 0.30 = $226.41
Google Platform Fee: $164.95 × 0.30 = $49.49
Total Platform Fee:  $275.90

KLIQ Fee:  ($754.70 + $164.95) × 0.35 = $321.88

Apple Refunds:  $0.00
Google Refunds: $0.00

Total Payout = ($754.70 + $164.95) − $275.90 − $321.88 − $0.00 = $321.87
```

---

## 4. Pivot Table (Month-by-Month Breakdown)

The pivot table shows Apple and Google side-by-side for each app in the selected month.

### Columns

| Column | Source | Formula |
|---|---|---|
| App | `application_name` | — |
| KLIQ % | `kliq_fee_pct` | From fee lookup |
| Apple Sales | `sales` (Apple) | Gross customer price in USD |
| Apple Fee (30%) | `platform_fee` (Apple) | `Apple Sales × 0.30` |
| Apple KLIQ Fee | `kliq_fee` (Apple) | `Apple Sales × KLIQ%` |
| Apple Refunds | `refund_amount` (Apple) | Absolute refund value |
| Apple Payout | `payout` (Apple) | `Sales − Fee − KLIQ − Refunds` |
| Google Sales | `sales` (Google) | Post-tax buyer amount in USD |
| Google Fee (30%) | `platform_fee` (Google) | `Google Sales × 0.30` |
| Google KLIQ Fee | `kliq_fee` (Google) | `Google Sales × KLIQ%` |
| Google Refunds | `refund_amount` (Google) | Absolute refund value |
| Google Payout | `payout` (Google) | `Sales − Fee − KLIQ − Refunds` |
| Total Payout | computed | `Apple Payout + Google Payout` |
| Refund Flag | computed | `⚠️` if any refund > 0, else blank |

### Pivot Construction

1. Filter `combined` dataframe by `selected_month`
2. Split into `apple_df` (platform == "Apple") and `google_df` (platform == "Google")
3. Rename columns with platform prefix
4. Outer merge on `application_name`
5. Fill NaN with 0 for money columns
6. Compute `Total Payout = Apple Payout + Google Payout`
7. Sort descending by Total Payout

---

## 5. KPI Cards

The 5 top-level KPI cards show aggregated totals for the **selected month** (or all time if "All Months" is selected):

| Card | Value | Description |
|---|---|---|
| `{month} Sales` | `SUM(sales)` | Gross customer price across both platforms |
| Platform Fees | `SUM(platform_fee)` | Total 30% platform deductions |
| KLIQ Fee | `SUM(kliq_fee)` | Total KLIQ fee across all apps |
| Refunds | `SUM(refund_amount)` | Total customer refunds |
| Coach Payout | `SUM(payout)` | Net payout after all deductions |

---

## 6. PDF Receipt — `generate_receipt_pdf()`

Each app gets a downloadable PDF receipt for the selected month.

### Line Items

| Row | Value |
|---|---|
| Google Playstore | `google_units` × `unit_price` = `google_sales` |
| Apple Appstore | `apple_units` × `unit_price` = `apple_sales` |
| *(blank separator)* | |
| Subtotal | `apple_sales + google_sales` |
| Platform Fees (30%) | `−(subtotal × 0.30)` |
| KLIQ Fee — *Gross Sales X%* | `−(subtotal × kliq_fee_pct / 100)` |
| Refunds *(if > 0)* | `−(apple_refunds + google_refunds)` |
| **Total Payout** | Passed from the table calculation |

### Product & Subscription Breakdown

Below the main line items, the PDF includes a per-SKU breakdown table (if product data exists):

| Column | Source |
|---|---|
| Platform | `Apple` or `Google` |
| Product | Product name / title |
| Type | `New`, `Renewal`, or `Purchase` |
| Period | `1 Month`, `3 Months`, `1 Year`, etc. |
| Units | Transaction count |
| Revenue | USD amount |

---

## 7. Filter Behaviour

| Filter | Affects | Does NOT affect |
|---|---|---|
| **Month** (selectbox) | KPI cards, pivot table, product details, PDF receipts | Monthly trend chart, App Summary, Top 15 chart |
| **App** (multiselect) | Everything (KPI, chart, table, products, summary, top 15) | — |
| **Platform** (radio) | Everything | — |
| **Refresh** (button) | Clears `st.cache_data` and reruns | — |

Default month selection: latest available month (index=1 in dropdown, index=0 is "All Months").

---

## 8. Data Refresh Pipeline

| Source | Refresh Function | Table Written |
|---|---|---|
| Apple App Store Connect API | `refresh_d1_appstore_sales()` | `d1_appstore_sales` |
| Google Play GCS earnings CSVs | `refresh_d1_google_earnings()` | `d1_google_earnings` |
| KLIQ prod_dataset events | `refresh_d1_inapp_purchases()` | `d1_inapp_products` |
| Manual config | — | `d1_app_fee_lookup` |

Run with: `/opt/anaconda3/envs/nhs-env/bin/python refresh_dashboard.py`

Streamlit caches query results for 600 seconds (10 minutes). Use the 🔄 Refresh button to force a cache clear.

---

## 9. Test Scenarios (for automation)

### 9.1 Data Integrity

- [ ] Apple sales query returns rows with `total_units > 0` and `sales > 0`
- [ ] Google sales query returns rows with `total_units > 0` and `sales > 0`
- [ ] No duplicate app names in the combined dataset (case-insensitive)
- [ ] All apps in fee_lookup exist in sales data
- [ ] Refund amounts are always ≥ 0

### 9.2 Calculation Accuracy

- [ ] `platform_fee == sales × 0.30` for every row (both platforms)
- [ ] `kliq_fee == sales × kliq_fee_pct / 100` for every row
- [ ] `payout == sales − platform_fee − kliq_fee − refund_amount` for every row
- [ ] `Total Payout == Apple Payout + Google Payout` in pivot table
- [ ] KPI card totals match sum of pivot table column totals

### 9.3 Filter Behaviour

- [ ] Selecting a month updates KPI cards to show only that month's data
- [ ] Selecting a month updates pivot table to show only that month's apps
- [ ] Selecting "All Months" shows all-time totals in KPI cards
- [ ] App filter restricts all sections to selected apps
- [ ] Platform filter restricts all sections to selected platform
- [ ] Monthly trend chart always shows all months (not filtered by month selectbox)
- [ ] App Summary and Top 15 always show all-time data

### 9.4 PDF Receipt

- [ ] PDF generates without error for every app in the pivot table
- [ ] Subtotal in PDF == Apple Sales + Google Sales
- [ ] Platform Fees in PDF == Subtotal × 0.30
- [ ] KLIQ Fee in PDF == Subtotal × kliq_fee_pct / 100
- [ ] Total Payout in PDF matches pivot table Total Payout
- [ ] Refund row appears only when refunds > 0
- [ ] Product breakdown table appears when product data exists for the app/month
- [ ] Product breakdown revenue sums match the platform sales totals (approximately, due to rounding)

### 9.5 Edge Cases

- [ ] App with Apple sales but no Google sales shows Google columns as $0.00
- [ ] App with Google sales but no Apple sales shows Apple columns as $0.00
- [ ] App with 0% KLIQ fee shows $0.00 KLIQ fee
- [ ] Month with no data shows "No data for the selected filters" message
- [ ] Refund flag (⚠️) appears only on rows where refund_amount > 0
