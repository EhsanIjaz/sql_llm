prompt = """

### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION].
Follow ALL rules below EXACTLY. Deviations will cause errors.
Use SUM() instead of MAX() for aggregation.
Donot use SUM() instead of COUNT().

**Rules***
- Always filter queries by month and year if not specified in the question.
- For `productivity`, `assortment`, or `stockout`, USE COUNT() , Refer to Example 2 and 3."
- For "growth," "expansion," "grow," or "growing," us the logic in  Examples 4 and 5.

### Instructions
- If the schema cannot answer the question, return "I do not know."
- The database contains only `llm_df` with monthly customer data.
- Avoid `TO_DATE`, `CAST`, or `EXTRACT` functions for dates.
- Always use `SUM()` for `sales` , `mto`,`mro` and `targets` columns unless `AVG()`, MAX() or `MIN()` is explicitly requested (never default to `AVG()`).
- Interpret "worst" as 'lowest', "top/best/highest" as ORDER BY ... DESC, and "worst" as ORDER BY ... ASC.
- Always enforce a LIMIT, defaulting to 1.

- `mro` (Missed Revenue Opportunity): Also known as "Potential Improvement," "Missed Gain," "Untapped Potential," or "Lost Earnings."
- `mto` (Missed Target Opportunity): Also called "Sales Shortfall," "Performance Gap," or "Missed Goals," "highest target missed."
- `sales`: Simply "Contribution" or "Contributed" in sales terms.

### Database Schema
CREATE TABLE `llm_df` (
  `month` INTEGER, -- Month (1-12)
  `year` INTEGER, -- Year
  `region` VARCHAR(50), -- Top-level region
  `city` VARCHAR(50), -- City within the region
  `area` VARCHAR(50), -- Area within the city
  `territory` VARCHAR(50), -- Territory within the area
  `distributor` VARCHAR(50), -- Distributor in the territory
  `route` VARCHAR(50), -- Route within the distributor
  `customer` VARCHAR(50), -- Unique customer ID
  `sku` VARCHAR(50), -- SKU identifier
  `brand` VARCHAR(50), -- Brand name
  `variant` VARCHAR(50), -- SKU variant
  `packtype` VARCHAR(50), -- SKU packaging type
  `sales` DECIMAL, -- Net sales value
  `primary sales` DECIMAL, -- Primary sales value
  `target` DECIMAL, -- Target sales value
  `mto` DECIMAL, -- Missed Target Opportunity
  `productivity` INTEGER, -- Customer productivity (1 = productive, 0 = not productive)
  `mro` DECIMAL, -- Missed Revenue Opportunity
  `unproductive_mro` INTEGER -- Unproductive Missed Revenue Opportunity,
  `unassorted_mro` INTEGER -- Unassorted Missed Revenue Opportunity,
  `stockout_mro` INTEGER -- Stockout Missed Revenue Opportunity,
  `stockout` INTEGER, -- Customer Stockout status (1 = stockout, 0 = no stockout)
  `assortment` INTEGER, -- Customer Assortment status (1 = full, 0 = not available)
  PRIMARY KEY (`month`, `year`, `customer`, `sku`)
);

### Examples

Example 1:  
Question: "Which city has the highest sales in October?"  
```sql
SELECT region, city, 
  SUM(sales) AS total_sales
FROM llm_df
WHERE month = 10 AND year = 2024
GROUP BY region, city
ORDER BY total_sales DESC
LIMIT 1;
Example 2:
Question:"which distributor had worst productivity percentage in lahore city in september?"
sql```
SELECT region, city, area, territory, distributor,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 1 THEN customer END) AS productive_shops, 
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 0 THEN customer END) AS un_productive_shops,
  COUNT(DISTINCT customer) AS total_shops, 
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS productivity_percentage,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS unproductivity_percentage
FROM llm_df
WHERE city = 'lahore'
GROUP BY region, city, area, territory, distributor
ORDER BY unproductivity_percentage DESC  -- Worst productivity (highest unproductivity)
LIMIT 1;

Example 3:
Question: which routes in region 'north b' had the highest stockouts percentage in dec
SELECT region, city, area, territory, distributor, route,
  COUNT(DISTINCT CASE WHEN month = 12 AND year = 2024 AND stockout = 1 THEN customer END) AS stockout_shops,
  COUNT(DISTINCT CASE WHEN month = 12 AND year = 2024 AND stockout = 0 THEN customer END) AS not_stockout_shops,
  COUNT(DISTINCT customer) AS total_shops, 
  (COUNT(DISTINCT CASE WHEN month = 12 AND year = 2024 AND stockout = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS stockout_percentage,
  (COUNT(DISTINCT CASE WHEN month = 12 AND year = 2024 AND stockout = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS no_stockout_percentage
FROM llm_df
WHERE region = 'north b'
GROUP BY region, city, area, territory, distributor, route
ORDER BY stockout_percentage DESC
LIMIT 1;

Example 4:
Question: "what the growth of city lahore?"
```sql
SELECT region, city,
  SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) AS sales_current_month, 
  SUM(CASE WHEN month = 10 THEN sales ELSE 0 END) AS sales_previous_month,
  ((SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) - SUM(CASE WHEN month = 10 THEN sales ELSE 0 END)) 
  / NULLIF(SUM(CASE WHEN month = 10 THEN sales ELSE 0 END), 0)) * 100 AS sales_growth_percentage
FROM llm_df
WHERE city = 'lahore'
  AND year = 2024
  AND month IN (10, 11)
GROUP BY region, city;

Example 5:
Question: "Show me the 5 territories that have experienced the most significant growth."
```sql
SELECT region, city, area, territory,
  SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) AS sales_current_month, 
  SUM(CASE WHEN month = 10 THEN sales ELSE 0 END) AS sales_previous_month,
  (((SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) - SUM(CASE WHEN month = 10 THEN sales ELSE 0 END)) 
  / NULLIF(SUM(CASE WHEN month = 10 THEN sales ELSE 0 END), 0)) * 100) AS sales_growth_percentage
FROM llm_df
WHERE year = 2024 AND month IN (10, 11)
GROUP BY region, city, area, territory
ORDER BY sales_growth_percentage DESC
LIMIT 5;

Example 6:
Question : Which distributor had the highest total MTO in the 'South A' region in December 2024?
```sql
SELECT region, city, area, territory, distributor,
  SUM(mto) AS total_mto
FROM llm_df
WHERE region = 'south a'
  AND month = 12
  AND year = 2024
GROUP BY region, city, area, territory, distributor
ORDER BY total_mto DESC
LIMIT 1;

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]:
[SQL]
"""


prompt_2 = """

### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION].
Follow ALL rules below EXACTLY. Deviations will cause errors.
use COUNT() function not SUM().

**Rules***
- Always filter queries by month and year if not specified in the question.
- For `productivity`, `assortment`, or `stockout`, USE COUNT() , Refer to Example 2 and 3."
- The database contains only `llm_df` with monthly customer data.
- Avoid `TO_DATE`, `CAST`, or `EXTRACT` functions for dates.
- Interpret "worst" as 'lowest', "top/best/highest" as ORDER BY ... DESC, and "worst" as ORDER BY ... ASC.
- Always enforce a LIMIT, defaulting to 1.


### Database Schema
CREATE TABLE `llm_df` (
  `month` INTEGER, -- Month (1-12)
  `year` INTEGER, -- Year
  `region` VARCHAR(50), -- Top-level region
  `city` VARCHAR(50), -- City within the region
  `area` VARCHAR(50), -- Area within the city
  `territory` VARCHAR(50), -- Territory within the area
  `distributor` VARCHAR(50), -- Distributor in the territory
  `route` VARCHAR(50), -- Route within the distributor
  `customer` VARCHAR(50), -- Unique customer ID
  `sku` VARCHAR(50), -- SKU identifier
  `brand` VARCHAR(50), -- Brand name
  `variant` VARCHAR(50), -- SKU variant
  `packtype` VARCHAR(50), -- SKU packaging type
  `sales` DECIMAL, -- Net sales value
  `primary sales` DECIMAL, -- Primary sales value
  `target` DECIMAL, -- Target sales value
  `mto` DECIMAL, -- Missed Target Opportunity
  `productivity` INTEGER, -- Customer productivity (1 = productive, 0 = not productive)
  `mro` DECIMAL, -- Missed Revenue Opportunity
  `unproductive_mro` INTEGER -- Unproductive Missed Revenue Opportunity,
  `unassorted_mro` INTEGER -- Unassorted Missed Revenue Opportunity,
  `stockout_mro` INTEGER -- Stockout Missed Revenue Opportunity,
  `stockout` INTEGER, -- Customer Stockout status (1 = stockout, 0 = no stockout)
  `assortment` INTEGER, -- Customer Assortment status (1 = full, 0 = not available)
  PRIMARY KEY (`month`, `year`, `customer`, `sku`)
);

### Examples

Example 1:
Question: Which distributor had the lowest productivity percentage in Lahore city in September?
sql```
SELECT region, city, area, territory, distributor,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 1 THEN customer END) AS productive_shops,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 0 THEN customer END) AS un_productive_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS productive_percentage
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_productive_percentage
FROM llm_df
WHERE city = 'lahore'
GROUP BY region, city, area, territory, distributor
ORDER BY productive_percentage ASC
LIMIT 1;

Example 2:
Question: Which area had the highest unproductivity percentage in February 2024?
sql```
SELECT region, city, area,
  COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 1 THEN customer END) AS productive_shops,
  COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 0 THEN customer END) AS un_productive_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS productive_percentage
  (COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_productive_percentage
FROM llm_df
GROUP BY region, city, area
ORDER BY un_productive_percentage DESC
LIMIT 1;

Example 3:
Question: Which distributor had the best assortment percentage in June 2024?
sql```
SELECT region, city, area, territory, distributor,
  COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 1 THEN customer END) AS us_assorted_shops,
  COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 0 THEN customer END) AS assorted_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_assorted_percentage
  (COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS assorted_percentage
FROM llm_df
GROUP BY region, city, area, territory, distributor
ORDER BY un_assorted_percentage DESC
LIMIT 1;

Example 4:
Question: Which route had the worst unassorted percentage in September 2024?
sql```
SELECT region, city, area, territory, distributor, route,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 1 THEN customer END) AS un_assorted_shops,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 0 THEN customer END) AS assorted_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS assorted_percentage
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_assorted_percentage
FROM llm_df
GROUP BY region, city, area, territory, distributor, route
ORDER BY assorted_percentage DESC
LIMIT 1;

Example 5:
Question: Which distributor had the worst stockout percentage in May 2024?
sql```
SELECT region, city, area, territory, distributor,
  COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 1 THEN customer END) AS stockout_shops,
  COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 0 THEN customer END) AS not_stockout_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS stockout_percentage
  (COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS not_stockout_percentage
FROM llm_df
GROUP BY region, city, area, territory, distributor
ORDER BY stockout_percentage DESC
LIMIT 1;

Example 6:
Question: Which area had the highest not-stockout percentage in April
sql```
SELECT region, city, area,
  COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 1 THEN customer END) AS stockout_shops,
  COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 0 THEN customer END) AS not_stockout_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS stockout_percentage
  (COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS not_stockout_percentage
FROM llm_df
GROUP BY region, city, area
ORDER BY not_stockout_percentage DESC
LIMIT 1;

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]:
[SQL]
"""
